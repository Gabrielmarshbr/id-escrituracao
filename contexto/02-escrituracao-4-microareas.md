# Escrituração — contexto operacional completo (foco: Aportes)
> Enviado pelo Gabriel na sessão de 07/09/2026. Texto dele, preservado.

## Estrutura da área
A área de Escrituração é dividida em 4 microáreas, sequenciais e interdependentes:
1. **Ofertas**  2. **Cadastro**  3. **Aportes** ← foco da automação  4. **Amortização**

## 1. Ofertas
- O time de Ofertas monta os suplementos de oferta em conjunto com o gestor.
- O jurídico sobe o documento para assinatura e envia o suplemento assinado
  pelo **Slack** (canal específico do fundo).
- Com o suplemento assinado, o time cadastra a oferta no **Portal ID** e
  libera a carteira/oferta para o gestor poder boletar aplicações.
- Características que variam por suplemento:
  - **Amortização programada** (com datas específicas) ou não.
  - **Oferta pública** (qualquer cotista qualificado para o fundo pode entrar)
    ou **oferta privada** (além da qualificação, o cotista precisa ser sócio ou
    ter relação familiar com os outros cotistas da oferta — exige verificação
    manual de trava/elegibilidade).

## 2. Cadastro
- Recebe apenas 2 dados iniciais do cotista: **nome e CPF/CNPJ**.
- Envia link de ficha cadastral (via Portal ID) para o e-mail do cotista.
- Cotista preenche a ficha → Escrituração analisa e aprova no portal →
  Compliance analisa e aprova → cliente recebe a ficha para assinar.
- Ficha fica disponível na página de investidores do Portal ID, em PDF anexado
  e também em formato nativo da própria página (pesquisável pelos dados do cotista).

## 3. Aportes (microárea do Gabriel — foco da automação)
**Pré-requisitos para um gestor conseguir boletar:**
- Cotista cadastrado e aprovado no Portal ID (etapa 2).
- Oferta cadastrada e carteira liberada (etapa 1).

**Volume:** 20+ boletas/dia, podendo chegar a 50+ em dias de pico. Aprovação é
manual, uma a uma.

**Checklist de análise por boleta (feito manualmente hoje):**
1. Verificar se o cotista **pode aportar naquele fundo/classe** (elegibilidade).
   - Oferta **privada**: checar se o cotista é sócio ou tem relação familiar com
     os demais cotistas daquela oferta (trava além da qualificação).
   - Oferta **pública**: basta a qualificação exigida pelo fundo.
2. Verificar se é o **primeiro aporte** do cotista naquele fundo → se sim, gerar
   o **Termo de Adesão (TA)** junto com o Boletim de Subscrição.
3. Verificar no **Regulamento** (buscado no Slack do fundo) se o **condomínio é
   aberto ou fechado** — Boletim de Subscrição só existe em condomínio fechado.
4. Verificar a **categoria de qualificação do cotista** (Geral / Qualificado /
   Profissional, categorias CVM) contra o exigido pela oferta/classe.
5. Aprovar ou reprovar a boleta no Portal ID.
6. Se aprovado: gerar os documentos necessários (BS, e TA se for o 1º aporte).
7. **Se o cotista for novo no sistema**: cadastrar no **Britech** e liberar
   visualização para todos os gestores e funcionários que precisam enxergar
   aquele fundo/cotista.

**Outras responsabilidades da microárea de Aportes:**
- Extrair relatórios do **Britech** (Saldo de Aplicações, Extrato de
  Movimentação, Histórico de Cotas, Carteira) — em PDF ou Excel — e enviar por
  e-mail para cotistas/gestores que pedem extrato de posição (fechamento de mês).
- Montar **Lista de Cotistas** sempre que o jurídico solicitar (diariamente).
  Processo: pegar cotistas atuais no Saldo de Aplicações do Britech + cruzar
  e-mail, representante legal e CPF do representante com a ficha cadastral de
  cada cotista. Às vezes pedem também quantidade de cotas e % de participação
  no PL do fundo.

## 4. Amortização
- Informações vêm dos gestores via Slack.
- **Fundo aberto (resgate):** não precisa de ATA — só boletagem no Portal ID,
  área de amortização.
- **Fundo fechado**, duas formas:
  - **Via suplemento**: já prevê datas de amortização (principal + juros, só
    principal, ou só juros), geralmente com carência de 12 meses após a criação
    da oferta.
  - **Via AMEX (Amortização Extraordinária)**: gestor pede → Risco e Escrituração
    validam → jurídico sobe ATA de amortização extraordinária com datas e valores
    → gestor ou o time sobe a boleta no portal → áreas aprovam/validam.

## Sistemas

### Britech
- Fonte dos relatórios: Saldo de Aplicações, Histórico de Cotas, Extrato de
  Movimentação, Carteira. Saem em **PDF e Excel**.
- Também gerencia os **usuários da plataforma** (gestores e funcionários). A
  microárea de Aportes cria usuários novos e libera visualização de cada
  fundo/cotista para quem precisa enxergar.

### Slack
- Plataforma de conversa entre funcionários, gestores e consultores.
- Um canal por fundo — **500+ fundos, 500+ canais**.
- Onde o jurídico posta os documentos oficiais: regulamento, lâmina, suplemento
  de oferta, ATAs.

### Portal ID
- Onde todas as operações são registradas: carteiras abertas, ofertas cadastradas,
  boletas de aporte e de amortização/resgate. Tem página própria de cotistas
  (ficha cadastral).
- Instável, com bugs frequentes. Duas sugestões de melhoria já registradas para
  levar à TI: trava contra boleta de cotista novo em oferta fechada, e paginação
  de 50 itens por página nas boletas em vez de 10.

## Objetivo declarado
Automação máxima do fluxo, com **prioridade total na microárea de Aportes**:
é onde está o maior volume manual e repetitivo (20–50+ boletas/dia), e as
decisões tomadas ali (elegibilidade, geração de BS/TA, cadastro no Britech) têm
efeito direto nas outras 3 microáreas.

## Pontas que dependem de decisão/estruturação
- Não existe base centralizada e estruturada de cotistas + qualificação CVM +
  relações societárias/familiares (necessária para elegibilidade em ofertas privadas).
- Não existe motor de regras que combine regulamento do fundo (regras fixas) +
  suplemento da oferta (regras variáveis) + tipo de condomínio (aberto/fechado) +
  qualificação do cotista.
- Extração de dados do Britech e do Slack é manual (sem API/integração conhecida).
