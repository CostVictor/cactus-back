from rest_framework import serializers
from django.contrib.auth import authenticate


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(email=email, password_hash=password)
        if user is None:
            raise serializers.ValidationError(
                "Credenciais inválidas. Por favor, tente novamente."
            )

        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    email = serializers.CharField()

    def validate(self, attrs):
        refresh_token = attrs.get("refresh_token")

        if refresh_token is None:
            raise serializers.ValidationError("Não foi possível identificar o usuário.")

        return attrs
