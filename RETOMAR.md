# ID - Escrituração — onde estamos

Abra o Claude Code **nesta pasta** e digite **`/retomar`**. Ele lê este
arquivo, confere o estado do projeto e diz onde paramos.

**Última sessão: 07/09/2026.** O brainstorming terminou, a spec está escrita e
o núcleo está construído e testado (142 testes). Existe uma página no navegador
que já gera Boletim e Termo de Adesão em PDF, ponta a ponta — verificado com o
Word de verdade.

**Para começar a usar, leia [`COMECAR.md`](COMECAR.md).**

---

## Leia nesta ordem

0. `COMECAR.md` — os três passos até a primeira boleta gerar documento.
0b. `INSTALAR.md` — como levar e instalar na máquina da empresa.
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

## O que trava o uso, hoje

**O mais urgente, e é do Gabriel:** marcar as duas minutas com as tags. Sem
elas nenhum documento é gerado. A lista de tags está em `modelos/CAMPOS.md`, e
os arquivos precisam ter estes nomes exatos:

- [ ] `modelos/boletim_subscricao.docx`
- [ ] `modelos/termo_adesao.docx`

Depois disso, cadastrar em `regras/fundos.yaml` e `regras/ofertas.yaml` os
fundos e ofertas que forem aparecendo — um por vez, na primeira boleta de cada.

## O que trava as próximas etapas

Os leitores de relatório não podem ser escritos sem ver o formato real. **Não
precisam ser anonimizados para viajar**: com o Claude Code rodando na máquina da
empresa, os arquivos reais são lidos lá e o que vai para o git é um arquivo de
teste com o mesmo layout e dados fictícios.
- [ ] **Saldo de Aplicações** (Britech, Excel)
- [ ] **Excel de cotistas** (Portal ID)
- [ ] **Ficha cadastral** em PDF: uma PF, uma PJ, uma de fundo
- [ ] **Print** da página de boletas do Portal ID

E duas coisas a verificar na máquina da empresa:

- [x] O Saldo de Aplicações separa a posição **por classe**? **Sim** (confirmado
      em 07/09/2026). O leitor deve produzir, por linha: documento do cotista,
      CNPJ do fundo e id da classe. A costura já existe em
      `base/repositorio.py::carregar_posicoes`.
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

## Estado do código

Construído e testado: motor de regras, valor por extenso, base compartilhada
(um arquivo por pessoa), leitura de `regras/*.yaml`, validação e preenchimento
de minuta, conversão em PDF pelo Word, emissão tudo-ou-nada, e a página no
navegador com cadastro de cotista.

Não construído, por depender de arquivos reais: os leitores do Saldo de
Aplicações (Britech), do Excel de cotistas e das fichas em PDF, e a entrada por
print no Claude Code. Estão como tasks 14 a 20 no plano.

**Regra de segurança que não se mexe:** sem Saldo de Aplicações carregado, o
sistema não presume primeiro aporte. Ou a pessoa responde na tela — e fica
registrado que a resposta veio de pessoa —, ou vira pendência.
