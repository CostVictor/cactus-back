from django.urls import path

from .views import OrdersView, OrderView, PaidOrderView, FulfilledOrderView

urlpatterns = [
    path("", OrdersView.as_view(), name="orders"),
    # path("pay", .as_view(), name="pay_orders"),
    # path("u/<str:username>", .as_view(), name="user_orders"),
    path("r/<str:public_id>", OrderView.as_view(), name="order"),
    path("r/<str:public_id>/paid", PaidOrderView.as_view(), name="paid_order"),
    path(
        "r/<str:public_id>/fulfilled",
        FulfilledOrderView.as_view(),
        name="fulfilled_order",
    ),
    # path("r/<str:public_id>/pay", .as_view(), name="pay_order"),
]
