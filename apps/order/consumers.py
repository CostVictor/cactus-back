from channels.db import database_sync_to_async
from core.consumers import SCWebsocketConsumer
from decimal import Decimal

from .models import Order
from .serializers import OrderSerializer


class OrderSnackConsumer(SCWebsocketConsumer):
    """Consumer para gerenciar atualizações em tempo real dos pedidos de lanches.

    Este consumer mantém uma conexão WebSocket com o cliente para enviar atualizações
    sobre mudanças no estoque de pedidos.
    """

    async def connect(self):
        self.group_name = "orders_snack_group"
        await self.accept()

        user = await self.get_user()
        if user and user.is_employee:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.send_data_orders()
            return

        await self.close(code=4003, reason="Usuário não autorizado.")

    async def disconnect(self, _):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def orders_update(self, _):
        await self.send_data_orders()

    async def send_data_orders(self):
        """Obtém e envia o estado atual dos pedidos de lanches para o cliente."""

        orders = await self.get_orders_snack()
        await self.send_json(orders)

    @database_sync_to_async
    def get_orders_snack(self):
        """Obtém todos os pedidos de lanches ainda não atendidos do banco de dados.

        Returns:
            list: Lista serializada de pedidos.
        """

        orders = Order.objects.filter(
            fulfilled=False, amount_lunch=Decimal(0)
        ).order_by("creation_date")

        serializer = OrderSerializer(
            orders,
            many=True,
            remove_field=["creator_user, creation_date", "fulfilled", "hidden"],
        )
        return serializer.data


class OrderLunchConsumer(SCWebsocketConsumer):
    """Consumer para gerenciar atualizações em tempo real dos pedidos de almoços.

    Este consumer mantém uma conexão WebSocket com o cliente para enviar atualizações
    sobre mudanças no estoque de pedidos.
    """

    async def connect(self):
        self.group_name = "orders_lunch_group"
        await self.accept()

        user = await self.get_user()
        if user and user.is_employee:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.send_data_orders()
            return

        await self.close(code=4003, reason="Usuário não autorizado.")

    async def disconnect(self, _):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def orders_update(self, _):
        await self.send_data_orders()

    async def send_data_orders(self):
        """Obtém e envia o estado atual dos pedidos de almoços para o cliente."""

        orders = await self.get_orders_lunch()
        await self.send_json(orders)

    @database_sync_to_async
    def get_orders_lunch(self):
        """Obtém todos os pedidos de almoços ainda não atendidos do banco de dados.

        Returns:
            list: Lista serializada de pedidos.
        """

        orders = Order.objects.filter(
            fulfilled=False, amount_lunch__gt=Decimal(0)
        ).order_by("creation_date")

        serializer = OrderSerializer(
            orders,
            many=True,
            remove_field=["creator_user, creation_date", "fulfilled", "hidden"],
        )
        return serializer.data
