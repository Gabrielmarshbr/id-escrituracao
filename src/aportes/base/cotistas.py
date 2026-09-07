"""dados/cotistas.<usuario>.json — a base de cotistas. NUNCA vai para o git.

Tres fontes alimentam esta base e vao discordar. A data da procedencia
resolve, bloco a bloco: qualificacao e cadastro tem historias separadas.

Um arquivo por pessoa, pelo mesmo motivo das boletas: a equipe trabalha junta
e ninguem pode sobrescrever o arquivo de ninguem. A fusao usa a mesma funcao
`mesclar` que resolve divergencia entre fontes — vence o bloco mais novo, nao
quem escreveu.
"""

import json
from datetime import date
from pathlib import Path

from aportes.base.nomes import arquivo_do_usuario
from aportes.dominio import Cotista, Procedencia, TipoPessoa
from aportes.qualificacao import Categoria

_PREFIXO = "cotistas"


def carregar_da_equipe(pasta: Path) -> dict[str, Cotista]:
    """Funde o que toda a equipe cadastrou, numa base so.

    Independe da ordem dos arquivos: quem decide e a data da procedencia.
    """
    base: dict[str, Cotista] = {}
    for caminho in sorted(pasta.glob(f"{_PREFIXO}.*.json")):
        for documento, cotista in carregar_cotistas(caminho).items():
            base[documento] = mesclar(base.get(documento), cotista)
    return base


def salvar_do_usuario(pasta: Path, usuario: str,
                      cotistas: dict[str, Cotista]) -> None:
    """Grava no arquivo desta pessoa. Nunca toca no de outra."""
    salvar_cotistas(arquivo_do_usuario(pasta, _PREFIXO, usuario), cotistas)


def carregar_cotistas(caminho: Path) -> dict[str, Cotista]:
    if not caminho.exists():
        return {}
    cru = json.loads(caminho.read_text(encoding="utf-8"))
    return {doc: _do_dicionario(doc, d) for doc, d in cru.items()}


def salvar_cotistas(caminho: Path, cotistas: dict[str, Cotista]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    cru = {doc: _para_dicionario(c) for doc, c in cotistas.items()}
    caminho.write_text(
        json.dumps(cru, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def mesclar(existente: Cotista | None, novo: Cotista) -> Cotista:
    """Bloco mais novo vence. Bloco ausente no novo preserva o que havia."""
    if existente is None:
        return novo

    cat, cat_proc = _mais_novo(
        (existente.categoria, existente.categoria_procedencia),
        (novo.categoria, novo.categoria_procedencia),
    )
    cad, cad_proc = _mais_novo(
        (existente.cadastro, existente.cadastro_procedencia),
        (novo.cadastro or None, novo.cadastro_procedencia),
    )
    return Cotista(
        documento=novo.documento,
        nome=novo.nome or existente.nome,
        tipo=novo.tipo or existente.tipo,
        categoria=cat, categoria_procedencia=cat_proc,
        cadastro=cad or {}, cadastro_procedencia=cad_proc,
    )


def _mais_novo(a, b):
    (valor_a, proc_a), (valor_b, proc_b) = a, b
    if valor_b is None or proc_b is None:
        return valor_a, proc_a
    if valor_a is None or proc_a is None:
        return valor_b, proc_b
    return (valor_b, proc_b) if proc_b.em >= proc_a.em else (valor_a, proc_a)


def _para_dicionario(c: Cotista) -> dict:
    return {
        "nome": c.nome,
        "tipo": c.tipo.value,
        "categoria": c.categoria.value if c.categoria else None,
        "categoria_procedencia": _proc_para(c.categoria_procedencia),
        "cadastro": c.cadastro,
        "cadastro_procedencia": _proc_para(c.cadastro_procedencia),
    }


def _do_dicionario(documento: str, d: dict) -> Cotista:
    return Cotista(
        documento=documento,
        nome=d["nome"],
        tipo=TipoPessoa(d["tipo"]),
        categoria=Categoria(d["categoria"]) if d.get("categoria") else None,
        categoria_procedencia=_proc_de(d.get("categoria_procedencia")),
        cadastro=d.get("cadastro") or {},
        cadastro_procedencia=_proc_de(d.get("cadastro_procedencia")),
    )


def _proc_para(p: Procedencia | None) -> dict | None:
    return {"fonte": p.fonte, "em": p.em.isoformat()} if p else None


def _proc_de(d: dict | None) -> Procedencia | None:
    return Procedencia(fonte=d["fonte"], em=date.fromisoformat(d["em"])) if d else None
