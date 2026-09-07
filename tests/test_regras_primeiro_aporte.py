from dataclasses import replace

from aportes.dominio import Condominio, Situacao
from aportes.regras import BOLETIM, TERMO_ADESAO, avaliar
from tests.conftest import DOC_COTISTA, faz_boleta, faz_classe


def test_sem_posicao_na_classe_gera_termo_de_adesao(base_completa):
    v = avaliar(faz_boleta(), base_completa)
    assert TERMO_ADESAO in v.documentos


def test_com_posicao_na_classe_nao_gera_termo_de_adesao(base_completa):
    base = replace(
        base_completa, posicoes=frozenset({(DOC_COTISTA, "F1/A")}),
    )
    v = avaliar(faz_boleta(), base)
    assert TERMO_ADESAO not in v.documentos
    assert BOLETIM in v.documentos


def test_posicao_em_outra_classe_do_mesmo_fundo_ainda_gera_termo(base_completa):
    """A chave e cotista + CLASSE, nao cotista + fundo."""
    base = replace(
        base_completa,
        classes={"F1/A": faz_classe(id="F1/A"), "F1/B": faz_classe(id="F1/B")},
        posicoes=frozenset({(DOC_COTISTA, "F1/A")}),
    )
    v = avaliar(faz_boleta(classe_id="F1/B"), base)
    assert TERMO_ADESAO in v.documentos


def test_termo_de_adesao_independe_do_condominio(base_completa):
    base = replace(
        base_completa,
        classes={"F1/A": faz_classe(condominio=Condominio.ABERTO)},
    )
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.LIBERADA
    assert v.documentos == (TERMO_ADESAO,)
