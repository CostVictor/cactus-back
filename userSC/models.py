from django.db import models


class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=128)
    is_employee = models.BooleanField(default=False)
    deletion_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "SC_User"

    def __str__(self):
        return self.nome


class User_details(models.Model):
    sc_user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    tel = models.CharField(max_length=15)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=2, blank=True, default="RN")
    path_img_profile = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "SC_User_details"

    def __str__(self):
        return f"{self.user.username} - Details"
