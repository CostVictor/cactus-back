from rest_framework import status, serializers
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import UserSerializer
from .models import User


class RegisterView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request):
        data = request.data

        if User.objects.filter(email=data["email"]):
            raise serializers.ValidationError("Este e-mail já está em uso.")

        serializer = UserSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(is_employee=False)

        return Response(
            {"message": "A conta foi cadastrada com sucesso."},
            status=status.HTTP_201_CREATED,
        )
