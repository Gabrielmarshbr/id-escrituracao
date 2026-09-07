import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def test_dados_e_saida_nunca_sao_rastreados_pelo_git():
    """Dado pessoal de cotista nao pode chegar ao repositorio.

    .gitignore depende de disciplina; este teste nao.
    """
    resultado = subprocess.run(
        ["git", "ls-files", "dados", "saida"],
        cwd=RAIZ, capture_output=True, text=True, check=True,
    )
    rastreados = resultado.stdout.split()
    assert rastreados == [], (
        "Arquivos com dado pessoal foram rastreados pelo git: "
        f"{rastreados}. Rode: git rm --cached <arquivo>"
    )
