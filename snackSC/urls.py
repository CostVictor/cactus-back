from django.urls import path
from .views import SnackCategoriesView, CategoryView, SnackView


urlpatterns = [
    path("", SnackCategoriesView.as_view(), name="categories"),
    path("<str:category_name>", CategoryView.as_view(), name="category"),
]
