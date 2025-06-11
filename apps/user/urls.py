from django.urls import path
from .views import RegisterView


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("<str:username>/", RegisterView.as_view(), name="user"),
]
