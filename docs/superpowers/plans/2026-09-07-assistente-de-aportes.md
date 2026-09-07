# Assistente de Aportes — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir o núcleo determinístico que decide se uma boleta de aporte pode ser aprovada e gera o Boletim de Subscrição e o Termo de Adesão em PDF.

**Architecture:** Duas camadas. O Claude Code lê o print da fila de boletas e transcreve; este núcleo Python decide e gera. O motor de regras é puro — recebe boleta e base de fatos, devolve veredito, sem tocar em disco. Ao redor dele ficam a persistência (YAML para regras, JSON para cotistas), os leitores de relatório e a geração de documento via `docxtpl` + Word COM.

**Tech Stack:** Python 3.12, docxtpl 0.20.2, python-docx 1.2.0, num2words 0.5.14, PyYAML 6.0.3, openpyxl 3.1.5, pdfplumber 0.11.10, pywin32 312, pytest 9.1.1.

**Spec:** `docs/superpowers/specs/2026-09-07-aportes-design.md`

## Global Constraints

- **Python 3.12.** Sintaxe moderna de tipos (`X | None`) é permitida.
- **LGPD:** nada sob `dados/` ou `saida/` pode ser rastreado pelo git. Um teste garante isso (Task 1). Nenhum teste, fixture ou mensagem de erro pode conter CPF, CNPJ, nome ou dado bancário real — só fictícios.
- **Dinheiro é `Decimal`, nunca `float`.** Construído a partir de `str`.
- **CPF/CNPJ são armazenados só com dígitos** (`"12345678901"`), formatados apenas na saída.
- **Ausência de informação nunca vira permissão.** Fato desconhecido é pendência, jamais um valor-padrão permissivo.
- **O motor de regras não aprova e não gera.** Ele devolve veredito; quem gera é outra camada.
- **Todo veredito carrega razão e procedência** (a fonte do fato e a data).
- **`requirements.txt` com versões travadas**, ambiente virtual em `.venv/` dentro da pasta do projeto.
- **A ferramenta roda na máquina da empresa.** Nenhum caminho absoluto da máquina de desenvolvimento entra no código.
- Mensagens ao usuário em **português**.

## Estrutura de arquivos

```
src/aportes/
├── __init__.py
├── dominio.py           # tipos: Cotista, Classe, Oferta, Boleta, Veredito
├── extenso.py           # valor por extenso e formatação em R$
├── qualificacao.py      # hierarquia das categorias CVM
├── regras.py            # o motor: avaliar(boleta, base) -> Veredito
├── base/
│   ├── __init__.py
│   ├── fundos.py        # regras/fundos.yaml
│   ├── ofertas.py       # regras/ofertas.yaml
│   ├── cotistas.py      # dados/cotistas.json
│   └── boletas.py       # dados/boletas.json (memória do que já foi visto)
├── documentos/
│   ├── __init__.py
│   ├── validador.py     # confere as tags de uma minuta .docx
│   ├── preenchimento.py # docxtpl
│   └── pdf.py           # Word COM
└── leitores/            # BLOQUEADO — depende dos arquivos de referência
tests/
```

Cada arquivo tem uma responsabilidade. `regras.py` não importa nada de `base/`
nem de `documentos/`: ele recebe os fatos prontos. É isso que o torna testável.

---

### Task 1: Esqueleto do projeto, ambiente e guardrail de LGPD

**Files:**
- Create: `requirements.txt`, `pytest.ini`, `src/aportes/__init__.py`, `tests/__init__.py`
- Test: `tests/test_privacidade.py`

**Interfaces:**
- Consumes: nada.
- Produces: o pacote `aportes` importável e a suíte de testes rodando.

- [ ] **Step 1: Criar o ambiente virtual e as dependências**

`requirements.txt`:

```
docxtpl==0.20.2
python-docx==1.2.0
num2words==0.5.14
PyYAML==6.0.3
openpyxl==3.1.5
pdfplumber==0.11.10
pywin32==312
pytest==9.1.1
```

```bash
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

- [ ] **Step 2: Criar a estrutura mínima do pacote**

`pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = src
```

Criar `src/aportes/__init__.py` e `tests/__init__.py` vazios.

- [ ] **Step 3: Escrever o teste de vazamento**

`tests/test_privacidade.py`:

```python
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def test_dados_e_saida_nunca_sao_rastreados_pelo_git():
    """Dado pessoal de cotista nao pode chegar ao repositorio.

    .gitignore depende de disciplina; este teste nao.
    """
    resultado = subprocess.run(
        ["git", "ls-files", "dados", "saida"],
        cwd=RAIZ, capture_output=True, text=True, check=True,
    )
    rastreados = resultado.stdout.split()
    assert rastreados == [], (
        "Arquivos com dado pessoal foram rastreados pelo git: "
        f"{rastreados}. Rode: git rm --cached <arquivo>"
    )
```

- [ ] **Step 4: Rodar o teste e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_privacidade.py -v`
Expected: PASS (nada sob `dados/` ou `saida/` está rastreado)

- [ ] **Step 5: Verificar que o teste realmente pega o problema**

```bash
mkdir -p dados && echo "teste" > dados/vazamento.txt
git add -f dados/vazamento.txt
.venv/Scripts/python.exe -m pytest tests/test_privacidade.py -v
```

Expected: FAIL, citando `dados/vazamento.txt`. Um guardrail que nunca falhou
não é guardrail. Depois:

```bash
git rm --cached dados/vazamento.txt && rm dados/vazamento.txt
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt pytest.ini src tests
git commit -m "chore: esqueleto do projeto e guardrail de LGPD"
```

---

### Task 2: Valor por extenso e formatação monetária

**Files:**
- Create: `src/aportes/extenso.py`
- Test: `tests/test_extenso.py`

**Interfaces:**
- Consumes: nada.
- Produces: `valor_por_extenso(valor: Decimal) -> str` e `formatar_reais(valor: Decimal) -> str`.

O Boletim de Subscrição traz o valor aportado numérico **e** por extenso. Os
valores esperados abaixo foram verificados contra `num2words` 0.5.14 nesta
máquina — não são adivinhados.

Uma decisão explícita: `num2words` produz `"mil, duzentos e trinta e quatro
reais"`, com vírgula. Documento jurídico brasileiro escreve sem. A vírgula é
removida.

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_extenso.py`:

```python
from decimal import Decimal

import pytest

from aportes.extenso import formatar_reais, valor_por_extenso


@pytest.mark.parametrize("valor,esperado", [
    ("1.00", "um real"),
    ("1.50", "um real e cinquenta centavos"),
    ("100.00", "cem reais"),
    ("1000.00", "mil reais"),
    ("1234.56", "mil duzentos e trinta e quatro reais e cinquenta e seis centavos"),
    ("1000000.00", "um milhao de reais"),
    ("1500000.75", "um milhao e quinhentos mil reais e setenta e cinco centavos"),
])
def test_valor_por_extenso(valor, esperado):
    resultado = valor_por_extenso(Decimal(valor))
    # comparacao sem acento para o teste nao depender de encoding do arquivo
    assert _sem_acento(resultado) == esperado


def test_extenso_nao_tem_virgula():
    """Documento juridico escreve 'mil duzentos', nao 'mil, duzentos'."""
    assert "," not in valor_por_extenso(Decimal("1234.56"))


def test_valor_por_extenso_recusa_float():
    """Dinheiro em float perde centavo em silencio."""
    with pytest.raises(TypeError):
        valor_por_extenso(1234.56)


def test_valor_por_extenso_recusa_negativo():
    with pytest.raises(ValueError):
        valor_por_extenso(Decimal("-1.00"))


@pytest.mark.parametrize("valor,esperado", [
    ("1.00", "1,00"),
    ("1234.56", "1.234,56"),
    ("1000000.00", "1.000.000,00"),
    ("1500000.75", "1.500.000,75"),
])
def test_formatar_reais(valor, esperado):
    assert formatar_reais(Decimal(valor)) == esperado


def _sem_acento(texto):
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_extenso.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'aportes.extenso'`

- [ ] **Step 3: Implementar**

`src/aportes/extenso.py`:

```python
"""Valor monetario por extenso e formatado, para o Boletim de Subscricao."""

from decimal import Decimal

from num2words import num2words


def valor_por_extenso(valor: Decimal) -> str:
    """'mil duzentos e trinta e quatro reais e cinquenta e seis centavos'."""
    _validar(valor)
    bruto = num2words(valor, lang="pt_BR", to="currency")
    return bruto.replace(",", "")


def formatar_reais(valor: Decimal) -> str:
    """'1.234,56' — sem o prefixo R$, que ja esta na minuta."""
    _validar(valor)
    inteiro, centavos = f"{valor:.2f}".split(".")
    with_dots = f"{int(inteiro):,}".replace(",", ".")
    return f"{with_dots},{centavos}"


def _validar(valor: Decimal) -> None:
    if not isinstance(valor, Decimal):
        raise TypeError(
            f"valor monetario precisa ser Decimal, veio {type(valor).__name__}. "
            "float perde centavo em silencio."
        )
    if valor < 0:
        raise ValueError(f"valor monetario nao pode ser negativo: {valor}")
```

- [ ] **Step 4: Rodar e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_extenso.py -v`
Expected: PASS, 13 testes.

- [ ] **Step 5: Commit**

```bash
git add src/aportes/extenso.py tests/test_extenso.py
git commit -m "feat: valor por extenso e formatacao em reais"
```

---

