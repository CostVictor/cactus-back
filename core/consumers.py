from rest_framework_simplejwt.tokens import AccessToken
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from apps.user.models import User


class SCWebsocketConsumer(AsyncJsonWebsocketConsumer):
    async def get_user(self) -> User | None:
        cookies = self.scope.get("cookies", {})
        access_token = cookies.get("access_token", None)

        if access_token:
            try:
                decoded_token = AccessToken(access_token)
                return await self.get_user_by_id(decoded_token["user_id"])
            except:
                await self.close(code=4001, reason="O token é inválido ou expirou.")

        return None

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        return User.objects.filter(id=user_id).first()
