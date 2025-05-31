from rest_framework import serializers
from django.db import transaction
from django.utils import timezone

from core.serializers import SCSerializer
from core.variables import days_week

from apps.snack.models import Snack
from apps.lunch.models import Dish, Composition

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
    snacks = BuySnackSerializer(many=True)
    lunch = BuyIngredientSerializer(many=True)
    creator_user = serializers.CharField(source="creator_user.username")

    class Meta:
        fields = [
            "public_id",
            "user",
            "creator_user",
            "creation_date",
            "final_payment_date",
            "amount_due",
            "amount_snacks",
            "amount_lunch",
            "fulfilled",
            "hidden",
            "description",
            "snacks",
            "lunch",
        ]
        read_only_fields = [
            "public_id",
            "user",
            "creator_user",
            "creation_date",
            "amount_snacks",
            "amount_lunch",
            "description",
            "snacks",
            "lunch",
        ]
        model = Order

    def create(self, validated_data):
        snacks = validated_data.pop("snacks", [])
        lunch = validated_data.pop("lunch", [])

        now = timezone.now()
        weekday = now.weekday() + 1

        dish = Dish.objects.filter(day=weekday).first()
        if not dish and lunch:
            raise serializers.ValidationError(
                f"Não foi possível encontrar o prato de {days_week[weekday]}."
            )

        with transaction.atomic():
            order = Order(**validated_data)
            order.creation_date = now
            order.save()

            amount_snack = 0
            for key, value in snacks.items():
                for product in value:
                    target_snack = Snack.objects.filter(
                        name=product["name"],
                        deletion_date__isnull=True,
                        category__name=key,
                        category__deletion_date__isnull=True,
                    ).first()

                    if not target_snack:
                        raise serializers.ValidationError(
                            f"O item {product['name']} não foi encontado."
                        )

                    buy_snack = BuySnack(
                        snack=target_snack,
                        order=order,
                        quantity_product=product["quantity"],
                        price_to_purchase=target_snack.price,
                    )
                    buy_snack.save()
                    amount_snack += product["quantity"] * target_snack.price

            amount_lunch = dish.price if lunch else 0
            for ingredient in lunch:
                target_composition = Composition.objects.filter(
                    dish__id=dish.id,
                    ingredient__name=ingredient["name"],
                    ingredient__deletion_date__isnull=True,
                ).first()

                if not target_composition:
                    raise serializers.ValidationError(
                        f"O ingrediente {ingredient['name']} não foi encontado."
                    )

                target_ingredient = target_composition.ingredient
                additional_charge = target_ingredient.additional_charge or 0

                buy_ingredient = BuyIngredient(
                    order=order,
                    composition=target_composition,
                    quantity_ingredient=ingredient["quantity"],
                    price_to_purchase_dish=dish.price,
                    price_to_purchase_ingredient=additional_charge,
                )
                buy_ingredient.save()

                amount_lunch += ingredient["quantity"] * additional_charge

            order.amount_due = amount_snack + amount_lunch
            order.amount_snacks = amount_snack
            order.amount_lunch = amount_lunch

            order.save()

        return order
