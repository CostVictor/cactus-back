from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.exceptions import AuthenticationFailed
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

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        data = {
            "username": user.username,
            "role": "employee" if user.is_employee else "client",
        }

        return generate_response_with_cookie(refresh, data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            raise Response(
                {"detail": "O token de atualização é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh_token = auth_header.split()[1]
        try:
            refresh_token.blacklist()
            # access_token.blacklist()

        except Exception as e:
            raise Response(
                {"detail": f"{e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

    def post(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            raise Response(
                {"detail": "O token de atualização é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        print(auth_header)

        refresh_token = auth_header.split()[1]
        try:
            # Valida o token de refresh.
            validated_token = self.get_token(refresh_token)
            user = validated_token["user"]

            new_refresh_token = RefreshToken.for_user(user)
            return generate_response_with_cookie(
                new_refresh_token, {"message": "Token atualizado."}
            )

        except Exception as e:
            raise AuthenticationFailed(f"{e}")
