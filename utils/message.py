from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def dispatch_message_websocket(group_name: str, type_message: str, message=""):
    """Dispara uma mensagem para um grupo de clientes websocket do sistema Cactus."""

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name, {"type": type_message, "message": message}
    )
