import secrets
import string

ALFABETO_SEM_AMBIGUOS = (
    string.ascii_letters.replace('l', '').replace('I', '').replace('O', '')
    + string.digits.replace('0', '').replace('1', '')
)


def gerar_senha(tamanho=12):
    """Gera senha aleatória segura (letras, dígitos e símbolo), sem caracteres ambíguos."""
    simbolos = '!@#$%&*'
    base = [secrets.choice(ALFABETO_SEM_AMBIGUOS) for _ in range(tamanho - 1)]
    base.append(secrets.choice(simbolos))
    secrets.SystemRandom().shuffle(base)
    return ''.join(base)
