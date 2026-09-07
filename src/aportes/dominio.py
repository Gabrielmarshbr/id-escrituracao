"""Os tipos que todo o resto do sistema usa para falar de aportes.

Todos imutaveis: um fato lido da base nao deve ser alterado por engano no
meio de uma avaliacao.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum

from aportes.qualificacao import Categoria


class TipoPessoa(Enum):
    PF = "pf"
    PJ = "pj"
    FUNDO = "fundo"


class Condominio(Enum):
    ABERTO = "aberto"
    FECHADO = "fechado"


class Situacao(Enum):
    LIBERADA = "liberada"
    NAO_ELEGIVEL = "nao_elegivel"
    PRECISA_DE_VOCE = "precisa_de_voce"
    FALTOU_DADO = "faltou_dado"


@dataclass(frozen=True)
class Procedencia:
    """De onde o fato veio e quando. Acompanha todo veredito."""

    fonte: str
    em: date

    def __str__(self) -> str:
        return f"{self.fonte} de {self.em.strftime('%d/%m/%Y')}"


@dataclass(frozen=True)
class Cotista:
    documento: str
    nome: str
    tipo: TipoPessoa
    categoria: Categoria | None
    categoria_procedencia: Procedencia | None
    cadastro: dict[str, str] = field(default_factory=dict)
    cadastro_procedencia: Procedencia | None = None

    def __post_init__(self) -> None:
        so_digitos = "".join(c for c in self.documento if c.isdigit())
        object.__setattr__(self, "documento", so_digitos)


@dataclass(frozen=True)
class Classe:
    """Uma classe de um fundo. O id e a chave usada em toda parte."""

    id: str
    fundo_nome: str
    fundo_cnpj: str
    nome: str
    condominio: Condominio
    qualificacao_exigida: Categoria
    procedencia: Procedencia


@dataclass(frozen=True)
class Oferta:
    id: str
    classe_id: str
    publica: bool
    qualificacao_exigida: Categoria | None = None
    valor_minimo: Decimal | None = None
    vigencia_ate: date | None = None


@dataclass(frozen=True)
class Boleta:
    id: str
    documento_cotista: str
    classe_id: str
    oferta_id: str | None
    valor: Decimal
    data: date

    def __post_init__(self) -> None:
        if not isinstance(self.valor, Decimal):
            raise TypeError(
                f"valor da boleta precisa ser Decimal, veio "
                f"{type(self.valor).__name__}"
            )
        so_digitos = "".join(c for c in self.documento_cotista if c.isdigit())
        object.__setattr__(self, "documento_cotista", so_digitos)


@dataclass(frozen=True)
class Base:
    """Os fatos conhecidos, ja carregados. O motor nao le disco."""

    cotistas: dict[str, Cotista]
    classes: dict[str, Classe]
    ofertas: dict[str, Oferta]

    #: (documento do cotista, CNPJ do fundo, id da classe), do Saldo de
    #: Aplicacoes. O CNPJ do fundo vem junto de proposito: a pergunta do
    #: Termo de Adesao e por fundo, e nao pode depender de a classe ja
    #: estar cadastrada em regras/fundos.yaml.
    posicoes: frozenset[tuple[str, str, str]]

    def tem_posicao_no_fundo(self, documento: str, fundo_cnpj: str) -> bool:
        """O cotista ja esta em alguma classe deste fundo?"""
        return any(
            doc == documento and cnpj == fundo_cnpj
            for doc, cnpj, _ in self.posicoes
        )


@dataclass(frozen=True)
class Veredito:
    situacao: Situacao
    motivo: str
    documentos: tuple[str, ...] = ()
    pendencias: tuple[str, ...] = ()
