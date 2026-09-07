import pytest

from aportes.documentos.pdf import ConversorWord


class WordFalso:
    """Substitui o COM do Word para testar o contrato sem abrir o Word."""

    def __init__(self):
        self.abriu = 0
        self.convertidos = []
        self.fechou = False

    def abrir(self):
        self.abriu += 1

    def converter_um(self, docx, pdf):
        self.convertidos.append((docx, pdf))

    def fechar(self):
        self.fechou = True


def test_abre_o_word_uma_vez_para_o_bloco_inteiro(tmp_path):
    falso = WordFalso()
    docs = [(tmp_path / f"{i}.docx", tmp_path / f"{i}.pdf") for i in range(5)]
    for caminho, _ in docs:
        caminho.write_bytes(b"")

    with ConversorWord(_word=falso) as conversor:
        for docx, pdf in docs:
            conversor.converter(docx, pdf)

    assert falso.abriu == 1
    assert len(falso.convertidos) == 5


def test_fecha_o_word_mesmo_se_der_erro(tmp_path):
    falso = WordFalso()
    with pytest.raises(RuntimeError):
        with ConversorWord(_word=falso):
            raise RuntimeError("erro no meio do bloco")
    assert falso.fechou is True


def test_recusa_docx_inexistente(tmp_path):
    falso = WordFalso()
    with ConversorWord(_word=falso) as conversor:
        with pytest.raises(FileNotFoundError):
            conversor.converter(tmp_path / "nao_existe.docx", tmp_path / "x.pdf")
