from django.urls import path
from .views import AllView, RegisterView, UserView


urlpatterns = [
    path("all/", AllView.as_view(), name="all_users"),
    path("register/", RegisterView.as_view(), name="register"),
    path("<str:username>/", UserView.as_view(), name="user"),
]
