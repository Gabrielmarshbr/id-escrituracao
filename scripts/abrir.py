"""Sobe a pagina de aportes e abre o navegador.

Ninguem roda isto na mao: quem usa clica no atalho Aportes.bat.
O servidor escuta so em 127.0.0.1 — nao fica visivel na rede.
"""

import sys
import threading
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aportes.configuracao import carregar, raiz_do_projeto  # noqa: E402
from aportes.web import criar_aplicacao  # noqa: E402

ENDERECO = "127.0.0.1"
PORTA = 5000


def main() -> None:
    config = carregar(raiz_do_projeto())
    config.pasta_dados.mkdir(parents=True, exist_ok=True)
    config.pasta_saida.mkdir(parents=True, exist_ok=True)

    print("Assistente de Aportes — Escrituracao")
    print(f"  dados:  {config.pasta_dados}")
    print(f"  saida:  {config.pasta_saida}")
    if not config.compartilhada:
        print("  (base local desta maquina; para a equipe compartilhar,")
        print("   copie config.exemplo.json para config.local.json)")
    print(f"\nAbrindo http://{ENDERECO}:{PORTA} no navegador.")
    print("Para fechar, feche esta janela preta.\n")

    threading.Timer(
        1.0, lambda: webbrowser.open(f"http://{ENDERECO}:{PORTA}")
    ).start()

    criar_aplicacao(config).run(host=ENDERECO, port=PORTA, debug=False)


if __name__ == "__main__":
    main()
