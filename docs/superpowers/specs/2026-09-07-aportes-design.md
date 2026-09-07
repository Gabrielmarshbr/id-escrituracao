# ID - Escrituração — Assistente de Aportes

**Data:** 07/09/2026
**Escopo:** microárea de Aportes da Escrituração
**Status:** desenho aprovado, pronto para virar plano de implementação

---

## 1. O problema

Gabriel trabalha na microárea de **Aportes** da Escrituração de uma
administradora de FIDCs. Chegam de 20 a 50+ boletas de aplicação por dia,
lançadas pelos gestores no Portal ID ao longo do dia. Cada uma é analisada e
aprovada manualmente, e a análise segue sempre o mesmo checklist:

1. O cotista pode aportar naquele fundo/classe? (elegibilidade)
2. É o primeiro aporte dele naquele fundo? (define se sai Termo de Adesão)
3. O condomínio do fundo é aberto ou fechado? (define se sai Boletim de Subscrição)
4. A categoria CVM do cotista atende ao exigido pela classe e pela oferta?
5. Aprovar ou reprovar no Portal ID, e gerar os documentos.

O contexto operacional completo está em `contexto/01-esteira-subscricao.md` e
`contexto/02-escrituracao-4-microareas.md`.

### O diagnóstico

O gargalo não é preencher documento. É que **cada boleta refaz consultas já
respondidas antes**.

O condomínio de um fundo é fato permanente do regulamento, mas hoje é
garimpado no Slack a cada boleta daquele fundo. A qualificação exigida pela
classe é fixa. As regras da oferta valem por toda a vida da oferta. A categoria
CVM do cotista muda raramente. Nada disso muda entre uma boleta e a próxima —
e mesmo assim é reconsultado 30 vezes por dia.

O projeto é, no fundo, **memória**: transformar consultas repetidas em fatos
registrados uma vez.

### Restrições duras

- **Não existe API** para Britech, Slack ou Portal ID. Toda entrada é arquivo
  exportado, PDF baixado à mão, ou print de tela.
- **A aprovação final no Portal ID é sempre manual.** A ferramenta chega até a
  porta do portal com parecer e documentos prontos; não aprova nada.
- **Duas máquinas.** O desenvolvimento acontece na máquina pessoal do Gabriel;
  a ferramenta **roda na máquina da empresa**, porque é lá que estão os
  relatórios do Britech, os prints do Portal ID e as fichas dos cotistas, e é
  de lá que os documentos sobem para o portal. Levar dado de cotista para
  máquina pessoal contraria a seção 3. Ver seção 13.

---

## 2. Arquitetura

Duas camadas, com uma divisão de responsabilidade que é o eixo do desenho:

**Camada de entrada — Claude Code.** Lê os prints da fila de boletas, interpreta
o que está na tela, conversa. É flexível e falível. **Transcreve, nunca decide.**

**Núcleo determinístico — Python.** Regras de elegibilidade, consulta à base,
preenchimento de modelo, geração de PDF. Mesma entrada, mesma saída, sempre,
com teste automatizado. **Decide e gera, nunca chuta.**

O passo falível (ler uma imagem) fica isolado, visível e **conferido pelo
Gabriel antes de virar consequência**. Nenhum documento é gerado a partir de
transcrição não confirmada.

### Abordagem técnica (decidida na sessão de 05-06/09/2026)

**Python + docxtpl + Word COM para PDF.**

As minutas são `.docx` normais com tags Jinja (`{{ campo }}`) e condicionais
(`{% if %}`) escritas **dentro do próprio Word**. O argumento decisivo: o
Gabriel edita o modelo e cria seção condicional sem depender de programador.
Adicionar um campo é editar o Word, não fazer um commit.

Alternativas descartadas: `python-docx` com marcadores (o Word quebra
`{{ campo }}` em vários *runs* internos, e a condicional vira `if` em Python);
PowerShell + Word COM fazendo tudo (lento no volume, condicional frágil,
praticamente não testável).

O Word COM faz **só o último passo**: `.docx` preenchido → PDF, com a
fidelidade que só o Word tem.

