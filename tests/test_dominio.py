from datetime import date
from decimal import Decimal

import pytest

from aportes.dominio import (
    Base, Boleta, Classe, Condominio, Cotista, Oferta,
    Procedencia, Situacao, TipoPessoa, Veredito,
)
from aportes.qualificacao import Categoria

PROC = Procedencia(fonte="ficha_pdf", em=date(2026, 3, 12))


def test_cotista_e_imutavel():
    c = Cotista(
        documento="11111111111", nome="Fulano de Tal", tipo=TipoPessoa.PF,
        categoria=Categoria.QUALIFICADO, categoria_procedencia=PROC,
        cadastro={}, cadastro_procedencia=None,
    )
    with pytest.raises(Exception):
        c.nome = "Outro"


def test_documento_guarda_so_digitos():
    c = Cotista(
        documento="111.111.111-11", nome="Fulano", tipo=TipoPessoa.PF,
        categoria=None, categoria_procedencia=None,
        cadastro={}, cadastro_procedencia=None,
    )
    assert c.documento == "11111111111"


def test_boleta_recusa_valor_float():
    with pytest.raises(TypeError):
        Boleta(id="B1", documento_cotista="11111111111", classe_id="F1/A",
               oferta_id="OF1", valor=1000.0, data=date(2026, 9, 7))


def test_base_encontra_posicao_do_cotista_na_classe():
    base = Base(
        cotistas={}, classes={}, ofertas={},
        posicoes=frozenset({("11111111111", "F1/A")}),
    )
    assert base.tem_posicao("11111111111", "F1/A") is True
    assert base.tem_posicao("11111111111", "F1/B") is False


def test_veredito_carrega_motivo():
    v = Veredito(
        situacao=Situacao.FALTOU_DADO,
        motivo="condominio da classe F1/A desconhecido",
        documentos=(), pendencias=("confira o regulamento no Slack do fundo",),
    )
    assert v.situacao is Situacao.FALTOU_DADO
    assert "F1/A" in v.motivo


def test_classe_e_oferta_montam_sem_erro():
    classe = Classe(
        id="F1/A", fundo_nome="Fundo Exemplo FIDC", fundo_cnpj="11111111000111",
        nome="Classe A", condominio=Condominio.FECHADO,
        qualificacao_exigida=Categoria.PROFISSIONAL, procedencia=PROC,
    )
    oferta = Oferta(
        id="OF1", classe_id="F1/A", publica=True,
        qualificacao_exigida=None, valor_minimo=Decimal("1000.00"),
        vigencia_ate=date(2026, 12, 31),
    )
    assert oferta.classe_id == classe.id


def test_procedencia_se_le_em_portugues():
    """Ela aparece no veredito quando a regra reprova alguem."""
    assert str(PROC) == "ficha_pdf de 12/03/2026"
