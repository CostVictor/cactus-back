from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from typing import Callable

from apps.user.models import User


class SCView(APIView):
    ignore_validation_for_methods: list[str] = []

    def http_method_not_allowed(self, request, *args, **kwargs):
        method = request.method.upper()
        return Response(
            {"detail": f"O Método {method} não é permitido."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def validate_before_access(self, user: User, method: str) -> bool:
        """Valida se um usuário tem permissão para acessar um método específico antes da execução.

        Esta função verifica se existe uma validação específico para o método solicitado
        e o executa, retornando True se a validação passar ou False caso contrário. Métodos
        listados em `ignore_validation_for_methods` são ignorados na validação.

        Nota: Ao sobreescrever essa função, a validação será aplicada a todos os métodos.

        Args:
            user (User): O objeto do usuário que está tentando acessar o método.
            method (str): O nome do método a ser validado (ex.: 'post', 'update').

        Returns:
            bool: True se o acesso é permitido, False se o acesso é negado ou a validação falhar.
        """

        validator_method_name = f"validate_{method}_before_access"

        if hasattr(self, validator_method_name):
            validator_method: Callable[[User, str], bool] = getattr(
                self, validator_method_name
            )

            if callable(validator_method) and not validator_method(user, method):
                return False

        return True
