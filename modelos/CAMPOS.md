# Como marcar as minutas no Word

As minutas ficam nesta pasta, com estes nomes exatos:

- `boletim_subscricao.docx`
- `termo_adesao.docx`

Você edita as duas no Word normalmente. Onde hoje há um dado que muda de
documento para documento, escreva uma **tag** no lugar. O programa troca a tag
pelo valor e nunca mexe em mais nada — estilo, numeração e sumário saem
intactos.

```
Subscritor: {{ nome_subscritor }}, inscrito no CPF/ME sob o nº {{ cpf_cnpj }}
```

---

## Campos disponíveis

Use exatamente estes nomes. Um nome diferente faz o programa **recusar-se a
gerar o documento**, dizendo qual campo não conhece — de propósito: é melhor
parar do que emitir Boletim com buraco.

### O subscritor

| Tag | O que sai |
|---|---|
| `{{ nome_subscritor }}` | Nome ou razão social |
| `{{ cpf_cnpj }}` | Já com máscara: `111.111.111-11` ou `11.111.111/0001-11` |
| `{{ endereco }}` | Endereço completo |
| `{{ email }}` | E-mail |
| `{{ banco }}` `{{ agencia }}` `{{ conta }}` | Dados bancários |
| `{{ representante_nome }}` | Representante legal (PJ e fundo) |
| `{{ representante_cpf }}` | CPF do representante, com máscara |

### O fundo e a oferta

| Tag | O que sai |
|---|---|
| `{{ fundo_nome }}` | Nome do fundo |
| `{{ fundo_cnpj }}` | CNPJ do fundo, com máscara |
| `{{ classe_nome }}` | Nome da classe |
| `{{ classe_id }}` | Identificador da classe |
| `{{ oferta_id }}` | Identificador da oferta |

### O aporte

| Tag | O que sai |
|---|---|
| `{{ valor_reais }}` | `10.000,00` — sem o `R$`, que já está na minuta |
| `{{ valor_extenso }}` | `dez mil reais` |
| `{{ data_boleta }}` | `07/09/2026` |

---

## Blocos que só aparecem às vezes

Para trechos que valem só para pessoa jurídica ou fundo — o bloco do
representante legal, tipicamente:

```
{% if pessoa_juridica %}
Neste ato representado por {{ representante_nome }}, CPF {{ representante_cpf }}.
{% endif %}
```

O bloco some inteiro quando o subscritor é pessoa física.

---

## Cuidado com a autocorreção do Word

O Word troca `"` reto por `"` curvo, e isso **quebra a tag em silêncio**. Depois
de editar a minuta, rode o validador:

```powershell
.venv\Scripts\python.exe -c "from pathlib import Path; import sys; sys.path.insert(0,'src'); from aportes.documentos.validador import validar_minuta; print(validar_minuta(Path('modelos/boletim_subscricao.docx')) or 'minuta ok')"
```

Ele lista aspa curva, chave desbalanceada e `{% if %}` sem `{% endif %}`.
Vale como hábito: editou a minuta, roda o validador.

---

## O quadro de integralização

Conforme combinado, **"Quantidade de Cotas subscritas" e "Preço de Emissão por
Cota" ficam com o texto descritivo fixo** que já está na minuta — não são tags.
Só **"Preço de Subscrição"** recebe o valor:

```
Preço de Subscrição: R$ {{ valor_reais }} ({{ valor_extenso }})
```

Tags dentro de tabela funcionam normalmente.
