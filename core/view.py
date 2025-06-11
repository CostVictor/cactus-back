from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from functools import wraps


class SCView(APIView):
    ignore_authentication_for_methods = []

    def http_method_not_allowed(self, request, *args, **kwargs):
        method = request.method.upper()
        return Response(
            {"detail": f"O Método {method} não é permitido."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def get_authenticators(self):
        if self.request.method.lower() in self.ignore_authentication_for_methods:
            return []

        return super().get_authenticators()

    def access_to_employee(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            _, request = args
            user = request.user

            if user.is_anonymous or not user.is_employee:
                raise PermissionDenied("Você não tem permissão para acessar essa rota.")

            return view(*args, **kwargs)

        return wrapper

    def access_to_owner(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            _, request = args
            user = request.user
            target_user = kwargs.get("target_user", None)

            if user.is_anonymous or user != target_user:
                raise PermissionDenied("Você não tem permissão para acessar essa rota.")

            return view(*args, **kwargs)

        return wrapper
