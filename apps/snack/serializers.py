from rest_framework import serializers
from django.db import transaction

from core.serializers import SCSerializer
from utils.formatters import format_price

from .models import SnackCategory, Description, Snack


class SnackSerializer(SCSerializer):
    class Meta:
        model = Snack
        fields = [
            "name",
            "quantity_in_stock",
            "price",
            "description",
            "path_img",
            "category",
        ]

        extra_kwargs = {
            "price": {
                "error_messages": {
                    "invalid": "Por favor, insira um valor numérico válido para o preço.",
                    "max_digits": "O preço não pode ter mais de 4 dígitos.",
                }
            },
        }

    def internal_value_for_price(self, value):
        """Converte o preço para um valor numerico ao receber do usuário."""

        return format_price(value, to_float=True)

    def validate_name(self, value):
        check_snack = Snack.objects.filter(
            name=value, deletion_date__isnull=True, category__deletion_date__isnull=True
        ).first()

        if check_snack:
            raise serializers.ValidationError(
                f'O item "{value}" já existe na categoria "{check_snack.category.name}".'
            )

        return value

    def validate_quantity_in_stock(self, value):
        # O mínimo existente no estoque deve ser 0.
        if value < 0:
            raise serializers.ValidationError(
                "A quantidade no estoque não pode ser menor que zero (0)."
            )

        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "O preço do item deve ser maior que zero (R$ 0,00)."
            )

        return value

    def representation_for_price(self, value):
        """Formata o preço para o padrão brasileiro (R$ XX,XX) antes de enviar."""

        return format_price(float(value))


class DescriptionSerializer(SCSerializer):
    category = serializers.CharField(source="category.name")

    class Meta:
        fields = ["title", "text", "illustration_url", "category"]
        model = Description


class CategorySerializer(SCSerializer):
    snacks = serializers.SerializerMethodField()
    description = DescriptionSerializer(required=False)

    class Meta:
        fields = [
            "name",
            "path_img",
            "snacks",
            "description",
        ]
        model = SnackCategory

    def get_snacks(self, obj):
        """Obtem todos os produtos não excluídos relacionados à categoria e ordena pelo nome."""

        snacks = obj.snacks.filter(deletion_date__isnull=True).order_by("name")
        return SnackSerializer(snacks, many=True, remove_field=["category"]).data

    def validate_name(self, value):
        """Verifica se existe uma categoria ativa com o mesmo nome."""

        if SnackCategory.objects.filter(name=value, deletion_date__isnull=True):
            raise serializers.ValidationError(f'A categoria "{value}" já existe.')
        return value

    def create(self, validated_data):
        """Cria uma nova categoria vazia."""

        active_category_count = SnackCategory.objects.filter(
            deletion_date__isnull=True
        ).count()

        with transaction.atomic():
            new_category = SnackCategory(**validated_data)
            new_category.position_order = active_category_count + 1
            new_category.save()

            description = Description(
                title=f"Venha experimentar nossos {new_category.name}!",
                text=f"Nossos {new_category.name.lower()} são preparados com ingredientes de qualidade, garantindo um sabor irresistível a cada mordida.",
                category=new_category,
            )
            description.save()

        return new_category

    def update(self, instance, validated_data):
        """Atualiza a categoria e sua descrição."""

        description_data = validated_data.pop("description", None)

        if description_data:
            serializer = DescriptionSerializer(
                instance.description,
                data=description_data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return super().update(instance, validated_data)

    def representation_for_description(self, value):
        """Remove o campo category da descrição, pois ele é desnecessário."""

        del value["category"]
        return value
