import os
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path(os.getenv("ADMIN_PANEL"), admin.site.urls),
    path("session/", include("sessionSC.urls"), name="session"),
    path("user/", include("userSC.urls"), name="user"),
    path("snacks/", include("snackSC.urls"), name="snacks"),
]
