from cactus.core.serializers import BaseWithNotIncludeField
from rest_framework import serializers
from django.db.models import Count

from .models import Product_category, Product


class ProductSerializer(BaseWithNotIncludeField):
    category = serializers.CharField(source="Product_category.name")

    class Meta:
        model = Product
        fields = [
            "name",
            "quantity_in_stock",
            "price",
            "description",
            "path_img",
            "category",
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

        category = Product_category.objects.filter(name=value)

        if not category:
            raise serializers.ValidationError(
                f'Nenhuma categoria "{value}" foi encontrada.'
            )

        return category.first()

    def create(self, validated_data):
        category = validated_data.pop("category")
        new_product = Product(**validated_data)
        new_product.save(category=category.id)

        return new_product


class CategorySerializer(BaseWithNotIncludeField):
    # Obtem todos os produtos relacionados à categoria.
    products = ProductSerializer(many=True)

    class Meta:
        model = Product_category
        fields = ["name", "position_order", "path_img", "products"]

    def create(self, validated_data):
        """Cria uma nova categoria sem incluir nenhum produto."""

        count_categories = Product_category.objects.aggregate(
            total_categorias=Count("id")
        )

        new_category = Product_category(**validated_data)
        new_category.save(position_order=count_categories["total_categorias"])

        return new_category
