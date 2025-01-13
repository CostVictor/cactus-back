import os
from django.contrib import admin
from django.urls import path, include, re_path
from snackSC import consumers as snack_consumers
from lunchSC import consumers as lunch_comsumers

urlpatterns = [
    path(os.getenv("ADMIN_PANEL"), admin.site.urls),
    path("session/", include("sessionSC.urls"), name="session"),
    path("user/", include("userSC.urls"), name="user"),
    path("snack/", include("snackSC.urls"), name="snack"),
    path("lunch/", include("lunchSC.urls"), name="lunch"),
]

websocket_urlpatterns = [
    re_path(r"^snack/$", snack_consumers.SnacksConsumer.as_asgi()),
    re_path(r"^lunch/$", lunch_comsumers.LunchConsumer.as_asgi()),
]
