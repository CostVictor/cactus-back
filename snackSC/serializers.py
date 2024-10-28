from cactus.core.serializers import SCSerializer
from rest_framework import serializers

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

    def validate_quantity_in_stock(value):
        # O mínimo existente no estoque deve ser 0.
        if value < 0:
            raise serializers.ValidationError(
                "A quantidade no estoque não pode ser menor que zero (0)."
            )

        return value

    def validate_price(value):
        # Verifica a existência de preços negativos.
        if value <= 0:
            raise serializers.ValidationError(
                "O valor do preço deve ser maior que zero (0)."
            )

        return value

    def validate_category(value):
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
        new_Snack.save(category=category.id)

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

        return DescriptionSerializer(obj.description, remove_field=["category"]).data

    def create(self, validated_data):
        """Cria uma nova categoria vazia."""

        active_category_count = Snack_category.objects.filter(
            deletion_date=None
        ).count()

        new_category = Snack_category(**validated_data)

        # Salva a categoria nova como última posição.
        new_category.save(position_order=active_category_count + 1)

        return new_category
