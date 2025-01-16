from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from django.utils import timezone
from rest_framework import status

from cactus.utils.formatters import format_price
from cactus.utils.converter import day_to_number_converter
from cactus.utils.message import dispatch_message_websocket
from cactus.core.authentication import SCAuthenticationHttp
from cactus.core.view import SCView

from .serializers import DishSerializer, IngredientSerializer, CompositionSerializer
from .models import Dish, Ingredient, Composition


class LunchWeekView(SCView):
    def get(self, _):
        """Retorna os dados de todos os pratos da semana."""

        serializer = DishSerializer(Dish.objects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DishView(SCView):
    def dispatch(self, request, *args, **kwargs):
        """Verifica se o prato existe antes de acessar a view."""

        dish_name = kwargs.get("dish_name")

        query_dish = get_object_or_404(Dish, day=day_to_number_converter(dish_name))
        kwargs["dish"] = query_dish

        return super().dispatch(request, *args, **kwargs)

    def get(self, _, dish_name, dish) -> Response:
        """Retorna os dados de um prato específico."""

        serializer = DishSerializer(dish)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, dish_name, dish) -> Response:
        """Cria uma nova composição no prato (adiciona um ingrediente existente)."""

        # Verificando se o usuário está autenticado e possui autorização.
        user, _ = SCAuthenticationHttp().authenticate(request)
        if not user.is_employee:
            raise PermissionDenied("Usuário não autorizado.")

        data = request.data
        data["dish"] = dish.id

        if "ingredient_name" not in data:
            raise ValidationError(
                'O campo "ingredient_name" é obrigatório para criar uma nova composição.'
            )

        ingredient = Ingredient.objects.filter(
            name=data.pop("ingredient_name"), deletion_date__isnull=True
        ).first()

        if not ingredient:
            raise ValidationError(
                "O ingrediente informado não existe. Por favor, verifique o nome do ingrediente."
            )

        data["ingredient"] = ingredient.id

        serializer = CompositionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Notifica todos os clientes websocket sobre a adição de uma nova composição no prato.
        dispatch_message_websocket("lunch_group", "lunch_update")

        return Response(
            {"message": f'Composição adicionada ao prato "{dish_name}" com sucesso.'},
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request, dish_name, dish) -> Response:
        """Atualiza os dados de um prato."""

        # Verificando se o usuário está autenticado e possui autorização.
        user, _ = SCAuthenticationHttp().authenticate(request)
        if not user.is_employee:
            raise PermissionDenied("Usuário não autorizado.")

        data = request.data

        if data.get("price", None):
            data["price"] = format_price(data["price"], to_float=True)

        serializer = DishSerializer(
            dish,
            data=data,
            partial=True,
            remove_fields=["day_name", "ingredients"],
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

    def validate_before_access(self, user) -> bool:
        """Verifica se o usuário é um funcionário."""

        return user.is_employee

    def get(self, _) -> Response:
        """Retorna os dados de todos os ingredientes."""

        ingredients = Ingredient.objects.filter(deletion_date__isnull=True)
        serializer = IngredientSerializer(ingredients, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request) -> Response:
        """Cria um novo ingrediente no estoque."""

        data = request.data

        if data.get("additional_charge", None):
            additional_charge = format_price(data["additional_charge"], to_float=True)

            # Verifica se o valor do adicional é 0.00 e remove o campo do JSON para que armazene NULL no banco de dados.
            if not additional_charge:
                del data["additional_charge"]
            else:
                data["additional_charge"] = additional_charge

        serializer = IngredientSerializer(data=data)
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

    def validate_before_access(self, user) -> bool:
        """Verifica se o usuário é um funcionário."""

        return user.is_employee

    def get(self, _, ingredient_name, ingredient) -> Response:
        """Retorna os dados de um ingrediente específico."""

        serializer = IngredientSerializer(ingredient)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, ingredient_name, ingredient) -> Response:
        """Atualiza os dados de um ingrediente."""

        data = request.data

        if data.get("additional_charge", None):
            additional_charge = format_price(data["additional_charge"], to_float=True)

            # Verifica se o valor do adicional é 0.00 e define o campo como NULL no JSON para que armazene no banco de dados.
            data["additional_charge"] = additional_charge if additional_charge else None

        serializer = IngredientSerializer(ingredient, data=data, partial=True)
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

    def validate_before_access(self, user) -> bool:
        """Verifica se o usuário é um funcionário."""

        return user.is_employee

    def get(self, _, dish_name, ingredient_name, composition) -> Response:
        """Retorna os dados de uma composição específica (Relação entre prato e ingrediente)."""

        serializer = CompositionSerializer(
            composition, remove_fields=["dish", "ingredient"]
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, dish_name, ingredient_name, composition) -> Response:
        """Atualiza os dados de uma composição (Relação entre prato e ingrediente)."""

        serializer = CompositionSerializer(
            composition,
            data=request.data,
            partial=True,
            remove_fields=["dish", "ingredient"],
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

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

        composition.delete()

        # Notifica todos os clientes websocket sobre a exclusão da composição.
        dispatch_message_websocket("lunch_group", "lunch_update")

        return Response(status=status.HTTP_204_NO_CONTENT)
