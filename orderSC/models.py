from django.db import models

from userSC.models import User
from snackSC.models import Snack
from lunchSC.models import Composition
from lunchSC.variables import days_week


class Order(models.Model):
    id = models.BigAutoField(primary_key=True)
    total_value = models.DecimalField(max_digits=5, decimal_places=2)
    creation_date = models.DateTimeField()
    order_fulfilled = models.BooleanField(default=False)
    final_payment_date = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    deletion_date = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    creator_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="configured_orders"
    )

    class Meta:
        db_table = "SC_Order"

    def __str__(self):
        hour = self.creation_date.hour
        date = self.creation_date.date

        return f"Pedido de {self.user.username} dia {date} às {hour}hrs"


class HistoryChangeOrder(models.Model):
    id = models.BigAutoField(primary_key=True)
    description = models.TextField()
    datetime = models.DateTimeField()
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="edited_orders"
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="editions")

    class Meta:
        db_table = "SC_History_change_order"

    def __str__(self):
        return f"Edição de {self.user.username} no pedido {self.order.id}"


class BuySnack(models.Model):
    snack = models.ForeignKey(Snack, on_delete=models.CASCADE, related_name="purchases")
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="purchased_snacks"
    )
    quantity_product = models.IntegerField(default=1)

    class Meta:
        db_table = "SC_Buy_snack"
        unique_together = ("snack", "order")

    def __str__(self):
        return f"Compra de {self.quantity_product} unidades de {self.snack.name} no pedido {self.order.id}"


class BuyComposition(models.Model):
    composition = models.ForeignKey(
        Composition, on_delete=models.CASCADE, related_name="purchases"
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="purchased_compositions"
    )
    quantity_ingredient = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "SC_Buy_composition"
        unique_together = ("composition", "order")

    def __str__(self):
        day = days_week[self.composition.dish.day]
        ingredient = self.composition.ingredient.name

        return f"Compra de {self.quantity_ingredient} unidades de {ingredient} do prato de {day}, pedido {self.order.id}"
