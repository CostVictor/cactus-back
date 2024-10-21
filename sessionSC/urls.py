from django.urls import path
from .views import LoginView, LogoutView, RefreshView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh_token/", RefreshView.as_view(), name="refresh"),
]
