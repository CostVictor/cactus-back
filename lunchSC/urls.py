from django.urls import path
from .views import LunchWeekView, DishView, IngredientsView, CompositionView

urlpatterns = [
    path("", LunchWeekView.as_view(), name="lunch_week"),
    path("<str:dish_name>/", DishView.as_view(), name="dish"),
    path(
        "<str:dish_name>/<str:ingredient_name>/",
        CompositionView.as_view(),
        name="composition",
    ),
    path(
        "ingredient/<str:ingredient_name>/",
        IngredientsView.as_view(),
        name="ingredient",
    ),
]
