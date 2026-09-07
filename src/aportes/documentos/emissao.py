"""Do veredito aos PDFs.

Monta os campos que as minutas usam, preenche, converte e grava — sem nunca
sobrescrever documento que ja existe e sem deixar nada pela metade.
"""

import re
import unicodedata
from pathlib import Path

from aportes.dominio import Boleta, Classe, Cotista, Oferta, TipoPessoa
from aportes.documentos.preenchimento import preencher
from aportes.extenso import formatar_reais, valor_por_extenso
from aportes.formatos import formatar_documento

#: Campos que o cadastro do cotista pode trazer e que a minuta pode usar.
#: Ausentes vem vazios de proposito: o preenchimento recusa campo vazio, em
#: vez de gerar documento com buraco.
CAMPOS_DE_CADASTRO = (
    "endereco", "email", "banco", "agencia", "conta",
    "representante_nome", "representante_cpf",
)


class MinutaAusente(Exception):
    """A minuta do documento nao esta em modelos/."""


def dados_para_minuta(boleta: Boleta, cotista: Cotista, classe: Classe,
                      oferta: Oferta) -> dict[str, str]:
    """Todos os campos disponiveis para as tags das minutas.

    Os nomes aqui sao o contrato com quem escreve a minuta no Word.
    Ver modelos/CAMPOS.md.
    """
    dados = {
        "nome_subscritor": cotista.nome,
        "cpf_cnpj": formatar_documento(cotista.documento),
        "tipo_pessoa": cotista.tipo.value,
        "pessoa_juridica": "sim" if cotista.tipo is not TipoPessoa.PF else "",
        "fundo_nome": classe.fundo_nome,
        "fundo_cnpj": formatar_documento(classe.fundo_cnpj),
        "classe_nome": classe.nome,
        "classe_id": classe.id,
        "oferta_id": oferta.id,
        "valor_reais": formatar_reais(boleta.valor),
        "valor_extenso": valor_por_extenso(boleta.valor),
        "data_boleta": boleta.data.strftime("%d/%m/%Y"),
    }
    for campo in CAMPOS_DE_CADASTRO:
        valor = cotista.cadastro.get(campo, "")
        if campo == "representante_cpf" and valor:
            valor = formatar_documento(valor)
        dados[campo] = valor
    return dados


def nome_base(boleta: Boleta, cotista: Cotista, classe: Classe) -> str:
    """Prefixo previsivel e ordenavel: data, cotista, classe.

    `emitir` acrescenta o tipo de documento e a extensao.
    """
    return (
        f"{boleta.data.isoformat()}"
        f"-{_url_amigavel(cotista.nome)}"
        f"-{_url_amigavel(classe.id)}"
    )


def emitir(documentos: tuple[str, ...], dados: dict[str, str], modelos: Path,
           saida: Path, prefixo: str, conversor) -> list[Path]:
    """Gera os PDFs de uma boleta. Tudo ou nada.

    Valida as minutas e os campos ANTES de escrever qualquer arquivo, para
    nao deixar um documento solto quando o segundo falha.
    """
    minutas = {}
    for documento in documentos:
        caminho = modelos / f"{documento}.docx"
        if not caminho.exists():
            raise MinutaAusente(
                f"a minuta de '{documento}' nao esta em {modelos}. "
                f"Esperado: {caminho.name}"
            )
        minutas[documento] = caminho

    destinos = {
        documento: saida / f"{prefixo}-{documento}.pdf"
        for documento in documentos
    }
    for documento, destino in destinos.items():
        if destino.exists():
            raise FileExistsError(
                f"o documento {destino.name} ja existe. Reprocessar e "
                "inofensivo, mas sobrescrever nao: apague ou renomeie o antigo."
            )

    saida.mkdir(parents=True, exist_ok=True)
    temporarios: list[Path] = []
    gerados: list[Path] = []
    try:
        # Preenche tudo primeiro: se faltar campo, nada foi convertido ainda.
        for documento, minuta in minutas.items():
            temporario = saida / f".{prefixo}-{documento}.docx"
            preencher(minuta, dados, temporario)
            temporarios.append(temporario)

        for temporario, documento in zip(temporarios, minutas):
            conversor.converter(temporario, destinos[documento])
            gerados.append(destinos[documento])
    finally:
        for temporario in temporarios:
            temporario.unlink(missing_ok=True)
    return gerados


def _url_amigavel(texto: str) -> str:
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")
