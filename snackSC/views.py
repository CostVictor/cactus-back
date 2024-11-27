from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework import status

from cactus.core.authentication import SCAuthentication
from cactus.core.view import SCView

from .models import Snack_category
from .serializers import CategorySerializer


class SnackCategoriesView(SCView):
    def get(self, _):
        # Ordena as categorias por `position_order`.
        categories = Snack_category.objects.all().order_by("position_order")
        serializer = CategorySerializer(categories, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request) -> Response:
        # Verificando se o usuário está autenticado e possui autorização.
        user, _ = SCAuthentication().authenticate(request)
        if not user.is_employee:
            raise PermissionDenied(
                "Você não tem autorização para acessar este recurso."
            )

        data = request.data
        if Snack_category.objects.filter(name=data["name"]):
            raise ValidationError(f'A categoria "{data["name"]}" já existe.')

        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Categoria criada com sucesso."}, status=status.HTTP_200_OK
        )


class CategoryView(SCView):
    permission_classes = [SCAuthentication]

    def get(
        self,
        request,
    ): ...

    def post(self, request): ...


class SnackView(SCView):
    permission_classes = [SCAuthentication]

    def get(self, request): ...
