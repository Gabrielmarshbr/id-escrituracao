from dataclasses import replace

from aportes.dominio import Situacao
from aportes.qualificacao import Categoria
from aportes.regras import avaliar
from tests.conftest import DOC_COTISTA, faz_boleta, faz_classe, faz_cotista, faz_oferta


def test_qualificacao_suficiente_libera(base_completa):
    v = avaliar(faz_boleta(), base_completa)
    assert v.situacao is Situacao.LIBERADA


def test_qualificacao_insuficiente_reprova(base_completa):
    base = replace(
        base_completa,
        cotistas={DOC_COTISTA: faz_cotista(categoria=Categoria.GERAL)},
        classes={"F1/A": faz_classe(exigida=Categoria.PROFISSIONAL)},
    )
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.NAO_ELEGIVEL
    assert "profissional" in v.motivo.lower()
    assert "geral" in v.motivo.lower()
    assert v.documentos == ()


def test_motivo_da_reprovacao_cita_a_procedencia(base_completa):
    """'Segundo a ficha de 12/03/2026' — para dar como discordar."""
    base = replace(
        base_completa,
        cotistas={DOC_COTISTA: faz_cotista(categoria=Categoria.GERAL)},
        classes={"F1/A": faz_classe(exigida=Categoria.PROFISSIONAL)},
    )
    v = avaliar(faz_boleta(), base)
    assert "12/03/2026" in v.motivo


def test_categoria_do_cotista_desconhecida_vira_pendencia(base_completa):
    base = replace(
        base_completa,
        cotistas={DOC_COTISTA: faz_cotista(categoria=None)},
    )
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.FALTOU_DADO
    assert any("ficha" in p.lower() for p in v.pendencias)


def test_oferta_exige_mais_que_a_classe(base_completa):
    """Vale a mais restritiva das duas."""
    base = replace(
        base_completa,
        cotistas={DOC_COTISTA: faz_cotista(categoria=Categoria.QUALIFICADO)},
        classes={"F1/A": faz_classe(exigida=Categoria.QUALIFICADO)},
        ofertas={"OF1": faz_oferta(exigida=Categoria.PROFISSIONAL)},
    )
    assert avaliar(faz_boleta(), base).situacao is Situacao.NAO_ELEGIVEL


def test_oferta_desconhecida_vira_pendencia(base_completa):
    base = replace(base_completa, ofertas={})
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.FALTOU_DADO
    assert any("oferta" in p.lower() for p in v.pendencias)


def test_oferta_privada_para_e_nao_gera_documento(base_completa):
    base = replace(base_completa, ofertas={"OF1": faz_oferta(publica=False)})
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.PRECISA_DE_VOCE
    assert "vinculo" in v.motivo.lower()
    assert v.documentos == ()


def test_oferta_privada_para_mesmo_com_tudo_em_ordem(base_completa):
    """Nem qualificacao perfeita libera oferta privada automaticamente."""
    base = replace(
        base_completa,
        cotistas={DOC_COTISTA: faz_cotista(categoria=Categoria.PROFISSIONAL)},
        ofertas={"OF1": faz_oferta(publica=False)},
    )
    assert avaliar(faz_boleta(), base).situacao is Situacao.PRECISA_DE_VOCE
