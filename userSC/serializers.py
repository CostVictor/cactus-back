from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email
from django.db import transaction
from rest_framework import serializers
from .models import User, User_details
from .variables import cities
import re


class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User_details
        fields = ["tel", "city", "state", "path_img_profile"]

    def validate_tel(self, value):
        # Define a regex para o formato (99) 99999-9999
        pattern = r"^\(\d{2}\) \d{5}-\d{4}$"

        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "O telefone deve estar no formato (99) 99999-9999."
            )

        return value

    def validate_city(self, value):
        # Verifica se o valor está entre os peritidos.
        if value not in cities:
            raise serializers.ValidationError(
                "Por favor, selecione uma opção de cidade válida."
            )

        return value


class UserSerializer(serializers.ModelSerializer):
    user_details = UserDetailsSerializer()

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
                "Por favor, defina um nome de usuário que facilite sua identificação."
            )

        if User.objects.filter(name=value):
            raise serializers.ValidationError(
                "Este nome de usuário já está em uso. Por favor, defina um nome que facilite sua identificação."
            )

        return value

    def validate_email(self, value):
        # Verifica se o email está no padrão válido. Caso contrário, retorna erro.
        validate_email(value)

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

        return make_password(value)

    def create(self, validated_data):
        """Cria o usuário e sua tabela de detalhes."""
        with transaction.atomic():
            userDetails = validated_data.pop("user_details")

            user = User(**validated_data)
            user.save()

            details = UserDetailsSerializer(data=userDetails)
            details.is_valid(raise_exception=True)
            details.save(sc_user=user)

        return user

    def update(self, instance, validated_data): ...

    def delete(self, validated_data): ...