### Task 3: Categorias CVM e hierarquia de qualificação

**Files:**
- Create: `src/aportes/qualificacao.py`
- Test: `tests/test_qualificacao.py`

**Interfaces:**
- Consumes: nada.
- Produces: `Categoria` (Enum com `GERAL`, `QUALIFICADO`, `PROFISSIONAL`), `atende(categoria_do_cotista, exigida) -> bool`, `mais_restritiva(a, b) -> Categoria`.

Profissional cobre o que exige Qualificado, que cobre o que exige Geral. O
contrário não. Quando classe e oferta exigem categorias diferentes, vale a mais
restritiva.

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_qualificacao.py`:

```python
import pytest

from aportes.qualificacao import Categoria, atende, mais_restritiva

GERAL = Categoria.GERAL
QUALIF = Categoria.QUALIFICADO
PROF = Categoria.PROFISSIONAL


@pytest.mark.parametrize("cotista,exigida,esperado", [
    (PROF, PROF, True),
    (PROF, QUALIF, True),
    (PROF, GERAL, True),
    (QUALIF, QUALIF, True),
    (QUALIF, GERAL, True),
    (QUALIF, PROF, False),
    (GERAL, GERAL, True),
    (GERAL, QUALIF, False),
    (GERAL, PROF, False),
])
def test_atende(cotista, exigida, esperado):
    assert atende(cotista, exigida) is esperado


@pytest.mark.parametrize("a,b,esperado", [
    (GERAL, PROF, PROF),
    (PROF, GERAL, PROF),
    (QUALIF, QUALIF, QUALIF),
    (GERAL, QUALIF, QUALIF),
])
def test_mais_restritiva(a, b, esperado):
    assert mais_restritiva(a, b) is esperado


def test_mais_restritiva_aceita_none():
    """A oferta pode nao exigir nada alem do que a classe ja exige."""
    assert mais_restritiva(QUALIF, None) is QUALIF
    assert mais_restritiva(None, QUALIF) is QUALIF


def test_categoria_vem_de_texto():
    assert Categoria("qualificado") is QUALIF


def test_categoria_desconhecida_falha_alto():
    with pytest.raises(ValueError):
        Categoria("semi-profissional")
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_qualificacao.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`src/aportes/qualificacao.py`:

```python
"""Categorias de investidor da CVM e a hierarquia entre elas."""

from enum import Enum


class Categoria(Enum):
    GERAL = "geral"
    QUALIFICADO = "qualificado"
    PROFISSIONAL = "profissional"


_ORDEM = {Categoria.GERAL: 0, Categoria.QUALIFICADO: 1, Categoria.PROFISSIONAL: 2}


def atende(categoria_do_cotista: Categoria, exigida: Categoria) -> bool:
    """Profissional cobre Qualificado, que cobre Geral. O contrario nao."""
    return _ORDEM[categoria_do_cotista] >= _ORDEM[exigida]


def mais_restritiva(a: Categoria | None, b: Categoria | None) -> Categoria | None:
    """A exigencia que vale quando classe e oferta pedem coisas diferentes."""
    if a is None:
        return b
    if b is None:
        return a
    return a if _ORDEM[a] >= _ORDEM[b] else b
```

- [ ] **Step 4: Rodar e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_qualificacao.py -v`
Expected: PASS, 17 testes.

- [ ] **Step 5: Commit**

```bash
git add src/aportes/qualificacao.py tests/test_qualificacao.py
git commit -m "feat: categorias CVM e hierarquia de qualificacao"
```

---

### Task 4: Os tipos do domínio

**Files:**
- Create: `src/aportes/dominio.py`
- Test: `tests/test_dominio.py`

**Interfaces:**
- Consumes: `Categoria` de `aportes.qualificacao`.
- Produces: `Procedencia`, `TipoPessoa`, `Condominio`, `Cotista`, `Classe`, `Oferta`, `Boleta`, `Base`, `Situacao`, `Veredito`. Todo o resto do sistema fala nestes tipos.

Todos imutáveis (`frozen=True`): um fato lido da base não deve ser alterado por
engano no meio de uma avaliação.

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_dominio.py`:

```python
from datetime import date
from decimal import Decimal

import pytest

from aportes.dominio import (
    Base, Boleta, Classe, Condominio, Cotista, Oferta,
    Procedencia, Situacao, TipoPessoa, Veredito,
)
from aportes.qualificacao import Categoria

PROC = Procedencia(fonte="ficha_pdf", em=date(2026, 3, 12))


def test_cotista_e_imutavel():
    c = Cotista(
        documento="11111111111", nome="Fulano de Tal", tipo=TipoPessoa.PF,
        categoria=Categoria.QUALIFICADO, categoria_procedencia=PROC,
        cadastro={}, cadastro_procedencia=None,
    )
    with pytest.raises(Exception):
        c.nome = "Outro"


def test_documento_guarda_so_digitos():
    c = Cotista(
        documento="111.111.111-11", nome="Fulano", tipo=TipoPessoa.PF,
        categoria=None, categoria_procedencia=None,
        cadastro={}, cadastro_procedencia=None,
    )
    assert c.documento == "11111111111"


def test_boleta_recusa_valor_float():
    with pytest.raises(TypeError):
        Boleta(id="B1", documento_cotista="11111111111", classe_id="F1/A",
               oferta_id="OF1", valor=1000.0, data=date(2026, 9, 7))


def test_base_encontra_posicao_do_cotista_na_classe():
    base = Base(
        cotistas={}, classes={}, ofertas={},
        posicoes=frozenset({("11111111111", "F1/A")}),
    )
    assert base.tem_posicao("11111111111", "F1/A") is True
    assert base.tem_posicao("11111111111", "F1/B") is False


def test_veredito_carrega_motivo():
    v = Veredito(
        situacao=Situacao.FALTOU_DADO,
        motivo="condominio da classe F1/A desconhecido",
        documentos=(), pendencias=("confira o regulamento no Slack do fundo",),
    )
    assert v.situacao is Situacao.FALTOU_DADO
    assert "F1/A" in v.motivo


def test_classe_e_oferta_montam_sem_erro():
    classe = Classe(
        id="F1/A", fundo_nome="Fundo Exemplo FIDC", fundo_cnpj="11111111000111",
        nome="Classe A", condominio=Condominio.FECHADO,
        qualificacao_exigida=Categoria.PROFISSIONAL, procedencia=PROC,
    )
    oferta = Oferta(
        id="OF1", classe_id="F1/A", publica=True,
        qualificacao_exigida=None, valor_minimo=Decimal("1000.00"),
        vigencia_ate=date(2026, 12, 31),
    )
    assert oferta.classe_id == classe.id
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_dominio.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`src/aportes/dominio.py`:

```python
"""Os tipos que todo o resto do sistema usa para falar de aportes."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum

from aportes.qualificacao import Categoria


class TipoPessoa(Enum):
    PF = "pf"
    PJ = "pj"
    FUNDO = "fundo"


class Condominio(Enum):
    ABERTO = "aberto"
    FECHADO = "fechado"


class Situacao(Enum):
    LIBERADA = "liberada"
    NAO_ELEGIVEL = "nao_elegivel"
    PRECISA_DE_VOCE = "precisa_de_voce"
    FALTOU_DADO = "faltou_dado"


@dataclass(frozen=True)
class Procedencia:
    """De onde o fato veio e quando. Acompanha todo veredito."""
    fonte: str
    em: date

    def __str__(self) -> str:
        return f"{self.fonte} de {self.em.strftime('%d/%m/%Y')}"


@dataclass(frozen=True)
class Cotista:
    documento: str
    nome: str
    tipo: TipoPessoa
    categoria: Categoria | None
    categoria_procedencia: Procedencia | None
    cadastro: dict[str, str] = field(default_factory=dict)
    cadastro_procedencia: Procedencia | None = None

    def __post_init__(self) -> None:
        so_digitos = "".join(c for c in self.documento if c.isdigit())
        object.__setattr__(self, "documento", so_digitos)


@dataclass(frozen=True)
class Classe:
    """Uma classe de um fundo. O id e a chave usada em toda parte."""
    id: str
    fundo_nome: str
    fundo_cnpj: str
    nome: str
    condominio: Condominio
    qualificacao_exigida: Categoria
    procedencia: Procedencia


@dataclass(frozen=True)
class Oferta:
    id: str
    classe_id: str
    publica: bool
    qualificacao_exigida: Categoria | None = None
    valor_minimo: Decimal | None = None
    vigencia_ate: date | None = None


@dataclass(frozen=True)
class Boleta:
    id: str
    documento_cotista: str
    classe_id: str
    oferta_id: str | None
    valor: Decimal
    data: date

    def __post_init__(self) -> None:
        if not isinstance(self.valor, Decimal):
            raise TypeError(
                f"valor da boleta precisa ser Decimal, veio "
                f"{type(self.valor).__name__}"
            )
        so_digitos = "".join(c for c in self.documento_cotista if c.isdigit())
        object.__setattr__(self, "documento_cotista", so_digitos)


@dataclass(frozen=True)
class Base:
    """Os fatos conhecidos, ja carregados. O motor nao le disco."""
    cotistas: dict[str, Cotista]
    classes: dict[str, Classe]
    ofertas: dict[str, Oferta]
    posicoes: frozenset[tuple[str, str]]

    def tem_posicao(self, documento: str, classe_id: str) -> bool:
        return (documento, classe_id) in self.posicoes


@dataclass(frozen=True)
class Veredito:
    situacao: Situacao
    motivo: str
    documentos: tuple[str, ...] = ()
    pendencias: tuple[str, ...] = ()
```

- [ ] **Step 4: Rodar e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_dominio.py -v`
Expected: PASS, 6 testes.

- [ ] **Step 5: Commit**

```bash
git add src/aportes/dominio.py tests/test_dominio.py
git commit -m "feat: tipos do dominio de aportes"
```

---

### Task 5: Motor de regras — cotista conhecido e condomínio

**Files:**
- Create: `src/aportes/regras.py`, `tests/conftest.py`
- Test: `tests/test_regras_cadastro.py`

**Interfaces:**
- Consumes: tudo de `aportes.dominio` e `aportes.qualificacao`.
- Produces: `avaliar(boleta: Boleta, base: Base) -> Veredito`.

As regras 1 e 2 da spec. Uma resposta **desconhecida** interrompe a boleta e
vira pendência; uma resposta conhecida, mesmo negativa, não interrompe — só
muda o que sai no fim.

Condomínio aberto **não** interrompe: o Termo de Adesão ainda pode sair.

- [ ] **Step 1: Escrever o conftest com os fatos de teste**

`tests/conftest.py`:

```python
"""Fatos ficticios reutilizados pelos testes do motor de regras.

