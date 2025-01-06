from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import status

from cactus.core.authentication import SCAuthenticationHttp
from cactus.core.view import SCView

from .serializers import DishSerializer, IngredientSerializer, CompositionSerializer
from .models import Dish, Ingredient


class LunchWeekView(SCView):
    def get(self, _):
        """Retorna todos os pratos da semana."""

        serializer = DishSerializer(Dish.objects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DishView(SCView):
    def dispatch(self, request, *args, **kwargs):
        """Verifica se o prato existe antes de acessar a view."""

        dish_name = kwargs.get("dish_name")

        query_dish = get_object_or_404(Dish, name=dish_name)
        kwargs["dish"] = query_dish

        return super().dispatch(request, *args, **kwargs)

    def get(self, _, dish_name, dish) -> Response:
        """Retorna um prato específico."""

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
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("lunch_group", {"type": "lunch_update"})

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

        serializer = DishSerializer(
            dish,
            data=request.data,
            partial=True,
            remove_fields=["day_name", "ingredients"],
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Notifica todos os clientes websocket sobre a edição do prato.
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("lunch_group", {"type": "lunch_update"})

        return Response(
            {"message": f'Prato "{dish_name}" atualizado com sucesso.'},
            status=status.HTTP_200_OK,
        )


class IngredientsView(SCView): ...


class CompositionView(SCView): ...
