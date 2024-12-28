from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from datetime import timedelta


def generate_response_with_cookie(
    refresh_token: RefreshToken, data: dict, status=status.HTTP_200_OK, days_long=7
):
    """Cria uma response com os cookies de access e refresh configurados em httponly."""

    # ~ Criação da response com cookies.
    response = Response(data, status=status)
    max_age = int(timedelta(days=days_long).total_seconds())

    response.set_cookie(
        key="refresh_token",
        value=str(refresh_token),
        secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
        samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
        httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
        max_age=max_age,
        path="/session/",
    )

    response.set_cookie(
        key="access_token",
        value=str(refresh_token.access_token),
        secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
        samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
        httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
        max_age=max_age,
        path="/",
    )

    return response
