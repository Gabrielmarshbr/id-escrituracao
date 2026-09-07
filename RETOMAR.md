# ID - Escrituração — onde estamos

Abra o Claude Code **nesta pasta**. Ele lê este arquivo e continua.

**Última sessão: 07/09/2026.** O brainstorming terminou. A spec está escrita,
aprovada em seções e commitada. O projeto saiu do papel.

---

## Leia nesta ordem

1. `docs/superpowers/specs/2026-09-07-aportes-design.md` — **a spec.** É a
   fonte de verdade do desenho. 13 seções.
2. `contexto/01-esteira-subscricao.md` e `contexto/02-escrituracao-4-microareas.md`
   — o contexto operacional, nas palavras do Gabriel.
3. `docs/superpowers/plans/` — o plano de implementação, se já existir.
4. `historico/` — transcrição da sessão de 05-06/09/2026, que se perdeu por
   falta de registro. É por isso que este arquivo existe.

## O que o projeto é, em três frases

Gabriel trabalha na microárea de **Aportes** da Escrituração de uma
administradora de FIDCs: 20 a 50+ boletas de aplicação por dia, cada uma
analisada e aprovada na mão. O gargalo não é preencher documento — é que cada
boleta refaz consultas já respondidas antes (o condomínio do fundo, a
qualificação da classe, as regras da oferta). A ferramenta é **memória**:
transforma consulta repetida em fato registrado uma vez, e no fim gera o
Boletim de Subscrição e o Termo de Adesão.

## Decisões fechadas — não reabrir sem motivo

- **Python + docxtpl + Word COM para PDF.** As tags moram no `.docx`, para o
  Gabriel editar o modelo no Word sem depender de programador.
- **Duas camadas:** Claude Code lê o print da fila de boletas e **transcreve**;
  o núcleo Python **decide e gera**. A transcrição é conferida pelo Gabriel
  antes de virar documento.
- **Duas máquinas:** desenvolve aqui (máquina pessoal), roda na máquina da
  empresa. Ele confirmou que pode instalar Python e Claude Code lá.
- **LGPD:** conhecimento operacional (`src/`, `regras/`, `modelos/`) sobe para
  o GitHub; dado pessoal de cotista (`dados/`, `saida/`) nunca sai da máquina.
- **Fora de escopo agora:** Slack, login no Portal ID, leitura do suplemento
  PDF, vínculo societário de oferta privada, amortização.

## O que trava a implementação

Sem estes arquivos não dá para escrever os leitores nem testes de verdade.
Todos vêm da máquina da empresa, **anonimizados**:

- [ ] Minuta `.docx` do **Boletim de Subscrição**
- [ ] Minuta `.docx` do **Termo de Adesão**
- [ ] **Saldo de Aplicações** (Britech, Excel)
- [ ] **Excel de cotistas** (Portal ID)
- [ ] **Ficha cadastral** em PDF: uma PF, uma PJ, uma de fundo
- [ ] **Print** da página de boletas do Portal ID

E duas coisas a verificar na máquina da empresa:

- [ ] O Saldo de Aplicações separa a posição **por classe**? A regra do Termo
      de Adesão depende disso (é por classe, não por fundo).
- [ ] A exportação de boletas traz **número/código da boleta**? É a chave de
      deduplicação.

## Como o Gabriel gosta de trabalhar

Pergunte **em texto corrido, uma coisa por mensagem**. Ele recusa painel de
múltipla escolha e responde em prosa longa, trazendo contexto que nenhuma
alternativa pré-escrita capturaria.

## Repositório

Ainda **não existe no GitHub**. Será privado, `id-escrituracao`, conta
`Gabrielmarshbr` (`gh` já autenticado). Git local já iniciado, com `.gitignore`
protegendo `dados/` e `saida/` desde antes do primeiro commit. **Não crie nem
envie nada sem autorização explícita.** Antes do primeiro push, decidir o que
fazer com `historico/` — recomendação: tirar do git.
