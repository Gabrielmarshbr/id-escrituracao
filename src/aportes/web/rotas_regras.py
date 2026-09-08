"""As abas Fundos e Ofertas: consultar, cadastrar e anexar documentos.

A regra e o documento que a sustenta ficam lado a lado. Na hora de aprovar uma
boleta, o regulamento esta a um clique — em vez de a uma busca em 500 canais
do Slack.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from flask import (
    abort, redirect, render_template, request, send_from_directory, url_for,
)

from aportes.base.documentos import (
    ArquivoRecusado, guardar, listar, pasta_da_oferta, pasta_do_fundo,
)
from aportes.base.escrita import JaExiste, acrescentar_classe, acrescentar_oferta
from aportes.base.repositorio import carregar_base
from aportes.dominio import Classe, Condominio, Oferta, Procedencia
from aportes.qualificacao import Categoria


def registrar_rotas(app, config):
    """Pendura as rotas de Fundos e Ofertas na aplicacao."""

    def _usuario():
        return app.config["USUARIO"]

    # ------------------------------------------------------------- fundos

    @app.get("/fundos")
    def fundos():
        base = carregar_base(config)
        busca = request.args.get("q", "").strip()
        return render_template(
            "fundos.html", config=config, usuario=_usuario(), busca=busca,
            classes=_filtrar_classes(base.classes, busca),
            total=len(base.classes),
            condominios=list(Condominio), categorias=list(Categoria),
            documentos=_documentos_por_fundo(config, base.classes),
            erro=request.args.get("erro"), hoje=date.today().isoformat(),
        )

    @app.post("/fundos")
    def cadastrar_fundo():
        f = request.form
        try:
            classe = Classe(
                id=_exigir(f, "id"),
                fundo_nome=_exigir(f, "fundo_nome"),
                fundo_cnpj=_digitos(_exigir(f, "fundo_cnpj")),
                nome=_exigir(f, "nome"),
                condominio=Condominio(_exigir(f, "condominio")),
                qualificacao_exigida=Categoria(_exigir(f, "qualificacao_exigida")),
                procedencia=Procedencia(
                    fonte=f.get("fonte") or "regulamento",
                    em=date.fromisoformat(f.get("lido_em") or date.today().isoformat()),
                ),
            )
            if len(classe.fundo_cnpj) != 14:
                raise ValueError("o CNPJ do fundo precisa ter 14 digitos")
            acrescentar_classe(
                config.pasta_regras / "fundos.yaml", classe, _usuario())
        except (ValueError, JaExiste) as erro:
            return redirect(url_for("fundos", erro=str(erro)))
        return redirect(url_for("fundos", q=classe.fundo_nome))

    @app.post("/fundos/<cnpj>/documentos")
    def anexar_ao_fundo(cnpj):
        return _anexar(pasta_do_fundo(config.pasta_documentos, cnpj), "fundos")

    # ------------------------------------------------------------ ofertas

    @app.get("/ofertas")
    def ofertas():
        base = carregar_base(config)
        busca = request.args.get("q", "").strip()
        return render_template(
            "ofertas.html", config=config, usuario=_usuario(), busca=busca,
            ofertas=_filtrar_ofertas(base.ofertas, busca, base.classes),
            classes=base.classes, total=len(base.ofertas),
            categorias=list(Categoria),
            documentos=_documentos_por_oferta(config, base.ofertas),
            erro=request.args.get("erro"),
        )

    @app.post("/ofertas")
    def cadastrar_oferta():
        f = request.form
        try:
            minimo = f.get("valor_minimo", "").strip()
            oferta = Oferta(
                id=_exigir(f, "id"),
                classe_id=_exigir(f, "classe_id"),
                publica=f.get("publica") == "sim",
                qualificacao_exigida=(
                    Categoria(f["qualificacao_exigida"])
                    if f.get("qualificacao_exigida") else None
                ),
                valor_minimo=_valor(minimo) if minimo else None,
                vigencia_ate=(
                    date.fromisoformat(f["vigencia_ate"])
                    if f.get("vigencia_ate") else None
                ),
            )
            if not f.get("publica"):
                raise ValueError(
                    "diga se a oferta e publica ou privada — este campo nao "
                    "tem valor-padrao"
                )
            acrescentar_oferta(
                config.pasta_regras / "ofertas.yaml", oferta, _usuario())
        except (ValueError, InvalidOperation, JaExiste) as erro:
            return redirect(url_for("ofertas", erro=str(erro)))
        return redirect(url_for("ofertas", q=oferta.id))

    @app.post("/ofertas/<oferta_id>/documentos")
    def anexar_a_oferta(oferta_id):
        return _anexar(pasta_da_oferta(config.pasta_documentos, oferta_id), "ofertas")

    # --------------------------------------------------------- documentos

    @app.get("/documentos/<tipo>/<chave>/<nome>")
    def baixar(tipo, chave, nome):
        if tipo not in ("fundos", "ofertas"):
            abort(404)
        pasta = (pasta_do_fundo if tipo == "fundos" else pasta_da_oferta)(
            config.pasta_documentos, chave)
        if not (pasta / nome).exists():
            abort(404)
        return send_from_directory(pasta, nome, as_attachment=True)

    def _anexar(pasta, volta_para):
        arquivo = request.files.get("arquivo")
        if arquivo is None or not arquivo.filename:
            return redirect(url_for(volta_para, erro="escolha um arquivo"))
        try:
            guardar(pasta, arquivo.filename, arquivo.read())
        except ArquivoRecusado as erro:
            return redirect(url_for(volta_para, erro=str(erro)))
        return redirect(url_for(volta_para))


# ------------------------------------------------------------- auxiliares

def _filtrar_classes(classes, busca):
    if not busca:
        return sorted(classes.values(), key=lambda c: (c.fundo_nome, c.nome))
    alvo = _sem_ruido(busca)
    encontradas = [
        c for c in classes.values()
        if alvo in _sem_ruido(f"{c.fundo_nome} {c.nome} {c.id} {c.fundo_cnpj}")
    ]
    return sorted(encontradas, key=lambda c: (c.fundo_nome, c.nome))


def _filtrar_ofertas(ofertas, busca, classes):
    def texto(o):
        classe = classes.get(o.classe_id)
        nome = f"{classe.fundo_nome} {classe.nome}" if classe else ""
        return f"{o.id} {o.classe_id} {nome}"

    lista = list(ofertas.values())
    if busca:
        alvo = _sem_ruido(busca)
        lista = [o for o in lista if alvo in _sem_ruido(texto(o))]
    return sorted(lista, key=lambda o: o.id)


def _documentos_por_fundo(config, classes):
    return {
        c.fundo_cnpj: [p.name for p in
                       listar(pasta_do_fundo(config.pasta_documentos, c.fundo_cnpj))]
        for c in classes.values()
    }


def _documentos_por_oferta(config, ofertas):
    return {
        o.id: [p.name for p in
               listar(pasta_da_oferta(config.pasta_documentos, o.id))]
        for o in ofertas.values()
    }


def _sem_ruido(texto: str) -> str:
    import unicodedata
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return "".join(c for c in sem_acento.lower() if c.isalnum() or c == " ")


def _exigir(form, campo):
    valor = form.get(campo, "").strip()
    if not valor:
        raise ValueError(f"o campo '{campo.replace('_', ' ')}' e obrigatorio")
    return valor


def _digitos(texto: str) -> str:
    return "".join(c for c in texto if c.isdigit())


def _valor(texto: str) -> Decimal:
    return Decimal(texto.replace(".", "").replace(",", "."))
