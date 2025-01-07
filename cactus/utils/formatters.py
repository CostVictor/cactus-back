from rest_framework.exceptions import ValidationError


def format_price(value, to_float=False):
    """
    Formata um valor numérico para o formato de preço em reais (R$) ou converte um preço formatado para float.

    Args:
        value (Union[float, str]): O valor a ser formatado. Pode ser um número ou uma string no formato "R$ X,XX"
        to_float (bool, optional): Se True, converte de string formatada para float. Se False, formata o número. Defaults to False.

    Returns:
        Union[str, float]: String formatada como preço (R$ X,XX) ou valor float

    Raises:
        ValidationError: Se o valor fornecido não puder ser convertido para número quando to_float=True
    """
    if to_float:
        newValue = value.replace("R$", "").replace(",", ".")
        try:
            value = float(newValue)
            if value < 0:
                raise ValidationError(
                    "O valor fornecido deve ser no mínimo zero (R$ 0,00)."
                )

            return value
        except:
            raise ValidationError("O valor fornecido não é válido.")

    return f"R$ {value:.2f}".replace(".", ",")