### Ambiente verificado — **na máquina pessoal**

Estes fatos foram testados na máquina de desenvolvimento. **Nenhum deles vale
para a máquina da empresa** até ser verificado lá (ver seção 13).

- Windows 10 Home, PowerShell
- Word 16.0 com COM funcionando (testado)
- Python 3.12.10
- LibreOffice **não** instalado
- `gh` 2.98.0 autenticado na conta `Gabrielmarshbr`
- PyPI acessível: `docxtpl` 0.20.2 + Jinja2, lxml, python-docx — tudo em wheel,
  sem compilador. Nada instalado ainda.

---

## 3. Privacidade e LGPD

**Regra:** conhecimento operacional sobe para o GitHub; dado pessoal nunca sai
da máquina.

A base contém CPF, CNPJ, endereço e dados bancários de investidores da
administradora. Repositório privado protege contra estranhos — não contra
LGPD, não contra política interna, e não resolve dado pessoal de cliente da
empresa morando numa conta GitHub pessoal.

| Vai para o GitHub | Fica só na máquina |
|---|---|
| `src/` — o código | `dados/cotistas.json` |
| `regras/` — fundos e ofertas (YAML) | `dados/saldos/` — exportações do Britech |
| `modelos/` — as minutas `.docx` | `dados/boletas.json` |
| `docs/`, `contexto/` | `saida/` — os PDFs gerados |

Duas defesas, porque `.gitignore` sozinho depende de disciplina:

1. `.gitignore` cobrindo `dados/` e `saida/`.
2. **Um teste automatizado que falha** se qualquer arquivo sob `dados/` ou
   `saida/` estiver rastreado pelo git.

Os arquivos de referência usados nos testes (exportações de exemplo) têm nomes
e CPF/CNPJ substituídos por fictícios antes de entrar no repositório.

---

## 4. A base de fatos

```
ID - Escrituração/
├── regras/            → GitHub. YAML, editável à mão pelo Gabriel.
│   ├── fundos.yaml
│   └── ofertas.yaml
├── modelos/           → GitHub. Minutas .docx com as tags.
├── dados/             → .gitignore
│   ├── cotistas.json
│   ├── saldos/        → exportações do Britech, como vieram
│   └── boletas.json
├── saida/             → .gitignore. PDFs gerados, em pastas por data.
├── contexto/          → GitHub. Contexto operacional.
├── docs/              → GitHub.
└── src/               → GitHub.
```

### `regras/fundos.yaml` — por fundo e classe

Nome do fundo, CNPJ, identificação da classe, **condomínio (aberto/fechado)**,
**qualificação CVM exigida**, e a procedência do fato (regulamento consultado
em qual data).

Este arquivo é o ativo do projeto. Em git, cada linha ganha data e histórico:
responde "quando decidimos que esse fundo é fechado, e com base em quê" — algo
que hoje só existe na cabeça do Gabriel e no Slack.

### `regras/ofertas.yaml` — por oferta

A que classe pertence, **pública ou privada**, qualificação exigida quando
difere da classe, valor mínimo, vigência.

### `dados/cotistas.json`

Nome/razão social, CPF/CNPJ, tipo (PF / PJ / fundo), categoria CVM, endereço,
dados bancários, e-mail, representante legal com CPF (quando PJ ou fundo).

Cada bloco de campos carrega **de onde veio e quando** (cadastro da ficha
baixada em tal data; qualificação do Excel de tal data). Quando as fontes
discordarem, a data resolve — e o veredito mostra a procedência.

### `dados/saldos/` — posições

As exportações de Saldo de Aplicações do Britech ficam **como saíram do
sistema**. O programa lê a mais recente quando precisa; não copia posição para
lugar nenhum. Menos estado, menos risco de trabalhar com posição velha sem
perceber.

Daí saem duas respostas: "é primeiro aporte neste fundo?" e a % de
participação no PL para a Lista de Cotistas.

### `dados/boletas.json`

O que já foi processado e quais documentos saíram. É a memória que faz o print
seguinte mostrar só o que é novo.

