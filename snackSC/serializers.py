from cactus.core.serializers import SCSerializer
from rest_framework import serializers
from django.db import transaction

from .models import Snack_category, Description, Snack


class SnackSerializer(SCSerializer):
    class Meta:
        model = Snack
        fields = [
            "name",
            "quantity_in_stock",
            "price",
            "description",
            "path_img",
        ]

    def validate_quantity_in_stock(self, value):
        # O mínimo existente no estoque deve ser 0.
        if value < 0:
            raise serializers.ValidationError(
                "A quantidade no estoque não pode ser menor que zero (0)."
            )

        return value

    def validate_price(self, value):
        # Verifica a existência de preços negativos.
        if value <= 0:
            raise serializers.ValidationError(
                "O valor do preço deve ser maior que zero (0)."
            )

        return value

    def validate_category(self, value):
        """Valida a existência de uma categoria com o nome fornecido e a retorna."""

        category = Snack_category.objects.filter(name=value)

        if not category:
            raise serializers.ValidationError(
                f'Nenhuma categoria "{value}" foi encontrada.'
            )

        return category.first()

    def create(self, validated_data):
        category = validated_data.pop("category")

        new_Snack = Snack(**validated_data)
        new_Snack.category = category.id
        new_Snack.save()

        return new_Snack


class DescriptionSerializer(SCSerializer):
    category = serializers.CharField(source="category.name")

    class Meta:
        fields = ["title", "text", "illustration_url", "category"]
        model = Description

    def validate(self, attrs):
        name_category = self.category.lower()
        title_description = attrs["title"].lower()

        # Verifica se no título da descrição não possui o nome da categoria e retorna erro.
        if name_category not in title_description:
            raise serializers.ValidationError(
                "O título da descrição deve incluir o nome da categoria."
            )

        return attrs


class CategorySerializer(SCSerializer):
    # Obtem todos os produtos relacionados à categoria.
    snacks = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        fields = ["name", "path_img", "snacks", "description"]
        model = Snack_category

    def get_snacks(self, obj):
        """Obtem todos os produtos relacionados à categoria e ordena pelo nome."""

        snacks = obj.snacks.all().order_by("name")
        return SnackSerializer(snacks, many=True).data

    def get_description(self, obj):
        """Obtem a descrição da categoria."""

        if hasattr(obj, "description"):
            return DescriptionSerializer(
                obj.description, remove_field=["category"]
            ).data

        return None

    def create(self, validated_data):
        """Cria uma nova categoria vazia."""

        active_category_count = Snack_category.objects.filter(
            deletion_date=None
        ).count()

        with transaction.atomic():
            new_category = Snack_category(**validated_data)

            # Define a categoria como última posição antes de salvar.
            new_category.position_order = active_category_count + 1
            new_category.save()

            description = Description(
                title=f"Venha experimentar nossos {new_category.name}!",
                text=f"Nossos {new_category.name.lower()} são preparados com ingredientes de qualidade, garantindo um sabor irresistível a cada mordida.",
                category=new_category,
            )
            description.save()

        return new_category
