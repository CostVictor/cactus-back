from rest_framework import serializers

from core.serializers import SCSerializer
from core.variables import days_week

from utils.formatters import format_price
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
        return {
            "formatted_amount": format_price(obj.price_to_purchase),
            "amount": obj.price_to_purchase,
        }

    def get_total_value(self, obj):
        total = obj.price_to_purchase * obj.quantity_product

        return {
            "formatted_amount": format_price(total),
            "amount": total,
        }


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
        return {
            "formatted_amount": format_price(obj.price_to_purchase_dish),
            "amount": obj.price_to_purchase_dish,
        }

    def get_ingredient_name(self, obj):
        return obj.ingredient.name

    def get_ingredient_price(self, obj):
        additional_charge = obj.price_to_purchase_ingredient

        if obj.quantity_ingredient and additional_charge:
            total = obj.quantity_ingredient * additional_charge

            return {
                "formatted_amount": format_price(total),
                "amount": total,
            }

        return {
            "formatted_amount": "R$ 0,00",
            "amount": 0,
        }


class OrderSerializer(SCSerializer):
    buy_snack = BuySnackSerializer(many=True)
    buy_lunch = BuyIngredientSerializer(many=True)
    values = serializers.SerializerMethodField()

    class Meta:
        fields = [
            "creation_date",
            "final_payment_date",
            "description",
            "buy_snack",
            "buy_lunch",
            "values",
        ]
        model = Order

    def get_values(self, _):
        buy_snack = self.fields["buy_snack"]
        buy_lunch = self.fields["buy_lunch"]

        values = {
            "snacks": {"formatted_amount": "", "amount": 0},
            "lunch": {"formatted_amount": "", "amount": 0},
            "total": {"formatted_amount": "", "amount": 0},
        }

        for buy in buy_snack:
            values["snacks"]["amount"] += buy["total_value"]["amount"]

        for buy in buy_lunch:
            values["lunch"]["amount"] += buy["ingredient_price"]["amount"]

        values["lunch"]["amount"] = (
            values["lunch"]["amount"]
            if not len(buy_lunch)
            else values["lunch"]["amount"] + buy_lunch[0]["dish_price"]["amount"]
        )

        total = values["snacks"]["amount"] + values["lunch"]["amount"]

        values["total"] = {
            "formatted_amount": format_price(total),
            "amount": total,
        }
        values["snacks"]["formatted_amount"] = format_price(values["snacks"]["amount"])
        values["lunch"]["formatted_amount"] = format_price(values["lunch"]["amount"])

        return values
