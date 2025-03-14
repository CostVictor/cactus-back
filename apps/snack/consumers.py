from channels.db import database_sync_to_async
from core.consumers import SCWebsocketConsumer

from .models import SnackCategory
from .serializers import CategorySerializer


class SnacksConsumer(SCWebsocketConsumer):
    """Consumer para gerenciar atualizações em tempo real dos lanches.

    Este consumer mantém uma conexão WebSocket com o cliente para enviar atualizações
    sobre mudanças no estoque de lanches. Ele também gerencia a autorização do usuário
    e a comunicação em grupo para atualizações em tempo real.
    """

    async def connect(self):
        self.group_name = "snacks_group"
        await self.accept()

        user = await self.get_user()
        if user and user.is_employee:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.send_stock_snacks()
            return

        await self.close(code=4003, reason="Usuário não autorizado.")

    async def disconnect(self, _):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def snacks_update(self, _):
        await self.send_stock_snacks()

    async def send_stock_snacks(self):
        """Obtém e envia o estado atual dos lanches para o cliente."""

        stock_snacks = await self.get_snacks()
        await self.send_json(stock_snacks)

    @database_sync_to_async
    def get_snacks(self):
        """Obtém todas as categorias e lanches ativos do banco de dados.

        Returns:
            list: Lista serializada de categorias e seus lanches associados.
        """

        categories = SnackCategory.objects.filter(deletion_date__isnull=True).order_by(
            "position_order"
        )
        serializer = CategorySerializer(categories, many=True)
        return serializer.data
