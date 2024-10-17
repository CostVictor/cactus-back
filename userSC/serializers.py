from django.db import transaction
from rest_framework import serializers
from .models import User, User_details


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
            "password_hash",
            "is_employee",
            "deletion_date",
            "user_details",
        ]

    def validate_name(self, value): ...

    def validate_email(self, value): ...

    def validate_password_hash(self, value): ...

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
