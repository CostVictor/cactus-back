import os
from django.contrib import admin
from django.urls import path, include, re_path
from apps.snack import consumers as snack_consumers
from apps.lunch import consumers as lunch_comsumers

urlpatterns = [
    path(os.getenv("ADMIN_PANEL"), admin.site.urls),
    path("session/", include("apps.session.urls"), name="session"),
    path("user/", include("apps.user.urls"), name="user"),
    path("snack/", include("apps.snack.urls"), name="snack"),
    path("lunch/", include("apps.lunch.urls"), name="lunch"),
]

websocket_urlpatterns = [
    re_path(r"^snack/$", snack_consumers.SnacksConsumer.as_asgi()),
    re_path(r"^lunch/$", lunch_comsumers.LunchConsumer.as_asgi()),
]
