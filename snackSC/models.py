from django.db import models


class Snack_category(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    position_order = models.IntegerField()
    path_img = models.CharField(max_length=255, blank=True, null=True)
    deletion_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "SC_Snack_category"

    def __str__(self):
        return self.name


class Description(models.Model):
    category = models.OneToOneField(
        Snack_category,
        on_delete=models.CASCADE,
        related_name="description",
        primary_key=True,
    )
    illustration_url = models.CharField(max_length=255)
    title = models.CharField(max_length=50)
    text = models.TextField()

    class Meta:
        db_table = "SC_Snack_category_description"

    def __str__(self):
        return f"{self.category.name} - Description"


class Snack(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    quantity_in_stock = models.IntegerField()
    price = models.DecimalField(max_digits=4, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    path_img = models.CharField(max_length=255, blank=True, null=True)
    deletion_date = models.DateTimeField(blank=True, null=True)
    category = models.ForeignKey(
        Snack_category, on_delete=models.CASCADE, related_name="snacks"
    )

    class Meta:
        db_table = "SC_Snack"

    def __str__(self):
        return self.name
