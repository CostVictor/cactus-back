from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)


class UserManager(BaseUserManager):
    def create_superuser(self, username, password, **extra_fields):
        """Cria um superusuário"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)

    # ADM do sistema.
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["password"]

    objects = UserManager()

    # Campos customizados.
    is_employee = models.BooleanField(default=False)
    deletion_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "SC_User"

    def __str__(self):
        return self.username


class UserDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    tel = models.CharField(max_length=15)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=2, blank=True, default="RN")
    path_img_profile = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "SC_User_details"

    def __str__(self):
        return f"{self.user.username} - Details"
