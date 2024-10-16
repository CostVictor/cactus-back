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

    def create(self, validated_data): ...

    def update(self, instance, validated_data): ...

    def delete(self, validated_data): ...