---

## 5. As três portas de entrada da base

Custos escalonados, e o desenho usa as três:

1. **Saldo de Aplicações (Britech, Excel)** — o esqueleto: quem está no fundo,
   CPF/CNPJ, posição. Grátis, em lote, reexportável a qualquer momento.
2. **Excel de cotistas (Portal ID)** — os dados cadastrais de **~40%** dos
   cotistas, de uma vez.
3. **Ficha cadastral em PDF (Portal ID)** — o resto, sob demanda, à medida que
   aparecem. Baixada manualmente, layout fixo, com **três variantes: PF, PJ e
   fundo**. Três leitores, cada um com seu teste.

O princípio que rege a porta 3:

> **Toda vez que uma ficha é aberta, o dado fica.**

Hoje abrir uma ficha é trabalho descartável — lê, copia, fecha, e amanhã abre
de novo. Aqui é investimento: aquele cotista fica cadastrado e nunca mais
custa nada.

É isso que conserta a **Lista de Cotistas**, hoje cara justamente porque exige
os dados cadastrais de todos os cotistas de um fundo de uma vez. Com a base
engordando pelo uso diário dos aportes, ela vai deixando de ser trabalho e
virando consulta.

---

## 6. O motor de regras

Cada boleta passa por cinco perguntas, nesta ordem. Uma resposta **desconhecida**
interrompe o processamento daquela boleta e vira pendência. Uma resposta
conhecida, mesmo negativa, não interrompe — só muda o que sai no fim.

**1. Conheço esse cotista?**
Não está na base → para: *"cotista novo — baixe a ficha no Portal ID"*. Sem
cadastro não há Boletim, porque o Boletim é feito dos dados dele.

**2. O condomínio desta classe é aberto ou fechado?**
`fundos.yaml` não sabe → para: *"confira o regulamento no Slack do fundo"*.
Uma vez por fundo, na vida.
Aberto → **não existe Boletim de Subscrição**, e ela diz isso em vez de gerar um
documento que não deveria existir. Isso não interrompe a boleta: o Termo de
Adesão ainda pode sair, pela regra 3.

**3. É o primeiro aporte deste cotista neste fundo?**
A chave é **cotista + fundo**, não cotista + classe: é um Termo de Adesão por
cotista por fundo, independente de em quantas classes ele entra. Quem já aderiu
ao fundo pela Classe A não assina de novo ao entrar na Classe B.

Consulta o Saldo de Aplicações, que separa a posição por classe. Cada posição
carrega o **CNPJ do fundo** junto do id da classe, de propósito: se a pergunta
dependesse de traduzir classe→fundo pelo `fundos.yaml`, uma classe ainda não
cadastrada ficaria invisível e sairia um Termo de Adesão indevido.

**O TA independe do condomínio** — sai sempre no primeiro aporte no fundo.

**4. A qualificação bate?**
Categoria do cotista contra a exigida pela classe e pela oferta, valendo **a
mais restritiva das duas**. Hierarquia CVM assumida: Profissional cobre o que
exige Qualificado, que cobre o que exige Geral; o contrário não. Categoria
ausente na base → para e pede a ficha.

**5. A oferta é privada?**
Se for, **para sempre, e não gera documento**. Vínculo societário ou familiar
entre cotistas é julgamento humano sobre informação que não está em arquivo
nenhum. A boleta cai no monte "precisa de você", marcada *"oferta privada —
verificação de vínculo obrigatória"*, com todo o resto já apurado: as regras 1
a 4 respondidas, os dados conferidos, e o que sairia se fosse liberada. Depois
que o Gabriel confirmar o vínculo, ele manda gerar — a ferramenta não opina
sobre o vínculo, nem antes nem depois.

### Os três compromissos sobre erro

**Ausência de informação nunca vira permissão.** Não saber o condomínio não é
"provavelmente fechado". É pendência. O sistema é otimista sobre o tempo do
Gabriel e pessimista sobre o próprio conhecimento.

**Ela não aprova nada.** Aprovar é ato dele, no Portal ID, com a
responsabilidade dele. O que sai é parecer com documento anexado.

