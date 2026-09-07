"""Le regras/ofertas.yaml, editado a mao pelo Gabriel."""

from decimal import Decimal
from pathlib import Path

import yaml

from aportes.base.fundos import _enum, _exigir
from aportes.dominio import Oferta
from aportes.qualificacao import Categoria


def carregar_ofertas(caminho: Path) -> dict[str, Oferta]:
    itens = yaml.safe_load(caminho.read_text(encoding="utf-8")) or []
    ofertas: dict[str, Oferta] = {}
    for item in itens:
        id_ = _exigir(item, "id", contexto="(sem id)")
        if id_ in ofertas:
            raise ValueError(f"oferta {id_} aparece duas vezes em {caminho}")
        exigida = item.get("qualificacao_exigida")
        minimo = item.get("valor_minimo")
        ofertas[id_] = Oferta(
            id=id_,
            classe_id=_exigir(item, "classe_id", id_),
            publica=bool(_exigir(item, "publica", id_)),
            qualificacao_exigida=(
                _enum(Categoria, exigida, "qualificacao_exigida", id_)
                if exigida is not None else None
            ),
            valor_minimo=Decimal(str(minimo)) if minimo is not None else None,
            vigencia_ate=item.get("vigencia_ate"),
        )
    return ofertas
