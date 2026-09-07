# ID - Escrituração — retomada do brainstorming

Este arquivo existe pra você não perder o fio de novo. Abra o Claude Code
**nesta pasta** e cole o bloco lá embaixo na primeira mensagem.

O brainstorming começou em 05/09/2026 e parou em 06/09/2026, 01:55.
O histórico completo daquela conversa está em `historico/`.

---

## Bloco pra colar na primeira mensagem

```
Vamos retomar um brainstorming interrompido. Use a skill
superpowers:brainstorming, caminho ARQUITETURAL. Não escreva código nem
crie repositório antes de eu aprovar o desenho.

# Projeto: ID - Escrituração

Trabalho no mercado financeiro. Quero automatizar quatro coisas:
criação de documentos, aprovação de boletas de aportes, confecção de
suplementos de ofertas e verificação de aporte (se o cotista pode
aportar naquele fundo e classe).

O repositório ainda NÃO existe. Vai ser privado, na conta GitHub
Gabrielmarshbr (o gh CLI já está instalado e autenticado nela). No
GitHub o nome vira "id-escrituracao"; a pasta local mantém o nome
bonito. A pasta local já existe: ~/Desktop/ID - Escrituração

## O que já foi decidido

Os quatro itens foram decompostos em subprojetos, sobre um núcleo
compartilhado (cadastro de fundos, classes, cotistas e regras de cada
classe):
  1. Verificação de aporte — motor de regras
  2. Aprovação de boletas — fluxo operacional (depende do 1)
  3. Criação de documentos — geração a partir de modelo + dados
  4. Suplemento de oferta — caso específico do 3 (depende do 3)

COMEÇAMOS PELO ITEM 3 (criação de documentos). Cada subprojeto terá sua
própria spec. Não misture os outros três agora.

A ABORDAGEM JÁ FOI ESCOLHIDA: **A — Python + docxtpl (tags {{ campo }}
e condicionais {% if %} dentro do próprio Word) + Word COM para gerar o
PDF.** O argumento decisivo foi eu mesmo conseguir editar modelo e criar
seção condicional sem depender de programador. As alternativas B
(python-docx com marcadores) e C (PowerShell + Word COM fazendo tudo)
foram descartadas.

## Requisitos levantados

- Formato: modelo .docx entra, PDF sai. Ninguém edita depois; o PDF é
  o que circula. A formatação da casa (estilos, numeração, sumário)
  precisa sair intacta.
- Fonte dos dados: sistema interno, acessado por EXPORTAÇÃO CSV/Excel
  (não por API). Sem credencial, sem rede.
- Volume: 2 a 5 modelos fixos, dezenas de documentos por semana.
  O ganho está em processar a planilha inteira em lote.
- Conferência: por amostragem. Preciso de um relatório do lote dizendo
  o que gerou, com que dados, e o que se recusou a gerar por dado
  faltando.
- Risco conhecido: a autocorreção do Word quebra as tags {{ }}. Defesa
  acordada: validar o modelo antes de rodar o lote.

## Ambiente já verificado nesta máquina

- Windows 10 Home, PowerShell
- Word 16.0 com COM funcionando (testado) → converte .docx em PDF com
  fidelidade total
- Python 3.12.10 instalado
- LibreOffice NÃO instalado
- gh 2.98.0 autenticado na conta Gabrielmarshbr
- PyPI acessível: docxtpl 0.20.2 + Jinja2, lxml, python-docx, tudo em
  wheel, sem compilador. NADA foi instalado ainda (só --dry-run).
- Máquina corporativa sem trava de instalação hoje — mas o desenho deve
  deixar a instalação reproduzível e auditável, porque "sem trava hoje"
  não é "sem trava sempre".

## Onde exatamente paramos

A abordagem A acabou de ser fechada. Faltavam TRÊS perguntas
estruturantes, e a primeira nem chegou a ser respondida:

  **como a planilha vira documentos** — uma linha = um documento? uma
  planilha = um lote? como o modelo certo é escolhido para cada linha?

Retome daí: faça essa pergunta, depois as outras duas, e siga para o
desenho.
```
