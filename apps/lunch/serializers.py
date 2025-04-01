from rest_framework import serializers

from core.serializers import SCSerializer
from core.variables import days_week
from utils.formatters import format_price

from .models import Dish, Ingredient, Composition


class DishSerializer(SCSerializer):
    day_name = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()

    class Meta:
        fields = [
            "day_name",
            "price",
            "initial_deadline",
            "deadline",
            "description",
            "path_img",
            "ingredients",
        ]
        model = Dish

    def get_day_name(self, obj):
        """Retorna o dia da semana."""

        return days_week[obj.day]

    def internal_value_for_price(self, value):
        """Converte o preço para um valor numerico ao receber do usuário."""

        return format_price(value, to_float=True)

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "O preço do prato deve ser maior que zero (R$ 0,00)."
            )

        return value

    def get_ingredients(self, obj):
        """Retorna os ingredientes do prato, separados por escolha única e múltipla."""

        ingredients = {"multiple_choice": []}

        # Obtém as composições do prato que não foram deletadas.
        compositions = (
            Composition.objects.filter(dish=obj, ingredient__deletion_date__isnull=True)
            .order_by("ingredient__name")
            .all()
        )

        for composition in compositions:
            choice_number = composition.config_choice_number
            ingredient = IngredientSerializer(composition.ingredient).data

            if choice_number:
                if "single_choice" not in ingredients:
                    ingredients["single_choice"] = {}

                if choice_number not in ingredients["single_choice"]:
                    ingredients["single_choice"][choice_number] = []

                ingredients["single_choice"][choice_number].append(ingredient)
                continue

            ingredients["multiple_choice"].append(ingredient)

        return ingredients

    def representation_for_price(self, value):
        """Formata o preço para o padrão brasileiro (R$ XX,XX) antes de enviar."""

        return format_price(float(value))


class IngredientSerializer(SCSerializer):
    class Meta:
        fields = ["name", "additional_charge"]
        model = Ingredient

    def internal_value_for_additional_charge(self, value):
        """Converte a quantidade adicional para um valor numerico ao receber do usuário."""

        if not value:
            return None

        return format_price(value, to_float=True)

    def validate_name(self, value):
        """Verifica se existe um ingrediente ativo com o mesmo nome."""

        if Ingredient.objects.filter(name=value, deletion_date__isnull=True).exists():
            raise serializers.ValidationError(f'O ingrediente "{value}" já existe.')

        return value

    def validate_additional_charge(self, value):
        """Verifica se a quantidade adicional do ingrediente é 0 (zero) e define o campo como NULL para armazenar no banco de dados."""

        if not value:
            return None

        if value < 0:
            raise serializers.ValidationError(
                "A quantidade adicional do ingrediente deve ser maior ou igual a zero (0)."
            )

        return value

    def representation_for_additional_charge(self, value):
        """Formata a quantidade adicional para o padrão brasileiro (R$ XX,XX) antes de enviar."""

        if value is None:
            return None

        return format_price(float(value))


class CompositionSerializer(SCSerializer):
    dish = serializers.PrimaryKeyRelatedField(queryset=Dish.objects.all())
    ingredient = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        fields = ["config_choice_number", "dish", "ingredient"]
        model = Composition

    def validate_config_choice_number(self, value):
        try:
            int(value)
            if value < 0:
                raise serializers.ValidationError(
                    "O número de escolha única do item tem que ser maior ou igual a zero (0)."
                )
        except:
            raise serializers.ValidationError(
                "Por favor, insira um valor válido para o número de escolha única."
            )

        return value
