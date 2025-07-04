from rest_framework.exceptions import (
    AuthenticationFailed,
    ValidationError,
    PermissionDenied,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework import status

from core.view import SCView
from apps.user.models import User

from .serializers import LoginSerializer
from .utils import generate_response_with_cookie


class LoginView(SCView):
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        if not user.is_active:
            comment = (
                user.comment or "Esta conta foi desativada por tempo indeterminado."
            )
            raise PermissionDenied(comment)

        new_token = RefreshToken.for_user(user)
        data = {
            "username": user.username,
            "role": "employee" if user.is_employee else "client",
        }

        return generate_response_with_cookie(new_token, data)


class LogoutView(SCView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            raise ValidationError("O token de atualização é obrigatório.")

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        serializer.is_valid()

        return Response(
            {
                "message": "Sua conta foi desconectada com sucesso.",
            },
            status=status.HTTP_200_OK,
        )


class RefreshView(SCView):
    """
    Atualiza os tokens de acesso.
    O token de refresh tem validade para apenas um uso.
    """

    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request) -> Response:
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            raise AuthenticationFailed("O token de atualização é obrigatório.")

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})

        try:
            # Validação e rotação do token
            serializer.is_valid(raise_exception=True)
        except:
            raise AuthenticationFailed("O token de atualização é inválido.")

        new_refresh = RefreshToken(serializer.validated_data["refresh"])
        # Obtém o user_id do refresh token para verificar o usuário
        user = User.objects.filter(id=new_refresh["user_id"]).first()

        if not user or not user.is_active:
            comment = (
                user.comment
                if user and user.comment
                else "Esta conta foi desativada por tempo indeterminado."
            )
            raise PermissionDenied(comment)

        data = {"message": "Tokens atualizados."}
        return generate_response_with_cookie(new_refresh, data)
