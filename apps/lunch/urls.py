from django.urls import path
from .views import (
    LunchWeekView,
    TodayView,
    DishView,
    IngredientsView,
    IngredientView,
    CompositionView,
)

urlpatterns = [
    path("", LunchWeekView.as_view(), name="lunch_week"),
    path("today", TodayView.as_view(), name="today"),
    path("i", IngredientsView.as_view(), name="ingredients"),
    path(
        "i/<str:ingredient_name>",
        IngredientView.as_view(),
        name="ingredient",
    ),
    path("d/<str:dish_name>", DishView.as_view(), name="dish"),
    path(
        "d/<str:dish_name>/<str:ingredient_name>",
        CompositionView.as_view(),
        name="composition",
    ),
]
