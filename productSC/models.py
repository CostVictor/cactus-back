from django.db import models


class Product_category(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    position_order = models.IntegerField()
    path_img = models.CharField(max_length=255, blank=True, null=True)
    deletion_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "SC_Product_category"

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    quantity_in_stock = models.IntegerField()
    price = models.DecimalField(max_digits=4, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    path_img = models.CharField(max_length=255, blank=True, null=True)
    deletion_date = models.DateTimeField(blank=True, null=True)
    category = models.ForeignKey(
        Product_category, on_delete=models.CASCADE, related_name="products"
    )

    class Meta:
        db_table = "SC_Product"

    def __str__(self):
        return self.name
