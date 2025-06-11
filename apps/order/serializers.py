from rest_framework import serializers
from django.db import transaction
from django.utils import timezone

from core.serializers import SCSerializer
from core.variables import days_week

from apps.snack.models import Snack
from apps.lunch.models import Dish, Composition
from apps.user.models import User

from apps.user.serializers import UserSerializer

from utils.formatters import format_price
from .models import Order, BuySnack, BuyIngredient


class BuySnackSerializer(SCSerializer):
    name = serializers.CharField(source="snack.name")

    class Meta:
        fields = [
            "name",
            "quantity_product",
            "price_to_purchase",
        ]
        model = BuySnack

    def representation_for_price_to_purchase(self, value):
        return {
            "formatted_amount": format_price(value),
            "amount": value,
        }


class BuyIngredientSerializer(SCSerializer):
    dish_name = serializers.SerializerMethodField()
    ingredient_name = serializers.CharField(source="composition.ingredient.name")

    class Meta:
        fields = [
            "dish_name",
            "ingredient_name",
            "quantity_ingredient",
            "price_to_purchase_dish",
            "price_to_purchase_ingredient",
        ]
        model = BuyIngredient

    def get_dish_name(self, obj):
        return days_week[obj.composition.dish.day]

    def representation_for_price_to_purchase_dish(self, value):
        return {
            "formatted_amount": format_price(value),
            "amount": value,
        }

    def representation_for_price_to_purchase_ingredient(self, value):
        return {
            "formatted_amount": format_price(value),
            "amount": value,
        }


class OrderSerializer(SCSerializer):
    snacks = serializers.JSONField()
    lunch = BuyIngredientSerializer(many=True)
    creator_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True, deletion_date__isnull=True)
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True, deletion_date__isnull=True)
    )
    description = serializers.CharField(required=False, allow_null=True)

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

    def representation_for_amount_due(self, value):
        return {
            "formatted_amount": format_price(value),
            "amount": value,
        }

    def representation_for_amount_snacks(self, value):
        return {
            "formatted_amount": format_price(value),
            "amount": value,
        }

    def representation_for_amount_lunch(self, value):
        return {
            "formatted_amount": format_price(value),
            "amount": value,
        }

    def representation_for_user(self, value):
        return value.username

    def representation_for_creator_user(self, value):
        return value.username

    def internal_value_for_description(self, value):
        if not value:
            return None

        return value

    def create(self, validated_data):
        snacks = validated_data.pop("snacks", [])
        lunch = validated_data.pop("lunch", [])

        if not snacks and not lunch:
            raise serializers.ValidationError("Nenhum item foi selecionado.")

        now = timezone.now()
        weekday = now.weekday() + 1

        dish = Dish.objects.filter(day=weekday).first()
        if not dish and lunch:
            raise serializers.ValidationError(f"Não foi possível encontrar o prato.")

        with transaction.atomic():
            order = Order(**validated_data)
            order.creation_date = now
            order.amount_due = 0
            order.amount_snacks = 0
            order.amount_lunch = 0
            order.save()

            amount_snack = 0
            for key, value in snacks.items():
                for product in value:
                    quantity = product["quantity"]

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

                    if quantity > target_snack.quantity_in_stock:
                        raise serializers.ValidationError(
                            f'O item "{target_snack.name}" possui apenas {target_snack.quantity_in_stock} unidades em estoque.'
                        )

                    target_snack.quantity_in_stock -= quantity
                    target_snack.save()

                    buy_snack = BuySnack(
                        snack=target_snack,
                        order=order,
                        quantity_product=quantity,
                        price_to_purchase=target_snack.price,
                    )
                    buy_snack.save()
                    amount_snack += quantity * target_snack.price

            amount_lunch = dish.price if lunch else 0
            choice_numbers = []

            for ingredient in lunch:
                name = ingredient["name"]

                target_composition = Composition.objects.filter(
                    dish__id=dish.id,
                    ingredient__name=name,
                    ingredient__deletion_date__isnull=True,
                ).first()

                if not target_composition:
                    raise serializers.ValidationError(
                        f"O ingrediente {name} não foi encontado."
                    )

                choice_number = target_composition.config_choice_number
                if choice_number and choice_number in choice_numbers:
                    raise serializers.ValidationError(
                        f'Você não pode escolher o ingrediente "{name}" pois um outro ingrediente marcado com o mesmo número de escolha única já foi selecionado.'
                    )
                choice_numbers.append(choice_number)

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
