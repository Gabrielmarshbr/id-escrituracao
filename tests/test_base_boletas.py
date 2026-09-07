from datetime import date
from decimal import Decimal

from aportes.base.boletas import carregar_vistas_da_equipe, chave, registrar
from aportes.dominio import Boleta


def _boleta(id="B1", valor="10000.00"):
    return Boleta(id=id, documento_cotista="11111111111", classe_id="F1/A",
                  oferta_id="OF1", valor=Decimal(valor), data=date(2026, 9, 7))


def test_pasta_sem_arquivo_nao_tem_nada_visto(tmp_path):
    assert carregar_vistas_da_equipe(tmp_path) == set()


def test_boleta_registrada_fica_vista(tmp_path):
    b = _boleta()
    registrar(tmp_path, "gabriel", b, ("boletim_subscricao",))
    assert chave(b) in carregar_vistas_da_equipe(tmp_path)


def test_registrar_duas_vezes_e_inofensivo(tmp_path):
    """Colar o mesmo print de novo nao pode duplicar nada."""
    b = _boleta()
    registrar(tmp_path, "gabriel", b, ("boletim_subscricao",))
    registrar(tmp_path, "gabriel", b, ("boletim_subscricao",))
    assert len(carregar_vistas_da_equipe(tmp_path)) == 1


def test_chave_usa_o_id_quando_existe():
    assert chave(_boleta(id="B123")) == "B123"


def test_chave_composta_quando_nao_ha_id():
    b = _boleta(id="")
    k = chave(b)
    assert "11111111111" in k and "F1/A" in k and "10000.00" in k


def test_boletas_diferentes_tem_chaves_diferentes():
    assert chave(_boleta(id="", valor="10000.00")) != chave(_boleta(id="", valor="20000.00"))
