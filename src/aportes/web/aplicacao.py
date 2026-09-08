"""A aplicacao web: formulario da boleta, veredito e cadastro de cotista.

Regra que atravessa tudo: esta porta LE as regras e nunca as escreve. Quando
falta um fundo ou uma oferta, ela diz o que falta e para — quem decide que um
fundo e fechado e quem responde pela area.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Flask, redirect, render_template, request, url_for

from aportes.base.boletas import carregar_vistas_da_equipe, chave, registrar
from aportes.base.nomes import usuario_da_maquina
from aportes.base.repositorio import carregar_base, salvar_cotista
from aportes.configuracao import Configuracao
from aportes.documentos.emissao import (
    CAMPOS_DE_CADASTRO, MinutaAusente, dados_para_minuta, emitir, nome_base,
)
from aportes.documentos.pdf import ConversorWord
from aportes.documentos.preenchimento import CampoFaltando
from aportes.dominio import Boleta, Cotista, Procedencia, Situacao, TipoPessoa
from aportes.extenso import formatar_reais
from aportes.formatos import formatar_documento
from aportes.qualificacao import Categoria
from aportes.regras import avaliar
from aportes.web.rotas_regras import registrar_rotas


def criar_aplicacao(config: Configuracao, usuario: str | None = None,
                    conversor=None) -> Flask:
    app = Flask(__name__)
    app.config["APORTES"] = config
    app.config["USUARIO"] = usuario or usuario_da_maquina()
    app.config["CONVERSOR"] = conversor  # None = usa o Word de verdade

    @app.get("/")
    def inicio():
        base = carregar_base(config)
        return render_template(
            "boleta.html", base=base, config=config, aba="boletas",
            usuario=app.config["USUARIO"], hoje=date.today().isoformat(),
            ofertas_por_classe=_ofertas_por_classe(base),
        )

    @app.post("/avaliar")
    def processar():
        base = carregar_base(config)
        try:
            boleta = _boleta_do_formulario(request.form)
        except ValueError as erro:
            return render_template(
                "boleta.html", base=base, config=config, aba="boletas",
                usuario=app.config["USUARIO"], hoje=date.today().isoformat(),
                ofertas_por_classe=_ofertas_por_classe(base),
                erro=str(erro), form=request.form,
            ), 400

        informado = _primeiro_aporte_do_formulario(request.form)
        veredito = avaliar(boleta, base, primeiro_aporte_informado=informado)

        ja_vista = chave(boleta) in carregar_vistas_da_equipe(config.pasta_dados)
        gerados, falha = [], None

        if veredito.situacao is Situacao.LIBERADA and not ja_vista:
            gerados, falha = _gerar(app, config, base, boleta, veredito)
            if falha is None:
                registrar(config.pasta_dados, app.config["USUARIO"], boleta,
                          veredito.documentos)

        return render_template(
            "veredito.html", veredito=veredito, boleta=boleta, base=base,
            aba="boletas",
            gerados=gerados, falha=falha, ja_vista=ja_vista,
            cotista=base.cotistas.get(boleta.documento_cotista),
        )

    @app.get("/api/cotista/<documento>")
    def consultar_cotista(documento):
        """Diz o que a base sabe do cotista, para a tela preencher na hora.

        Poupa descobrir so depois de mandar analisar que ele nem esta na base.
        """
        so_digitos = "".join(c for c in documento if c.isdigit())
        cotista = carregar_base(config).cotistas.get(so_digitos)
        if cotista is None:
            return {"conhecido": False}
        return {
            "conhecido": True,
            "nome": cotista.nome,
            "tipo": cotista.tipo.value,
            "categoria": cotista.categoria.value if cotista.categoria else None,
            "procedencia": (str(cotista.categoria_procedencia)
                            if cotista.categoria_procedencia else None),
        }

    @app.get("/cotista")
    def formulario_cotista():
        return render_template(
            "cotista.html", campos=CAMPOS_DE_CADASTRO, aba="boletas",
            categorias=list(Categoria), tipos=list(TipoPessoa),
            documento=request.args.get("documento", ""),
        )

    @app.post("/cotista")
    def gravar_cotista():
        f = request.form
        documento = "".join(c for c in f.get("documento", "") if c.isdigit())
        if len(documento) not in (11, 14):
            return render_template(
                "cotista.html", campos=CAMPOS_DE_CADASTRO, aba="boletas",
                categorias=list(Categoria), tipos=list(TipoPessoa),
                documento=f.get("documento", ""),
                erro="CPF deve ter 11 digitos e CNPJ 14.",
            ), 400

        procedencia = Procedencia(
            fonte=f.get("fonte") or "informado na tela", em=date.today())
        cotista = Cotista(
            documento=documento,
            nome=f.get("nome", "").strip(),
            tipo=TipoPessoa(f.get("tipo", "pf")),
            categoria=Categoria(f["categoria"]) if f.get("categoria") else None,
            categoria_procedencia=procedencia if f.get("categoria") else None,
            cadastro={c: f.get(c, "").strip() for c in CAMPOS_DE_CADASTRO
                      if f.get(c, "").strip()},
            cadastro_procedencia=procedencia,
        )
        salvar_cotista(config, app.config["USUARIO"], cotista)
        return redirect(url_for("inicio", cadastrado=documento))

    app.jinja_env.filters["documento"] = formatar_documento
    app.jinja_env.filters["reais"] = formatar_reais
    registrar_rotas(app, config)
    return app


def _ofertas_por_classe(base) -> dict[str, list[dict]]:
    """Para a tela filtrar a oferta assim que a classe e escolhida."""
    por_classe: dict[str, list[dict]] = {}
    for oferta in base.ofertas.values():
        por_classe.setdefault(oferta.classe_id, []).append(
            {"id": oferta.id, "publica": oferta.publica})
    return por_classe


def _boleta_do_formulario(form) -> Boleta:
    documento = "".join(c for c in form.get("documento_cotista", "") if c.isdigit())
    if not documento:
        raise ValueError("informe o CPF ou CNPJ do cotista")
    if not form.get("classe_id"):
        raise ValueError("escolha a classe")
    try:
        valor = Decimal(form.get("valor", "").replace(".", "").replace(",", "."))
    except (InvalidOperation, AttributeError):
        raise ValueError(
            f"valor invalido: {form.get('valor')!r}. Use 10000,00"
        ) from None
    if valor <= 0:
        raise ValueError("o valor do aporte precisa ser maior que zero")
    return Boleta(
        id=form.get("id_boleta", "").strip(),
        documento_cotista=documento,
        classe_id=form["classe_id"],
        oferta_id=form.get("oferta_id") or None,
        valor=valor,
        data=date.fromisoformat(form.get("data") or date.today().isoformat()),
    )


def _primeiro_aporte_do_formulario(form) -> bool | None:
    resposta = form.get("primeiro_aporte", "")
    return {"sim": True, "nao": False}.get(resposta)


def _gerar(app, config, base, boleta, veredito):
    """Devolve (pdfs gerados, mensagem de falha)."""
    cotista = base.cotistas[boleta.documento_cotista]
    classe = base.classes[boleta.classe_id]
    oferta = base.ofertas[boleta.oferta_id]
    dados = dados_para_minuta(boleta, cotista, classe, oferta)
    prefixo = nome_base(boleta, cotista, classe)
    destino = config.pasta_saida / boleta.data.isoformat()

    conversor = app.config["CONVERSOR"]
    try:
        if conversor is not None:
            return emitir(veredito.documentos, dados, config.pasta_modelos,
                          destino, prefixo, conversor), None
        with ConversorWord() as word:
            return emitir(veredito.documentos, dados, config.pasta_modelos,
                          destino, prefixo, word), None
    except (MinutaAusente, CampoFaltando, FileExistsError) as erro:
        return [], str(erro)
