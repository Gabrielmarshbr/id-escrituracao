from datetime import date

from aportes.base.repositorio import carregar_base, salvar_cotista
from aportes.configuracao import Configuracao, carregar
from aportes.dominio import Condominio, Cotista, Procedencia, TipoPessoa
from aportes.qualificacao import Categoria

PROC = Procedencia(fonte="ficha_pdf", em=date(2026, 3, 12))

FUNDOS = """
- id: F1/A
  fundo_nome: Fundo Exemplo FIDC
  fundo_cnpj: "11.111.111/0001-11"
  nome: Classe A
  condominio: fechado
  qualificacao_exigida: qualificado
  fonte: regulamento
  lido_em: 2026-01-15
"""

OFERTAS = """
- id: OF1
  classe_id: F1/A
  publica: true
"""


def _config(tmp_path, regras=True):
    if regras:
        (tmp_path / "regras").mkdir()
        (tmp_path / "regras" / "fundos.yaml").write_text(FUNDOS, encoding="utf-8")
        (tmp_path / "regras" / "ofertas.yaml").write_text(OFERTAS, encoding="utf-8")
    return Configuracao(raiz=tmp_path, pasta_dados=tmp_path / "dados",
                        pasta_saida=tmp_path / "saida")


def _cotista(documento="11111111111", categoria=Categoria.PROFISSIONAL,
             cadastro=None):
    return Cotista(
        documento=documento, nome="Fulano de Tal", tipo=TipoPessoa.PF,
        categoria=categoria, categoria_procedencia=PROC,
        cadastro=cadastro or {}, cadastro_procedencia=PROC,
    )


def test_monta_a_base_com_regras_e_cotistas(tmp_path):
    config = _config(tmp_path)
    salvar_cotista(config, "gabriel", _cotista())

    base = carregar_base(config)
    assert base.classes["F1/A"].condominio is Condominio.FECHADO
    assert base.ofertas["OF1"].publica is True
    assert base.cotistas["11111111111"].nome == "Fulano de Tal"


def test_projeto_sem_regras_ainda_carrega(tmp_path):
    """Instalacao nova nao pode explodir: ela mostra pendencia."""
    base = carregar_base(_config(tmp_path, regras=False))
    assert base.classes == {} and base.ofertas == {}


def test_sem_leitor_do_britech_nenhum_fundo_tem_saldo(tmp_path):
    """Enquanto a task 14 nao existe, a base admite que nao sabe."""
    assert carregar_base(_config(tmp_path)).fundos_com_saldo == frozenset()


def test_salvar_nao_toca_no_arquivo_de_outra_pessoa(tmp_path):
    config = _config(tmp_path)
    salvar_cotista(config, "maria", _cotista("22222222222"))
    antes = (config.pasta_dados / "cotistas.maria.json").read_text(encoding="utf-8")

    salvar_cotista(config, "gabriel", _cotista("11111111111"))

    assert (config.pasta_dados / "cotistas.maria.json").read_text(
        encoding="utf-8") == antes
    assert set(carregar_base(config).cotistas) == {"11111111111", "22222222222"}


def test_salvar_duas_vezes_mescla_em_vez_de_duplicar(tmp_path):
    config = _config(tmp_path)
    salvar_cotista(config, "gabriel", _cotista(cadastro={"email": "a@exemplo.invalido"}))
    salvar_cotista(config, "gabriel", _cotista(cadastro={"email": "b@exemplo.invalido"}))

    cotistas = carregar_base(config).cotistas
    assert len(cotistas) == 1
    assert cotistas["11111111111"].cadastro["email"] == "b@exemplo.invalido"


# --- configuracao ---------------------------------------------------------

def test_sem_config_local_usa_as_pastas_do_projeto(tmp_path):
    config = carregar(tmp_path)
    assert config.pasta_dados == tmp_path / "dados"
    assert config.compartilhada is False


def test_config_local_aponta_para_a_pasta_da_empresa(tmp_path):
    import json
    compartilhada = tmp_path / "rede" / "aportes" / "dados"
    (tmp_path / "config.local.json").write_text(
        json.dumps({"pasta_dados": str(compartilhada)}), encoding="utf-8")

    config = carregar(tmp_path)
    assert config.pasta_dados == compartilhada
    assert config.compartilhada is True
