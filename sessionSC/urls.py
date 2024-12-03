from django.urls import path
from .views import LoginView, LogoutView, RefreshView, CheckAuthView

# Caso altere a URL base, mudar também nos cookies do arquivo utils do app sessionSC.

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh_token/", RefreshView.as_view(), name="refresh"),
    path("check_auth/", CheckAuthView.as_view(), name="check_auth"),
]
