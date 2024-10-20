from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.hashers import check_password
from userSC.models import User


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            # Verifica se o usuário existe.
            user = User.objects.get(email=email)

            # Valida a senha.
            if check_password(password, user.password):
                attrs["user"] = user

                return attrs
        except:
            pass

        # Retorna erro caso o usuário não exista ou se a senha estiver incorreta.
        raise AuthenticationFailed(
            "Credenciais inválidas. Por favor, tente novamente.",
        )


class LogoutSerializer(serializers.Serializer):
    def validate(self, attrs):
        refresh_token = attrs.get("refresh_token")

        if refresh_token is None:
            raise serializers.AuthenticationFailed(
                "Não foi possível identificar o token do usuário.",
            )

        return attrs
