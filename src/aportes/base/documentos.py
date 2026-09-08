"""Regulamentos, suplementos e ATAs anexados a um fundo ou a uma oferta.

A regra em regras/*.yaml diz "este fundo e fechado, segundo o regulamento lido
em tal data". O documento em si mora aqui — a prova junto da afirmacao, a um
clique na hora de aprovar a boleta, em vez de a uma busca em 500 canais.

Ficam em dados/, na pasta compartilhada: sao documentos internos da
administradora e nao vao para o git.
"""

import re
import unicodedata
from pathlib import Path

EXTENSOES = {".pdf", ".docx", ".doc"}
TAMANHO_MAXIMO = 40 * 1024 * 1024  # 40 MB


class ArquivoRecusado(Exception):
    """Extensao ou tamanho fora do aceito."""


def pasta_do_fundo(raiz_documentos: Path, fundo_cnpj: str) -> Path:
    return raiz_documentos / "fundos" / _seguro(fundo_cnpj)


def pasta_da_oferta(raiz_documentos: Path, oferta_id: str) -> Path:
    return raiz_documentos / "ofertas" / _seguro(oferta_id)


def listar(pasta: Path) -> list[Path]:
    if not pasta.exists():
        return []
    return sorted(p for p in pasta.iterdir() if p.is_file())


def guardar(pasta: Path, nome_original: str, conteudo: bytes) -> Path:
    """Grava o anexo. Recusa extensao inesperada e arquivo grande demais."""
    nome = _nome_seguro(nome_original)
    if Path(nome).suffix.lower() not in EXTENSOES:
        raise ArquivoRecusado(
            f"'{nome_original}' nao e um tipo aceito. "
            f"Aceitos: {', '.join(sorted(EXTENSOES))}"
        )
    if len(conteudo) > TAMANHO_MAXIMO:
        raise ArquivoRecusado(
            f"'{nome_original}' tem {len(conteudo) // (1024 * 1024)} MB; "
            f"o limite e {TAMANHO_MAXIMO // (1024 * 1024)} MB."
        )
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / nome
    if destino.exists():
        destino = pasta / f"{Path(nome).stem}-{_proximo(pasta, nome)}{Path(nome).suffix}"
    destino.write_bytes(conteudo)
    return destino


def _proximo(pasta: Path, nome: str) -> int:
    raiz, sufixo = Path(nome).stem, Path(nome).suffix
    n = 2
    while (pasta / f"{raiz}-{n}{sufixo}").exists():
        n += 1
    return n


def _nome_seguro(nome: str) -> str:
    """So o nome do arquivo, sem caminho, sem acento, sem surpresa."""
    nome = Path(nome.replace("\\", "/")).name
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", nome)
        if unicodedata.category(c) != "Mn"
    )
    limpo = re.sub(r"[^A-Za-z0-9._-]+", "-", sem_acento).strip("-.")
    if not limpo:
        raise ArquivoRecusado(f"nome de arquivo invalido: {nome!r}")
    return limpo[:120]


def _seguro(texto: str) -> str:
    limpo = re.sub(r"[^A-Za-z0-9._-]+", "-", str(texto)).strip("-.")
    if not limpo:
        raise ArquivoRecusado(f"identificador invalido: {texto!r}")
    return limpo
