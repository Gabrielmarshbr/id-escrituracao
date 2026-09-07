"""Conversao .docx -> PDF pelo proprio Word, via COM.

E o unico jeito de garantir fidelidade total a formatacao da casa. O Word abre
uma vez por bloco: abrir e fechar por arquivo custa segundos que se multiplicam
por 40.
"""

from pathlib import Path

_FORMATO_PDF = 17


class _WordCOM:
    """A conversa real com o Word. Substituivel nos testes."""

    def __init__(self) -> None:
        self._app = None

    def abrir(self) -> None:
        import win32com.client  # importado aqui: so existe no Windows

        self._app = win32com.client.Dispatch("Word.Application")
        self._app.Visible = False
        self._app.DisplayAlerts = False

    def converter_um(self, docx: Path, pdf: Path) -> None:
        documento = self._app.Documents.Open(str(docx.resolve()))
        try:
            documento.SaveAs(str(pdf.resolve()), FileFormat=_FORMATO_PDF)
        finally:
            documento.Close(False)

    def fechar(self) -> None:
        if self._app is not None:
            self._app.Quit()
            self._app = None


class ConversorWord:
    """Gerenciador de contexto: uma instancia do Word para o bloco inteiro."""

    def __init__(self, _word=None) -> None:
        self._word = _word if _word is not None else _WordCOM()

    def __enter__(self) -> "ConversorWord":
        self._word.abrir()
        return self

    def __exit__(self, *_) -> None:
        self._word.fechar()

    def converter(self, docx: Path, pdf: Path) -> None:
        if not docx.exists():
            raise FileNotFoundError(f"nao encontrei o documento {docx}")
        pdf.parent.mkdir(parents=True, exist_ok=True)
        self._word.converter_um(docx, pdf)