Nenhum dado real. Documentos sao sequencias obviamente inventadas.
"""

from datetime import date
from decimal import Decimal

import pytest

from aportes.dominio import (
    Base, Boleta, Classe, Condominio, Cotista, Oferta, Procedencia, TipoPessoa,
)
from aportes.qualificacao import Categoria

PROC = Procedencia(fonte="regulamento", em=date(2026, 1, 15))
PROC_FICHA = Procedencia(fonte="ficha_pdf", em=date(2026, 3, 12))

DOC_COTISTA = "11111111111"


def faz_cotista(documento=DOC_COTISTA, categoria=Categoria.PROFISSIONAL,
                tipo=TipoPessoa.PF, cadastro=None):
    return Cotista(
        documento=documento, nome="Fulano de Tal", tipo=tipo,
        categoria=categoria,
        categoria_procedencia=PROC_FICHA if categoria else None,
        cadastro=cadastro or {}, cadastro_procedencia=PROC_FICHA,
    )


def faz_classe(id="F1/A", condominio=Condominio.FECHADO,
               exigida=Categoria.QUALIFICADO):
    return Classe(
        id=id, fundo_nome="Fundo Exemplo FIDC", fundo_cnpj="11111111000111",
        nome="Classe A", condominio=condominio,
        qualificacao_exigida=exigida, procedencia=PROC,
    )


def faz_oferta(id="OF1", classe_id="F1/A", publica=True, exigida=None):
    return Oferta(id=id, classe_id=classe_id, publica=publica,
                  qualificacao_exigida=exigida)


def faz_boleta(documento=DOC_COTISTA, classe_id="F1/A", oferta_id="OF1",
               valor="10000.00"):
    return Boleta(id="B1", documento_cotista=documento, classe_id=classe_id,
                  oferta_id=oferta_id, valor=Decimal(valor),
                  data=date(2026, 9, 7))


@pytest.fixture
def base_completa():
    """Base que conhece tudo: cotista Profissional, classe fechada, oferta publica."""
    return Base(
        cotistas={DOC_COTISTA: faz_cotista()},
        classes={"F1/A": faz_classe()},
        ofertas={"OF1": faz_oferta()},
        posicoes=frozenset(),
    )
```

- [ ] **Step 2: Escrever os testes que falham**

`tests/test_regras_cadastro.py`:

```python
from dataclasses import replace

from aportes.dominio import Base, Condominio, Situacao
from aportes.regras import avaliar
from tests.conftest import DOC_COTISTA, faz_boleta, faz_classe


def test_cotista_desconhecido_vira_pendencia(base_completa):
    base = replace(base_completa, cotistas={})
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.FALTOU_DADO
    assert "cotista" in v.motivo.lower()
    assert any("ficha" in p.lower() for p in v.pendencias)
    assert v.documentos == ()


def test_classe_desconhecida_vira_pendencia(base_completa):
    base = replace(base_completa, classes={})
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.FALTOU_DADO
    assert "F1/A" in v.motivo
    assert any("regulamento" in p.lower() for p in v.pendencias)


def test_condominio_aberto_nao_gera_boletim_mas_nao_interrompe(base_completa):
    """Aberto e resposta conhecida: tira o BS, deixa o TA seguir."""
    base = replace(
        base_completa,
        classes={"F1/A": faz_classe(condominio=Condominio.ABERTO)},
    )
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.LIBERADA
    assert "boletim_subscricao" not in v.documentos
    assert "termo_adesao" in v.documentos


def test_condominio_fechado_gera_boletim(base_completa):
    v = avaliar(faz_boleta(), base_completa)
    assert v.situacao is Situacao.LIBERADA
    assert "boletim_subscricao" in v.documentos


def test_ausencia_de_informacao_nunca_libera(base_completa):
    """A regra que sustenta o desenho inteiro."""
    for campo in ("cotistas", "classes"):
        base = replace(base_completa, **{campo: {}})
        assert avaliar(faz_boleta(), base).situacao is not Situacao.LIBERADA
```

- [ ] **Step 3: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_regras_cadastro.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'aportes.regras'`

- [ ] **Step 4: Implementar**

`src/aportes/regras.py`:

```python
"""O motor de regras.

