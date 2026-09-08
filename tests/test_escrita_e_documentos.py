from datetime import date
from decimal import Decimal

import pytest

from aportes.base.documentos import (
    ArquivoRecusado, guardar, listar, pasta_da_oferta, pasta_do_fundo,
)
from aportes.base.escrita import JaExiste, acrescentar_classe, acrescentar_oferta
from aportes.base.fundos import carregar_classes
from aportes.base.ofertas import carregar_ofertas
from aportes.dominio import Classe, Condominio, Oferta, Procedencia
from aportes.qualificacao import Categoria

CABECALHO = """# Uma entrada por CLASSE de fundo. Registre uma vez.
# O 'fonte' e o 'lido_em' aparecem no veredito.

"""


def _classe(id="F1/A"):
    return Classe(
        id=id, fundo_nome="Fundo Exemplo FIDC", fundo_cnpj="11111111000111",
        nome="Classe A", condominio=Condominio.FECHADO,
        qualificacao_exigida=Categoria.PROFISSIONAL,
        procedencia=Procedencia(fonte="regulamento", em=date(2026, 1, 15)),
    )


# --- escrita das regras ---------------------------------------------------

def test_classe_gravada_e_lida_de_volta(tmp_path):
    caminho = tmp_path / "fundos.yaml"
    caminho.write_text(CABECALHO, encoding="utf-8")

    acrescentar_classe(caminho, _classe(), registrado_por="maria")

    lida = carregar_classes(caminho)["F1/A"]
    assert lida.condominio is Condominio.FECHADO
    assert lida.qualificacao_exigida is Categoria.PROFISSIONAL
    assert lida.fundo_cnpj == "11111111000111"


def test_o_cabecalho_comentado_sobrevive(tmp_path):
    """Quem edita o arquivo a mao depende dele para saber o formato."""
    caminho = tmp_path / "fundos.yaml"
    caminho.write_text(CABECALHO, encoding="utf-8")

    acrescentar_classe(caminho, _classe(), registrado_por="maria")

    texto = caminho.read_text(encoding="utf-8")
    assert texto.startswith("# Uma entrada por CLASSE")
    assert "# O 'fonte' e o 'lido_em'" in texto


def test_guarda_quem_registrou(tmp_path):
    """A regra deixou de ser editada so pelo responsavel: de quem veio importa."""
    caminho = tmp_path / "fundos.yaml"
    acrescentar_classe(caminho, _classe(), registrado_por="maria")
    assert "registrado_por: maria" in caminho.read_text(encoding="utf-8")


def test_duas_classes_convivem(tmp_path):
    caminho = tmp_path / "fundos.yaml"
    caminho.write_text(CABECALHO, encoding="utf-8")
    acrescentar_classe(caminho, _classe("F1/A"), registrado_por="maria")
    acrescentar_classe(caminho, _classe("F1/B"), registrado_por="gabriel")
    assert set(carregar_classes(caminho)) == {"F1/A", "F1/B"}


def test_id_repetido_e_recusado(tmp_path):
    caminho = tmp_path / "fundos.yaml"
    acrescentar_classe(caminho, _classe(), registrado_por="maria")
    with pytest.raises(JaExiste) as erro:
        acrescentar_classe(caminho, _classe(), registrado_por="gabriel")
    assert "F1/A" in str(erro.value)


def test_oferta_gravada_e_lida_de_volta(tmp_path):
    caminho = tmp_path / "ofertas.yaml"
    acrescentar_oferta(caminho, Oferta(
        id="OF1", classe_id="F1/A", publica=False,
        qualificacao_exigida=Categoria.PROFISSIONAL,
        valor_minimo=Decimal("1000.00"), vigencia_ate=date(2026, 12, 31),
    ), registrado_por="maria")

    lida = carregar_ofertas(caminho)["OF1"]
    assert lida.publica is False
    assert lida.qualificacao_exigida is Categoria.PROFISSIONAL
    assert lida.valor_minimo == Decimal("1000.00")


def test_oferta_sem_campos_opcionais(tmp_path):
    caminho = tmp_path / "ofertas.yaml"
    acrescentar_oferta(caminho, Oferta(id="OF1", classe_id="F1/A", publica=True),
                       registrado_por="maria")
    lida = carregar_ofertas(caminho)["OF1"]
    assert lida.qualificacao_exigida is None and lida.valor_minimo is None


# --- documentos anexados --------------------------------------------------

def test_guarda_e_lista_o_regulamento(tmp_path):
    pasta = pasta_do_fundo(tmp_path, "11.111.111/0001-11")
    guardar(pasta, "Regulamento Consolidado.pdf", b"%PDF-1.4 conteudo")
    assert [p.name for p in listar(pasta)] == ["Regulamento-Consolidado.pdf"]


def test_cnpj_com_barra_nao_vira_subpasta(tmp_path):
    """'/' no CNPJ nao pode criar caminho novo."""
    pasta = pasta_do_fundo(tmp_path, "11.111.111/0001-11")
    assert pasta.parent == tmp_path / "fundos"


def test_nome_com_travessia_de_caminho_e_neutralizado(tmp_path):
    pasta = pasta_da_oferta(tmp_path, "OF1")
    gravado = guardar(pasta, "../../../etc/senha.pdf", b"%PDF")
    assert gravado.parent == pasta
    assert ".." not in gravado.name


def test_extensao_inesperada_e_recusada(tmp_path):
    with pytest.raises(ArquivoRecusado) as erro:
        guardar(pasta_do_fundo(tmp_path, "1"), "script.exe", b"MZ")
    assert "nao e um tipo aceito" in str(erro.value)


def test_arquivo_grande_demais_e_recusado(tmp_path):
    with pytest.raises(ArquivoRecusado) as erro:
        guardar(pasta_do_fundo(tmp_path, "1"), "grande.pdf", b"x" * (41 * 1024 * 1024))
    assert "limite" in str(erro.value)


def test_dois_arquivos_de_mesmo_nome_nao_se_sobrescrevem(tmp_path):
    pasta = pasta_do_fundo(tmp_path, "1")
    guardar(pasta, "regulamento.pdf", b"%PDF primeiro")
    guardar(pasta, "regulamento.pdf", b"%PDF segundo")
    assert len(listar(pasta)) == 2


def test_pasta_sem_documento_lista_vazio(tmp_path):
    assert listar(pasta_do_fundo(tmp_path, "1")) == []
