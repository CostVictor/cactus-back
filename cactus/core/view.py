from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from userSC.models import User


class SCView(APIView):
    def get(self, request: Request) -> Response:
        return Response(
            {"detail": 'O Método GET não é permitido.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def post(self, request: Request) -> Response:
        return Response(
            {"detail": 'O Método POST não é permitido.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def put(self, request: Request) -> Response:
        return Response(
            {"detail": 'O Método PUT não é permitido.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def patch(self, request: Request) -> Response:
        return Response(
            {"detail": 'O Método PATCH não é permitido.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def delete(self, request: Request) -> Response:
        return Response(
            {"detail": 'O Método DELETE não é permitido.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def validate_before_access(self, user: User) -> bool:
        """Validar o que é exigido para acessar qualquer endpoint da view."""

        return True

    def validate_get_before_access(self, user: User) -> bool:
        """Validar o que é exigido para acessar o método get da view."""

        return True

    def validate_post_before_access(self, user: User) -> bool:
        """Validar o que é exigido para acessar o método post da view."""

        return True

    def validate_put_before_access(self, user: User) -> bool:
        """Validar o que é exigido para acessar o método put da view."""

        return True

    def validate_patch_before_access(self, user: User) -> bool:
        """Validar o que é exigido para acessar o método patch da view."""

        return True

    def validate_delete_before_access(self, user: User) -> bool:
        """Validar o que é exigido para acessar o método delete da view."""

        return True