Puro: recebe uma boleta e os fatos conhecidos, devolve um veredito.
Nao le disco, nao gera documento, nao aprova nada.
"""

from aportes.dominio import Base, Boleta, Condominio, Situacao, Veredito

BOLETIM = "boletim_subscricao"
TERMO_ADESAO = "termo_adesao"


def avaliar(boleta: Boleta, base: Base) -> Veredito:
    cotista = base.cotistas.get(boleta.documento_cotista)
    if cotista is None:
        return Veredito(
            situacao=Situacao.FALTOU_DADO,
            motivo=f"cotista {boleta.documento_cotista} nao esta na base",
            pendencias=("baixe a ficha cadastral do cotista no Portal ID",),
        )

    classe = base.classes.get(boleta.classe_id)
    if classe is None:
        return Veredito(
            situacao=Situacao.FALTOU_DADO,
            motivo=f"classe {boleta.classe_id} desconhecida",
            pendencias=(
                f"confira o regulamento no Slack e registre a classe "
                f"{boleta.classe_id} em regras/fundos.yaml",
            ),
        )

    documentos: list[str] = [TERMO_ADESAO]
    if classe.condominio is Condominio.FECHADO:
        documentos.insert(0, BOLETIM)

    return Veredito(
        situacao=Situacao.LIBERADA,
        motivo=f"classe {classe.id} e condominio {classe.condominio.value}",
        documentos=tuple(documentos),
    )
```

Nesta task o Termo de Adesão sai sempre; a Task 6 introduz a condição de
primeiro aporte.

- [ ] **Step 5: Rodar e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_regras_cadastro.py -v`
Expected: PASS, 5 testes.

- [ ] **Step 6: Commit**

```bash
git add src/aportes/regras.py tests/conftest.py tests/test_regras_cadastro.py
git commit -m "feat: motor de regras - cotista conhecido e condominio"
```

---

### Task 6: Motor de regras — primeiro aporte na classe

**Files:**
- Modify: `src/aportes/regras.py`
- Test: `tests/test_regras_primeiro_aporte.py`

**Interfaces:**
- Consumes: `avaliar` da Task 5, `Base.tem_posicao`.
- Produces: nenhuma assinatura nova.

O Termo de Adesão sai no primeiro aporte do cotista **na classe** — não no
fundo. Quem já está no fundo mas entra numa classe nova assina de novo. E o TA
independe do condomínio.

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_regras_primeiro_aporte.py`:

```python
from dataclasses import replace

from aportes.dominio import Condominio, Situacao
from aportes.regras import BOLETIM, TERMO_ADESAO, avaliar
from tests.conftest import DOC_COTISTA, faz_boleta, faz_classe


def test_sem_posicao_na_classe_gera_termo_de_adesao(base_completa):
    v = avaliar(faz_boleta(), base_completa)
    assert TERMO_ADESAO in v.documentos


def test_com_posicao_na_classe_nao_gera_termo_de_adesao(base_completa):
    base = replace(
        base_completa, posicoes=frozenset({(DOC_COTISTA, "F1/A")}),
    )
    v = avaliar(faz_boleta(), base)
    assert TERMO_ADESAO not in v.documentos
    assert BOLETIM in v.documentos


def test_posicao_em_outra_classe_do_mesmo_fundo_ainda_gera_termo(base_completa):
    """A chave e cotista + CLASSE, nao cotista + fundo."""
    base = replace(
        base_completa,
        classes={"F1/A": faz_classe(id="F1/A"), "F1/B": faz_classe(id="F1/B")},
        posicoes=frozenset({(DOC_COTISTA, "F1/A")}),
    )
    v = avaliar(faz_boleta(classe_id="F1/B"), base)
    assert TERMO_ADESAO in v.documentos


def test_termo_de_adesao_independe_do_condominio(base_completa):
    base = replace(
        base_completa,
        classes={"F1/A": faz_classe(condominio=Condominio.ABERTO)},
    )
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.LIBERADA
    assert v.documentos == (TERMO_ADESAO,)
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_regras_primeiro_aporte.py -v`
Expected: FAIL em `test_com_posicao_na_classe_nao_gera_termo_de_adesao` — o TA
está saindo sempre.

- [ ] **Step 3: Implementar**

Em `src/aportes/regras.py`, substituir o bloco que monta `documentos` por:

```python
    documentos: list[str] = []
    if classe.condominio is Condominio.FECHADO:
        documentos.append(BOLETIM)

    primeiro_aporte = not base.tem_posicao(boleta.documento_cotista, classe.id)
    if primeiro_aporte:
        documentos.append(TERMO_ADESAO)

    motivo = (
        f"classe {classe.id}, condominio {classe.condominio.value}, "
        f"{'primeiro aporte na classe' if primeiro_aporte else 'aporte subsequente'}"
    )

    return Veredito(
        situacao=Situacao.LIBERADA,
        motivo=motivo,
        documentos=tuple(documentos),
    )
```

- [ ] **Step 4: Rodar a suíte inteira**

Run: `.venv/Scripts/python.exe -m pytest -v`
Expected: PASS. Os testes da Task 5 continuam válidos porque lá a base não tem
posição — todos são primeiro aporte.

- [ ] **Step 5: Commit**

```bash
git add src/aportes/regras.py tests/test_regras_primeiro_aporte.py
git commit -m "feat: termo de adesao no primeiro aporte da classe"
```

---

### Task 7: Motor de regras — qualificação e oferta privada

**Files:**
- Modify: `src/aportes/regras.py`
- Test: `tests/test_regras_elegibilidade.py`

**Interfaces:**
- Consumes: `atende` e `mais_restritiva` de `aportes.qualificacao`.
- Produces: nenhuma assinatura nova.

As regras 4 e 5. Oferta privada para sempre e **não gera documento nenhum**: a
verificação de vínculo societário ou familiar é julgamento humano.

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_regras_elegibilidade.py`:

```python
from dataclasses import replace

from aportes.dominio import Situacao
from aportes.qualificacao import Categoria
from aportes.regras import avaliar
from tests.conftest import DOC_COTISTA, faz_boleta, faz_classe, faz_cotista, faz_oferta


def test_qualificacao_suficiente_libera(base_completa):
    v = avaliar(faz_boleta(), base_completa)
    assert v.situacao is Situacao.LIBERADA


def test_qualificacao_insuficiente_reprova(base_completa):
    base = replace(
        base_completa,
        cotistas={DOC_COTISTA: faz_cotista(categoria=Categoria.GERAL)},
        classes={"F1/A": faz_classe(exigida=Categoria.PROFISSIONAL)},
    )
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.NAO_ELEGIVEL
    assert "profissional" in v.motivo.lower()
    assert "geral" in v.motivo.lower()
    assert v.documentos == ()


def test_motivo_da_reprovacao_cita_a_procedencia(base_completa):
    """'Segundo a ficha de 12/03/2026' — para dar como discordar."""
    base = replace(
        base_completa,
        cotistas={DOC_COTISTA: faz_cotista(categoria=Categoria.GERAL)},
        classes={"F1/A": faz_classe(exigida=Categoria.PROFISSIONAL)},
    )
    v = avaliar(faz_boleta(), base)
    assert "12/03/2026" in v.motivo


def test_categoria_do_cotista_desconhecida_vira_pendencia(base_completa):
    base = replace(
        base_completa,
        cotistas={DOC_COTISTA: faz_cotista(categoria=None)},
    )
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.FALTOU_DADO
    assert any("ficha" in p.lower() for p in v.pendencias)


def test_oferta_exige_mais_que_a_classe(base_completa):
    """Vale a mais restritiva das duas."""
    base = replace(
        base_completa,
        cotistas={DOC_COTISTA: faz_cotista(categoria=Categoria.QUALIFICADO)},
        classes={"F1/A": faz_classe(exigida=Categoria.QUALIFICADO)},
        ofertas={"OF1": faz_oferta(exigida=Categoria.PROFISSIONAL)},
    )
    assert avaliar(faz_boleta(), base).situacao is Situacao.NAO_ELEGIVEL


def test_oferta_desconhecida_vira_pendencia(base_completa):
    base = replace(base_completa, ofertas={})
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.FALTOU_DADO
    assert any("oferta" in p.lower() for p in v.pendencias)


def test_oferta_privada_para_e_nao_gera_documento(base_completa):
    base = replace(base_completa, ofertas={"OF1": faz_oferta(publica=False)})
    v = avaliar(faz_boleta(), base)
    assert v.situacao is Situacao.PRECISA_DE_VOCE
    assert "vinculo" in v.motivo.lower()
    assert v.documentos == ()


def test_oferta_privada_para_mesmo_com_tudo_em_ordem(base_completa):
    """Nem qualificacao perfeita libera oferta privada automaticamente."""
    base = replace(
        base_completa,
        cotistas={DOC_COTISTA: faz_cotista(categoria=Categoria.PROFISSIONAL)},
        ofertas={"OF1": faz_oferta(publica=False)},
    )
    assert avaliar(faz_boleta(), base).situacao is Situacao.PRECISA_DE_VOCE
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_regras_elegibilidade.py -v`
Expected: FAIL — o motor ainda não olha qualificação nem oferta.

- [ ] **Step 3: Implementar**

Em `src/aportes/regras.py`, inserir depois do bloco da classe e **antes** do
bloco que monta `documentos`:

```python
    oferta = base.ofertas.get(boleta.oferta_id) if boleta.oferta_id else None
    if oferta is None:
        return Veredito(
            situacao=Situacao.FALTOU_DADO,
            motivo=f"oferta {boleta.oferta_id} desconhecida",
            pendencias=(
                f"registre a oferta {boleta.oferta_id} em regras/ofertas.yaml, "
                "a partir do suplemento assinado",
            ),
        )

    if cotista.categoria is None:
        return Veredito(
            situacao=Situacao.FALTOU_DADO,
            motivo=f"categoria CVM de {cotista.nome} desconhecida",
            pendencias=(
                f"baixe a ficha cadastral de {cotista.nome} no Portal ID "
                "para registrar a categoria",
            ),
        )

    exigida = mais_restritiva(
        classe.qualificacao_exigida, oferta.qualificacao_exigida
    )
    if not atende(cotista.categoria, exigida):
        return Veredito(
            situacao=Situacao.NAO_ELEGIVEL,
            motivo=(
                f"exige {exigida.value}; {cotista.nome} consta como "
                f"{cotista.categoria.value}, segundo "
                f"{cotista.categoria_procedencia}"
            ),
        )

    if not oferta.publica:
        return Veredito(
            situacao=Situacao.PRECISA_DE_VOCE,
            motivo=(
                f"oferta {oferta.id} e privada: exige verificacao de vinculo "
                "societario ou familiar com os demais cotistas"
            ),
            pendencias=(
                "confirme o vinculo e mande gerar os documentos manualmente",
            ),
        )
```

Ajustar o import no topo:

```python
from aportes.qualificacao import atende, mais_restritiva
```

- [ ] **Step 4: Rodar a suíte inteira**

Run: `.venv/Scripts/python.exe -m pytest -v`
Expected: PASS. Se algum teste da Task 5 ou 6 quebrar por falta de oferta na
base, é sinal de que a `base_completa` do conftest precisa da oferta — ela já
tem.

- [ ] **Step 5: Commit**

```bash
git add src/aportes/regras.py tests/test_regras_elegibilidade.py
git commit -m "feat: elegibilidade por qualificacao e trava de oferta privada"
```

---

### Task 8: Persistência das regras (fundos e ofertas em YAML)

**Files:**
- Create: `src/aportes/base/__init__.py`, `src/aportes/base/fundos.py`, `src/aportes/base/ofertas.py`
- Create: `regras/fundos.yaml`, `regras/ofertas.yaml` (com um exemplo fictício comentado)
- Test: `tests/test_base_regras.py`

**Interfaces:**
- Consumes: `Classe`, `Oferta`, `Condominio`, `Procedencia`, `Categoria`.
- Produces: `carregar_classes(caminho: Path) -> dict[str, Classe]` e `carregar_ofertas(caminho: Path) -> dict[str, Oferta]`.

Estes arquivos são editados à mão pelo Gabriel. Por isso o leitor precisa
**falhar alto e em português** quando o YAML estiver errado — um campo faltando
não pode virar valor-padrão silencioso.

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_base_regras.py`:

```python
import pytest

from aportes.base.fundos import carregar_classes
from aportes.base.ofertas import carregar_ofertas
from aportes.dominio import Condominio
from aportes.qualificacao import Categoria

YAML_CLASSES = """
- id: F1/A
  fundo_nome: Fundo Exemplo FIDC
  fundo_cnpj: "11.111.111/0001-11"
  nome: Classe A
  condominio: fechado
  qualificacao_exigida: profissional
  fonte: regulamento
  lido_em: 2026-01-15
"""

YAML_OFERTAS = """
- id: OF1
  classe_id: F1/A
  publica: true
  valor_minimo: "1000.00"
  vigencia_ate: 2026-12-31
