from django.core.management.base import BaseCommand
from django.db import transaction

from lunch.models import Dish


class Command(BaseCommand):
    help = "Verifica a existência dos 5 pratos da semana, criando-os caso não existam."

    def handle(self, *args, **options):
        if not Dish.objects.exists():
            with transaction.atomic():
                for day in range(5):
                    dish = Dish(day=day + 1, price=10)
                    dish.save()
