from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.tokens import AccessToken
from django.conf import settings

from .view import SCView
from userSC.models import User


class SCAuthenticationHttp(JWTAuthentication):
    """Autenticação de usuário do sistema cactus através de JWT em Cookies HttpOnly."""

    def authenticate(self, request) -> tuple[User, AccessToken]:
        """Valida se o usuário está autenticado."""

        # Obtem o token de acesso (access_token).
        token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE"])

        if token is None:
            raise AuthenticationFailed("O token não foi encontrado.")

        try:
            validated_token = AccessToken(token)
            return self.get_user(validated_token), validated_token

        except:
            raise AuthenticationFailed("O token é inválido ou expirou.")

    def has_permission(self, request, view):
        """Retorna se o usuário possui permição para acessar a view."""

        # Verifica se o usuário está autenticado.
        user, _ = self.authenticate(request)

        # Verifica se a view atual herda `SCView` para execução do método de validação de acesso.
        if issubclass(view.__class__, SCView):
            validation_methods = {
                "get": view.validate_get_before_access,
                "post": view.validate_post_before_access,
                "put": view.validate_put_before_access,
                "patch": view.validate_patch_before_access,
                "delete": view.validate_delete_before_access,
            }

            # Validação global para a view.
            validated_all = view.validate_before_access(user)

            # Obtem o método da request.
            request_method = request.method.lower()
            method_current = validation_methods.get(request_method)
            validated_for_method = False

            # Validação do método corrente.
            if method_current is not None:
                validated_for_method = method_current(user)

            if not validated_all or not validated_for_method:
                raise PermissionDenied("Usuário não autorizado.")

        return True
