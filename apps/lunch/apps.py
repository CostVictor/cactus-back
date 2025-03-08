from django.core.management import call_command
from django.db.models.signals import post_migrate
from django.apps import AppConfig


class LunchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.lunch"

    def ready(self):
        post_migrate.connect(self.check_dishes)

    def check_dishes(self, sender, **kwargs):
        call_command("check_dishes")
