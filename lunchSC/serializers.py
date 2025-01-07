from cactus.core.serializers import SCSerializer
from cactus.utils.formatters import format_price
from rest_framework import serializers

from .models import Dish, Ingredient, Composition
from .variables import days_week


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

    def validate_price(self, value):
        if not value:
            raise serializers.ValidationError(
                "O preço do prato deve ser maior que zero (R$ 0,00)."
            )

        return value

    def get_ingredients(self, obj):
        """Retorna os ingredientes do prato, separados por escolha única e múltipla."""

        ingredients = {"multiple_choice": []}

        # Obtém as composições do prato que não foram deletadas.
        compositions = Composition.objects.filter(
            dish=obj, ingredient__deletion_date__isnull=True
        )

        # Serializa as composições.
        compositions_serialize = CompositionSerializer(
            compositions, many=True, remove_fields=["dish"]
        )

        for composition in compositions_serialize:
            choice_number = composition.config_choice_number
            ingredient = composition.ingredient

            if choice_number:
                if "single_choice" not in ingredients:
                    ingredients["single_choice"] = {}

                if choice_number not in ingredients["single_choice"]:
                    ingredients["single_choice"][choice_number] = []

                ingredients["single_choice"][choice_number].append(ingredient)

            else:
                ingredients["multiple_choice"].append(ingredient)

        return ingredients

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["price"] = format_price(float(representation["price"]))
        return representation


class IngredientSerializer(SCSerializer):
    class Meta:
        fields = ["name", "additional_charge"]
        model = Ingredient

    def validate_name(self, value):
        """Verifica se existe um ingrediente ativo com o mesmo nome."""

        if Ingredient.objects.filter(name=value, deletion_date__isnull=True):
            raise serializers.ValidationError(f'O ingrediente "{value}" já existe.')

        return value

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        additional_charge = representation["additional_charge"]
        if additional_charge:
            representation["additional_charge"] = format_price(float(additional_charge))
        return representation


class CompositionSerializer(SCSerializer):
    dish = DishSerializer()
    ingredient = IngredientSerializer()

    class Meta:
        fields = ["config_choice_number", "dish", "ingredient"]
        model = Composition

    def validate_config_choice_number(self, value):
        try:
            int(value)

            # Verifica a existência de números negativos.
            if value < 0:
                raise serializers.ValidationError(
                    "O número de escolha única do item tem que ser maior ou igual a zero (0)."
                )
        except:
            raise serializers.ValidationError(
                "Por favor, insira um valor válido para o número de escolha única."
            )

        return value
