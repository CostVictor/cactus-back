from rest_framework import serializers
from django.db import transaction
from django.utils import timezone

from core.serializers import SCSerializer
from core.variables import days_week

from apps.snack.models import Snack
from apps.lunch.models import Dish, Composition
from apps.user.models import User

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
        amount = float(value)

        return {
            "formatted_amount": format_price(amount),
            "amount": amount,
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
        amount = float(value)

        return {
            "formatted_amount": format_price(amount),
            "amount": amount,
        }

    def representation_for_price_to_purchase_ingredient(self, value):
        amount = float(value)

        return {
            "formatted_amount": format_price(amount),
            "amount": amount,
        }


class OrderSerializer(SCSerializer):
    snacks = serializers.SerializerMethodField()
    lunch = serializers.SerializerMethodField()
    input_snacks = serializers.JSONField()
    input_lunch = serializers.ListField()
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
            "description",
            "snacks",
            "lunch",
            "input_snacks",
            "input_lunch",
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
        amount = float(value)

        return {
            "formatted_amount": format_price(amount),
            "amount": amount,
        }

    def representation_for_amount_snacks(self, value):
        amount = float(value)

        return {
            "formatted_amount": format_price(amount),
            "amount": amount,
        }

    def representation_for_amount_lunch(self, value):
        amount = float(value)

        return {
            "formatted_amount": format_price(amount),
            "amount": amount,
        }

    def representation_for_user(self, value):
        user = User.objects.filter(id=value).first()
        return user.username

    def representation_for_creator_user(self, value):
        user = User.objects.filter(id=value).first()
        return user.username

    def get_snacks(self, obj):
        return BuySnackSerializer(obj.purchased_snacks, many=True).data

    def get_lunch(self, obj):
        return BuyIngredientSerializer(obj.purchased_compositions, many=True).data

    def internal_value_for_description(self, value):
        if not value:
            return None

        return value

    def create(self, validated_data):
        snacks = validated_data.pop("input_snacks", {})
        lunch = validated_data.pop("input_lunch", [])

        if not snacks and not lunch:
            raise serializers.ValidationError("Nenhum item foi selecionado.")

        now = timezone.now()
        time = now.time()
        weekday = now.weekday() + 1

        dish = Dish.objects.filter(day=weekday).first()
        if not dish and lunch:
            raise serializers.ValidationError("Não foi possível encontrar o prato.")

        if dish:
            if dish.initial_deadline and time < dish.initial_deadline:
                raise serializers.ValidationError(
                    f"Você só pode pedir almoço a partir das {dish.initial_deadline.strftime('%H:%M')} horas."
                )
            if dish.deadline and time > dish.deadline:
                raise serializers.ValidationError(
                    f"Os pedidos de almoço de hoje só estão disponíveis até as {dish.deadline.strftime('%H:%M')} horas."
                )

        with transaction.atomic():
            order = Order.objects.create(
                creation_date=now,
                amount_due=0,
                amount_snacks=0,
                amount_lunch=0,
                **validated_data,
            )

            amount_snack = 0

            # Carrega todos os snacks relevantes de uma vez
            all_snack_names = [
                (key, product["name"])
                for key, items in snacks.items()
                for product in items
            ]
            snack_queryset = Snack.objects.filter(
                name__in=[name for _, name in all_snack_names],
                deletion_date__isnull=True,
                category__name__in=[key for key, _ in all_snack_names],
                category__deletion_date__isnull=True,
            ).select_related("category")

            snack_map = {
                (snack.category.name, snack.name): snack for snack in snack_queryset
            }

            for key, items in snacks.items():
                for product in items:
                    name = product["name"]
                    quantity = product["quantity"]

                    target_snack = snack_map.get((key, name))
                    if not target_snack:
                        raise serializers.ValidationError(
                            f"O item {name} não foi encontrado."
                        )

                    if quantity > target_snack.quantity_in_stock:
                        raise serializers.ValidationError(
                            f'O item "{target_snack.name}" possui apenas {target_snack.quantity_in_stock} unidades em estoque.'
                        )

                    target_snack.quantity_in_stock -= quantity
                    target_snack.save(update_fields=["quantity_in_stock"])

                    BuySnack.objects.create(
                        snack=target_snack,
                        order=order,
                        quantity_product=quantity,
                        price_to_purchase=target_snack.price,
                    )

                    amount_snack += quantity * target_snack.price

            amount_lunch = dish.price if lunch else 0
            choice_numbers = set()

            if lunch:
                # Carrega todos os ingredientes e composições de uma vez
                ingredient_names = [item["name"] for item in lunch]
                composition_queryset = Composition.objects.select_related(
                    "ingredient"
                ).filter(
                    dish_id=dish.id,
                    ingredient__name__in=ingredient_names,
                    ingredient__deletion_date__isnull=True,
                )

                composition_map = {
                    comp.ingredient.name: comp for comp in composition_queryset
                }

                for item in lunch:
                    name = item["name"]
                    quantity = item["quantity"]

                    composition = composition_map.get(name)
                    if not composition:
                        raise serializers.ValidationError(
                            f"O ingrediente {name} não foi encontrado."
                        )

                    choice_number = composition.config_choice_number
                    if choice_number:
                        if choice_number in choice_numbers:
                            raise serializers.ValidationError(
                                f'Você não pode escolher o ingrediente "{name}" pois um outro ingrediente marcado com o mesmo número de escolha única já foi selecionado.'
                            )

                        choice_numbers.add(choice_number)

                    additional_charge = composition.ingredient.additional_charge or 0

                    BuyIngredient.objects.create(
                        order=order,
                        composition=composition,
                        quantity_ingredient=quantity,
                        price_to_purchase_dish=dish.price,
                        price_to_purchase_ingredient=additional_charge,
                    )

                    amount_lunch += (
                        (quantity - 1) * additional_charge if quantity > 1 else 0
                    )

            order.amount_due = amount_snack + amount_lunch
            order.amount_snacks = amount_snack
            order.amount_lunch = amount_lunch
            order.save(update_fields=["amount_due", "amount_snacks", "amount_lunch"])

        return order
