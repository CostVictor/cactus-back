from rest_framework import serializers


def price_validator(value):
    # Verifica a existência de preços negativos.
    if value <= 0:
        raise serializers.ValidationError(
            "O valor do preço deve ser maior que zero (0)."
        )

    return value
