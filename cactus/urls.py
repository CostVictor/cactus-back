import os
from django.contrib import admin
from django.urls import path, include, re_path
from apps.snack import consumers as snack_consumers
from apps.lunch import consumers as lunch_comsumers
from apps.order import consumers as order_consumers

urlpatterns = [
    path(os.getenv("ADMIN_PANEL"), admin.site.urls),
    path("session/", include("apps.session.urls"), name="session"),
    path("user/", include("apps.user.urls"), name="user"),
    path("snack/", include("apps.snack.urls"), name="snack"),
    path("lunch/", include("apps.lunch.urls"), name="lunch"),
    path("order/", include("apps.order.urls"), name="order"),
]

websocket_urlpatterns = [
    re_path(r"^ws/snack/$", snack_consumers.SnacksConsumer.as_asgi()),
    re_path(r"^ws/lunch/$", lunch_comsumers.LunchConsumer.as_asgi()),
    re_path(r"^ws/order/snack/$", order_consumers.OrderSnackConsumer.as_asgi()),
    re_path(r"^ws/order/lunch/$", order_consumers.OrderLunchConsumer.as_asgi()),
]
