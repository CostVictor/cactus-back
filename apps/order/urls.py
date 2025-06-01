from django.urls import path

from .views import OrdersView, OrderView, PaidOrderView

urlpatterns = [
    path("", OrdersView.as_view(), name="orders"),
    # path("pay", OrdersView.as_view(), name="pay_orders"),
    path("<str:public_id>/", OrderView.as_view(), name="order"),
    path("<str:public_id>/paid", PaidOrderView.as_view(), name="paid_order"),
    # path("<str:public_id>/pay", PayView.as_view(), name="pay_order"),
]
