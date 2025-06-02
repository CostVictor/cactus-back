from channels.db import database_sync_to_async
from core.consumers import SCWebsocketConsumer

from .models import Order
from .serializers import OrderSerializer


class OrderConsumer(SCWebsocketConsumer):
    """Consumer para gerenciar atualizações em tempo real dos pedidos.

    Este consumer mantém uma conexão WebSocket com o cliente para enviar atualizações
    sobre mudanças no estoque de pedidos.
    """

    async def connect(self):
        self.group_name = "orders_group"
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
        """Obtém e envia o estado atual dos pedidos para o cliente."""

        orders = await self.get_orders()
        await self.send_json(orders)

    @database_sync_to_async
    def get_orders(self):
        """Obtém todos os pedidos ainda não atendidos do banco de dados.

        Returns:
            list: Lista serializada de pedidos.
        """

        orders = Order.objects.filter(fulfilled=False).order_by("creation_date")
        serializer = OrderSerializer(
            orders,
            many=True,
            remove_field=["creator_user, creation_date", "fulfilled", "hidden"],
        )
        return serializer.data
