from urllib import request
from core.view import SCView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from datetime import timedelta

from utils.message import dispatch_message_websocket
from apps.user.models import User

from .models import Order
from .serializers import OrderSerializer


class OrdersView(SCView):
    def get(self, request):
        """
        Retorna uma lista de pedidos conforme parâmetros da requisição.

        Parâmetros de consulta (query params):
        - date (opcional): filtra pedidos pela data de criação (formato esperado: YYYY-MM-DD).
        - paid (opcional): filtra pedidos pagos ou não pagos.
          - "true" -> retorna pedidos pagos.
          - qualquer outro valor ou ausente -> retorna pedidos não pagos.
        """

        query_param_date = request.query_params.get("date", None)

        # Pedidos pagos -> final_payment_date != Null
        # Pedidos não pagos -> final_payment_date == Null
        has_final_payment_date = (
            not request.query_params.get("paid", "false").lower() == "true"
        )

        query_filter = {
            "final_payment_date__isnull": has_final_payment_date,
            "user": request.user,
        }

        if query_param_date:
            query_filter["creation_date__date"] = query_param_date

        orders = Order.objects.filter(**query_filter)
        orders_serializer = OrderSerializer(
            orders, many=True, remove_field=["input_snacks", "input_lunch", "user"]
        )

        return Response(orders_serializer.data, status=status.HTTP_200_OK)

    def post(self, response):
        """Cria um novo pedido."""

        data = response.data
        message = "Pedido criado com sucesso."

        creator_user = response.user
        target_username = data.get("username", None)
        target_user = (
            User.objects.filter(
                username=target_username.replace("Func.", "")
                .replace("(Você)", "")
                .strip(),
                deletion_date__isnull=True,
                is_active=True,
            ).first()
            if target_username
            else None
        )

        data["creator_user"] = creator_user.id
        data["user"] = (
            target_user.id
            if target_user and creator_user.is_employee
            else creator_user.id
        )

        with transaction.atomic():
            serializer = OrderSerializer(
                data=data,
                remove_field=[
                    "public_id",
                    "creation_date",
                    "final_payment_date",
                    "amount_snacks",
                    "amount_lunch",
                    "amount_due",
                    "fulfilled",
                    "snacks",
                    "lunch",
                ],
            )
            serializer.is_valid(raise_exception=True)
            order = serializer.save()

            is_order_lunch = order.amount_lunch > 0

            if creator_user.is_employee:
                message = "A compra foi registrada."

                if (not target_user or target_user.is_employee) or (
                    not target_user.is_employee
                    and data.get("wasPaid", "false").lower() == "true"
                ):
                    order.final_payment_date = timezone.now()

                if not is_order_lunch:
                    order.fulfilled = True

                order.save()

        dispatch_message_websocket(
            "orders_lunch_group" if is_order_lunch else "orders_snack_group",
            "orders_update",
        )

        return Response({"message": message}, status=status.HTTP_201_CREATED)


class UserOrdersView(SCView):
    def dispatch(self, request, *args, **kwargs):
        username = kwargs.get("username")

        query_user = get_object_or_404(User, username=username)
        kwargs["target_user"] = query_user

        return super().dispatch(request, *args, **kwargs)

    @SCView.access_to_employee
    def get(self, request, username, target_user):
        """
        Retorna a lista de pedidos de um usuário conforme parâmetros da requisição.

        Parâmetros de consulta (query params):
        - date (opcional): filtra pedidos pela data de criação (formato esperado: YYYY-MM-DD).
        - paid (opcional): filtra pedidos pagos ou não pagos.
          - "true"  -> retorna pedidos pagos.
          - qualquer outro valor ou ausente -> retorna pedidos não pagos.
        """

        query_param_date = request.query_params.get("date", None)

        # Pedidos pagos -> final_payment_date != Null
        # Pedidos não pagos -> final_payment_date == Null
        has_final_payment_date = (
            not request.query_params.get("paid", "false").lower() == "true"
        )

        query_filter = {
            "final_payment_date__isnull": has_final_payment_date,
            "user": target_user,
        }

        if query_param_date:
            query_filter["creation_date__date"] = query_param_date

        orders = Order.objects.filter(**query_filter)
        orders_serializer = OrderSerializer(
            orders, many=True, remove_field=["input_snacks", "input_lunch", "user"]
        )

        return Response(orders_serializer.data, status=status.HTTP_200_OK)


