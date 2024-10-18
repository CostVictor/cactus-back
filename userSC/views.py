from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import UserSerializer


class RegisterView(APIView):
    def post(self, request):
        print(request.data)
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data["is_employee"] = False
        serializer.save()

        return Response(
            {"message": "A conta foi cadastrada com sucesso."},
            status=status.HTTP_201_CREATED,
        )
