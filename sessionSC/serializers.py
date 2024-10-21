from rest_framework.exceptions import AuthenticationFailed
from rest_framework import serializers
from userSC.models import User


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                attrs["user"] = user
                return attrs
        except:
            pass

        # Retorna erro caso o usuário não exista ou se a senha estiver incorreta.
        raise AuthenticationFailed(
            "Credenciais inválidas. Por favor, tente novamente.",
        )
