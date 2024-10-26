from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework import status

from cactus.core.view import SCView
from cactus.core.authentication import SCAuthentication
from .utils import generate_response_with_cookie
from .serializers import LoginSerializer


class LoginView(SCView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prev_token = request.COOKIES.get("refresh_token")
        if prev_token:
            try:
                invalid_token = RefreshToken(prev_token)
                invalid_token.blacklist()
            except:
                # O token já é inválido.
                pass

        user = serializer.validated_data["user"]
        new_token = RefreshToken.for_user(user)
        data = {
            "username": user.username,
            "role": "employee" if user.is_employee else "client",
        }

        return generate_response_with_cookie(new_token, data)


class LogoutView(SCView):
    permission_classes = [SCAuthentication]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            raise ValidationError("O token de atualização é obrigatório.")

        try:
            invalid_token = RefreshToken(refresh_token)
            invalid_token.blacklist()

        except:
            # O token já é inválido.
            pass

        return Response(
            {
                "message": "Sua conta foi desconectada com sucesso.",
            },
            status=status.HTTP_200_OK,
        )


class RefreshView(TokenRefreshView):
    """
    Atualiza os tokens de acesso.
    O token de refresh tem validade para apenas um uso.
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request) -> Response:
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            raise ValidationError("O token de atualização é obrigatório.")

        try:
            # Revogação do token de atualização anterior.
            prev_token = RefreshToken(refresh_token)
            prev_token.blacklist()

            user = prev_token.user
            new_refresh_token = RefreshToken.for_user(user)

            data = {"message": "Tokens atualizados."}
            return generate_response_with_cookie(new_refresh_token, data)

        except:
            # O token de atualização é inválido (O usuário terá que fazer login novamente).
            raise AuthenticationFailed("O token de atualização é inválido.")
