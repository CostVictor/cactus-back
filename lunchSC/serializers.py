from cactus.core.serializers import SCSerializer
from cactus.utils.validators import price_validator
from rest_framework import serializers

from .models import Dish, Ingredient, Composition
from .variables import days_week


class DishSerializer(SCSerializer):
    day_name = serializers.SerializerMethodField()

    class Meta:
        fields = [
            "day_name",
            "price",
            "initial_deadline",
            "deadline",
            "description",
            "path_img",
        ]
        model = Dish

    def get_day_name(self, obj):
        """Retorna o dia da semana."""

        return days_week[obj.day]

    def validate_price(self, value):
        price_validator(value)
        return value


class IngredientSerializer(SCSerializer):
    class Meta:
        fields = ["name", "additional_charge"]
        model = Ingredient

    def validate_name(self, value):
        """Verifica se existe um ingrediente ativo com o mesmo nome."""

        if Ingredient.objects.filter(name=value, deletion_date__isnull=True):
            raise serializers.ValidationError(f'O ingrediente "{value}" já existe.')

        return value

    def validate_additional_charge(self, value):
        """Verifica se o valor adicional é menor que 0."""

        try:
            float(value)

            # Verifica a existência de preços negativos.
            if value < 0:
                raise serializers.ValidationError(
                    "O valor do preço adicional deve ser, no mínimo, zero (0)."
                )
        except:
            raise serializers.ValidationError("Por favor, insira um valor válido.")

        return value


class CompositionSerializer(SCSerializer):
    dish = serializers.SerializerMethodField()
    ingredient = IngredientSerializer()

    class Meta:
        fields = ["config_choice_number", "dish", "ingredient"]
        model = Composition

    def get_dish(self, obj):
        """Obtem o nome do dia da semana."""

        return days_week[obj.day]

    def validate_config_choice_number(self, value):
        try:
            int(value)

            # Verifica a existência de números negativos.
            if value < 0:
                raise serializers.ValidationError(
                    "O número de escolha única do item tem que ser maior ou igual a zero (0)."
                )
        except:
            raise serializers.ValidationError("Por favor, insira um número válido.")

        return value

    def validate_dish(self, value):
        query_dish = Dish.objects.filter(day=value)

        if not query_dish:
            raise serializers.ValidationError(
                f'Não possível encontrar um dia da semana correspondente a "{value}".'
            )

        return query_dish

    def validate_ingredient(self, value):
        query_ingredient = Ingredient.objects.filter(name=value)

        if not query_ingredient:
            raise serializers.ValidationError(
                f'Nenhum ingrediente "{value}" foi encontrado.'
            )

        return query_ingredient
