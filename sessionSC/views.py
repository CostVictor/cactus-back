from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import LoginSerializer, LogoutSerializer


class LoginView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data.get("refresh_token")
        access_token = serializer.validated_data.get("access_token")

        try:
            refresh_token.blacklist()
            access_token.blacklist()

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

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            raise Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Valida o token de refresh.
            validated_token = self.get_token(refresh_token)
            user = validated_token["user"]

            new_refresh_token = RefreshToken.for_user(user)
            return Response(
                {
                    "refresh": str(new_refresh_token),
                    "access": str(new_refresh_token.access_token),
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            raise AuthenticationFailed(f"{e}")
