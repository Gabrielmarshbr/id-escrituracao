"""Fatos ficticios reutilizados pelos testes do motor de regras.

Nenhum dado real. Documentos sao sequencias obviamente inventadas.
"""

from datetime import date
from decimal import Decimal

import pytest

from aportes.dominio import (
    Base, Boleta, Classe, Condominio, Cotista, Oferta, Procedencia, TipoPessoa,
)
from aportes.qualificacao import Categoria

PROC = Procedencia(fonte="regulamento", em=date(2026, 1, 15))
PROC_FICHA = Procedencia(fonte="ficha_pdf", em=date(2026, 3, 12))

DOC_COTISTA = "11111111111"
CNPJ_FUNDO = "11111111000111"


def faz_cotista(documento=DOC_COTISTA, categoria=Categoria.PROFISSIONAL,
                tipo=TipoPessoa.PF, cadastro=None):
    return Cotista(
        documento=documento, nome="Fulano de Tal", tipo=tipo,
        categoria=categoria,
        categoria_procedencia=PROC_FICHA if categoria else None,
        cadastro=cadastro or {}, cadastro_procedencia=PROC_FICHA,
    )


def faz_classe(id="F1/A", condominio=Condominio.FECHADO,
               exigida=Categoria.QUALIFICADO):
    return Classe(
        id=id, fundo_nome="Fundo Exemplo FIDC", fundo_cnpj=CNPJ_FUNDO,
        nome="Classe A", condominio=condominio,
        qualificacao_exigida=exigida, procedencia=PROC,
    )


def faz_oferta(id="OF1", classe_id="F1/A", publica=True, exigida=None):
    return Oferta(id=id, classe_id=classe_id, publica=publica,
                  qualificacao_exigida=exigida)


def faz_boleta(documento=DOC_COTISTA, classe_id="F1/A", oferta_id="OF1",
               valor="10000.00"):
    return Boleta(id="B1", documento_cotista=documento, classe_id=classe_id,
                  oferta_id=oferta_id, valor=Decimal(valor),
                  data=date(2026, 9, 7))


@pytest.fixture
def base_completa():
    """Base que conhece tudo: cotista Profissional, classe fechada, oferta publica."""
    return Base(
        cotistas={DOC_COTISTA: faz_cotista()},
        classes={"F1/A": faz_classe()},
        ofertas={"OF1": faz_oferta()},
        posicoes=frozenset(),
    )
