from rest_framework.response import Response
from rest_framework import status

from cactus.core.authentication import SCAuthentication
from cactus.core.view import SCView

from .models import Product_category
from .serializers import CategorySerializer


class ListCategoryProductsView(SCView):
    def get(self, _):
        # Ordena os valores por `position_order`.
        categories = Product_category.objects.all().order_by("position_order")
        serializer = CategorySerializer(categories, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class CategoryView(SCView):
    permission_classes = [SCAuthentication]

    def post(self, request): ...


class ProductView(SCView):
    permission_classes = [SCAuthentication]

    def get(self, request): ...
