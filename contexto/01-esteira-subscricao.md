# Esteira de Subscrição de Cotistas — contexto para automação
> Enviado pelo Gabriel na sessão de 07/09/2026. Texto dele, preservado.

## Visão geral do fluxo
Trabalho em uma gestora/administradora de FIDCs. A esteira de uma nova entrada
de cotista em um fundo segue este fluxo, e a ideia é automatizar/apoiar as
etapas abaixo:

1. **Oferta** — o gestor do fundo lança uma oferta (emissão) de uma classe/série
   específica. Cada oferta tem regras próprias (pode ser aberta a novos
   investidores ou restrita aos já existentes, pode ter valor mínimo, pode
   exigir qualificação específica etc.).
2. **Regulamento do fundo** — documento base que define, para cada classe do
   fundo, quais categorias de investidor podem entrar (Geral / Qualificado /
   Profissional, nas categorias da CVM) e outras regras fixas que raramente
   mudam entre ofertas.
3. **Boleta de aporte** — quando um gestor lança uma oferta, ele preenche uma
   boleta no Portal ID informando os dados do aporte (cotista, valor, classe).
   Hoje isso é feito manualmente pelo gestor no portal (temos sugestões de
   melhoria pendentes de levar para TI: trava para impedir boleta de cotista
   novo em oferta fechada, e paginação de 50 boletas por página em vez de 10).
4. **Cotistas / Ficha de cotista** — cada cotista tem um cadastro com seus
   dados (nome/razão social, CPF/CNPJ, dados bancários, representante legal
   quando PJ) e sua ficha de qualificação (categoria CVM: Geral, Qualificado
   ou Profissional). Ainda não decidido como essa base de cotistas e
   qualificações será estruturada/alimentada.
5. **Análise de perfil do cotista / elegibilidade** — antes de aceitar o
   aporte, é preciso checar se aquele cotista pode entrar (a) naquela oferta
   específica e (b) naquela classe do fundo. As regras de elegibilidade são
   uma mistura de:
   - regras fixas por fundo/classe (vêm do regulamento, raramente mudam)
   - regras variáveis por oferta/emissão (podem mudar a cada nova oferta)
   O sistema precisa avisar automaticamente se o cotista pode ou não entrar,
   cruzando a categoria de qualificação do cotista com as regras da
   oferta/classe.
6. **Boletim de Subscrição** — documento formal (minuta docx fixa, não muda
   por fundo/gestor) que formaliza a subscrição das cotas. Campos principais:
   identificação do subscritor (nome/razão social, CPF/ME ou CNPJ/ME conforme
   pessoa física ou jurídica, endereço, dados bancários, representante legal
   se PJ), características da oferta, valor total aportado (numérico e por
   extenso), e cálculo de integralização (quantidade de cotas, preço de
   emissão, preço de subscrição). As colunas "Quantidade de Cotas subscritas"
   e "Preço de Emissão por Cota" usam texto descritivo fixo (não valor
   calculado); só "Preço de Subscrição" traz o valor total em R$.
7. **Termo de Adesão e Ciência de Risco** — documento anexo ao boletim na
   primeira vez que um cotista entra no fundo (declaração de ciência dos
   riscos — mercado, liquidez, concentração etc., termos do Regulamento e do
   Anexo da Classe). Em aportes subsequentes do mesmo cotista, o TA não
   precisa ser reenviado.

## Fontes de dados hoje
- Ofertas de aporte chegam em **PDF** enviado pelos gestores.
- Saldos/posições de cotistas vêm de PDFs do Portal ID ("Saldos de Aplicações
  de Cotistas", "Histórico de Cota", "Extrato Consolidado/Extrato Cotista",
  "Movimentação de Cotistas").
- Valores de aporte às vezes chegam via print de tela do sistema, com valor
  bruto e valor líquido (após IOF).
- Não há acesso de login ao Portal ID para automação direta — o preenchimento
  final no portal é sempre manual.

## Resultado esperado de cada etapa (documentos gerados)
- Boletim de Subscrição preenchido (docx/PDF), pronto para conferência e
  upload manual no Portal ID.
- Termo de Adesão anexado apenas na primeira entrada do cotista no fundo.
- Planilhas "Lista de Cotistas" por fundo (Nome, CPF/CNPJ, Representantes,
  Qtd. Cotas, Participação), a partir dos PDFs de saldo do Portal ID.
- Verificação de elegibilidade (categoria CVM do cotista x regras da
  oferta/classe) antes de formalizar a subscrição.

## Em aberto
- Estrutura de dados para a base de cotistas + qualificações (fonte de
  verdade ainda não definida).
- Regras de elegibilidade por oferta ainda tratadas caso a caso, sem um
  motor de regras centralizado.
