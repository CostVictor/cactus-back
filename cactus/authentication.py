from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings

from .core.view import SCView


class SCAuthentication(JWTAuthentication):
    """Autenticação de usuário do sistema cactus através de JWT em Cookies HttpOnly."""

    def authenticate(self, request):
        """Valida se o usuário está autenticado."""

        # Obtem o token de acesso (access_token).
        token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE"])

        if token is None:
            AuthenticationFailed("Acesso negado: token não encontrado.")

        try:
            validated_token = AccessToken(token)
            return self.get_user(validated_token), validated_token

        except:
            raise AuthenticationFailed(f"Acesso negado: O token é inválido ou expirou")

    def has_permission(self, request, view):
        """Retorna se o usuário possui permição para acessar a view."""

        # Verifica se o usuário está autenticado.
        user, _ = self.authenticate(request)

        # Verifica se a view atual herda `SCView` para execução do método de validação de acesso.
        if issubclass(view.__class__, SCView):
            validated = view.validate_before_access(user)
            if not validated:
                raise AuthenticationFailed(
                    f"Você não tem autorização para acessar este recurso."
                )

        return True
