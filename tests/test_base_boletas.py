from datetime import date
from decimal import Decimal

from aportes.base.boletas import carregar_vistas, chave, registrar
from aportes.dominio import Boleta


def _boleta(id="B1", valor="10000.00"):
    return Boleta(id=id, documento_cotista="11111111111", classe_id="F1/A",
                  oferta_id="OF1", valor=Decimal(valor), data=date(2026, 9, 7))


def test_arquivo_inexistente_nao_tem_nada_visto(tmp_path):
    assert carregar_vistas(tmp_path / "b.json") == set()


def test_boleta_registrada_fica_vista(tmp_path):
    caminho = tmp_path / "b.json"
    b = _boleta()
    registrar(caminho, b, ("boletim_subscricao",))
    assert chave(b) in carregar_vistas(caminho)


def test_registrar_duas_vezes_e_inofensivo(tmp_path):
    caminho = tmp_path / "b.json"
    b = _boleta()
    registrar(caminho, b, ("boletim_subscricao",))
    registrar(caminho, b, ("boletim_subscricao",))
    assert len(carregar_vistas(caminho)) == 1


def test_chave_usa_o_id_quando_existe():
    assert chave(_boleta(id="B123")) == "B123"


def test_chave_composta_quando_nao_ha_id():
    b = _boleta(id="")
    k = chave(b)
    assert "11111111111" in k and "F1/A" in k and "10000.00" in k


def test_boletas_diferentes_tem_chaves_diferentes():
    assert chave(_boleta(id="", valor="10000.00")) != chave(_boleta(id="", valor="20000.00"))
