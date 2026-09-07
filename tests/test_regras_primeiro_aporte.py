from dataclasses import replace

from aportes.dominio import Condominio, Situacao
from aportes.regras import BOLETIM, TERMO_ADESAO, avaliar
from tests.conftest import CNPJ_FUNDO, DOC_COTISTA, faz_boleta, faz_classe


def test_sem_posicao_no_fundo_gera_termo_de_adesao(base_completa):
    v = avaliar(faz_boleta(), base_completa)
    assert TERMO_ADESAO in v.documentos


def test_com_posicao_no_fundo_nao_gera_termo_de_adesao(base_completa):
    base = replace(
        base_completa, posicoes=frozenset({(DOC_COTISTA, CNPJ_FUNDO, "F1/A")}),
    )
    v = avaliar(faz_boleta(), base)
    assert TERMO_ADESAO not in v.documentos
    assert BOLETIM in v.documentos


def test_posicao_em_outra_classe_do_mesmo_fundo_nao_gera_termo(base_completa):
    """Um Termo de Adesao por cotista por FUNDO, nao por classe.

    Quem ja aderiu ao fundo pela Classe A nao assina de novo ao entrar na B.
    """
    base = replace(
        base_completa,
        classes={"F1/A": faz_classe(id="F1/A"), "F1/B": faz_classe(id="F1/B")},
        posicoes=frozenset({(DOC_COTISTA, CNPJ_FUNDO, "F1/A")}),
    )
    v = avaliar(faz_boleta(classe_id="F1/B"), base)
    assert TERMO_ADESAO not in v.documentos


def test_posicao_em_outro_fundo_ainda_gera_termo(base_completa):
    """Aderir ao Fundo X nao dispensa o Termo de Adesao do Fundo Y."""
    base = replace(
        base_completa,
        posicoes=frozenset({(DOC_COTISTA, "99999999000199", "F9/A")}),
    )
    v = avaliar(faz_boleta(), base)
    assert TERMO_ADESAO in v.documentos


def test_posicao_em_classe_nao_cadastrada_do_mesmo_fundo_conta(base_completa):
    """A posicao carrega o CNPJ do fundo, entao nao depende do fundos.yaml.

    Se dependesse, uma classe ainda nao registrada ficaria invisivel e sairia
    um Termo de Adesao indevido.
    """
    base = replace(
        base_completa,
        posicoes=frozenset({(DOC_COTISTA, CNPJ_FUNDO, "F1/Z-nao-cadastrada")}),
    )
    v = avaliar(faz_boleta(), base)
    assert TERMO_ADESAO not in v.documentos


def test_termo_de_adesao_independe_do_condominio(base_completa):
    base = replace(
        base_completa,
        classes={"F1/A": faz_classe(condominio=Condominio.ABERTO)},
    )
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.LIBERADA
    assert v.documentos == (TERMO_ADESAO,)
