# Como começar a usar

Três passos, nesta ordem. Depois deles, a equipe consegue lançar uma boleta e
receber o Boletim de Subscrição em PDF.

---

## Passo 1 — Instalar (uma vez por máquina)

Está no [`INSTALAR.md`](INSTALAR.md). Resumo: Python 3.12, `git clone`, criar o
ambiente, rodar os testes.

Ao final, confira que o Word converte nesta máquina:

```powershell
.venv\Scripts\python.exe scripts\fumaca_pdf.py
```

Abra o PDF que aparecer em `saida\fumaca\` e olhe. Se estiver legível, o
caminho `.docx → PDF` está de pé.

---

## Passo 2 — Marcar as minutas (uma vez, e é você quem faz)

**Sem este passo nada é gerado.** O programa não inventa documento: ele preenche
o que já está escrito.

Coloque nesta pasta as duas minutas, com estes nomes exatos:

```
modelos\boletim_subscricao.docx
modelos\termo_adesao.docx
```

Abra cada uma no Word e, onde hoje há dado que muda de documento para documento,
escreva a tag correspondente. A lista completa de tags está em
[`modelos/CAMPOS.md`](modelos/CAMPOS.md).

Depois de editar, rode o validador — a autocorreção do Word quebra tags em
silêncio, e é para isso que ele existe:

```powershell
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'src'); from pathlib import Path; from aportes.documentos.validador import validar_minuta; print(validar_minuta(Path('modelos/boletim_subscricao.docx')) or 'minuta ok')"
```

---

## Passo 3 — Cadastrar os fundos e as ofertas que vocês usam

Também é você: quem decide que um fundo é fechado é quem responde pela área. A
tela do navegador **lê** essas regras e nunca as escreve.

Abra `regras\fundos.yaml` e `regras\ofertas.yaml`. Os dois têm um exemplo
comentado dentro. Não precisa cadastrar os 500 fundos — só os que aparecerem,
um por vez, na primeira boleta de cada.

Depois de editar, confira que carregou:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

---

## Pronto: o dia a dia

**Para a equipe** — clique duas vezes em **`Aportes.bat`**. Abre uma página no
navegador com o formulário da boleta. Preenche, clica em Analisar, e o
resultado vem em um de quatro estados:

| Resultado | O que significa |
|---|---|
| **Liberada** | Regras conferidas. Os PDFs estão na pasta de saída. |
| **Não elegível** | O cotista não pode entrar. O motivo diz por quê e com base em qual fonte. |
| **Precisa de análise humana** | Oferta privada. Nenhum documento é gerado — vínculo societário é decisão de gente. |
| **Faltou dado** | Diz exatamente o que falta e onde buscar. |

Se o cotista ainda não estiver na base, a própria tela oferece cadastrá-lo. Uma
vez cadastrado, ele nunca mais custa nada.

**Para você, no Claude Code** — abra o projeto e cole o print da fila de
boletas. Eu transcrevo, você confere, e o bloco inteiro é processado de uma vez.

**Aprovar no Portal ID continua manual**, nos dois casos. O que o sistema faz é
chegar até a porta do portal com a decisão tomada e os documentos prontos.

---

## Para a equipe compartilhar a mesma base

Enquanto não fizer isso, cada máquina tem a sua base e vocês divergem em uma
semana.

Copie `config.exemplo.json` para `config.local.json` e aponte para uma pasta de
rede da empresa ou o OneDrive **corporativo** — nunca um pessoal, porque é dado
de investidor:

```json
{
  "pasta_dados": "\\\\servidor\\escrituracao\\aportes\\dados",
  "pasta_saida": "\\\\servidor\\escrituracao\\aportes\\saida"
}
```

Cada pessoa grava só no próprio arquivo (`cotistas.maria.json`,
`cotistas.gabriel.json`), e o programa funde tudo na leitura. Ninguém sobrescreve
ninguém, e dá para saber quem cadastrou o quê.

---

## O que ainda não existe

**A leitura dos relatórios do Britech e do Portal ID.** Por isso o formulário
pergunta *"é o primeiro aporte deste cotista neste fundo?"* — sem o Saldo de
Aplicações carregado, o sistema não sabe, e **não vai adivinhar**. Sua resposta
é usada e fica registrada como resposta de pessoa, não como fato apurado.

Quando o leitor do Britech existir, essa pergunta some sozinha.

**A leitura da ficha cadastral em PDF.** Por enquanto o cadastro de cotista é
digitado na tela.

O que destrava as duas coisas está no [`RETOMAR.md`](RETOMAR.md).
