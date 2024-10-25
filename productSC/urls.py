from django.urls import path
from .views import ListCategoryProductsView, ProductView


urlpatterns = [
    path("", ListCategoryProductsView.as_view(), name="categories"),
    path("<str:product_name>/", ProductView.as_view(), name="product"),
]
