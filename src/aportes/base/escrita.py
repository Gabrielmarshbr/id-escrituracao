"""Acrescenta classes e ofertas aos YAML de regras, pela tela.

Preserva o bloco de comentarios do topo do arquivo — ele explica o formato
para quem edita a mao, e perder isso tornaria o arquivo hostil.

Toda entrada gravada aqui guarda quem registrou. A regra deixou de ser
editada so pelo responsavel pela area, entao saber de quem veio importa.
"""

from datetime import date
from pathlib import Path

import yaml

from aportes.dominio import Classe, Oferta


class JaExiste(Exception):
    """Ja ha uma entrada com este id. Editar e outra operacao."""


def acrescentar_classe(caminho: Path, classe: Classe, registrado_por: str) -> None:
    entrada = {
        "id": classe.id,
        "fundo_nome": classe.fundo_nome,
        "fundo_cnpj": classe.fundo_cnpj,
        "nome": classe.nome,
        "condominio": classe.condominio.value,
        "qualificacao_exigida": classe.qualificacao_exigida.value,
        "fonte": classe.procedencia.fonte,
        "lido_em": classe.procedencia.em,
        "registrado_por": registrado_por,
        "registrado_em": date.today(),
    }
    _acrescentar(caminho, entrada, "classe")


def acrescentar_oferta(caminho: Path, oferta: Oferta, registrado_por: str) -> None:
    entrada = {
        "id": oferta.id,
        "classe_id": oferta.classe_id,
        "publica": oferta.publica,
        "registrado_por": registrado_por,
        "registrado_em": date.today(),
    }
    if oferta.qualificacao_exigida is not None:
        entrada["qualificacao_exigida"] = oferta.qualificacao_exigida.value
    if oferta.valor_minimo is not None:
        entrada["valor_minimo"] = str(oferta.valor_minimo)
    if oferta.vigencia_ate is not None:
        entrada["vigencia_ate"] = oferta.vigencia_ate
    _acrescentar(caminho, entrada, "oferta")


def _acrescentar(caminho: Path, entrada: dict, o_que: str) -> None:
    texto = caminho.read_text(encoding="utf-8") if caminho.exists() else ""
    existentes = yaml.safe_load(texto) or []
    if any(item.get("id") == entrada["id"] for item in existentes):
        raise JaExiste(
            f"ja existe {o_que} com o id '{entrada['id']}' em {caminho.name}. "
            "Para mudar o que esta registrado, edite o arquivo."
        )

    bloco = yaml.safe_dump(
        [entrada], allow_unicode=True, sort_keys=False, default_flow_style=False
    )
    novo = _comentarios_do_topo(texto) + _corpo(texto) + bloco
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(novo, encoding="utf-8")


def _comentarios_do_topo(texto: str) -> str:
    """O cabecalho comentado do arquivo, que explica o formato a quem edita."""
    linhas: list[str] = []
    for linha in texto.splitlines():
        if linha.startswith("#") or not linha.strip():
            linhas.append(linha)
        else:
            break
    return "\n".join(linhas).rstrip() + "\n" if linhas else ""


def _corpo(texto: str) -> str:
    """O resto do arquivo, sem o cabecalho comentado."""
    linhas = texto.splitlines()
    inicio = 0
    for i, linha in enumerate(linhas):
        if not (linha.startswith("#") or not linha.strip()):
            inicio = i
            break
    else:
        return ""
    corpo = "\n".join(linhas[inicio:]).rstrip()
    return corpo + "\n" if corpo else ""
