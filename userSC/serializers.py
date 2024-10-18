from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from django.db import transaction
from rest_framework import serializers
from .models import User, User_details
import re


class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User_details
        fields = ["tel", "city", "state", "path_img_profile"]


class UserSerializer(serializers.ModelSerializer):
    user_details = UserDetailsSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "password",
            "user_details",
        ]

    def validate_name(self, value):
        if len(value) < 10:
            raise serializers.ValidationError(
                "Por favor, defina um nome que facilite sua identificação."
            )

        if User.objects.filter(name=value):
            raise serializers.ValidationError(
                "Este nome já está em uso. Por favor, defina um nome que facilite sua identificação."
            )

        return value

    def validate_email(self, value):
        try:
            # Verifica se o email está no padrão válido.
            validate_email(value)
        except Exception as e:
            raise serializers.ValidationError(f"E-mail inválido: {e}")

        return value

    def validate_password(self, value):
        try:
            # Valida a senha com as regras definidas em 'Settings.py'.
            validate_password(value)
        except Exception as e:
            raise serializers.ValidationError(f"Senha inválida: {e}")

        # Verifica se a senha contém pelo menos um símbolo (Django não oferece por padrão).
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise serializers.ValidationError(
                "Senha inválida: A senha deve conter pelo menos um caractere especial."
            )

        return value

    def create(self, validated_data):
        """Cria o usuário e sua tabela de detalhes."""
        with transaction.atomic():
            userDetails = validated_data.pop("user_details")
            user = User(**validated_data)
            user.set_password(validated_data["password"])
            user.save()

            User_details.objects.create(id=user.id, **userDetails)

        return user

    def update(self, instance, validated_data): ...

    def delete(self, validated_data): ...
