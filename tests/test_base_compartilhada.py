"""A base e usada por mais de uma pessoa, sobre a mesma fila de boletas.

Cada pessoa escreve apenas o seu arquivo; a leitura funde todos. Escrita
simultanea deixa de ser possivel porque nao existe arquivo disputado.
"""

from datetime import date
from decimal import Decimal

from aportes.base.boletas import carregar_vistas_da_equipe, chave, registrar
from aportes.base.cotistas import carregar_da_equipe, salvar_do_usuario
from aportes.dominio import Boleta, Cotista, Procedencia, TipoPessoa
from aportes.qualificacao import Categoria

VELHO = Procedencia(fonte="excel_portal", em=date(2026, 1, 10))
NOVO = Procedencia(fonte="ficha_pdf", em=date(2026, 6, 20))


def _cotista(documento, categoria, proc, cadastro=None, nome="Fulano de Tal"):
    return Cotista(
        documento=documento, nome=nome, tipo=TipoPessoa.PF,
        categoria=categoria, categoria_procedencia=proc,
        cadastro=cadastro or {}, cadastro_procedencia=proc,
    )


def _boleta(id="B1"):
    return Boleta(id=id, documento_cotista="11111111111", classe_id="F1/A",
                  oferta_id="OF1", valor=Decimal("10000.00"),
                  data=date(2026, 9, 7))


# --- cotistas -------------------------------------------------------------

def test_pasta_vazia_devolve_base_vazia(tmp_path):
    assert carregar_da_equipe(tmp_path) == {}


def test_le_o_que_cada_pessoa_escreveu(tmp_path):
    salvar_do_usuario(tmp_path, "gabriel", {
        "11111111111": _cotista("11111111111", Categoria.PROFISSIONAL, NOVO)})
    salvar_do_usuario(tmp_path, "maria", {
        "22222222222": _cotista("22222222222", Categoria.GERAL, VELHO)})

    todos = carregar_da_equipe(tmp_path)
    assert set(todos) == {"11111111111", "22222222222"}


def test_gravar_nao_toca_no_arquivo_de_outra_pessoa(tmp_path):
    salvar_do_usuario(tmp_path, "maria", {
        "22222222222": _cotista("22222222222", Categoria.GERAL, VELHO)})
    antes = (tmp_path / "cotistas.maria.json").read_text(encoding="utf-8")

    salvar_do_usuario(tmp_path, "gabriel", {
        "11111111111": _cotista("11111111111", Categoria.PROFISSIONAL, NOVO)})

    assert (tmp_path / "cotistas.maria.json").read_text(encoding="utf-8") == antes


def test_mesmo_cotista_em_dois_arquivos_vence_o_mais_novo(tmp_path):
    """Nao vence quem escreveu: vence o bloco com procedencia mais nova."""
    salvar_do_usuario(tmp_path, "maria", {
        "11111111111": _cotista("11111111111", Categoria.GERAL, VELHO,
                                {"email": "antigo@exemplo.invalido"})})
    salvar_do_usuario(tmp_path, "gabriel", {
        "11111111111": _cotista("11111111111", Categoria.PROFISSIONAL, NOVO,
                                {"email": "novo@exemplo.invalido"})})

    c = carregar_da_equipe(tmp_path)["11111111111"]
    assert c.categoria is Categoria.PROFISSIONAL
    assert c.cadastro["email"] == "novo@exemplo.invalido"


def test_fusao_nao_depende_da_ordem_dos_arquivos(tmp_path):
    """Trocar quem escreveu primeiro nao pode mudar o resultado."""
    salvar_do_usuario(tmp_path, "zelia", {
        "11111111111": _cotista("11111111111", Categoria.PROFISSIONAL, NOVO)})
    salvar_do_usuario(tmp_path, "ana", {
        "11111111111": _cotista("11111111111", Categoria.GERAL, VELHO)})

    assert carregar_da_equipe(tmp_path)["11111111111"].categoria is Categoria.PROFISSIONAL


def test_arquivo_de_outro_tipo_na_pasta_e_ignorado(tmp_path):
    (tmp_path / "boletas.gabriel.json").write_text("{}", encoding="utf-8")
    (tmp_path / "anotacoes.txt").write_text("nada", encoding="utf-8")
    assert carregar_da_equipe(tmp_path) == {}


# --- boletas vistas -------------------------------------------------------

def test_boleta_vista_por_uma_pessoa_nao_reaparece_para_outra(tmp_path):
    registrar(tmp_path, "maria", _boleta("B1"), ("boletim_subscricao",))
    assert chave(_boleta("B1")) in carregar_vistas_da_equipe(tmp_path)


def test_vistas_sao_a_uniao_da_equipe(tmp_path):
    registrar(tmp_path, "maria", _boleta("B1"), ())
    registrar(tmp_path, "gabriel", _boleta("B2"), ())
    assert carregar_vistas_da_equipe(tmp_path) == {"B1", "B2"}


def test_registrar_guarda_quem_processou(tmp_path):
    """A trilha de auditoria sai de graca da divisao por dono."""
    import json
    registrar(tmp_path, "maria", _boleta("B1"), ("boletim_subscricao",))
    registro = json.loads((tmp_path / "boletas.maria.json").read_text(encoding="utf-8"))
    assert registro["B1"]["documentos"] == ["boletim_subscricao"]


def test_pasta_vazia_nao_tem_boleta_vista(tmp_path):
    assert carregar_vistas_da_equipe(tmp_path) == set()
