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


class LogoutSerializer(serializers.Serializer):
    def validate(self, attrs):
        refresh_token = attrs.get("refresh")
        access_token = attrs.get("access")

        if refresh_token is None or access_token is None:
            raise serializers.AuthenticationFailed(
                "Não foi possível identificar o token do usuário.",
            )

        attrs["refresh_token"] = refresh_token
        attrs["access_token"] = access_token

        return attrs
