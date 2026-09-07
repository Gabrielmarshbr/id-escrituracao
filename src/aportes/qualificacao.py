"""Categorias de investidor da CVM e a hierarquia entre elas."""

from enum import Enum


class Categoria(Enum):
    GERAL = "geral"
    QUALIFICADO = "qualificado"
    PROFISSIONAL = "profissional"


_ORDEM = {Categoria.GERAL: 0, Categoria.QUALIFICADO: 1, Categoria.PROFISSIONAL: 2}


def atende(categoria_do_cotista: Categoria, exigida: Categoria) -> bool:
    """Profissional cobre Qualificado, que cobre Geral. O contrario nao."""
    return _ORDEM[categoria_do_cotista] >= _ORDEM[exigida]


def mais_restritiva(a: Categoria | None, b: Categoria | None) -> Categoria | None:
    """A exigencia que vale quando classe e oferta pedem coisas diferentes."""
    if a is None:
        return b
    if b is None:
        return a
    return a if _ORDEM[a] >= _ORDEM[b] else b
