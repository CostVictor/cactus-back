from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.tokens import AccessToken
from django.conf import settings

from .view import SCView
from apps.user.models import User


class SCAuthenticationHttp(JWTAuthentication):
    """Autenticador de usuário do sistema cactus através de
    JWT em Cookies HttpOnly (Deve ser utilizado em views que herdem `SCView`)."""

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
        """Retorna se o usuário possui permição para acessar o método da view."""

        method = request.method.lower()

        # Verifica se a view atual herda `SCView` para execução do método de validação de acesso.
        if (
            issubclass(view.__class__, SCView)
            and method not in view.ignore_validation_for_methods
        ):
            # Verifica se o usuário está autenticado.
            user, _ = self.authenticate(request)

            if not view.validate_before_access(user, method):
                raise PermissionDenied("Usuário não autorizado.")

        return True
