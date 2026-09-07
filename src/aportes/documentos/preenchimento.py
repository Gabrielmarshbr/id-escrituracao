"""Preenche uma minuta .docx com docxtpl.

O programa nunca reconstroi o documento: so preenche o que o Gabriel escreveu
no Word. E por isso que estilo, numeracao e sumario saem intactos.
"""

from pathlib import Path

from docxtpl import DocxTemplate

from aportes.documentos.validador import tags_da_minuta


class CampoFaltando(Exception):
    """Um campo da minuta nao tem dado. O documento nao e gerado."""


def preencher(minuta: Path, dados: dict[str, str], destino: Path) -> None:
    exigidas = tags_da_minuta(minuta)
    faltando = sorted(
        tag for tag in exigidas
        if not str(dados.get(tag, "")).strip()
    )
    if faltando:
        raise CampoFaltando(
            f"a minuta {minuta.name} exige campos sem dado: "
            f"{', '.join(faltando)}. O documento nao foi gerado."
        )

    modelo = DocxTemplate(minuta)
    modelo.render(dados)
    destino.parent.mkdir(parents=True, exist_ok=True)
    modelo.save(destino)
