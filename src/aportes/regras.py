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
