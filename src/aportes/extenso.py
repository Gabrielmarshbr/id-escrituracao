"""Valor monetario por extenso e formatado, para o Boletim de Subscricao."""

from decimal import Decimal

from num2words import num2words


def valor_por_extenso(valor: Decimal) -> str:
    """'mil duzentos e trinta e quatro reais e cinquenta e seis centavos'."""
    _validar(valor)
    bruto = num2words(valor, lang="pt_BR", to="currency")
    return bruto.replace(",", "")


def formatar_reais(valor: Decimal) -> str:
    """'1.234,56' — sem o prefixo R$, que ja esta na minuta."""
    _validar(valor)
    inteiro, centavos = f"{valor:.2f}".split(".")
    com_pontos = f"{int(inteiro):,}".replace(",", ".")
    return f"{com_pontos},{centavos}"


def _validar(valor: Decimal) -> None:
    if not isinstance(valor, Decimal):
        raise TypeError(
            f"valor monetario precisa ser Decimal, veio {type(valor).__name__}. "
            "float perde centavo em silencio."
        )
    if valor < 0:
        raise ValueError(f"valor monetario nao pode ser negativo: {valor}")