# class PayOrdersView(SCView):
#     def post(self, response): ...


class OverviewView(SCView):
    @SCView.access_to_employee
    def get(self, _):
        """
        Retorna um resumo dos pedidos de pagamento por usuário, classificando-os entre pagos no dia atual e pendentes, com base na data de pagamento final.
        """

        today_date = timedelta.now().date()

        orders = Order.objects.filter(
            Q(final_payment_date__isnull=True) | Q(final_payment_date__date=today_date),
        ).order_by("user__username")

        orders_serializer = OrderSerializer(
            orders, many=True, remove_field=["input_snacks", "input_lunch"]
        )

        data = {}

        for order in orders_serializer:
            user = order["user"]
            amount_due = order["amount_due"]

            if user not in data:
                if user == request.user.username:
                    user = f"{user} (Você)"

                data[user] = {"payment_pending": [], "paid_today": []}

            if order["final_payment_date"]:
                data[user]["paid_today"].append(amount_due)
                continue

            data[user]["payment_pending"].append(amount_due)

        return Response(data, status=status.HTTP_200_OK)


class OrderView(SCView):
    def dispatch(self, request, *args, **kwargs):
        public_id = kwargs.get("public_id")

        query_order = get_object_or_404(
            Order,
            public_id=public_id,
        )
        kwargs["order"] = query_order

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, public_id, order):
        """Retorna os detalhes de um pedido."""

        user = request.user

        if not user.is_employee and order.user != user:
            raise PermissionDenied("Você não tem permissão para acessar este pedido.")

        order_serializer = OrderSerializer(
            order, remove_field=["input_snacks", "input_lunch"]
        )
        return Response(order_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, public_id, order):
        """Apaga todos os registros associado a um pedido caso ele não tenha sido pago."""

        user = request.user

        if not user.is_employee and order.user != user:
            raise PermissionDenied("Você não tem permissão para apagar este pedido.")

        if order.final_payment_date or order.fulfilled:
            raise ValidationError(
                "Não é possível apagar um pedido que já foi pago ou atendido."
            )

        is_order_lunch = order.amount_lunch > 0

        with transaction.atomic():
            for item in order.purchased_snacks.all():
                target_snack = item.snack
                target_snack.quantity_in_stock += item.quantity_product
                target_snack.save()

            order.delete()

        dispatch_message_websocket(
            "orders_lunch_group" if is_order_lunch else "orders_snack_group",
            "orders_update",
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class PaidOrderView(SCView):
    def dispatch(self, request, *args, **kwargs):
        public_id = kwargs.get("public_id")

        query_order = get_object_or_404(
            Order,
            public_id=public_id,
        )
        kwargs["order"] = query_order

        return super().dispatch(request, *args, **kwargs)

    @SCView.access_to_employee
    def post(self, _, public_id, order):
        """Marca um pedido como pago de forma manual."""

        order.final_payment_date = timezone.now()
        order.fulfilled = True
        order.save()

        dispatch_message_websocket(
            "orders_lunch_group" if order.amount_lunch > 0 else "orders_snack_group",
            "orders_update",
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class FulfilledOrderView(SCView):
    def dispatch(self, request, *args, **kwargs):
        public_id = kwargs.get("public_id")

        query_order = get_object_or_404(
            Order,
            public_id=public_id,
        )
        kwargs["order"] = query_order

        return super().dispatch(request, *args, **kwargs)

    @SCView.access_to_employee
    def post(self, _, public_id, order):
        """Marca um pedido como atendido."""

        order.fulfilled = True
        order.save()

        dispatch_message_websocket(
            "orders_lunch_group" if order.amount_lunch > 0 else "orders_snack_group",
            "orders_update",
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


# class PayOrderView(SCView):
#     def post(self, response): ...
