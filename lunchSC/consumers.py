from channels.db import database_sync_to_async
from cactus.core.consumers import SCWebsocketConsumer

from .serializers import IngredientSerializer, DishSerializer
from .models import Ingredient, Dish


class LunchConsumer(SCWebsocketConsumer):
    """Consumer para gerenciar atualizações em tempo real dos almoços.

    Este consumer mantém uma conexão WebSocket com o cliente para enviar atualizações
    sobre mudanças no estoque de almoço. Ele também gerencia a autorização do usuário
    e a comunicação em grupo para atualizações em tempo real.
    """

    async def connect(self):
        self.group_name = "lunch_group"
        await self.accept()

        user = await self.get_user()
        if user and user.is_employee:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.send_stock_lunch()
            return

        await self.close(code=4003, reason="Usuário não autorizado.")

    async def disconnect(self, _):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def lunch_update(self, _):
        await self.send_stock_lunch()

    async def send_stock_lunch(self):
        """Obtém e envia o estado atual do estoque de almoço para o cliente."""

        stock_lunch = await self.get_lunch()
        await self.send_json(stock_lunch)

    @database_sync_to_async
    def get_lunch(self):
        """Obter os dados dos ingredientes e dos pratos."""

        ingredients = Ingredient.objects.filter(deletion_date__isnull=True)
        ingredient_serializer = IngredientSerializer(ingredients, many=True)

        dish_serializer = DishSerializer(Dish.objects, many=True)

        return {
            "ingredients": ingredient_serializer.data,
            "dishes": dish_serializer.data,
        }
