from dataclasses import replace

from aportes.dominio import Condominio, Situacao
from aportes.regras import avaliar
from tests.conftest import faz_boleta, faz_classe


def test_cotista_desconhecido_vira_pendencia(base_completa):
    base = replace(base_completa, cotistas={})
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.FALTOU_DADO
    assert "cotista" in v.motivo.lower()
    assert any("ficha" in p.lower() for p in v.pendencias)
    assert v.documentos == ()


def test_classe_desconhecida_vira_pendencia(base_completa):
    base = replace(base_completa, classes={})
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.FALTOU_DADO
    assert "F1/A" in v.motivo
    assert any("regulamento" in p.lower() for p in v.pendencias)


def test_condominio_aberto_nao_gera_boletim_mas_nao_interrompe(base_completa):
    """Aberto e resposta conhecida: tira o BS, deixa o TA seguir."""
    base = replace(
        base_completa,
        classes={"F1/A": faz_classe(condominio=Condominio.ABERTO)},
    )
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.LIBERADA
    assert "boletim_subscricao" not in v.documentos
    assert "termo_adesao" in v.documentos


def test_condominio_fechado_gera_boletim(base_completa):
    v = avaliar(faz_boleta(), base_completa)
    assert v.situacao is Situacao.LIBERADA
    assert "boletim_subscricao" in v.documentos


def test_ausencia_de_informacao_nunca_libera(base_completa):
    """A regra que sustenta o desenho inteiro."""
    for campo in ("cotistas", "classes"):
        base = replace(base_completa, **{campo: {}})
        assert avaliar(faz_boleta(), base).situacao is not Situacao.LIBERADA
