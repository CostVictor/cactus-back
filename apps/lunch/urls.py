from django.urls import path
from .views import (
    LunchWeekView,
    DishView,
    IngredientsView,
    IngredientView,
    CompositionView,
)

urlpatterns = [
    path("", LunchWeekView.as_view(), name="lunch_week"),
    path("ingredients/", IngredientsView.as_view(), name="ingredients"),
    path(
        "ingredients/<str:ingredient_name>/",
        IngredientView.as_view(),
        name="ingredient",
    ),
    path("<str:dish_name>/", DishView.as_view(), name="dish"),
    path(
        "<str:dish_name>/<str:ingredient_name>/",
        CompositionView.as_view(),
        name="composition",
    ),
]
