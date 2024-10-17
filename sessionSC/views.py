from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, LogoutSerializer


class LoginView(APIView):
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
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data.get("refresh_token")

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

        except Exception as e:
            raise serializers.ValidationError(
                f"{e}", status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "title": "Logout Efetuado",
                "text": "Sua conta foi desconectada com sucesso.",
            },
            status=status.HTTP_200_OK,
        )
