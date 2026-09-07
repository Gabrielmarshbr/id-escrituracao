"""Formatacao de CPF e CNPJ para a saida.

A base guarda so digitos; a mascara existe so no documento.
"""


def formatar_documento(documento: str) -> str:
    """'11111111111' -> '111.111.111-11'; 14 digitos -> CNPJ."""
    d = "".join(c for c in documento if c.isdigit())
    if len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    if len(d) == 14:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    return documento
