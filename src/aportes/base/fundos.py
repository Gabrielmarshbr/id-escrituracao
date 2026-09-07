"""Le regras/fundos.yaml, editado a mao pelo Gabriel.

Falha alto e em portugues: campo faltando nunca vira valor-padrao.
"""

from pathlib import Path

import yaml

from aportes.dominio import Classe, Condominio, Procedencia
from aportes.qualificacao import Categoria


def carregar_classes(caminho: Path) -> dict[str, Classe]:
    itens = yaml.safe_load(caminho.read_text(encoding="utf-8")) or []
    classes: dict[str, Classe] = {}
    for item in itens:
        id_ = _exigir(item, "id", contexto="(sem id)")
        if id_ in classes:
            raise ValueError(f"classe {id_} aparece duas vezes em {caminho}")
        classes[id_] = Classe(
            id=id_,
            fundo_nome=_exigir(item, "fundo_nome", id_),
            fundo_cnpj=_so_digitos(_exigir(item, "fundo_cnpj", id_)),
            nome=_exigir(item, "nome", id_),
            condominio=_enum(Condominio, _exigir(item, "condominio", id_),
                             "condominio", id_),
            qualificacao_exigida=_enum(
                Categoria, _exigir(item, "qualificacao_exigida", id_),
                "qualificacao_exigida", id_,
            ),
            procedencia=Procedencia(
                fonte=_exigir(item, "fonte", id_),
                em=_exigir(item, "lido_em", id_),
            ),
        )
    return classes


def _exigir(item: dict, campo: str, contexto: str = ""):
    if campo not in item or item[campo] is None:
        raise ValueError(
            f"falta o campo '{campo}' na classe {contexto}. "
            "Nenhum campo tem valor-padrao: informacao ausente e pendencia."
        )
    return item[campo]


def _enum(tipo, valor, campo: str, contexto: str):
    try:
        return tipo(str(valor).strip().lower())
    except ValueError:
        validos = ", ".join(m.value for m in tipo)
        raise ValueError(
            f"'{valor}' nao e um valor valido para '{campo}' na classe "
            f"{contexto}. Validos: {validos}"
        ) from None


def _so_digitos(texto: str) -> str:
    return "".join(c for c in str(texto) if c.isdigit())
