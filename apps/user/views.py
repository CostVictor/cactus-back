from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework import status

from core.view import SCView

from .models import User
from .serializers import UserSerializer


class AllView(SCView):
    @SCView.access_to_employee
    def get(self, request):
        """Retorna o nome de todos os usuários não funcionários e o nome do funcionário solicitante."""

        users = (
            User.objects.filter(
                deletion_date__isnull=True,
                is_employee=False,
                is_active=True,
            )
            .order_by("username")
            .all()
        )

        all_names = {
            "applicant": request.user.username,
            "users": [user.username for user in users],
        }

        return Response(all_names, status=status.HTTP_200_OK)


class RegisterView(SCView):
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "limited_access"

    def post(self, request):
        """Cria um novo usuário."""

        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Garante que todos os mecanismos de ADM sejam revogados.
        # serializer.save(is_employee=False, is_staff=False, is_superuser=False)

        # Remover em produção!!
        serializer.save(is_employee=True, is_staff=True, is_superuser=True)
        # ~

        return Response(
            {"message": "A conta foi cadastrada com sucesso."},
            status=status.HTTP_201_CREATED,
        )


class UserView(SCView):
    def dispatch(self, request, *args, **kwargs):
        username = kwargs.get("username")
        query_user = get_object_or_404(
            User, username=username, is_active=True, deletion_date__isnull=True
        )

        if request.user == query_user or request.user.is_employee:
            kwargs["target_user"] = query_user
            return super().dispatch(request, *args, **kwargs)

        return Response({"message": "Acesso negado."}, status=status.HTTP_403_FORBIDDEN)

    def get(self, _, username, target_user):
        """Retorna os dados do usuário."""

        serializer = UserSerializer(target_user, remove_field=["email", "password"])
        return Response(serializer.data, status=status.HTTP_200_OK)

    @SCView.access_to_owner
    def patch(self, request, username, target_user):
        """Edita os dados do usuário."""

        serializer = UserSerializer(target_user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @SCView.access_to_owner
    def delete(self, _, username, target_user):
        """Marca o usuário como excluído."""

        target_user.deletion_date = timezone.now()
        target_user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