"""


def _escreve(tmp_path, nome, conteudo):
    caminho = tmp_path / nome
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


def test_carrega_classe(tmp_path):
    classes = carregar_classes(_escreve(tmp_path, "f.yaml", YAML_CLASSES))
    classe = classes["F1/A"]
    assert classe.condominio is Condominio.FECHADO
    assert classe.qualificacao_exigida is Categoria.PROFISSIONAL
    assert classe.fundo_cnpj == "11111111000111"
    assert classe.procedencia.fonte == "regulamento"


def test_arquivo_vazio_devolve_base_vazia(tmp_path):
    assert carregar_classes(_escreve(tmp_path, "f.yaml", "")) == {}


def test_campo_faltando_falha_alto(tmp_path):
    ruim = YAML_CLASSES.replace("  condominio: fechado\n", "")
    with pytest.raises(ValueError) as erro:
        carregar_classes(_escreve(tmp_path, "f.yaml", ruim))
    assert "condominio" in str(erro.value)
    assert "F1/A" in str(erro.value)


def test_condominio_invalido_falha_alto(tmp_path):
    ruim = YAML_CLASSES.replace("fechado", "semiaberto")
    with pytest.raises(ValueError) as erro:
        carregar_classes(_escreve(tmp_path, "f.yaml", ruim))
    assert "semiaberto" in str(erro.value)


def test_id_duplicado_falha_alto(tmp_path):
    with pytest.raises(ValueError) as erro:
        carregar_classes(_escreve(tmp_path, "f.yaml", YAML_CLASSES + YAML_CLASSES))
    assert "F1/A" in str(erro.value)


def test_carrega_oferta(tmp_path):
    from decimal import Decimal
    ofertas = carregar_ofertas(_escreve(tmp_path, "o.yaml", YAML_OFERTAS))
    oferta = ofertas["OF1"]
    assert oferta.publica is True
    assert oferta.qualificacao_exigida is None
    assert oferta.valor_minimo == Decimal("1000.00")


def test_oferta_sem_publica_falha_alto(tmp_path):
    """'Publica ou privada' nunca pode ter valor-padrao."""
    ruim = YAML_OFERTAS.replace("  publica: true\n", "")
    with pytest.raises(ValueError) as erro:
        carregar_ofertas(_escreve(tmp_path, "o.yaml", ruim))
    assert "publica" in str(erro.value)
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_base_regras.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`src/aportes/base/__init__.py` — vazio.

`src/aportes/base/fundos.py`:

```python
"""Le regras/fundos.yaml, editado a mao pelo Gabriel.

Falha alto e em portugues: campo faltando nunca vira valor-padrao.
"""

from pathlib import Path

import yaml

from aportes.dominio import Classe, Condominio, Procedencia
from aportes.qualificacao import Categoria


def carregar_classes(caminho: Path) -> dict[str, Classe]:
    itens = yaml.safe_load(caminho.read_text(encoding="utf-8")) or []
    classes: dict[str, Classe] = {}
    for item in itens:
        id_ = _exigir(item, "id", contexto="(sem id)")
        if id_ in classes:
            raise ValueError(f"classe {id_} aparece duas vezes em {caminho}")
        classes[id_] = Classe(
            id=id_,
            fundo_nome=_exigir(item, "fundo_nome", id_),
            fundo_cnpj=_so_digitos(_exigir(item, "fundo_cnpj", id_)),
            nome=_exigir(item, "nome", id_),
            condominio=_enum(Condominio, _exigir(item, "condominio", id_),
                             "condominio", id_),
            qualificacao_exigida=_enum(
                Categoria, _exigir(item, "qualificacao_exigida", id_),
                "qualificacao_exigida", id_,
            ),
            procedencia=Procedencia(
                fonte=_exigir(item, "fonte", id_),
                em=_exigir(item, "lido_em", id_),
            ),
        )
    return classes


def _exigir(item: dict, campo: str, contexto: str = ""):
    if campo not in item or item[campo] is None:
        raise ValueError(
            f"falta o campo '{campo}' na classe {contexto}. "
            "Nenhum campo tem valor-padrao: informacao ausente e pendencia."
        )
    return item[campo]


def _enum(tipo, valor, campo: str, contexto: str):
    try:
        return tipo(str(valor).strip().lower())
    except ValueError:
        validos = ", ".join(m.value for m in tipo)
        raise ValueError(
            f"'{valor}' nao e um valor valido para '{campo}' na classe "
            f"{contexto}. Validos: {validos}"
        ) from None


def _so_digitos(texto: str) -> str:
    return "".join(c for c in str(texto) if c.isdigit())
```

`src/aportes/base/ofertas.py`:

```python
"""Le regras/ofertas.yaml, editado a mao pelo Gabriel."""

from decimal import Decimal
from pathlib import Path

import yaml

from aportes.base.fundos import _enum, _exigir
from aportes.dominio import Oferta
from aportes.qualificacao import Categoria


def carregar_ofertas(caminho: Path) -> dict[str, Oferta]:
    itens = yaml.safe_load(caminho.read_text(encoding="utf-8")) or []
    ofertas: dict[str, Oferta] = {}
    for item in itens:
        id_ = _exigir(item, "id", contexto="(sem id)")
        if id_ in ofertas:
            raise ValueError(f"oferta {id_} aparece duas vezes em {caminho}")
        exigida = item.get("qualificacao_exigida")
        minimo = item.get("valor_minimo")
        ofertas[id_] = Oferta(
            id=id_,
            classe_id=_exigir(item, "classe_id", id_),
            publica=bool(_exigir(item, "publica", id_)),
            qualificacao_exigida=(
                _enum(Categoria, exigida, "qualificacao_exigida", id_)
                if exigida is not None else None
            ),
            valor_minimo=Decimal(str(minimo)) if minimo is not None else None,
            vigencia_ate=item.get("vigencia_ate"),
        )
    return ofertas
```

- [ ] **Step 4: Criar os arquivos de regras com um exemplo comentado**

`regras/fundos.yaml`:

```yaml
# Uma entrada por CLASSE de fundo. Registre uma vez; nunca mais e perguntado.
# O 'fonte' e o 'lido_em' aparecem no veredito quando a regra reprova alguem.
#
# - id: F1/A                        # chave usada nas boletas
#   fundo_nome: Fundo Exemplo FIDC
#   fundo_cnpj: "11.111.111/0001-11"
#   nome: Classe A
#   condominio: fechado             # aberto | fechado
#   qualificacao_exigida: profissional   # geral | qualificado | profissional
#   fonte: regulamento
#   lido_em: 2026-01-15
```

`regras/ofertas.yaml`:

```yaml
# Uma entrada por OFERTA, a partir do suplemento assinado.
#
# - id: OF1
#   classe_id: F1/A
#   publica: true                   # false = privada: para sempre para conferencia
#   qualificacao_exigida: profissional   # opcional; so se for alem da classe
#   valor_minimo: "1000.00"         # opcional
#   vigencia_ate: 2026-12-31        # opcional
```

- [ ] **Step 5: Rodar e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_base_regras.py -v`
Expected: PASS, 7 testes.

- [ ] **Step 6: Commit**

```bash
git add src/aportes/base regras tests/test_base_regras.py
git commit -m "feat: leitura de regras/fundos.yaml e regras/ofertas.yaml"
```

---

### Task 9: Persistência dos cotistas, com procedência

**Files:**
- Create: `src/aportes/base/cotistas.py`
- Test: `tests/test_base_cotistas.py`

**Interfaces:**
- Consumes: `Cotista`, `TipoPessoa`, `Procedencia`, `Categoria`.
- Produces: `carregar_cotistas(caminho: Path) -> dict[str, Cotista]`, `salvar_cotistas(caminho: Path, cotistas: dict[str, Cotista]) -> None`, `mesclar(existente: Cotista | None, novo: Cotista) -> Cotista`.

Três fontes alimentam a mesma base e vão discordar. `mesclar` resolve pela
**data da procedência**: o bloco mais novo vence, bloco a bloco (cadastro e
qualificação separados). Arquivo em `dados/`, portanto **nunca no git**.

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_base_cotistas.py`:

```python
from datetime import date

from aportes.base.cotistas import carregar_cotistas, mesclar, salvar_cotistas
from aportes.dominio import Cotista, Procedencia, TipoPessoa
from aportes.qualificacao import Categoria

VELHO = Procedencia(fonte="excel_portal", em=date(2026, 1, 10))
NOVO = Procedencia(fonte="ficha_pdf", em=date(2026, 6, 20))


def _cotista(categoria, cat_proc, cadastro, cad_proc, nome="Fulano de Tal"):
    return Cotista(
        documento="11111111111", nome=nome, tipo=TipoPessoa.PF,
        categoria=categoria, categoria_procedencia=cat_proc,
        cadastro=cadastro, cadastro_procedencia=cad_proc,
    )


def test_ida_e_volta_pelo_disco(tmp_path):
    caminho = tmp_path / "cotistas.json"
    original = {
        "11111111111": _cotista(
            Categoria.QUALIFICADO, NOVO,
            {"email": "fulano@exemplo.invalido", "endereco": "Rua Ficticia, 1"},
            NOVO,
        )
    }
    salvar_cotistas(caminho, original)
    assert carregar_cotistas(caminho) == original


def test_arquivo_inexistente_devolve_base_vazia(tmp_path):
    assert carregar_cotistas(tmp_path / "nao_existe.json") == {}


def test_mesclar_prefere_o_bloco_mais_novo():
    existente = _cotista(Categoria.GERAL, VELHO, {"email": "antigo@exemplo.invalido"}, VELHO)
    novo = _cotista(Categoria.QUALIFICADO, NOVO, {"email": "novo@exemplo.invalido"}, NOVO)
    r = mesclar(existente, novo)
    assert r.categoria is Categoria.QUALIFICADO
    assert r.cadastro["email"] == "novo@exemplo.invalido"


def test_mesclar_mantem_o_bloco_mais_novo_que_ja_estava():
    """Reimportar um Excel antigo nao pode sobrescrever uma ficha recente."""
    existente = _cotista(Categoria.QUALIFICADO, NOVO, {"email": "novo@exemplo.invalido"}, NOVO)
    antigo = _cotista(Categoria.GERAL, VELHO, {"email": "antigo@exemplo.invalido"}, VELHO)
    r = mesclar(existente, antigo)
    assert r.categoria is Categoria.QUALIFICADO
    assert r.cadastro["email"] == "novo@exemplo.invalido"


def test_mesclar_combina_blocos_de_fontes_diferentes():
    """Excel traz a qualificacao; a ficha traz o cadastro."""
    do_excel = _cotista(Categoria.QUALIFICADO, VELHO, {}, None)
    da_ficha = _cotista(None, None, {"endereco": "Rua Ficticia, 1"}, NOVO)
    r = mesclar(do_excel, da_ficha)
    assert r.categoria is Categoria.QUALIFICADO
    assert r.cadastro["endereco"] == "Rua Ficticia, 1"


def test_mesclar_sem_existente_devolve_o_novo():
    novo = _cotista(Categoria.GERAL, VELHO, {}, VELHO)
    assert mesclar(None, novo) == novo
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_base_cotistas.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`src/aportes/base/cotistas.py`:

```python
"""dados/cotistas.json — a base de cotistas. NUNCA vai para o git.

