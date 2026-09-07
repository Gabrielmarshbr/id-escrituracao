"""Nome dos arquivos por pessoa, e o usuario da maquina.

Cada pessoa escreve apenas o seu arquivo. O nome sai daqui, num lugar so,
para que cotistas e boletas sigam a mesma regra.
"""

import getpass
import re
from pathlib import Path

_INVALIDO = re.compile(r"[^a-z0-9_-]+")


def normalizar_usuario(usuario: str) -> str:
    """'Maria Silva' -> 'maria-silva'. Nome de arquivo previsivel e seguro."""
    limpo = _INVALIDO.sub("-", usuario.strip().lower()).strip("-")
    if not limpo:
        raise ValueError(f"nome de usuario invalido: {usuario!r}")
    return limpo


def usuario_da_maquina() -> str:
    """Quem esta operando, para assinar o que essa pessoa gravar."""
    return normalizar_usuario(getpass.getuser())


def arquivo_do_usuario(pasta: Path, prefixo: str, usuario: str) -> Path:
    return pasta / f"{prefixo}.{normalizar_usuario(usuario)}.json"
