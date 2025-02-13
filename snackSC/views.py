from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import status
from django.db import transaction
from datetime import datetime

from cactus.core.authentication import SCAuthenticationHttp
from cactus.utils.formatters import format_price
from cactus.core.view import SCView
from userSC.models import User

from .models import Snack_category, Snack
from .serializers import CategorySerializer, SnackSerializer


class SnackCategoriesView(SCView):
    def get(self, _):
        """Retorna todas as categorias e lanches."""

        # Ordena as categorias por `position_order`.
        categories = Snack_category.objects.filter(deletion_date__isnull=True).order_by(
            "position_order"
        )
        serializer = CategorySerializer(
            categories, many=True, remove_field=["update_description"]
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request) -> Response:
        """Cria uma nova categoria."""

        # Verificando se o usuário está autenticado e possui autorização.
        user, _ = SCAuthenticationHttp().authenticate(request)
        if not user.is_employee:
            raise PermissionDenied(
                "Você não tem autorização para acessar este recurso."
            )

        serializer = CategorySerializer(
            data=request.data, remove_field=["snacks", "update_description"]
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Notifica todos os clientes websocket sobre a nova categoria no estoque de lanches.
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "snacks_group", {"type": "snacks_update"}
        )

        return Response(
            {"message": "Categoria criada com sucesso."}, status=status.HTTP_201_CREATED
        )


class CategoryView(SCView):
    permission_classes = [SCAuthenticationHttp]

    def dispatch(self, request, *args, **kwargs):
        """Verifica se a categoria existe antes de acessar os endpoints."""

        category_name = kwargs.get("category_name")

        query_category = get_object_or_404(
            Snack_category, name=category_name, deletion_date__isnull=True
        )
        kwargs["category"] = query_category

        return super().dispatch(request, *args, **kwargs)

    def validate_before_access(self, user: User) -> bool:
        """Verifica se o usuário tem autorização para acessar os endpoints."""

        return user.is_employee

    def get(self, _, _category_name, category):
        """Retorna os dados da categoria."""

        serializer = CategorySerializer(
            [category], many=True, remove_field=["snacks", "update_description"]
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, category_name, category):
        """Cria um novo item (Snack) na categoria."""

        data = request.data
        data["price"] = format_price(data["price"], to_float=True)
        data["category"] = category.id

        serializer = SnackSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Notifica todos os clientes websocket sobre o novo item no estoque de lanches.
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "snacks_group", {"type": "snacks_update"}
        )

        return Response(
            {"message": f"Item criado com sucesso na categoria {category_name}."},
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request, category_name, category):
        """Edita os dados da categoria."""

        serializer = CategorySerializer(
            category, data=request.data, partial=True, remove_field=["snacks"]
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Notifica todos os clientes websocket sobre a edição da categoria no estoque de lanches.
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "snacks_group", {"type": "snacks_update"}
        )

        return Response(
            {"message": f"{category_name} editada com sucesso."},
            status=status.HTTP_200_OK,
        )

    def delete(self, _, _category_name, category):
        """Marca a categoria e todos os seus itens como excluídos."""

        with transaction.atomic():
            snacks = category.snacks.filter(deletion_date__isnull=True).all()
            now = datetime.now()

            for snack in snacks:
                snack.deletion_date = now
                snack.save()

            category.deletion_date = now
            category.save()

            active_categories = Snack_category.objects.filter(
                deletion_date__isnull=True
            ).all()

            for index, category in enumerate(active_categories):
                category.position_order = index + 1
                category.save()

        # Notifica todos os clientes websocket sobre a exclusão da categoria no estoque de lanches.
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "snacks_group", {"type": "snacks_update"}
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class SnackView(SCView):
    permission_classes = [SCAuthenticationHttp]

    def dispatch(self, request, *args, **kwargs):
        """Verifica se a categoria e o item existe antes de acessar os endpoints."""

        category_name = kwargs.get("category_name")
        snack_name = kwargs.get("snack_name")

        query_category = get_object_or_404(
            Snack_category, name=category_name, deletion_date__isnull=True
        )
        query_snack = get_object_or_404(
            Snack, name=snack_name, category=query_category, deletion_date__isnull=True
        )
        kwargs["snack"] = query_snack

        return super().dispatch(request, *args, **kwargs)

    def validate_before_access(self, user: User) -> bool:
        """Verifica se o usuário tem autorização para acessar os endpoints."""

        return user.is_employee

    def get(self, _, _category_name, _snack_name, snack):
        """Retorna os dados do lanche."""

        serializer = SnackSerializer(snack)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, category_name, snack_name, snack):
        """Edita os dados do lanche."""

        serializer = SnackSerializer(
            snack, data=request.data, partial=True, remove_field=["category"]
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Notifica todos os clientes websocket sobre a edição do lanche no estoque de lanches.
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "snacks_group", {"type": "snacks_update"}
        )

        return Response(
            {
                "message": f"O item {snack_name} da categoria {category_name} foi editado com sucesso."
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, _, _category_name, _snack_name, snack):
        """Marca o item como excluído."""

        now = datetime.now()
        snack.deletion_date = now
        snack.save()

        # Notifica todos os clientes websocket sobre a exclusão do lanche no estoque de lanches.
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "snacks_group", {"type": "snacks_update"}
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