Tres fontes alimentam este arquivo e vao discordar. A data da procedencia
resolve, bloco a bloco: qualificacao e cadastro tem historias separadas.
"""

import json
from datetime import date
from pathlib import Path

from aportes.dominio import Cotista, Procedencia, TipoPessoa
from aportes.qualificacao import Categoria


def carregar_cotistas(caminho: Path) -> dict[str, Cotista]:
    if not caminho.exists():
        return {}
    cru = json.loads(caminho.read_text(encoding="utf-8"))
    return {doc: _do_dicionario(doc, d) for doc, d in cru.items()}


def salvar_cotistas(caminho: Path, cotistas: dict[str, Cotista]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    cru = {doc: _para_dicionario(c) for doc, c in cotistas.items()}
    caminho.write_text(
        json.dumps(cru, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def mesclar(existente: Cotista | None, novo: Cotista) -> Cotista:
    """Bloco mais novo vence. Bloco ausente no novo preserva o que havia."""
    if existente is None:
        return novo

    cat, cat_proc = _mais_novo(
        (existente.categoria, existente.categoria_procedencia),
        (novo.categoria, novo.categoria_procedencia),
    )
    cad, cad_proc = _mais_novo(
        (existente.cadastro, existente.cadastro_procedencia),
        (novo.cadastro or None, novo.cadastro_procedencia),
    )
    return Cotista(
        documento=novo.documento,
        nome=novo.nome or existente.nome,
        tipo=novo.tipo or existente.tipo,
        categoria=cat, categoria_procedencia=cat_proc,
        cadastro=cad or {}, cadastro_procedencia=cad_proc,
    )


def _mais_novo(a, b):
    (valor_a, proc_a), (valor_b, proc_b) = a, b
    if valor_b is None or proc_b is None:
        return valor_a, proc_a
    if valor_a is None or proc_a is None:
        return valor_b, proc_b
    return (valor_b, proc_b) if proc_b.em >= proc_a.em else (valor_a, proc_a)


def _para_dicionario(c: Cotista) -> dict:
    return {
        "nome": c.nome,
        "tipo": c.tipo.value,
        "categoria": c.categoria.value if c.categoria else None,
        "categoria_procedencia": _proc_para(c.categoria_procedencia),
        "cadastro": c.cadastro,
        "cadastro_procedencia": _proc_para(c.cadastro_procedencia),
    }


def _do_dicionario(documento: str, d: dict) -> Cotista:
    return Cotista(
        documento=documento,
        nome=d["nome"],
        tipo=TipoPessoa(d["tipo"]),
        categoria=Categoria(d["categoria"]) if d.get("categoria") else None,
        categoria_procedencia=_proc_de(d.get("categoria_procedencia")),
        cadastro=d.get("cadastro") or {},
        cadastro_procedencia=_proc_de(d.get("cadastro_procedencia")),
    )


def _proc_para(p: Procedencia | None) -> dict | None:
    return {"fonte": p.fonte, "em": p.em.isoformat()} if p else None


def _proc_de(d: dict | None) -> Procedencia | None:
    return Procedencia(fonte=d["fonte"], em=date.fromisoformat(d["em"])) if d else None
```

- [ ] **Step 4: Rodar e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_base_cotistas.py -v`
Expected: PASS, 6 testes.

- [ ] **Step 5: Rodar o guardrail de LGPD**

Run: `.venv/Scripts/python.exe -m pytest tests/test_privacidade.py -v`
Expected: PASS — `dados/cotistas.json` não pode ter sido rastreado.

- [ ] **Step 6: Commit**

```bash
git add src/aportes/base/cotistas.py tests/test_base_cotistas.py
git commit -m "feat: base de cotistas com procedencia por bloco"
```

---

### Task 10: Memória das boletas já processadas

**Files:**
- Create: `src/aportes/base/boletas.py`
- Test: `tests/test_base_boletas.py`

**Interfaces:**
- Consumes: `Boleta`.
- Produces: `carregar_vistas(caminho: Path) -> set[str]`, `registrar(caminho: Path, boleta: Boleta, documentos: tuple[str, ...]) -> None`, `chave(boleta: Boleta) -> str`.

É o que faz colar o mesmo print duas vezes ser inofensivo. Se a exportação
trouxer número da boleta, ele é a chave; senão, a chave composta (cotista +
classe + valor + data) — que colapsa duas boletas idênticas no mesmo dia, e
por isso avisa.

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_base_boletas.py`:

```python
from datetime import date
from decimal import Decimal

from aportes.base.boletas import carregar_vistas, chave, registrar
from aportes.dominio import Boleta


def _boleta(id="B1", valor="10000.00"):
    return Boleta(id=id, documento_cotista="11111111111", classe_id="F1/A",
                  oferta_id="OF1", valor=Decimal(valor), data=date(2026, 9, 7))


def test_arquivo_inexistente_nao_tem_nada_visto(tmp_path):
    assert carregar_vistas(tmp_path / "b.json") == set()


def test_boleta_registrada_fica_vista(tmp_path):
    caminho = tmp_path / "b.json"
    b = _boleta()
    registrar(caminho, b, ("boletim_subscricao",))
    assert chave(b) in carregar_vistas(caminho)


def test_registrar_duas_vezes_e_inofensivo(tmp_path):
    caminho = tmp_path / "b.json"
    b = _boleta()
    registrar(caminho, b, ("boletim_subscricao",))
    registrar(caminho, b, ("boletim_subscricao",))
    assert len(carregar_vistas(caminho)) == 1


def test_chave_usa_o_id_quando_existe():
    assert chave(_boleta(id="B123")) == "B123"


def test_chave_composta_quando_nao_ha_id():
    b = _boleta(id="")
    k = chave(b)
    assert "11111111111" in k and "F1/A" in k and "10000.00" in k


def test_boletas_diferentes_tem_chaves_diferentes(tmp_path):
    assert chave(_boleta(id="", valor="10000.00")) != chave(_boleta(id="", valor="20000.00"))
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_base_boletas.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`src/aportes/base/boletas.py`:

```python
"""dados/boletas.json — o que ja foi processado. NUNCA vai para o git.

