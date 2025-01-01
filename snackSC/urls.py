from django.urls import path
from .views import SnackCategoriesView, CategoryView, SnackView


urlpatterns = [
    path("", SnackCategoriesView.as_view(), name="categories"),
    path("<str:category_name>/", CategoryView.as_view(), name="category"),
    path("<str:category_name>/<str:snack_name>/", SnackView.as_view(), name="snack"),
]
