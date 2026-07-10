import re

from django.core.exceptions import ValidationError


def validar_cpf(valor):
    """Valida dígitos verificadores de CPF. Silencioso se vazio (obrigatoriedade é decidida no form)."""
    digitos = re.sub(r'\D', '', valor or '')
    if not digitos:
        return

    if len(digitos) != 11 or digitos == digitos[0] * 11:
        raise ValidationError('CPF inválido.')

    soma = sum(int(digitos[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    digito1 = 0 if resto == 10 else resto

    soma = sum(int(digitos[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    digito2 = 0 if resto == 10 else resto

    if digitos[-2:] != f'{digito1}{digito2}':
        raise ValidationError('CPF inválido.')
