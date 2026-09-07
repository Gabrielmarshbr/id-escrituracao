"""dados/boletas.json — o que ja foi processado. NUNCA vai para o git.

E a memoria que faz o print seguinte mostrar so o que e novo.
"""

import json
from pathlib import Path

from aportes.dominio import Boleta


def chave(boleta: Boleta) -> str:
    """O id da boleta quando existe; senao, chave composta.

    A composta colapsa duas boletas identicas no mesmo dia. Se a exportacao
    do Portal ID trouxer numero da boleta, use-o.
    """
    if boleta.id:
        return boleta.id
    return "|".join([
        boleta.documento_cotista, boleta.classe_id,
        f"{boleta.valor:.2f}", boleta.data.isoformat(),
    ])


def carregar_vistas(caminho: Path) -> set[str]:
    if not caminho.exists():
        return set()
    return set(json.loads(caminho.read_text(encoding="utf-8")).keys())


def registrar(caminho: Path, boleta: Boleta, documentos: tuple[str, ...]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    registro = (
        json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else {}
    )
    registro[chave(boleta)] = {
        "processada_em": boleta.data.isoformat(),
        "classe_id": boleta.classe_id,
        "documentos": list(documentos),
    }
    caminho.write_text(
        json.dumps(registro, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
