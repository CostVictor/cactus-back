import os
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path(os.getenv("ADMIN_PANEL"), admin.site.urls),
]
