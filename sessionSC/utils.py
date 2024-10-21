from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from datetime import timedelta


def generate_response_with_cookie(
    refresh_token: RefreshToken, data: dict, status=status.HTTP_200_OK, days_long=365
):
    """Cria uma response com os cookies de access e refresh configurados em httponly."""

    response = Response(data, status=status)

    response.set_cookie(
        key="refresh_token",
        value=str(refresh_token),
        httponly=True,
        secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
        samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
        max_age=timedelta(days=days_long).total_seconds(),
        path="api/session/",
    )

    response.set_cookie(
        key="access_token",
        value=str(refresh_token.access_token),
        httponly=True,
        secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
        samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
        max_age=timedelta(days=days_long).total_seconds(),
        path="/",
    )

    return response
