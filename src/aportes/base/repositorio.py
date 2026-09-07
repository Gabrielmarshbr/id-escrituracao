"""Junta tudo numa Base, e grava o que a pessoa cadastrar.

E o unico lugar que sabe onde cada coisa mora. O motor de regras recebe a Base
pronta e nao toca em disco.
"""

from pathlib import Path

from aportes.base.cotistas import carregar_da_equipe, mesclar, salvar_do_usuario
from aportes.base.cotistas import carregar_cotistas
from aportes.base.fundos import carregar_classes
from aportes.base.nomes import arquivo_do_usuario
from aportes.base.ofertas import carregar_ofertas
from aportes.configuracao import Configuracao
from aportes.dominio import Base, Cotista


def carregar_base(config: Configuracao) -> Base:
    posicoes, fundos_com_saldo = carregar_posicoes(config.pasta_saldos)
    return Base(
        cotistas=carregar_da_equipe(config.pasta_dados),
        classes=_se_existir(config.pasta_regras / "fundos.yaml", carregar_classes),
        ofertas=_se_existir(config.pasta_regras / "ofertas.yaml", carregar_ofertas),
        posicoes=posicoes,
        fundos_com_saldo=fundos_com_saldo,
    )


def carregar_posicoes(
    pasta_saldos: Path,
) -> tuple[frozenset[tuple[str, str, str]], frozenset[str]]:
    """Posicoes do Saldo de Aplicacoes, e os fundos que os saldos cobrem.

    Ainda nao ha leitor do Britech (task 14 do plano). Ate ele existir, nenhum
    fundo e coberto — e o motor de regras se recusa a presumir primeiro aporte,
    que e exatamente o comportamento certo.
    """
    if not pasta_saldos.exists():
        return frozenset(), frozenset()
    return frozenset(), frozenset()


def salvar_cotista(config: Configuracao, usuario: str, cotista: Cotista) -> None:
    """Grava no arquivo desta pessoa, mesclando com o que ela ja tinha.

    Nao toca no arquivo de ninguem mais. Se outra pessoa tiver um bloco mais
    novo do mesmo cotista, a fusao na leitura resolve.
    """
    arquivo = arquivo_do_usuario(config.pasta_dados, "cotistas", usuario)
    meus = carregar_cotistas(arquivo)
    meus[cotista.documento] = mesclar(meus.get(cotista.documento), cotista)
    salvar_do_usuario(config.pasta_dados, usuario, meus)


def _se_existir(caminho: Path, leitor):
    return leitor(caminho) if caminho.exists() else {}
