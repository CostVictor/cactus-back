from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .serializers import UserSerializer


class RegisterView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request):
        """Cria um novo usuário."""

        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Garante que todos os mecanismos de ADM sejam revogados.
        # serializer.save(is_employee=False, is_staff=False, is_superuser=False)

        # Remover em produção!!
        serializer.save(is_employee=True, is_staff=True, is_superuser=True)
        # ~

        return Response(
            {"message": "A conta foi cadastrada com sucesso."},
            status=status.HTTP_201_CREATED,
        )
