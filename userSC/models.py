from django.db import models


class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    email = models.CharField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=128)
    is_employee = models.BooleanField(default=False)
    deletion_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.nome


class User_details(models.Model):
    id = models.OneToOneField(User, on_delete=models.CASCADE)
    tel = models.CharField(max_length=15)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=2, blank=True, default="RN")
    path_img_profile = models.CharField(max_length=255, blank=True, null=True)
