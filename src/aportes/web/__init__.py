"""A porta B: uma pagina local, para quem nao usa Claude Code.

Sem terminal, sem conta, sem rede externa. Roda na propria maquina e escuta
so em localhost.
"""

from aportes.web.aplicacao import criar_aplicacao

__all__ = ["criar_aplicacao"]
