"""Onde ficam as pastas.

`dados/` e `saida/` moram numa pasta de rede da empresa ou no OneDrive
corporativo, para a equipe compartilhar a mesma base. O caminho fica em
`config.local.json`, que nao vai para o git — cada maquina aponta para o mesmo
lugar sem nada cravado no codigo.

Sem esse arquivo, tudo cai dentro da pasta do projeto, que e o suficiente para
uma pessoa so.
"""

import json
from dataclasses import dataclass
from pathlib import Path

NOME_DO_ARQUIVO = "config.local.json"


@dataclass(frozen=True)
class Configuracao:
    raiz: Path
    pasta_dados: Path
    pasta_saida: Path

    @property
    def pasta_regras(self) -> Path:
        return self.raiz / "regras"

    @property
    def pasta_modelos(self) -> Path:
        return self.raiz / "modelos"

    @property
    def pasta_documentos(self) -> Path:
        """Regulamentos, suplementos e ATAs anexados. Fica em dados/."""
        return self.pasta_dados / "documentos"

    @property
    def pasta_saldos(self) -> Path:
        return self.pasta_dados / "saldos"

    @property
    def compartilhada(self) -> bool:
        """A base esta fora da pasta do projeto (ou seja, na rede)?"""
        return self.pasta_dados.resolve() != (self.raiz / "dados").resolve()


def carregar(raiz: Path) -> Configuracao:
    arquivo = raiz / NOME_DO_ARQUIVO
    cru = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {}
    return Configuracao(
        raiz=raiz,
        pasta_dados=_caminho(raiz, cru.get("pasta_dados"), "dados"),
        pasta_saida=_caminho(raiz, cru.get("pasta_saida"), "saida"),
    )


def raiz_do_projeto() -> Path:
    """A pasta do projeto, a partir de onde este arquivo esta."""
    return Path(__file__).resolve().parent.parent.parent


def _caminho(raiz: Path, valor: str | None, padrao: str) -> Path:
    if not valor:
        return raiz / padrao
    caminho = Path(valor)
    return caminho if caminho.is_absolute() else raiz / caminho
