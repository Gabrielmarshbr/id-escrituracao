"""Quando nao ha Saldo de Aplicacoes, a pessoa pode responder — e fica registrado.

Enquanto o leitor do Britech nao existe, a base nunca sabe a posicao. Sem uma
saida, nenhuma boleta passa. A saida nao pode ser presumir: e perguntar, usar a
resposta, e dizer no veredito que ela veio de uma pessoa.
"""

from dataclasses import replace

from aportes.dominio import Situacao
from aportes.regras import TERMO_ADESAO, avaliar
from tests.conftest import faz_boleta


def test_sem_saldo_e_sem_resposta_continua_pendencia(base_completa):
    base = replace(base_completa, fundos_com_saldo=frozenset())
    assert avaliar(faz_boleta(), base).situacao is Situacao.FALTOU_DADO


def test_pessoa_informa_que_e_primeiro_aporte(base_completa):
    base = replace(base_completa, fundos_com_saldo=frozenset())
    v = avaliar(faz_boleta(), base, primeiro_aporte_informado=True)
    assert v.situacao is Situacao.LIBERADA
    assert TERMO_ADESAO in v.documentos


def test_pessoa_informa_que_nao_e_primeiro_aporte(base_completa):
    base = replace(base_completa, fundos_com_saldo=frozenset())
    v = avaliar(faz_boleta(), base, primeiro_aporte_informado=False)
    assert v.situacao is Situacao.LIBERADA
    assert TERMO_ADESAO not in v.documentos


def test_veredito_diz_que_a_resposta_veio_de_pessoa(base_completa):
    """Fato informado nao pode se passar por fato apurado."""
    base = replace(base_completa, fundos_com_saldo=frozenset())
    v = avaliar(faz_boleta(), base, primeiro_aporte_informado=True)
    assert "informado" in v.motivo.lower()


def test_saldo_carregado_manda_mais_que_o_informado(base_completa):
    """Com Saldo de Aplicacoes na mao, o arquivo vence o palpite."""
    base = replace(
        base_completa,
        posicoes=frozenset({("11111111111", "11111111000111", "F1/A")}),
    )
    v = avaliar(faz_boleta(), base, primeiro_aporte_informado=True)
    assert TERMO_ADESAO not in v.documentos
    assert "informado" not in v.motivo.lower()