**Todo veredito vem com razão e fonte.** Nunca *"não pode aportar"* seco.
Sempre *"a classe exige Profissional; o cotista consta como Qualificado,
segundo a ficha baixada em 12/03/2026"*. Dá para discordar dela — e ao
discordar, sabe-se exatamente qual fato corrigir.

Consequência: o sistema fica **mais rápido conforme é usado, e nunca mais
permissivo**. Cada pendência resolvida é um fundo ou um cotista que sai da fila
para sempre.

---

## 7. Os documentos

### Boletim de Subscrição

Minuta fixa, **não varia por fundo nem por gestor**. Só existe em condomínio
fechado. Campos: identificação do subscritor (nome/razão social, CPF ou CNPJ,
endereço, dados bancários, representante legal quando PJ ou fundo),
características da oferta, valor total aportado (numérico e por extenso), e o
quadro de integralização.

No quadro: **"Quantidade de Cotas subscritas" e "Preço de Emissão por Cota"
usam texto descritivo fixo**, não valor calculado. Só **"Preço de Subscrição"**
traz o valor total em R$.

### Termo de Adesão e Ciência de Risco

Sai no primeiro aporte do cotista **no fundo**, independente do condomínio.
Um por cotista por fundo, em quantas classes ele entrar.

### Como o preenchimento funciona

**O modelo é do Gabriel.** `.docx` em `modelos/`, editável no Word. Estilo da
casa, numeração e sumário saem intactos porque o programa nunca reconstrói o
documento — só preenche o que já está lá.

As diferenças entre PF, PJ e fundo são **condicionais dentro do próprio
modelo**: o bloco de representante legal aparece só quando o subscritor é PJ ou
fundo. Criadas e editadas no Word, sem tocar em código.

**Validador de modelo.** Comando que confere a minuta e lista as tags
encontradas, denunciando aspas curvas trocadas pela autocorreção do Word, tag
partida no meio, ou `{% if %}` sem `{% endif %}`. Rodado depois de editar o
modelo, não a cada boleta. Sem ele, um clique errado no Word quebra o bloco
inteiro em silêncio.

**Valor por extenso é calculado por código**, com teste — inclusive centavos,
"um mil" e concordância.

**Campo sem dado impede a geração.** O documento não sai; vira pendência com o
nome do campo que faltou. Nunca sai Boletim com buraco ou com placeholder.

**PDF pelo Word COM.** O Word abre **uma vez por bloco** e converte todos os
documentos daquele bloco — a conversão é a parte lenta, e não faz sentido
pagá-la 40 vezes.

**Saída previsível, sem sobrescrever.** Pasta por data, nome padronizado por
fundo, classe, cotista e data. Documento que já existe gera aviso, não
sobrescrita: reprocessar o mesmo print duas vezes precisa ser inofensivo.

**Relatório do bloco** junto da saída: o que gerou, com quais dados, de que
fonte vieram, o que parou e por quê. É o que sustenta a conferência por
amostragem — confere-se alguns, mas sabe-se o que aconteceu com todos.

---

## 8. O ciclo de trabalho

**Uma vez, no começo.** Exportar o Saldo de Aplicações dos fundos que trabalha
e o Excel de cotistas do Portal ID para `dados/`. A base nasce com o esqueleto
completo e os dados cadastrais de ~40% dos cotistas.

**Quando senta para trabalhar um bloco.** Abre o Claude Code nesta pasta e cola
o print da página de boletas do Portal ID — que traz fundo, carteira aportada,
dados do cotista e valor do aporte, tudo numa tela.

A transcrição é apresentada em tabela para conferência. Confirmada, o núcleo
processa e devolve três montes:

- **Passou** — PDFs prontos em `saida/`, com o TA junto quando é primeiro
  aporte na classe.
- **Precisa de você** — oferta privada, ou caso fora das regras. Diz por quê.
- **Faltou dado** — diz exatamente o quê e onde buscar: *"fundo ABC: condomínio
  desconhecido, confira o regulamento no Slack"*, *"cotista Fulano: falta
  endereço, baixe a ficha no Portal ID"*.

