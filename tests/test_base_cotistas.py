from datetime import date

from aportes.base.cotistas import carregar_cotistas, mesclar, salvar_cotistas
from aportes.dominio import Cotista, Procedencia, TipoPessoa
from aportes.qualificacao import Categoria

VELHO = Procedencia(fonte="excel_portal", em=date(2026, 1, 10))
NOVO = Procedencia(fonte="ficha_pdf", em=date(2026, 6, 20))


def _cotista(categoria, cat_proc, cadastro, cad_proc, nome="Fulano de Tal"):
    return Cotista(
        documento="11111111111", nome=nome, tipo=TipoPessoa.PF,
        categoria=categoria, categoria_procedencia=cat_proc,
        cadastro=cadastro, cadastro_procedencia=cad_proc,
    )


def test_ida_e_volta_pelo_disco(tmp_path):
    caminho = tmp_path / "cotistas.json"
    original = {
        "11111111111": _cotista(
            Categoria.QUALIFICADO, NOVO,
            {"email": "fulano@exemplo.invalido", "endereco": "Rua Ficticia, 1"},
            NOVO,
        )
    }
    salvar_cotistas(caminho, original)
    assert carregar_cotistas(caminho) == original


def test_arquivo_inexistente_devolve_base_vazia(tmp_path):
    assert carregar_cotistas(tmp_path / "nao_existe.json") == {}


def test_mesclar_prefere_o_bloco_mais_novo():
    existente = _cotista(Categoria.GERAL, VELHO, {"email": "antigo@exemplo.invalido"}, VELHO)
    novo = _cotista(Categoria.QUALIFICADO, NOVO, {"email": "novo@exemplo.invalido"}, NOVO)
    r = mesclar(existente, novo)
    assert r.categoria is Categoria.QUALIFICADO
    assert r.cadastro["email"] == "novo@exemplo.invalido"


def test_mesclar_mantem_o_bloco_mais_novo_que_ja_estava():
    """Reimportar um Excel antigo nao pode sobrescrever uma ficha recente."""
    existente = _cotista(Categoria.QUALIFICADO, NOVO, {"email": "novo@exemplo.invalido"}, NOVO)
    antigo = _cotista(Categoria.GERAL, VELHO, {"email": "antigo@exemplo.invalido"}, VELHO)
    r = mesclar(existente, antigo)
    assert r.categoria is Categoria.QUALIFICADO
    assert r.cadastro["email"] == "novo@exemplo.invalido"


def test_mesclar_combina_blocos_de_fontes_diferentes():
    """Excel traz a qualificacao; a ficha traz o cadastro."""
    do_excel = _cotista(Categoria.QUALIFICADO, VELHO, {}, None)
    da_ficha = _cotista(None, None, {"endereco": "Rua Ficticia, 1"}, NOVO)
    r = mesclar(do_excel, da_ficha)
    assert r.categoria is Categoria.QUALIFICADO
    assert r.cadastro["endereco"] == "Rua Ficticia, 1"


def test_mesclar_sem_existente_devolve_o_novo():
    novo = _cotista(Categoria.GERAL, VELHO, {}, VELHO)
    assert mesclar(None, novo) == novo
