from django.db import models
import uuid

from apps.user.models import User
from apps.snack.models import Snack
from apps.lunch.models import Composition

from core.variables import days_week


class Order(models.Model):
    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    amount_snacks = models.DecimalField(max_digits=5, decimal_places=2)
    amount_lunch = models.DecimalField(max_digits=5, decimal_places=2)
    amount_due = models.DecimalField(max_digits=5, decimal_places=2)
    creation_date = models.DateTimeField()
    fulfilled = models.BooleanField(default=False)
    final_payment_date = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    hidden = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    creator_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="configured_orders"
    )

    class Meta:
        db_table = "Order"

    def __str__(self):
        hour = self.creation_date.hour
        date = self.creation_date.strftime("%d/%m/%Y")

        return f"Pedido de {self.user.username} feito dia {date} às {hour}hrs"


class BuySnack(models.Model):
    snack = models.ForeignKey(Snack, on_delete=models.CASCADE, related_name="purchases")
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="purchased_snacks"
    )
    quantity_product = models.IntegerField(default=1)
    price_to_purchase = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        db_table = "Buy_snack"
        unique_together = ("snack", "order")

    def __str__(self):
        return f"Compra de {self.quantity_product} unidades de {self.snack.name} no pedido {self.order.id}"


class BuyIngredient(models.Model):
    composition = models.ForeignKey(
        Composition, on_delete=models.CASCADE, related_name="purchases"
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="purchased_compositions"
    )
    quantity_ingredient = models.IntegerField(blank=True, null=True)
    price_to_purchase_dish = models.DecimalField(max_digits=4, decimal_places=2)
    price_to_purchase_ingredient = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        db_table = "Buy_composition"
        unique_together = ("composition", "order")

    def __str__(self):
        day = days_week[self.composition.dish.day]
        ingredient = self.composition.ingredient.name

        return f"Compra de {self.quantity_ingredient} unidades de {ingredient} do prato de {day}, pedido {self.order.id}"