E a memoria que faz o print seguinte mostrar so o que e novo.
"""

import json
from pathlib import Path

from aportes.dominio import Boleta


def chave(boleta: Boleta) -> str:
    """O id da boleta quando existe; senao, chave composta.

    A composta colapsa duas boletas identicas no mesmo dia. Se a exportacao
    do Portal ID trouxer numero da boleta, use-o.
    """
    if boleta.id:
        return boleta.id
    return "|".join([
        boleta.documento_cotista, boleta.classe_id,
        f"{boleta.valor:.2f}", boleta.data.isoformat(),
    ])


def carregar_vistas(caminho: Path) -> set[str]:
    if not caminho.exists():
        return set()
    return set(json.loads(caminho.read_text(encoding="utf-8")).keys())


def registrar(caminho: Path, boleta: Boleta, documentos: tuple[str, ...]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    registro = (
        json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else {}
    )
    registro[chave(boleta)] = {
        "processada_em": boleta.data.isoformat(),
        "classe_id": boleta.classe_id,
        "documentos": list(documentos),
    }
    caminho.write_text(
        json.dumps(registro, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
```

- [ ] **Step 4: Rodar e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_base_boletas.py -v`
Expected: PASS, 6 testes.

- [ ] **Step 5: Commit**

```bash
git add src/aportes/base/boletas.py tests/test_base_boletas.py
git commit -m "feat: memoria das boletas ja processadas"
```

---

### Task 11: Validador de minuta .docx

**Files:**
- Create: `src/aportes/documentos/__init__.py`, `src/aportes/documentos/validador.py`
- Test: `tests/test_validador.py`

**Interfaces:**
- Consumes: nada do projeto.
- Produces: `tags_da_minuta(caminho: Path) -> set[str]`, `validar_minuta(caminho: Path) -> list[str]` (lista de problemas; vazia = tudo certo).

A defesa contra a autocorreção do Word. Os testes **constroem minutas
sintéticas com `python-docx`**, então esta task não depende das minutas reais.

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_validador.py`:

```python
from docx import Document

from aportes.documentos.validador import tags_da_minuta, validar_minuta


def _minuta(tmp_path, *paragrafos, nome="m.docx"):
    doc = Document()
    for p in paragrafos:
        doc.add_paragraph(p)
    caminho = tmp_path / nome
    doc.save(caminho)
    return caminho


def test_encontra_as_tags(tmp_path):
    c = _minuta(tmp_path, "Subscritor: {{ nome_subscritor }}", "CPF: {{ cpf_cnpj }}")
    assert tags_da_minuta(c) == {"nome_subscritor", "cpf_cnpj"}


def test_minuta_correta_nao_tem_problema(tmp_path):
    c = _minuta(tmp_path, "{% if pessoa_juridica %}Rep: {{ rep_nome }}{% endif %}")
    assert validar_minuta(c) == []


def test_denuncia_aspas_curvas(tmp_path):
    """A autocorrecao do Word troca as aspas e quebra a tag em silencio."""
    c = _minuta(tmp_path, "{% if pessoa_juridica == “sim” %}x{% endif %}")
    problemas = validar_minuta(c)
    assert any("curva" in p.lower() for p in problemas)


def test_denuncia_condicional_sem_fechamento(tmp_path):
    c = _minuta(tmp_path, "{% if pessoa_juridica %}Rep: {{ rep_nome }}")
    problemas = validar_minuta(c)
    assert any("endif" in p.lower() for p in problemas)


def test_denuncia_chave_desbalanceada(tmp_path):
    c = _minuta(tmp_path, "Subscritor: {{ nome_subscritor }")
    problemas = validar_minuta(c)
    assert any("chave" in p.lower() for p in problemas)


def test_le_tags_dentro_de_tabela(tmp_path):
    """O quadro de integralizacao do Boletim e uma tabela."""
    doc = Document()
    tabela = doc.add_table(rows=1, cols=1)
    tabela.cell(0, 0).text = "Preco de Subscricao: R$ {{ valor_reais }}"
    caminho = tmp_path / "t.docx"
    doc.save(caminho)
    assert "valor_reais" in tags_da_minuta(caminho)
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_validador.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`src/aportes/documentos/__init__.py` — vazio.

`src/aportes/documentos/validador.py`:

```python
"""Confere uma minuta .docx antes de ela ser usada num bloco.

Existe por causa da autocorrecao do Word, que quebra tags em silencio.
"""

import re
from pathlib import Path

from docx import Document

_TAG = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")
_ASPAS_CURVAS = "“”‘’"


def _texto_todo(caminho: Path) -> str:
    doc = Document(caminho)
    partes = [p.text for p in doc.paragraphs]
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                partes.append(celula.text)
    return "\n".join(partes)


def tags_da_minuta(caminho: Path) -> set[str]:
    return set(_TAG.findall(_texto_todo(caminho)))


def validar_minuta(caminho: Path) -> list[str]:
    texto = _texto_todo(caminho)
    problemas: list[str] = []

    curvas = [c for c in _ASPAS_CURVAS if c in texto]
    if curvas:
        problemas.append(
            f"aspa curva encontrada ({''.join(curvas)}): a autocorrecao do Word "
            "trocou a aspa reta e isso quebra a tag. Desative a autocorrecao "
            "de aspas e corrija."
        )

    if texto.count("{{") != texto.count("}}"):
        problemas.append(
            f"chave desbalanceada: {texto.count('{{')} aberturas '{{{{' para "
            f"{texto.count('}}')} fechamentos '}}}}'"
        )

    abre = len(re.findall(r"\{%\s*if\b", texto))
    fecha = len(re.findall(r"\{%\s*endif\s*%\}", texto))
    if abre != fecha:
        problemas.append(
            f"condicional sem fechamento: {abre} '{{% if %}}' para "
            f"{fecha} '{{% endif %}}'"
        )

    abre_for = len(re.findall(r"\{%\s*for\b", texto))
    fecha_for = len(re.findall(r"\{%\s*endfor\s*%\}", texto))
    if abre_for != fecha_for:
        problemas.append(
            f"repeticao sem fechamento: {abre_for} '{{% for %}}' para "
            f"{fecha_for} '{{% endfor %}}'"
        )

    return problemas
```

- [ ] **Step 4: Rodar e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_validador.py -v`
Expected: PASS, 6 testes.

- [ ] **Step 5: Commit**

```bash
git add src/aportes/documentos tests/test_validador.py
git commit -m "feat: validador de minuta docx"
```

---

### Task 12: Preenchimento da minuta

**Files:**
- Create: `src/aportes/documentos/preenchimento.py`
- Test: `tests/test_preenchimento.py`

**Interfaces:**
- Consumes: `tags_da_minuta` da Task 11.
- Produces: `preencher(minuta: Path, dados: dict[str, str], destino: Path) -> None` e a exceção `CampoFaltando`.

Campo do modelo sem dado correspondente **impede a geração**. Nunca sai
documento com buraco ou com placeholder.

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_preenchimento.py`:

```python
import pytest
from docx import Document

from aportes.documentos.preenchimento import CampoFaltando, preencher


def _minuta(tmp_path, *paragrafos):
    doc = Document()
    for p in paragrafos:
        doc.add_paragraph(p)
    caminho = tmp_path / "minuta.docx"
    doc.save(caminho)
    return caminho


def _texto(caminho):
    return "\n".join(p.text for p in Document(caminho).paragraphs)


def test_preenche_as_tags(tmp_path):
    minuta = _minuta(tmp_path, "Subscritor: {{ nome_subscritor }}",
                     "Valor: R$ {{ valor_reais }}")
    destino = tmp_path / "saida.docx"
    preencher(minuta, {"nome_subscritor": "Fulano de Tal",
                       "valor_reais": "10.000,00"}, destino)
    texto = _texto(destino)
    assert "Fulano de Tal" in texto
    assert "10.000,00" in texto


def test_nenhuma_tag_sobra_no_documento(tmp_path):
    minuta = _minuta(tmp_path, "Subscritor: {{ nome_subscritor }}")
    destino = tmp_path / "saida.docx"
    preencher(minuta, {"nome_subscritor": "Fulano de Tal"}, destino)
    texto = _texto(destino)
    assert "{{" not in texto and "}}" not in texto


def test_campo_faltando_impede_a_geracao(tmp_path):
    minuta = _minuta(tmp_path, "{{ nome_subscritor }} - {{ endereco }}")
    destino = tmp_path / "saida.docx"
    with pytest.raises(CampoFaltando) as erro:
        preencher(minuta, {"nome_subscritor": "Fulano de Tal"}, destino)
    assert "endereco" in str(erro.value)
    assert not destino.exists(), "documento incompleto nao pode ser gravado"


def test_campo_vazio_conta_como_faltando(tmp_path):
    """String vazia no Boletim e um buraco, nao um valor."""
    minuta = _minuta(tmp_path, "{{ endereco }}")
    destino = tmp_path / "saida.docx"
    with pytest.raises(CampoFaltando):
        preencher(minuta, {"endereco": "  "}, destino)


def test_condicional_do_word_funciona(tmp_path):
    minuta = _minuta(
        tmp_path,
        "{% if pessoa_juridica %}Representante: {{ rep_nome }}{% endif %}",
    )
    destino = tmp_path / "saida.docx"
    preencher(minuta, {"pessoa_juridica": "", "rep_nome": "-"}, destino)
    assert "Representante" not in _texto(destino)


def test_dado_extra_nao_atrapalha(tmp_path):
    minuta = _minuta(tmp_path, "{{ nome_subscritor }}")
    destino = tmp_path / "saida.docx"
    preencher(minuta, {"nome_subscritor": "Fulano de Tal", "sobra": "x"}, destino)
    assert "Fulano de Tal" in _texto(destino)
```

Nota: `test_condicional_do_word_funciona` passa `pessoa_juridica` vazio de
propósito — condicionais são exceção à regra de campo vazio, e a implementação
trata isso: só as tags `{{ }}` exigem valor.

- [ ] **Step 2: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_preenchimento.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`src/aportes/documentos/preenchimento.py`:

```python
"""Preenche uma minuta .docx com docxtpl.

