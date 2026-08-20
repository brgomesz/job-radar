"""Aplicação web enxuta para acompanhar e organizar vagas encontradas."""

import os
import secrets
from functools import wraps

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

from database.database import (
    definir_situacao,
    listar_vagas,
    opcoes_filtro_painel,
    resumo_painel,
)

SITUACOES = ("nova", "candidatei", "entrevista", "proposta", "descartada")


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("DASHBOARD_SECRET_KEY", "desenvolvimento-sem-segredo"),
        DASHBOARD_PASSWORD=os.getenv("DASHBOARD_PASSWORD", ""),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=bool(os.getenv("VERCEL_ENV")),
    )
    if config:
        app.config.update(config)

    if os.getenv("VERCEL_ENV") and not app.config.get("TESTING"):
        if app.config["SECRET_KEY"] == "desenvolvimento-sem-segredo" or not app.config["DASHBOARD_PASSWORD"]:
            raise RuntimeError(
                "Em produção, defina DASHBOARD_SECRET_KEY e DASHBOARD_PASSWORD antes de publicar o painel."
            )

    def acesso_exigido(view):
        @wraps(view)
        def envoltoria(*args, **kwargs):
            senha = app.config["DASHBOARD_PASSWORD"]
            if senha and not session.get("dashboard_autenticado"):
                return redirect(url_for("login", next=request.full_path))
            return view(*args, **kwargs)
        return envoltoria

    @app.context_processor
    def csrf_contexto():
        token = session.get("csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["csrf_token"] = token
        return {"csrf_token": token, "situacoes": SITUACOES}

    def csrf_valido() -> bool:
        return secrets.compare_digest(session.get("csrf_token", ""), request.form.get("csrf_token", ""))

    @app.get("/login")
    def login():
        if not app.config["DASHBOARD_PASSWORD"]:
            return redirect(url_for("inicio"))
        return render_template("login.html")

    @app.post("/login")
    def autenticar():
        if not csrf_valido():
            abort(400)
        if secrets.compare_digest(request.form.get("senha", ""), app.config["DASHBOARD_PASSWORD"]):
            session["dashboard_autenticado"] = True
            proxima = request.args.get("next", "")
            destino = proxima if proxima.startswith("/") and not proxima.startswith("//") else url_for("inicio")
            return redirect(destino)
        flash("Senha inválida.", "erro")
        return redirect(url_for("login"))

    @app.post("/sair")
    @acesso_exigido
    def sair():
        if not csrf_valido():
            abort(400)
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @acesso_exigido
    def inicio():
        filtros = {
            "perfil": request.args.get("perfil", ""),
            "situacao": request.args.get("situacao", ""),
            "site": request.args.get("site", ""),
            "busca": request.args.get("busca", "").strip(),
        }
        vagas = listar_vagas(**filtros)
        return render_template(
            "inicio.html",
            resumo=resumo_painel(),
            vagas=vagas,
            filtros=filtros,
            perfis=opcoes_filtro_painel("perfil"),
            sites=opcoes_filtro_painel("site"),
        )

    @app.post("/vagas/<job_id>/situacao")
    @acesso_exigido
    def atualizar_situacao(job_id: str):
        if not csrf_valido():
            abort(400)
        situacao = request.form.get("situacao", "")
        if situacao not in SITUACOES:
            abort(400)
        definir_situacao(job_id, situacao)
        flash("Situação atualizada.", "sucesso")
        return redirect(request.referrer or url_for("inicio"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
