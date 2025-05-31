from core.view import SCView
from django.shortcuts import get_object_or_404

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

        creator_user = response.user
        target_username = data.get("username", None)
        target_user = (
            User.objects.filter(
                username=target_username, is_active=True, deletion_date__isnull=True
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

        serializer = OrderSerializer(
            data=data,
            remove_field=[
                "public_id",
                "creation_date",
                "final_payment_date",
                "full_amount",
                "amount_snacks",
                "amount_lunch",
                "amount_due",
                "fulfilled",
                "hidden",
            ],
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        dispatch_message_websocket("orders_group", "orders_update")

        return Response(
            {"message": "Pedido criado com sucesso."}, status=status.HTTP_201_CREATED
        )


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

        order.delete()
        dispatch_message_websocket("order_group", "order_update")

        return Response(status=status.HTTP_204_NO_CONTENT)


# class PaidOrderView(SCView):
#     def post(self, response): ...


# class PayOrderView(SCView):
#     def post(self, response): ...
