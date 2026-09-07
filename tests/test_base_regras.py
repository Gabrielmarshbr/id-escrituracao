from decimal import Decimal

import pytest

from aportes.base.fundos import carregar_classes
from aportes.base.ofertas import carregar_ofertas
from aportes.dominio import Condominio
from aportes.qualificacao import Categoria

YAML_CLASSES = """
- id: F1/A
  fundo_nome: Fundo Exemplo FIDC
  fundo_cnpj: "11.111.111/0001-11"
  nome: Classe A
  condominio: fechado
  qualificacao_exigida: profissional
  fonte: regulamento
  lido_em: 2026-01-15
"""

YAML_OFERTAS = """
- id: OF1
  classe_id: F1/A
  publica: true
  valor_minimo: "1000.00"
  vigencia_ate: 2026-12-31
"""


def _escreve(tmp_path, nome, conteudo):
    caminho = tmp_path / nome
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


def test_carrega_classe(tmp_path):
    classes = carregar_classes(_escreve(tmp_path, "f.yaml", YAML_CLASSES))
    classe = classes["F1/A"]
    assert classe.condominio is Condominio.FECHADO
    assert classe.qualificacao_exigida is Categoria.PROFISSIONAL
    assert classe.fundo_cnpj == "11111111000111"
    assert classe.procedencia.fonte == "regulamento"


def test_arquivo_vazio_devolve_base_vazia(tmp_path):
    assert carregar_classes(_escreve(tmp_path, "f.yaml", "")) == {}


def test_campo_faltando_falha_alto(tmp_path):
    ruim = YAML_CLASSES.replace("  condominio: fechado\n", "")
    with pytest.raises(ValueError) as erro:
        carregar_classes(_escreve(tmp_path, "f.yaml", ruim))
    assert "condominio" in str(erro.value)
    assert "F1/A" in str(erro.value)


def test_condominio_invalido_falha_alto(tmp_path):
    ruim = YAML_CLASSES.replace("fechado", "semiaberto")
    with pytest.raises(ValueError) as erro:
        carregar_classes(_escreve(tmp_path, "f.yaml", ruim))
    assert "semiaberto" in str(erro.value)


def test_id_duplicado_falha_alto(tmp_path):
    with pytest.raises(ValueError) as erro:
        carregar_classes(_escreve(tmp_path, "f.yaml", YAML_CLASSES + YAML_CLASSES))
    assert "F1/A" in str(erro.value)


def test_carrega_oferta(tmp_path):
    ofertas = carregar_ofertas(_escreve(tmp_path, "o.yaml", YAML_OFERTAS))
    oferta = ofertas["OF1"]
    assert oferta.publica is True
    assert oferta.qualificacao_exigida is None
    assert oferta.valor_minimo == Decimal("1000.00")


def test_oferta_sem_publica_falha_alto(tmp_path):
    """'Publica ou privada' nunca pode ter valor-padrao."""
    ruim = YAML_OFERTAS.replace("  publica: true\n", "")
    with pytest.raises(ValueError) as erro:
        carregar_ofertas(_escreve(tmp_path, "o.yaml", ruim))
    assert "publica" in str(erro.value)
