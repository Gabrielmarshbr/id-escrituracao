from decimal import Decimal

import pytest

from aportes.extenso import formatar_reais, valor_por_extenso


def _sem_acento(texto):
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


@pytest.mark.parametrize("valor,esperado", [
    ("1.00", "um real"),
    ("1.50", "um real e cinquenta centavos"),
    ("100.00", "cem reais"),
    ("1000.00", "mil reais"),
    ("1234.56", "mil duzentos e trinta e quatro reais e cinquenta e seis centavos"),
    ("1000000.00", "um milhao de reais"),
    ("1500000.75", "um milhao e quinhentos mil reais e setenta e cinco centavos"),
])
def test_valor_por_extenso(valor, esperado):
    resultado = valor_por_extenso(Decimal(valor))
    # comparacao sem acento para o teste nao depender de encoding do arquivo
    assert _sem_acento(resultado) == esperado


def test_extenso_nao_tem_virgula():
    """Documento juridico escreve 'mil duzentos', nao 'mil, duzentos'."""
    assert "," not in valor_por_extenso(Decimal("1234.56"))


def test_valor_por_extenso_recusa_float():
    """Dinheiro em float perde centavo em silencio."""
    with pytest.raises(TypeError):
        valor_por_extenso(1234.56)


def test_valor_por_extenso_recusa_negativo():
    with pytest.raises(ValueError):
        valor_por_extenso(Decimal("-1.00"))


@pytest.mark.parametrize("valor,esperado", [
    ("1.00", "1,00"),
    ("1234.56", "1.234,56"),
    ("1000000.00", "1.000.000,00"),
    ("1500000.75", "1.500.000,75"),
])
def test_formatar_reais(valor, esperado):
    assert formatar_reais(Decimal(valor)) == esperado
