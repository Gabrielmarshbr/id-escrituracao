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
