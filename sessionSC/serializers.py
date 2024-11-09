from rest_framework.exceptions import AuthenticationFailed
from rest_framework import serializers
from userSC.models import User

from .variables import restrictions


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = User.objects.filter(email=email).first()
        if user is None or not user.check_password(password):
            # Retorna erro caso o usuário não exista ou se a senha estiver incorreta.
            raise AuthenticationFailed(
                "Credenciais inválidas. Por favor, tente novamente.",
            )

        attrs["user"] = user
        return attrs


class CheckAuthSerializer(serializers.Serializer):
    restriction = serializers.CharField(max_length=8)

    def validate(self, attrs):
        restriction = attrs.get("restriction")

        if not restriction:
            raise serializers.ValidationError(
                "O nível de restrição do acesso é obrigatório."
            )

        if restriction not in restrictions:
            raise serializers.ValidationError("A restrição fornecida não é válida.")

        return attrs
