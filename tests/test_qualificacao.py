import pytest

from aportes.qualificacao import Categoria, atende, mais_restritiva

GERAL = Categoria.GERAL
QUALIF = Categoria.QUALIFICADO
PROF = Categoria.PROFISSIONAL


@pytest.mark.parametrize("cotista,exigida,esperado", [
    (PROF, PROF, True),
    (PROF, QUALIF, True),
    (PROF, GERAL, True),
    (QUALIF, QUALIF, True),
    (QUALIF, GERAL, True),
    (QUALIF, PROF, False),
    (GERAL, GERAL, True),
    (GERAL, QUALIF, False),
    (GERAL, PROF, False),
])
def test_atende(cotista, exigida, esperado):
    assert atende(cotista, exigida) is esperado


@pytest.mark.parametrize("a,b,esperado", [
    (GERAL, PROF, PROF),
    (PROF, GERAL, PROF),
    (QUALIF, QUALIF, QUALIF),
    (GERAL, QUALIF, QUALIF),
])
def test_mais_restritiva(a, b, esperado):
    assert mais_restritiva(a, b) is esperado


def test_mais_restritiva_aceita_none():
    """A oferta pode nao exigir nada alem do que a classe ja exige."""
    assert mais_restritiva(QUALIF, None) is QUALIF
    assert mais_restritiva(None, QUALIF) is QUALIF


def test_categoria_vem_de_texto():
    assert Categoria("qualificado") is QUALIF


def test_categoria_desconhecida_falha_alto():
    with pytest.raises(ValueError):
        Categoria("semi-profissional")