O programa nunca reconstroi o documento: so preenche o que o Gabriel escreveu
no Word. E por isso que estilo, numeracao e sumario saem intactos.
"""

from pathlib import Path

from docxtpl import DocxTemplate

from aportes.documentos.validador import tags_da_minuta


class CampoFaltando(Exception):
    """Um campo da minuta nao tem dado. O documento nao e gerado."""


def preencher(minuta: Path, dados: dict[str, str], destino: Path) -> None:
    exigidas = tags_da_minuta(minuta)
    faltando = sorted(
        tag for tag in exigidas
        if not str(dados.get(tag, "")).strip()
    )
    if faltando:
        raise CampoFaltando(
            f"a minuta {minuta.name} exige campos sem dado: "
            f"{', '.join(faltando)}. O documento nao foi gerado."
        )

    modelo = DocxTemplate(minuta)
    modelo.render(dados)
    destino.parent.mkdir(parents=True, exist_ok=True)
    modelo.save(destino)
```

- [ ] **Step 4: Rodar e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_preenchimento.py -v`
Expected: PASS, 6 testes.

- [ ] **Step 5: Rodar a suíte inteira**

Run: `.venv/Scripts/python.exe -m pytest -v`
Expected: PASS, tudo.

- [ ] **Step 6: Commit**

```bash
git add src/aportes/documentos/preenchimento.py tests/test_preenchimento.py
git commit -m "feat: preenchimento de minuta com recusa por campo faltando"
```

---

### Task 13: Conversão em PDF pelo Word

**Files:**
- Create: `src/aportes/documentos/pdf.py`, `scripts/fumaca_pdf.py`
- Test: `tests/test_pdf.py`

**Interfaces:**
- Consumes: nada do projeto.
- Produces: `ConversorWord` (gerenciador de contexto) com o método `converter(docx: Path, pdf: Path) -> None`.

O Word abre **uma vez por bloco** e converte todos os documentos — a conversão
é a parte lenta e não faz sentido pagá-la 40 vezes. O teste automático cobre só
o contrato; a conversão real é fumaça manual, porque depende do Word instalado.

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_pdf.py`:

```python
from pathlib import Path

import pytest

from aportes.documentos.pdf import ConversorWord


class WordFalso:
    """Substitui o COM do Word para testar o contrato sem abrir o Word."""

    def __init__(self):
        self.abriu = 0
        self.convertidos = []
        self.fechou = False

    def abrir(self):
        self.abriu += 1

    def converter_um(self, docx, pdf):
        self.convertidos.append((docx, pdf))

    def fechar(self):
        self.fechou = True


def test_abre_o_word_uma_vez_para_o_bloco_inteiro(tmp_path):
    falso = WordFalso()
    docs = [(tmp_path / f"{i}.docx", tmp_path / f"{i}.pdf") for i in range(5)]
    for caminho, _ in docs:
        caminho.write_bytes(b"")

    with ConversorWord(_word=falso) as conversor:
        for docx, pdf in docs:
            conversor.converter(docx, pdf)

    assert falso.abriu == 1
    assert len(falso.convertidos) == 5


def test_fecha_o_word_mesmo_se_der_erro(tmp_path):
    falso = WordFalso()
    with pytest.raises(RuntimeError):
        with ConversorWord(_word=falso):
            raise RuntimeError("erro no meio do bloco")
    assert falso.fechou is True


def test_recusa_docx_inexistente(tmp_path):
    falso = WordFalso()
    with ConversorWord(_word=falso) as conversor:
        with pytest.raises(FileNotFoundError):
            conversor.converter(tmp_path / "nao_existe.docx", tmp_path / "x.pdf")
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_pdf.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`src/aportes/documentos/pdf.py`:

```python
"""Conversao .docx -> PDF pelo proprio Word, via COM.

E o unico jeito de garantir fidelidade total a formatacao da casa. O Word abre
uma vez por bloco: abrir e fechar por arquivo custa segundos que se multiplicam
por 40.
"""

from pathlib import Path

_FORMATO_PDF = 17


class _WordCOM:
    """A conversa real com o Word. Substituivel nos testes."""

    def __init__(self) -> None:
        self._app = None

    def abrir(self) -> None:
        import win32com.client  # importado aqui: so existe no Windows

        self._app = win32com.client.Dispatch("Word.Application")
        self._app.Visible = False
        self._app.DisplayAlerts = False

    def converter_um(self, docx: Path, pdf: Path) -> None:
        documento = self._app.Documents.Open(str(docx.resolve()))
        try:
            documento.SaveAs(str(pdf.resolve()), FileFormat=_FORMATO_PDF)
        finally:
            documento.Close(False)

    def fechar(self) -> None:
        if self._app is not None:
            self._app.Quit()
            self._app = None


class ConversorWord:
    """Gerenciador de contexto: uma instancia do Word para o bloco inteiro."""

    def __init__(self, _word=None) -> None:
        self._word = _word if _word is not None else _WordCOM()

    def __enter__(self) -> "ConversorWord":
        self._word.abrir()
        return self

    def __exit__(self, *_) -> None:
        self._word.fechar()

    def converter(self, docx: Path, pdf: Path) -> None:
        if not docx.exists():
            raise FileNotFoundError(f"nao encontrei o documento {docx}")
        pdf.parent.mkdir(parents=True, exist_ok=True)
        self._word.converter_um(docx, pdf)
```

- [ ] **Step 4: Rodar e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_pdf.py -v`
Expected: PASS, 3 testes.

- [ ] **Step 5: Escrever o script de fumaça manual**

`scripts/fumaca_pdf.py`:

```python
"""Teste de fumaca do Word COM. Rodar A MAO, e OLHAR o PDF gerado.

Nao e automatizavel de forma confiavel: depende do Word instalado.
Na maquina da empresa, este e o primeiro script a rodar.

    .venv/Scripts/python.exe scripts/fumaca_pdf.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from docx import Document  # noqa: E402

from aportes.documentos.pdf import ConversorWord  # noqa: E402

SAIDA = Path(__file__).resolve().parent.parent / "saida" / "fumaca"


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    docx = SAIDA / "fumaca.docx"
    pdf = SAIDA / "fumaca.pdf"

    doc = Document()
    doc.add_heading("Teste de fumaca", level=1)
    doc.add_paragraph("Se voce esta lendo isto em PDF, o Word COM funciona.")
    doc.add_paragraph("Acentuacao: cotas, subscricao, integralizacao, R$ 1.234,56")
    doc.save(docx)

    with ConversorWord() as conversor:
        conversor.converter(docx, pdf)

    print(f"PDF gerado em: {pdf}")
    print("ABRA O ARQUIVO E CONFIRA. Este teste so vale olhado por gente.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Rodar o teste de fumaça e olhar o PDF**

Run: `.venv/Scripts/python.exe scripts/fumaca_pdf.py`
Expected: o PDF é criado em `saida/fumaca/fumaca.pdf`. **Abrir e conferir** —
texto legível, acentuação correta. Este passo não é automatizável.

- [ ] **Step 7: Commit**

```bash
git add src/aportes/documentos/pdf.py scripts/fumaca_pdf.py tests/test_pdf.py
git commit -m "feat: conversao em PDF pelo Word COM"
```

---

## Bloqueado — depende dos arquivos de referência

Estas tasks não podem ser escritas com honestidade sem os arquivos reais, e
serão detalhadas quando eles chegarem. Escrever leitor contra um formato
imaginado é escrever leitor errado.

**Task 14 — leitor do Saldo de Aplicações (Britech, Excel).** Precisa de uma
exportação anonimizada. **Verificar primeiro:** o relatório separa a posição
por classe? A regra do Termo de Adesão depende disso.

**Task 15 — leitor do Excel de cotistas (Portal ID).** Precisa de uma
exportação anonimizada.

**Task 16 — leitores de ficha cadastral em PDF.** Três variantes: PF, PJ e
fundo. Precisa de um exemplo anonimizado de cada.

**Task 17 — mapeamento das minutas.** Quais tags o Boletim de Subscrição e o
Termo de Adesão precisam, e de onde cada uma vem. Precisa das minutas `.docx`.
Inclui confirmar a redação do valor por extenso contra um Boletim real — a
Task 2 decidiu remover a vírgula do `num2words`, e essa decisão precisa bater
com o que a casa escreve.

**Task 18 — o comando do bloco.** Junta tudo: transcrição conferida → motor →
documentos → PDF → relatório em três montes. Depende das tasks acima.

**Task 19 — instalação na máquina da empresa.** Verificar Word COM
(`scripts/fumaca_pdf.py`), Python e Claude Code. Guardar as wheels para
instalação offline.

---

## Auto-revisão

**Cobertura da spec:**

| Seção da spec | Onde é implementada |
|---|---|
| §2 arquitetura (núcleo determinístico) | Tasks 4-7 |
| §3 privacidade / LGPD | Task 1 (guardrail), Tasks 9-10 (`dados/`) |
| §4 base de fatos | Tasks 8, 9, 10 |
| §5 três portas de entrada | **Bloqueado** (Tasks 14-16) |
| §6 motor de regras, as 5 perguntas | Tasks 5, 6, 7 |
| §6 procedência no veredito | Task 7 (`test_motivo_da_reprovacao_cita_a_procedencia`) |
| §7 valor por extenso | Task 2 |
| §7 validador de modelo | Task 11 |
| §7 campo faltando impede geração | Task 12 |
| §7 PDF, Word uma vez por bloco | Task 13 |
| §7 saída sem sobrescrever | **Task 18** (bloqueado) |
| §8 só o que é novo aparece | Task 10 |
| §10 falhar alto no leitor | Task 8 (YAML); Tasks 14-16 para os relatórios |
| §13 duas máquinas | Task 13 (fumaça), Task 19 |

**Consistência de tipos:** `Categoria`, `Condominio`, `TipoPessoa`,
`Procedencia`, `Situacao`, `Veredito`, `Base`, `Boleta`, `Classe`, `Oferta`,
`Cotista` são definidos nas Tasks 3-4 e usados com os mesmos nomes e campos nas
Tasks 5-13. `avaliar(boleta, base)`, `atende`, `mais_restritiva`,
`valor_por_extenso`, `formatar_reais`, `tags_da_minuta`, `validar_minuta`,
`preencher`, `carregar_classes`, `carregar_ofertas`, `carregar_cotistas`,
`salvar_cotistas`, `mesclar`, `carregar_vistas`, `registrar`, `chave`,
`ConversorWord.converter` — todos declarados no bloco **Produces** da task que
os cria antes de aparecerem em qualquer outra.

**Lacuna conhecida e deliberada:** a saída sem sobrescrever (§7) fica na Task
18, junto do comando do bloco, porque é lá que o nome do arquivo é decidido.
