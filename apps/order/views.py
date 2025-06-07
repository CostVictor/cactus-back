from core.view import SCView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction

from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from utils.message import dispatch_message_websocket

from apps.user.models import User

from .models import Order
from .serializers import OrderSerializer


class OrdersView(SCView):
    def get(self, request):
        """Retorna os detalhes de todos os pedidos."""

        user = request.user
        orders = Order.objects

        if not user.is_employee:
            orders = orders.filter(user=user)

        order_serializer = OrderSerializer(orders, many=True)
        return Response(order_serializer.data, status=status.HTTP_200_OK)

    def post(self, response):
        """Cria um novo pedido."""

        data = response.data
        message = "Pedido criado com sucesso."

        creator_user = response.user
        target_username = data.get("username", None)
        target_user = (
            User.objects.filter(
                username=target_username.replace("Func.", "").strip(),
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
                    "hidden",
                ],
            )
            serializer.is_valid(raise_exception=True)
            order = serializer.save()

            if (not target_user and creator_user.is_employee) or (
                target_user and target_user.is_employee
            ):
                message = "A compra foi registrada."
                order.final_payment_date = timezone.now()

                if not order.purchased_compositions.exists():
                    order.fulfilled = True
                    order.hidden = True

                order.save()

        dispatch_message_websocket("orders_group", "orders_update")

        return Response({"message": message}, status=status.HTTP_201_CREATED)


# class PayOrdersView(SCView):
#     def post(self, response): ...


class OrderView(SCView):
    def dispatch(self, request, *args, **kwargs):
        is_employee = request.user.is_employee
        public_id = kwargs.get("public_id")

        if is_employee:
            kwargs["order"] = get_object_or_404(
                Order,
                public_id=public_id,
            )
            return super().dispatch(request, *args, **kwargs)

        query_order = get_object_or_404(
            Order,
            public_id=public_id,
            user=request.user,
        )
        kwargs["order"] = query_order

        return super().dispatch(request, *args, **kwargs)

    def get(self, _, public_id, order):
        """Retorna os detalhes de um pedido."""

        order_serializer = OrderSerializer(order)
        return Response(order_serializer.data, status=status.HTTP_200_OK)

    def delete(self, _, public_id, order):
        """Apaga todos os registros associado a um pedido caso ele não tenha sido pago."""

        if order.final_payment_date:
            raise ValidationError("Não é possivel apagar um pedido que já foi pago.")

        with transaction.atomic():
            for item in order.purchased_snacks:
                target_snack = item.snack
                target_snack.quantity_in_stock += item.quantity_product
                target_snack.save()

            order.delete()

        dispatch_message_websocket("order_group", "order_update")

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
        order.hidden = True
        order.save()

        dispatch_message_websocket("order_group", "order_update")

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

        dispatch_message_websocket("order_group", "order_update")

        return Response(status=status.HTTP_204_NO_CONTENT)


# class PayOrderView(SCView):
#     def post(self, response): ...
