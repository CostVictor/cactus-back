import os
from django.contrib import admin
from django.urls import path, include
from sessionSC.views import LoginView, LogoutView, RefreshView


urlpatterns = [
    path(os.getenv("ADMIN_PANEL"), admin.site.urls),
    path("api/login/", LoginView.as_view(), name="login"),
    path("api/logout/", LogoutView.as_view(), name="logout"),
    path("api/refresh_token/", RefreshView.as_view(), name="refresh"),
    path("api/user/", include("userSC.urls")),
]
