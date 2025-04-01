from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.db.models import Max
from rest_framework import status

from utils.converter import day_to_number_converter
from utils.message import dispatch_message_websocket
from core.authentication import SCAuthenticationHttp
from core.view import SCView

from .serializers import DishSerializer, IngredientSerializer, CompositionSerializer
from .models import Dish, Ingredient, Composition


class LunchWeekView(SCView):
    def get(self, _):
        """Retorna os dados de todos os pratos da semana."""

        serializer = DishSerializer(Dish.objects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DishView(SCView):
    permission_classes = [SCAuthenticationHttp]
    ignore_validation_for_methods = ["get"]

    def dispatch(self, request, *args, **kwargs):
        """Verifica se o prato existe antes de acessar a view."""

        dish_name = kwargs.get("dish_name")

        query_dish = get_object_or_404(Dish, day=day_to_number_converter(dish_name))
        kwargs["dish"] = query_dish

        return super().dispatch(request, *args, **kwargs)

    def validate_before_access(self, user, _):
        """Verifica se o usuário tem autorização para acessar os endpoints post e patch."""

        return user.is_employee

    def get(self, _, dish_name, dish) -> Response:
        """Retorna os dados de um prato específico."""

        serializer = DishSerializer(dish)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, dish_name, dish) -> Response:
        """Cria novas composições no prato (adiciona ingredientes existentes)."""

        data = request.data
        data["dish"] = dish.id

        if data.get("config_choice_number", None):
            max_choice_number = Composition.objects.filter(
                dish=dish, ingredient__deletion_date__isnull=True
            ).aggregate(Max("config_choice_number"))["config_choice_number__max"]

            if data["config_choice_number"] > max_choice_number + 1:
                raise ValidationError(
                    "O número de escolha única ultrapassa o valor permitido."
                )

        if "list_ingredients" not in data:
            raise ValidationError(
                'O campo "list_ingredients" é obrigatório para criar novas composições.'
            )

        if not isinstance(data["list_ingredients"], list):
            raise ValidationError("Não foi possível identificar os ingredientes.")

        with transaction.atomic():
            for ingredient_name in data.pop("list_ingredients"):
                ingredient = Ingredient.objects.filter(
                    name=ingredient_name, deletion_date__isnull=True
                ).first()

                if not ingredient:
                    raise ValidationError(
                        f'Ingrediente "{ingredient_name}" não encontrado.'
                    )

                if Composition.objects.filter(
                    dish=dish, ingredient=ingredient
                ).exists():
                    raise ValidationError(
                        f'O ingrediente "{ingredient_name}" já está vinculado ao prato de {dish_name}.'
                    )

                data["ingredient"] = ingredient.id

                serializer = CompositionSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()

        # Notifica todos os clientes websocket sobre a adição de uma nova composição no prato.
        dispatch_message_websocket("lunch_group", "lunch_update")

        return Response(
            {"message": f'Composições adicionadas ao prato "{dish_name}" com sucesso.'},
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request, dish_name, dish) -> Response:
        """Atualiza os dados de um prato."""

        serializer = DishSerializer(
            dish,
            data=request.data,
            partial=True,
            remove_field=["day_name", "ingredients"],
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Notifica todos os clientes websocket sobre a edição do prato.
        dispatch_message_websocket("lunch_group", "lunch_update")

        return Response(
            {"message": f'Prato "{dish_name}" atualizado com sucesso.'},
            status=status.HTTP_200_OK,
        )


class IngredientsView(SCView):
    permission_classes = [SCAuthenticationHttp]

    def validate_before_access(self, user, _) -> bool:
        """Verifica se o usuário é um funcionário para acessar qualquer endpoint."""

        return user.is_employee

    def get(self, _) -> Response:
        """Retorna os dados de todos os ingredientes."""

        ingredients = Ingredient.objects.filter(deletion_date__isnull=True)
        serializer = IngredientSerializer(ingredients, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request) -> Response:
        """Cria um novo ingrediente no estoque."""

        serializer = IngredientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Notifica todos os clientes websocket sobre a adição de um novo ingrediente ao estoque.
        dispatch_message_websocket("lunch_group", "lunch_update")

        return Response(
            {"message": "Ingrediente criado com sucesso."},
            status=status.HTTP_201_CREATED,
        )


class IngredientView(SCView):
    permission_classes = [SCAuthenticationHttp]

    def dispatch(self, request, *args, **kwargs):
        """Verifica se o ingrediente existe antes de acessar a view."""

        ingredient_name = kwargs.get("ingredient_name")

        query_ingredient = get_object_or_404(
            Ingredient, name=ingredient_name, deletion_date__isnull=True
        )
        kwargs["ingredient"] = query_ingredient

        return super().dispatch(request, *args, **kwargs)

    def validate_before_access(self, user, _) -> bool:
        """Verifica se o usuário é um funcionário para acessar qualquer endpoint."""

        return user.is_employee

    def get(self, _, ingredient_name, ingredient) -> Response:
        """Retorna os dados de um ingrediente específico."""

        serializer = IngredientSerializer(ingredient)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, ingredient_name, ingredient) -> Response:
        """Atualiza os dados de um ingrediente."""

        serializer = IngredientSerializer(ingredient, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Notifica todos os clientes websocket sobre a edição do ingrediente.
        dispatch_message_websocket("lunch_group", "lunch_update")

        return Response(
            {"message": f'Ingrediente "{ingredient_name}" atualizado com sucesso.'},
            status=status.HTTP_200_OK,
        )

    def delete(self, _, ingredient_name, ingredient) -> Response:
        """Marca o ingrediente como excluído."""

        ingredient.deletion_date = timezone.now()
        ingredient.save()

        # Notifica todos os clientes websocket sobre a exclusão do ingrediente.
        dispatch_message_websocket("lunch_group", "lunch_update")

        return Response(status=status.HTTP_204_NO_CONTENT)


class CompositionView(SCView):
    permission_classes = [SCAuthenticationHttp]

    def dispatch(self, request, *args, **kwargs):
        """Verifica se a composição existe antes de acessar a view."""

        dish_name = kwargs.get("dish_name")
        ingredient_name = kwargs.get("ingredient_name")

        query_composition = get_object_or_404(
            Composition,
            dish__day=day_to_number_converter(dish_name),
            ingredient__name=ingredient_name,
            ingredient__deletion_date__isnull=True,
        )
        kwargs["composition"] = query_composition

        return super().dispatch(request, *args, **kwargs)

    def validate_before_access(self, user, _) -> bool:
        """Verifica se o usuário é um funcionário para acessar qualquer endpoint."""

        return user.is_employee

    def get(self, _, dish_name, ingredient_name, composition) -> Response:
        """Retorna os dados de uma composição específica (Relação entre prato e ingrediente)."""

        serializer = CompositionSerializer(
            composition, remove_field=["dish", "ingredient"]
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, dish_name, ingredient_name, composition) -> Response:
        """Atualiza os dados de uma composição (Relação entre prato e ingrediente)."""

        data = request.data

        if "config_choice_number" not in data or not isinstance(
            data["config_choice_number"], int
        ):
            raise ValidationError(
                "O campo numérico 'config_choice_number' é obrigatório para atualizar a composição."
            )

        dish = composition.dish

        max_choice_number = Composition.objects.filter(
            dish=dish, ingredient__deletion_date__isnull=True
        ).aggregate(Max("config_choice_number"))["config_choice_number__max"]

        if data["config_choice_number"] > max_choice_number + 1:
            raise ValidationError(
                "O número de escolha única ultrapassa o valor permitido."
            )

        # A verificação dos blocos deve iniciar a partir da composição que está sendo modificada,
        # pois a mesma pode deixar de existir.
        current_choice_number = composition.config_choice_number

        with transaction.atomic():
            serializer = CompositionSerializer(
                composition,
                data=data,
                partial=True,
                remove_field=["dish", "ingredient"],
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            if current_choice_number:
                # Atualiza a numeração das composições do prato para manter a ordem numérica, caso necessário.
                possible_affected_compositions = (
                    Composition.objects.filter(
                        dish=dish,
                        ingredient__deletion_date__isnull=True,
                        config_choice_number__gte=current_choice_number,
                    )
                    .order_by("config_choice_number")
                    .all()
                )

                for target in possible_affected_compositions:
                    if target.config_choice_number == current_choice_number:
                        # Se existir uma composição com a mesma numeração, mantém a ordem atual.
                        break

                    target.config_choice_number -= 1
                    target.save()

        # Notifica todos os clientes websocket sobre a edição da composição.
        dispatch_message_websocket("lunch_group", "lunch_update")

        return Response(
            {
                "message": f'Composição entre "{dish_name}" e "{ingredient_name}" atualizada com sucesso.'
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, _, dish_name, ingredient_name, composition) -> Response:
        """Exclui uma composição (Relação entre prato e ingrediente)."""

        with transaction.atomic():
            choice_number = composition.config_choice_number
            dish = composition.dish

            composition.delete()

            if choice_number:
                # Atualiza a numeração das composições do prato para manter a ordem numérica, caso necessário.

                possible_affected_compositions = (
                    Composition.objects.filter(
                        dish=dish,
                        ingredient__deletion_date__isnull=True,
                        config_choice_number__gte=choice_number,
                    )
                    .order_by("config_choice_number")
                    .all()
                )

                for target in possible_affected_compositions:
                    if target.config_choice_number == choice_number:
                        # Se existir uma composição com a mesma numeração, mantém a ordem atual.
                        break

                    target.config_choice_number -= 1
                    target.save()

        # Notifica todos os clientes websocket sobre a exclusão da composição.
        dispatch_message_websocket("lunch_group", "lunch_update")

        return Response(status=status.HTTP_204_NO_CONTENT)
