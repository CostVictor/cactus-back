from rest_framework import serializers

from core.serializers import SCSerializer
from core.variables import days_week

from .models import Order, BuySnack, BuyIngredient


class BuySnackSerializer(SCSerializer):
    name = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    total_value = serializers.SerializerMethodField()

    class Meta:
        fields = [
            "name",
            "price",
            "total_value",
            "quantity_product",
        ]
        model = BuySnack

    def get_name(self, obj):
        return obj.snack.name

    def get_price(self, obj):
        return obj.snack.price

    def get_total_value(self, obj):
        return obj.quantity_product * obj.snack.price


class BuyIngredientSerializer(SCSerializer):
    dish_name = serializers.SerializerMethodField()
    dish_price = serializers.SerializerMethodField()
    ingredient_name = serializers.SerializerMethodField()
    ingredient_price = serializers.SerializerMethodField()

    class Meta:
        fields = [
            "dish_name",
            "dish_price",
            "ingredient_name",
            "ingredient_price",
            "quantity_ingredient",
        ]
        model = BuyIngredient

    def get_dish_name(self, obj):
        return days_week[obj.dish.day]

    def get_dish_price(self, obj):
        return obj.dish.price

    def get_ingredient_name(self, obj):
        return obj.ingredient.name

    def get_ingredient_price(self, obj):
        additional_charge = obj.ingredient.additional_charge

        if obj.quantity_ingredient and additional_charge:
            return obj.quantity_ingredient * additional_charge

        return 0


class OrderSerializer(SCSerializer):
    buy_snack = BuySnackSerializer()
    buy_lunch = BuyIngredientSerializer()
    total_value = serializers.SerializerMethodField()

    class Meta:
        fields = [
            "total_value",
            "creation_date",
            "final_payment_date",
            "description",
        ]
        model = Order

    def get_total_value(self, obj):
        print(obj.buy_snack)
        print(obj.buy_lunch)

    def validate_total_value(self, value):
        if not value:
            raise serializers.ValidationError(
                "O valor do pedido deve ser maior que zero (R$ 0,00)"
            )

        return value
