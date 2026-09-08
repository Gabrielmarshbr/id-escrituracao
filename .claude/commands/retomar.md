---
description: Recupera o contexto do projeto ID - Escrituração e diz onde paramos
---

Você está retomando o projeto **ID - Escrituração** — automação da microárea de
Aportes de uma administradora de FIDCs. Pode ser que você já tenha o contexto
desta conversa, ou pode ser uma sessão nova, sem nenhum.

Faça o seguinte, em ordem:

1. Leia `RETOMAR.md` na raiz do projeto. Ele é o mapa: decisões fechadas, o que
   está construído, o que falta, e como o Gabriel prefere trabalhar.
2. Leia a spec em `docs/superpowers/specs/2026-09-07-aportes-design.md`. É a
   fonte de verdade do desenho — não reabra decisões que estão lá sem motivo.
3. Olhe o plano em `docs/superpowers/plans/` para ver quais tasks já foram
   feitas e quais continuam bloqueadas.
4. Rode a suíte de testes e confira que está verde:
   `.venv\Scripts\python.exe -m pytest -q`
5. Veja o estado do git: `git status -sb` e `git log --oneline -5`.

Depois disso, escreva um resumo **curto** para o Gabriel, com:

- em que ponto o projeto está, em duas ou três frases;
- o resultado da suíte de testes (número real, não estimativa);
- qual é o próximo passo concreto, e de quem ele depende — dele ou de você.

Não invente progresso: se algo estiver quebrado ou faltando, diga.

Regras que valem sempre neste projeto:

- **Pergunte em texto corrido, uma coisa por mensagem.** Nada de painel de
  múltipla escolha — o Gabriel responde em prosa e traz contexto que nenhuma
  alternativa pré-escrita capturaria.
- **`dados/` e `saida/` nunca vão para o git nem saem da máquina da empresa.**
  Contêm CPF, endereço e dados bancários de investidores.
- **Ausência de informação nunca vira permissão.** Fato desconhecido é
  pendência, jamais um valor-padrão permissivo.
- **Nada de criar repositório, dar push ou qualquer ação para fora sem
  autorização explícita dele.**
