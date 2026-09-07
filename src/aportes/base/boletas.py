"""dados/boletas.<usuario>.json — o que ja foi processado. NUNCA vai para o git.

E a memoria que faz o print seguinte mostrar so o que e novo.

Um arquivo por pessoa: a equipe trabalha a mesma fila, e escrita simultanea num
arquivo unico numa pasta de rede sobrescreve em silencio. Cada pessoa escreve
so o seu; a leitura e a uniao de todos.
"""

import json
from pathlib import Path

from aportes.base.nomes import arquivo_do_usuario
from aportes.dominio import Boleta

_PREFIXO = "boletas"


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


def carregar_vistas_da_equipe(pasta: Path) -> set[str]:
    """A uniao do que toda a equipe ja processou."""
    vistas: set[str] = set()
    for caminho in sorted(pasta.glob(f"{_PREFIXO}.*.json")):
        vistas |= set(json.loads(caminho.read_text(encoding="utf-8")).keys())
    return vistas


def registrar(pasta: Path, usuario: str, boleta: Boleta,
              documentos: tuple[str, ...]) -> None:
    """Grava no arquivo desta pessoa. Nunca toca no de outra."""
    caminho = arquivo_do_usuario(pasta, _PREFIXO, usuario)
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
