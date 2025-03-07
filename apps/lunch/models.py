from django.db import models
from core.variables import days_week


class Dish(models.Model):
    id = models.BigAutoField(primary_key=True)
    day = models.IntegerField()
    price = models.DecimalField(max_digits=4, decimal_places=2)
    initial_deadline = models.TimeField(
        help_text="Insira um horário no formato HH:MM:SS.", blank=True, null=True
    )
    deadline = models.TimeField(
        help_text="Insira um horário no formato HH:MM:SS.", blank=True, null=True
    )
    description = models.TextField(blank=True, null=True)
    path_img = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "SC_Dish"

    def __str__(self):
        return f"Prato - {days_week[self.day]}"


class Ingredient(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    additional_charge = models.DecimalField(
        max_digits=3, decimal_places=2, blank=True, null=True
    )
    deletion_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "SC_Ingredient"

    def __str__(self):
        return self.name


class Composition(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    config_choice_number = models.IntegerField()

    class Meta:
        db_table = "SC_Composition"
        unique_together = ("dish", "ingredient")

    def __str__(self):
        return f"Composição - {days_week[self.dish.day]} / {self.ingredient.name}"