**Só o que é novo aparece.** As boletas já processadas são reconhecidas e
ignoradas em silêncio. Colar o mesmo print de novo é inofensivo.

**Quando resolve uma pendência.** O fato é registrado uma vez — o condomínio do
fundo, a ficha do cotista — e nunca mais é perguntado.

**Caminho alternativo.** A fila de boletas do Portal ID também é exportável em
planilha. Não é o caminho principal (as boletas chegam ao longo do dia, e
exportar a planilha inteira a cada boleta nova é desperdício), mas serve para
conferir se nada escapou ou recuperar um dia inteiro de uma vez.

**Aprovar no Portal ID continua manual.**

O ganho está no terceiro monte encolhendo. Na primeira semana muita coisa cai
em "faltou dado", porque a base está vazia. Na terceira, os fundos e cotistas
recorrentes já estão registrados, e o que sobra é o primeiro monte para
conferir por amostragem e o segundo para decidir.

---

## 9. Testes

**O motor de regras é a parte com teste de verdade.** Não lê arquivo nem
escreve nada: recebe cotista, classe, oferta e valor, devolve veredito. Cada
linha do checklist vira caso de teste — Qualificado em classe que exige
Profissional, aporte na classe B de quem já está na A do mesmo fundo, oferta privada,
condomínio desconhecido. Teste escrito antes do código.

**Os leitores são testados contra arquivos reais, anonimizados.** Uma
exportação de cada tipo — Saldo do Britech, Excel de cotistas do Portal ID,
ficha PF, ficha PJ, ficha de fundo — com nomes e CPF/CNPJ fictícios, guardada
no repositório. É o único jeito honesto de testar leitura de relatório: contra
o formato que o sistema realmente produz, não contra o imaginado.

**Valor por extenso**: tabela de casos, incluindo os chatos.

**Preenchimento do `.docx`**: testável sem abrir o Word — verifica que as tags
sumiram e que os valores certos estão no documento.

**Conversão em PDF pelo Word COM**: teste de fumaça manual, um documento,
olhado por gente. Não é automatizável de forma confiável.

**A transcrição do print não é testável.** Por isso é conferida antes de virar
qualquer coisa. É o único ponto do sistema onde a correção depende de
julgamento humano no momento, e o desenho está organizado para que seja o
único.

**Teste de vazamento**: falha se qualquer arquivo de `dados/` ou `saida/`
estiver rastreado pelo git.

---

## 10. Riscos conhecidos

**O layout dos relatórios vai mudar.** Britech ou Portal ID atualizam, uma
coluna troca de nome. Defesa: **falhar alto** — se as colunas esperadas não
estão lá, o leitor recusa o arquivo e diz qual sumiu. Nunca "não achei, assumo
vazio", que é a falha que vira Boletim errado.

**O Word vai quebrar uma tag.** Defesa: o validador de modelo, rodado como
hábito depois de mexer na minuta.

**A base vai envelhecer.** Um cotista Geral vira Qualificado e a ficha na base é
de seis meses atrás. Sem política de validade inventada: a **data da fonte
aparece junto do veredito**, e o julgamento sobre "isso está velho demais?"
continua humano. É informação, não regra.

**Vai aparecer oferta com regra desconhecida.** Cai em "precisa de você". O
sistema não tem caminho para decidir errado; só tem caminho para se recusar a
decidir.

**Dado pessoal pode vazar para o git por descuido.** Um `git add .` distraído.
Defesa automatizada, na seção 3.

**Dependência pode ser bloqueada um dia.** `requirements.txt` com versões
travadas, ambiente virtual dentro da pasta do projeto, e as wheels guardadas
para permitir instalação offline.

---

## 11. Fora de escopo

Deliberadamente não construído nesta rodada:

- **Integração com Slack.** App do Slack exige aprovação do workspace
  (dependência da TI). E o ganho é pequeno: o regulamento de cada fundo é lido
  **uma vez na vida**. Se a TI liberar depois, entra como conveniência para
  buscar e baixar o documento — nunca como decisor, porque extrair "condomínio
  aberto ou fechado" de cláusula jurídica é a espécie de leitura que erra em
  silêncio.
