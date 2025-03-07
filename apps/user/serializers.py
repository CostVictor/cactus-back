from django.core.validators import validate_email
from core.serializers import SCSerializer
from django.db import transaction
from rest_framework import serializers
import re

from .models import User, UserDetails
from .variables import cities


class UserDetailsSerializer(SCSerializer):
    class Meta:
        model = UserDetails
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


class UserSerializer(SCSerializer):
    user_details = UserDetailsSerializer()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "user_details"]

    def validate_username(self, value):
        if len(value) < 10:
            raise serializers.ValidationError(
                "Por favor, defina um nome de usuário que facilite sua identificação."
            )

        return value

    def validate_email(self, value):
        # Verifica se o email está no padrão válido. Caso contrário, retorna erro.
        validate_email(value)

        return value

    def create(self, validated_data):
        """Cria o usuário e sua tabela de detalhes."""
        with transaction.atomic():
            userDetails = validated_data.pop("user_details")
            password = validated_data.pop("password")

            user = User(**validated_data)
            user.set_password(password)
            user.save()

            details = UserDetailsSerializer(data=userDetails)
            details.is_valid(raise_exception=True)
            details.save(user=user)

        return user
