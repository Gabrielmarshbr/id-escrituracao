"""O motor de regras.

Puro: recebe uma boleta e os fatos conhecidos, devolve um veredito.
Nao le disco, nao gera documento, nao aprova nada.
"""

from aportes.dominio import Base, Boleta, Condominio, Situacao, Veredito
from aportes.qualificacao import atende, mais_restritiva

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

    if not base.conhece_saldo_do_fundo(classe.fundo_cnpj):
        return Veredito(
            situacao=Situacao.FALTOU_DADO,
            motivo=(
                f"nao sei a posicao do fundo {classe.fundo_nome}: nenhum Saldo "
                "de Aplicacoes carregado cobre esse fundo"
            ),
            pendencias=(
                f"exporte o Saldo de Aplicacoes do fundo {classe.fundo_nome} no "
                "Britech e coloque em dados/saldos/",
            ),
        )

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

    documentos: list[str] = []
    if classe.condominio is Condominio.FECHADO:
        documentos.append(BOLETIM)

    # O Termo de Adesao e um por cotista por FUNDO, nao por classe: quem ja
    # aderiu ao fundo por outra classe nao assina de novo.
    primeiro_aporte = not base.tem_posicao_no_fundo(
        boleta.documento_cotista, classe.fundo_cnpj
    )
    if primeiro_aporte:
        documentos.append(TERMO_ADESAO)

    motivo = (
        f"classe {classe.id}, condominio {classe.condominio.value}, "
        f"{'primeiro aporte no fundo' if primeiro_aporte else 'aporte subsequente'}"
    )

    return Veredito(
        situacao=Situacao.LIBERADA,
        motivo=motivo,
        documentos=tuple(documentos),
    )
