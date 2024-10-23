from rest_framework.request import Request
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .utils import generate_response_with_cookie
from .serializers import LoginSerializer


class LoginView(APIView):
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


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            raise Response(
                {"detail": "O token de atualização é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
    """Atualiza os tokens de acesso.
    O token de refresh tem validade para apenas um uso.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request: Request, *args, **kwargs) -> Response:
        return super().post(request, *args, **kwargs)
