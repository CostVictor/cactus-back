from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone

from core.authentication import SCAuthenticationHttp
from utils.message import dispatch_message_websocket
from utils.formatters import format_price
from core.view import SCView
from apps.user.models import User

from .models import SnackCategory, Snack
from .serializers import CategorySerializer, SnackSerializer


class SnackCategoriesView(SCView):
    permission_classes = [SCAuthenticationHttp]
    ignore_validation_for_methods = ["get"]

    def validate_before_access(self, user, _):
        """Verifica se o usuário tem autorização para acessar os endpoints post e patch."""

        return user.is_employee

    def get(self, _):
        """Retorna todas as categorias e lanches."""

        # Ordena as categorias por `position_order`.
        categories = SnackCategory.objects.filter(deletion_date__isnull=True).order_by(
            "position_order"
        )
        serializer = CategorySerializer(categories, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request) -> Response:
        """Cria uma nova categoria."""

        serializer = CategorySerializer(
            data=request.data,
            remove_field=["snacks"],
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Notifica todos os clientes websocket sobre a nova categoria no estoque de lanches.
        dispatch_message_websocket("snacks_group", "snacks_update")

        return Response(
            {"message": "Categoria criada com sucesso."}, status=status.HTTP_201_CREATED
        )

    def patch(self, request: Request) -> Response:
        """Edita a posição das categorias."""

        new_order = request.data.get("update_position_order", None)
        if new_order:
            with transaction.atomic():
                for index, name in enumerate(new_order):
                    category = SnackCategory.objects.filter(
                        deletion_date__isnull=True,
                        name=name,
                    ).first()
                    if category:
                        category.position_order = index + 1
                        category.save()

            # Notifica todos os clientes websocket sobre a edição da posição das categorias.
            dispatch_message_websocket("snacks_group", "snacks_update")

            return Response(
                {"message": "Posição das categorias atualizada com sucesso."},
                status=status.HTTP_200_OK,
            )

        raise ValidationError('O campo "update_position_order" é obrigatório.')


class CategoryView(SCView):
    permission_classes = [SCAuthenticationHttp]

    def dispatch(self, request, *args, **kwargs):
        """Verifica se a categoria existe antes de acessar os endpoints."""

        category_name = kwargs.get("category_name")

        query_category = get_object_or_404(
            SnackCategory, name=category_name, deletion_date__isnull=True
        )
        kwargs["category"] = query_category

        return super().dispatch(request, *args, **kwargs)

    def validate_before_access(self, user: User, _) -> bool:
        """Verifica se o usuário tem autorização para acessar qualquer endpoint."""
        return user.is_employee

    def get(self, _, category_name, category):
        """Retorna os dados da categoria."""

        serializer = CategorySerializer(
            category,
            remove_field=["snacks"],
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, category_name, category):
        """Cria um novo item (Snack) na categoria."""

        data = request.data
        data["category"] = category.id

        serializer = SnackSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Notifica todos os clientes websocket sobre o novo item no estoque de lanches.
        dispatch_message_websocket("snacks_group", "snacks_update")

        return Response(
            {"message": f"Item criado com sucesso na categoria {category_name}."},
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request, category_name, category):
        """Edita os dados da categoria."""

        serializer = CategorySerializer(
            category,
            data=request.data,
            partial=True,
            remove_field=["snacks"],
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Notifica todos os clientes websocket sobre a edição da categoria no estoque de lanches.
        dispatch_message_websocket("snacks_group", "snacks_update")

        return Response(
            {"message": f"{category_name} editada com sucesso."},
            status=status.HTTP_200_OK,
        )

    def delete(self, _, category_name, category):
        """Marca a categoria como excluída."""

        with transaction.atomic():
            category.deletion_date = timezone.now()
            category.save()

            active_categories = SnackCategory.objects.filter(
                deletion_date__isnull=True
            ).all()

            for index, category in enumerate(active_categories):
                category.position_order = index + 1
                category.save()

        # Notifica todos os clientes websocket sobre a exclusão da categoria no estoque de lanches.
        dispatch_message_websocket("snacks_group", "snacks_update")

        return Response(status=status.HTTP_204_NO_CONTENT)


class SnackView(SCView):
    permission_classes = [SCAuthenticationHttp]

    def dispatch(self, request, *args, **kwargs):
        """Verifica se a categoria e o item existe antes de acessar os endpoints."""

        category_name = kwargs.get("category_name")
        snack_name = kwargs.get("snack_name")

        query_category = get_object_or_404(
            SnackCategory, name=category_name, deletion_date__isnull=True
        )
        query_snack = get_object_or_404(
            Snack, name=snack_name, category=query_category, deletion_date__isnull=True
        )
        kwargs["snack"] = query_snack

        return super().dispatch(request, *args, **kwargs)

    def validate_before_access(self, user: User, _) -> bool:
        """Verifica se o usuário tem autorização para acessar qualquer endpoint."""

        return user.is_employee

    def get(self, _, category_name, snack_name, snack):
        """Retorna os dados do lanche."""

        serializer = SnackSerializer(snack)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, category_name, snack_name, snack):
        """Edita os dados do lanche."""

        data = request.data
        if data.get("price", None):
            data["price"] = format_price(data["price"], to_float=True)

        serializer = SnackSerializer(
            snack, data=data, partial=True, remove_field=["category"]
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Notifica todos os clientes websocket sobre a edição do lanche no estoque de lanches.
        dispatch_message_websocket("snacks_group", "snacks_update")

        return Response(
            {
                "message": f"O item {snack_name} da categoria {category_name} foi editado com sucesso."
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, _, category_name, snack_name, snack):
        """Marca o item como excluído."""

        snack.deletion_date = timezone.now()
        snack.save()

        # Notifica todos os clientes websocket sobre a exclusão do lanche no estoque de lanches.
        dispatch_message_websocket("snacks_group", "snacks_update")

        return Response(status=status.HTTP_204_NO_CONTENT)
