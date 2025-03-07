from rest_framework.throttling import ScopedRateThrottle
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .serializers import UserSerializer
from .models import User


class RegisterView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request):
        """Cria um novo usuário."""

        data = request.data

        # Valida se o `email` já existe.
        if User.objects.filter(email=data["email"]):
            raise PermissionDenied("Este e-mail já está em uso.")

        # Valida se o `username` já existe.
        if User.objects.filter(username=data["username"]):
            raise PermissionDenied(
                "Este nome de usuário já está em uso. Por favor, defina um nome que facilite sua identificação."
            )

        serializer = UserSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Garante que todos os mecanismos de ADM sejam revogados.
        serializer.save(is_employee=False, is_staff=False, is_superuser=False)

        return Response(
            {"message": "A conta foi cadastrada com sucesso."},
            status=status.HTTP_201_CREATED,
        )
