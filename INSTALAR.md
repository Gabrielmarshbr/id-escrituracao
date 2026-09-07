# Instalar na máquina da empresa

Este projeto é desenvolvido na máquina pessoal do Gabriel e **roda na máquina
da empresa** — é lá que estão os relatórios do Britech, os prints do Portal ID
e as fichas dos cotistas, e é de lá que os documentos sobem para o portal.

---

## Antes de tudo: o que existe hoje

O que está construído é o **núcleo** — motor de regras, base de fatos,
preenchimento de minuta, conversão em PDF. Tudo testado.

**Ainda não existe um comando que pegue uma boleta e gere um documento.**
Isso é a task 18 do plano, e depende dos leitores de relatório, que dependem
dos arquivos de referência (ver `RETOMAR.md`).

Na máquina da empresa, hoje, dá para rodar duas coisas: a suíte de testes e o
teste de fumaça do Word. É o suficiente para provar que a base funciona lá —
não é ferramenta de trabalho ainda.

---

## 1. Levar o projeto

Não há repositório no GitHub. É cópia de pasta — pendrive, OneDrive, rede.

**Copie a pasta inteira, menos:**

| Pasta | Por que não copiar |
|---|---|
| `.venv/` | Tem caminhos absolutos da outra máquina cravados dentro. Lá ela não funciona; será recriada no passo 3. |
| `saida/` | Só contém o PDF do teste de fumaça. |
| `dados/` | Está vazia. E, quando não estiver, **nunca** deve fazer o caminho inverso: dado de cotista não sai da máquina da empresa. |

---

## 2. Instalar o que falta

**Python 3.12** — obrigatório, é do que a ferramenta é feita.

**Claude Code** — para retomar o projeto na máquina da empresa.

> Instale o Claude Code cedo, mesmo antes de precisar dele. A camada que lê o
> print da fila de boletas é o Claude Code. Se a rede da empresa barrar a saída
> para a Anthropic, essa entrada não existe naquela máquina e o desenho muda.
> Melhor descobrir agora.

**Word** — certamente já está lá. É ele que gera os PDFs.

---

## 3. Preparar o ambiente

No PowerShell, **dentro da pasta do projeto**:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

As versões estão travadas no `requirements.txt` — são exatamente as que foram
testadas na máquina de desenvolvimento.

**Se o PyPI estiver bloqueado pela rede da empresa**, este passo falha. Há
saída: baixar as wheels na máquina pessoal e levar junto, instalando offline.
Abra o Claude Code na pasta e peça o pacote offline.

---

## 4. Conferir que funciona

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Esperado: **89 testes passando**.

```powershell
.\.venv\Scripts\python.exe scripts\fumaca_pdf.py
```

Esperado: um PDF em `saida\fumaca\fumaca.pdf`. **Abra e olhe.** Este teste só
vale conferido por gente — é ele que prova que o Word daquela máquina converte
com fidelidade, que é a razão de o Word estar no desenho.

Se qualquer um dos dois falhar, não tente resolver sozinho: abra o Claude Code
na pasta e mostre o erro. Falha aqui é informação, não problema.

---

## 5. Regra que não se quebra

`dados/` e `saida/` existem **só** na máquina da empresa. Não voltam para a
máquina pessoal e não vão para o GitHub — nem para depurar um erro.

Se um leitor falhar com um arquivo real, o que atravessa é uma **cópia
anonimizada** feita lá, ou a mensagem de erro. Nunca o arquivo original.

Há um teste que falha se qualquer arquivo dessas pastas for rastreado pelo
git. Ele roda junto com os outros.

---

## Depois de instalar

Abra o Claude Code na pasta e leia o `RETOMAR.md`. Ele lista os arquivos de
referência que destravam a próxima etapa e as duas verificações a fazer nos
sistemas (se o Saldo de Aplicações do Britech separa posição por classe, e se
a exportação de boletas traz número da boleta).
