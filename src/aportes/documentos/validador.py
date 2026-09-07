"""Confere uma minuta .docx antes de ela ser usada num bloco.

Existe por causa da autocorrecao do Word, que quebra tags em silencio.
"""

import re
from pathlib import Path

from docx import Document

_TAG = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")
_ASPAS_CURVAS = "“”‘’"


def _texto_todo(caminho: Path) -> str:
    doc = Document(caminho)
    partes = [p.text for p in doc.paragraphs]
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                partes.append(celula.text)
    return "\n".join(partes)


def tags_da_minuta(caminho: Path) -> set[str]:
    return set(_TAG.findall(_texto_todo(caminho)))


def validar_minuta(caminho: Path) -> list[str]:
    texto = _texto_todo(caminho)
    problemas: list[str] = []

    curvas = [c for c in _ASPAS_CURVAS if c in texto]
    if curvas:
        problemas.append(
            f"aspa curva encontrada ({''.join(curvas)}): a autocorrecao do Word "
            "trocou a aspa reta e isso quebra a tag. Desative a autocorrecao "
            "de aspas e corrija."
        )

    if texto.count("{{") != texto.count("}}"):
        problemas.append(
            f"chave desbalanceada: {texto.count('{{')} aberturas '{{{{' para "
            f"{texto.count('}}')} fechamentos '}}}}'"
        )

    abre = len(re.findall(r"\{%\s*if\b", texto))
    fecha = len(re.findall(r"\{%\s*endif\s*%\}", texto))
    if abre != fecha:
        problemas.append(
            f"condicional sem fechamento: {abre} '{{% if %}}' para "
            f"{fecha} '{{% endif %}}'"
        )

    abre_for = len(re.findall(r"\{%\s*for\b", texto))
    fecha_for = len(re.findall(r"\{%\s*endfor\s*%\}", texto))
    if abre_for != fecha_for:
        problemas.append(
            f"repeticao sem fechamento: {abre_for} '{{% for %}}' para "
            f"{fecha_for} '{{% endfor %}}'"
        )

    return problemas
