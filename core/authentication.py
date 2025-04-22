from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.tokens import AccessToken
from django.conf import settings

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
            user = self.get_user(validated_token)

            if user.is_active:
                return user, validated_token

            comment = (
                user.comment or "Esta conta foi desativada por tempo indeterminado."
            )
            raise PermissionDenied(comment)

        except:
            raise AuthenticationFailed("O token é inválido ou expirou.")