- **Login automatizado no Portal ID.** Não há acesso.
- **Leitura automática do suplemento de oferta em PDF.** Formato livre, varia
  por gestor — a espécie ruim de extração.
- **Motor de vínculo societário/familiar** para ofertas privadas. É julgamento
  humano.
- **Amortização** (microárea 4), incluindo AMEX.
- **Lista de Cotistas** como comando próprio. Ela é o segundo entregável,
  depende da mesma base, e ganha uma spec própria depois que o assistente de
  boleta estiver rodando.

---

## 12. Pendências para a implementação

Coisas a verificar ao começar, não decididas aqui:

1. ~~**O Saldo de Aplicações do Britech separa a posição por classe?**~~
   **Respondido em 07/09/2026: separa.** O leitor deve produzir, por linha,
   o documento do cotista, o CNPJ do fundo e o id da classe.
2. **A exportação de boletas do Portal ID traz número ou código da boleta?** Se
   traz, é a chave de deduplicação. Se não, a chave composta (cotista + fundo +
   valor + data) é menos sólida: duas boletas idênticas no mesmo dia colapsam
   em uma. Vale checar também se o print exibe esse identificador.
3. **Arquivos de referência.** São necessários, anonimizados: Saldo de
   Aplicações (Britech), Excel de cotistas (Portal ID), ficha PF, ficha PJ,
   ficha de fundo, print da página de boletas, e as minutas `.docx` do Boletim
   de Subscrição e do Termo de Adesão.
4. **Repositório GitHub.** Privado, `id-escrituracao`, conta `Gabrielmarshbr`.
   Criado e enviado só mediante autorização explícita. Antes do primeiro push,
   decidir o que fazer com `historico/` — é transcrição de conversa, o tipo de
   arquivo onde nomes aparecem sem ninguém perceber. Recomendação: tirar do git
   e manter só local.

---

## 13. Duas máquinas

O desenvolvimento acontece na máquina pessoal. A ferramenta roda na máquina da
empresa. Isso não é preferência: os dados estão lá, os documentos sobem de lá,
e a seção 3 proíbe trazer dado de cotista para cá.

### O que a máquina da empresa precisa

| | Situação |
|---|---|
| **Word** | Certamente já instalado. Sem preocupação. |
| **Python + bibliotecas** | Gabriel confirmou que **pode instalar**. |
| **Claude Code** | Gabriel confirmou que **pode instalar**. |
| **Git** | **Não é necessário para rodar.** Só para desenvolver e atualizar. |

### Consequências no desenho

**Claude Code na máquina da empresa é pré-requisito da entrada por print.** A
camada que lê o print é o Claude Code. Se ele não puder rodar lá — instalação
bloqueada ou saída de rede para a Anthropic barrada, comum em ambiente
corporativo — o núcleo Python continua funcionando, mas a entrada volta a ser a
exportação da planilha de boletas. **Verificar cedo**: instalar e rodar um
comando trivial, antes de qualquer coisa depender disso.

**A instalação precisa ser reproduzível.** `requirements.txt` com versões
travadas e ambiente virtual dentro da pasta do projeto. As wheels ficam
guardadas para permitir instalação offline — "posso instalar hoje" não é
"poderei instalar sempre", e refazer a instalação não pode depender de o PyPI
estar liberado naquele dia.

**Como o código chega lá.** Com Git instalado, `git clone` e depois `git pull`
para atualizar. Sem Git, copiar a pasta (pendrive ou rede) e substituir. Os
dois funcionam; o segundo é mais manual. Não é decisão que precise ser tomada
agora.

**O que nunca atravessa.** `dados/` e `saida/` existem só na máquina da
empresa. Não vêm para cá nem para o GitHub — nem para depurar. Se um leitor
falhar com um arquivo real, o que atravessa é uma **cópia anonimizada** feita
lá, ou a mensagem de erro.
