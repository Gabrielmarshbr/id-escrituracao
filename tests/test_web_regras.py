"""As abas Fundos e Ofertas: consultar, cadastrar e anexar.

A partir daqui a tela ESCREVE regra — antes era privilegio de quem edita o
YAML. Por isso os testes cobrem tambem o que ela nao pode deixar passar:
CNPJ malformado, id repetido, oferta sem dizer se e publica.
"""

import io

import pytest

from aportes.configuracao import Configuracao
from aportes.web import criar_aplicacao


@pytest.fixture
def cliente(tmp_path):
    (tmp_path / "regras").mkdir()
    (tmp_path / "regras" / "fundos.yaml").write_text(
        "# cabecalho que explica o formato\n\n", encoding="utf-8")
    (tmp_path / "regras" / "ofertas.yaml").write_text("", encoding="utf-8")
    (tmp_path / "modelos").mkdir()
    config = Configuracao(raiz=tmp_path, pasta_dados=tmp_path / "dados",
                          pasta_saida=tmp_path / "saida")
    app = criar_aplicacao(config, usuario="maria")
    app.config["TESTING"] = True
    c = app.test_client()
    c.raiz = tmp_path
    return c


CLASSE = {
    "id": "EXEMPLO/A", "fundo_nome": "Fundo Exemplo FIDC",
    "fundo_cnpj": "11.111.111/0001-11", "nome": "Classe A Senior",
    "condominio": "fechado", "qualificacao_exigida": "qualificado",
    "fonte": "regulamento", "lido_em": "2026-01-15",
}
OFERTA = {"id": "1a-emissao", "classe_id": "EXEMPLO/A", "publica": "sim"}


def _cadastrar_classe(c, **mudancas):
    return c.post("/fundos", data={**CLASSE, **mudancas}, follow_redirects=True)


# --- aba Fundos -----------------------------------------------------------

def test_aba_fundos_abre_vazia(cliente):
    r = cliente.get("/fundos")
    assert r.status_code == 200
    assert "Nenhuma classe cadastrada" in r.text


def test_cadastrar_classe_pela_tela(cliente):
    r = _cadastrar_classe(cliente)
    assert "Fundo Exemplo FIDC" in r.text
    assert "Classe A Senior" in r.text


def test_classe_cadastrada_ja_serve_na_aba_boletas(cliente):
    """De nada adianta registrar se a boleta nao enxerga."""
    _cadastrar_classe(cliente)
    assert "Fundo Exemplo FIDC" in cliente.get("/").text


def test_grava_quem_registrou(cliente):
    _cadastrar_classe(cliente)
    texto = (cliente.raiz / "regras" / "fundos.yaml").read_text(encoding="utf-8")
    assert "registrado_por: maria" in texto


def test_cabecalho_do_yaml_sobrevive_ao_cadastro(cliente):
    _cadastrar_classe(cliente)
    texto = (cliente.raiz / "regras" / "fundos.yaml").read_text(encoding="utf-8")
    assert texto.startswith("# cabecalho que explica o formato")


def test_cnpj_invalido_e_recusado(cliente):
    r = _cadastrar_classe(cliente, fundo_cnpj="123")
    assert "14 digitos" in r.text
    assert "Classe A Senior" not in r.text


def test_id_repetido_e_recusado(cliente):
    _cadastrar_classe(cliente)
    r = _cadastrar_classe(cliente, fundo_nome="Outro Fundo")
    assert "ja existe" in r.text


def test_campo_obrigatorio_faltando_e_recusado(cliente):
    r = _cadastrar_classe(cliente, condominio="")
    assert "obrigatorio" in r.text


def test_busca_filtra_a_lista(cliente):
    _cadastrar_classe(cliente)
    _cadastrar_classe(cliente, id="OUTRO/A", fundo_nome="Fundo Diferente FIDC",
                      fundo_cnpj="22.222.222/0001-22")
    r = cliente.get("/fundos?q=diferente")
    # o CNPJ formatado so aparece na tabela, nunca no formulario de cadastro
    assert "22.222.222/0001-22" in r.text
    assert "11.111.111/0001-11" not in r.text


def test_busca_ignora_acento_e_pontuacao_do_cnpj(cliente):
    _cadastrar_classe(cliente)
    assert "Fundo Exemplo FIDC" in cliente.get("/fundos?q=11111111000111").text


# --- aba Ofertas ----------------------------------------------------------

def test_cadastrar_oferta_pela_tela(cliente):
    _cadastrar_classe(cliente)
    r = cliente.post("/ofertas", data=OFERTA, follow_redirects=True)
    assert "1a-emissao" in r.text
    assert "pública" in r.text


def test_oferta_sem_dizer_se_e_publica_e_recusada(cliente):
    """'Publica ou privada' nunca pode ter valor-padrao."""
    _cadastrar_classe(cliente)
    r = cliente.post("/ofertas", data={**OFERTA, "publica": ""},
                     follow_redirects=True)
    assert "publica ou privada" in r.text


def test_oferta_privada_aparece_marcada(cliente):
    _cadastrar_classe(cliente)
    r = cliente.post("/ofertas", data={**OFERTA, "publica": "nao"},
                     follow_redirects=True)
    assert "privada" in r.text


# --- documentos anexados --------------------------------------------------

def _anexar(cliente, url, nome="Regulamento.pdf", conteudo=b"%PDF-1.4"):
    return cliente.post(url, data={"arquivo": (io.BytesIO(conteudo), nome)},
                        content_type="multipart/form-data", follow_redirects=True)


def test_anexar_regulamento_ao_fundo_e_baixar(cliente):
    _cadastrar_classe(cliente)
    r = _anexar(cliente, "/fundos/11111111000111/documentos")
    assert "Regulamento.pdf" in r.text

    baixado = cliente.get("/documentos/fundos/11111111000111/Regulamento.pdf")
    assert baixado.status_code == 200
    assert baixado.data == b"%PDF-1.4"


def test_anexar_suplemento_a_oferta(cliente):
    _cadastrar_classe(cliente)
    cliente.post("/ofertas", data=OFERTA, follow_redirects=True)
    r = _anexar(cliente, "/ofertas/1a-emissao/documentos", nome="Suplemento.pdf")
    assert "Suplemento.pdf" in r.text


def test_arquivo_de_tipo_inesperado_e_recusado(cliente):
    _cadastrar_classe(cliente)
    r = _anexar(cliente, "/fundos/11111111000111/documentos", nome="virus.exe")
    assert "nao e um tipo aceito" in r.text


def test_documento_inexistente_da_404(cliente):
    assert cliente.get("/documentos/fundos/1/nao-existe.pdf").status_code == 404


def test_tipo_de_documento_desconhecido_da_404(cliente):
    assert cliente.get("/documentos/outro/1/x.pdf").status_code == 404


def test_travessia_de_caminho_no_download_nao_passa(cliente):
    """..%2f e o truque classico para sair da pasta."""
    r = cliente.get("/documentos/fundos/1/..%2f..%2fconfig.local.json")
    assert r.status_code == 404


# --- consulta de cotista pela tela ----------------------------------------

def test_consulta_diz_que_nao_conhece(cliente):
    assert cliente.get("/api/cotista/11111111111").json == {"conhecido": False}


def test_consulta_devolve_nome_e_categoria(cliente):
    cliente.post("/cotista", data={
        "documento": "111.111.111-11", "nome": "Fulano de Tal", "tipo": "pf",
        "categoria": "profissional", "fonte": "ficha do Portal ID"},
        follow_redirects=True)

    d = cliente.get("/api/cotista/111.111.111-11").json
    assert d["conhecido"] is True
    assert d["nome"] == "Fulano de Tal"
    assert d["categoria"] == "profissional"
    assert "ficha do Portal ID" in d["procedencia"]
