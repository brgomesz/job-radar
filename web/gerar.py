"""Gera docs/index.html a partir do jobs.db — a página pública do radar.

Roda no fim de cada ciclo, dentro do workflow (ver jobradar.yml), logo
depois do banco daquele run ser recolocado por cima do estado remoto. O
HTML é commitado junto com o banco e servido pelo GitHub Pages, então a
página fica atualizada a cada 3h sem nenhum serviço extra no ar — mesma
filosofia de custo zero do resto do projeto (Actions como cron, SQLite
como banco, Git como persistência).

Por que existe, além do Telegram: notificação é boa pra "olha isso
agora" e ruim pra "quero rever o que apareceu essa semana". O usuário
limpou o histórico do chat e perdeu a lista inteira, mesmo com as vagas
todas no banco — a página é a metade que faltava (histórico navegável,
filtrável, que não depende de mensagem nenhuma sobreviver).
"""

import html
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone

from core.config import DB_PATH

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(_RAIZ, "web", "template.html")
SAIDA = os.path.join(_RAIZ, "docs", "index.html")

# Espelha o --perfil do workflow. As chaves antigas do banco (brasil,
# internacional e as vagas sem perfil, anteriores ao campo existir) são
# do radar de Dados/BI da autora original e não têm o que fazer nesta
# página — ficam no banco, fora da vitrine.
PERFIS_NA_PAGINA = ("dev", "admin")

# Rótulo por perfil. Não importado de core.perfis de propósito: aquele
# módulo carrega todos os scrapers (e o Playwright junto), coisa que um
# gerador de HTML não deveria arrastar só pra ler dois nomes.
ROTULOS = {"dev": "Dev", "admin": "Administrativo"}

_FUSO_BR = timezone(timedelta(hours=-3))


def _quando_entrou(bruto: str) -> str:
    """`encontrada_em` (quando a vaga entrou no NOSSO banco) formatada no
    horário de Brasília.

    O banco guarda em UTC: a coluna usa CURRENT_TIMESTAMP do SQLite, que é
    sempre UTC, e o robô roda em runner do GitHub, também em UTC. Mostrar o
    valor cru na página daria uma hora 3h adiantada -- vaga achada às 7h da
    manhã apareceria como 10h.

    Não confundir com `publicado_em`, que é a data que a FONTE anuncia
    (texto livre, formato de cada site). As duas aparecem na página, com
    rótulo, porque respondem perguntas diferentes: "isso é novidade pra
    mim?" e "esse anúncio é velho?".
    """
    if not bruto:
        return ""
    try:
        quando = datetime.fromisoformat(bruto)
    except ValueError:
        return ""  # formato inesperado: melhor não mostrar nada do que mentir
    if quando.tzinfo is None:
        quando = quando.replace(tzinfo=timezone.utc)
    return quando.astimezone(_FUSO_BR).strftime("%d/%m %H:%M")


def carregar_vagas(db_path: str = "") -> list[dict]:
    """Vagas dos perfis em produção, da mais relevante pra menos.

    Ordena por relevância e, dentro da mesma nota, pela mais recente:
    empate de nota é comum (a escala tem 10 degraus pra centenas de
    vagas), e nesse caso o que decide é qual anúncio ainda está fresco.
    """
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    marcadores = ",".join("?" for _ in PERFIS_NA_PAGINA)
    try:
        linhas = conn.execute(
            f"""
            SELECT titulo, empresa, local, link, site, relevancia, perfil,
                   modalidade, publicado_em, encontrada_em
            FROM vagas_vistas
            WHERE perfil IN ({marcadores})
            ORDER BY relevancia DESC, encontrada_em DESC
            """,
            PERFIS_NA_PAGINA,
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "t": l["titulo"],
            "e": l["empresa"],
            "l": l["local"] or "—",
            "u": l["link"],
            "s": l["site"],
            "r": l["relevancia"] or 0,
            "p": l["perfil"],
            "m": l["modalidade"] or "",
            "d": _quando_entrou(l["encontrada_em"] or ""),
            "pub": l["publicado_em"] or "",
        }
        for l in linhas
    ]


def montar_html(vagas: list[dict], agora: datetime | None = None) -> str:
    """Template + dados. Os dados entram como JSON dentro de <script>, e
    por isso "</" é escapado: um título de vaga que contivesse "</script>"
    fecharia a tag no meio do JSON e quebraria a página inteira. Escapar
    aqui (e não confiar que nenhuma vaga vai ter isso) é a diferença entre
    a página aguentar qualquer título e quebrar num dia qualquer."""
    agora = agora or datetime.now(_FUSO_BR)
    dados = json.dumps(vagas, ensure_ascii=False).replace("</", "<\\/")
    modelo = open(TEMPLATE, encoding="utf-8").read()
    return (
        modelo
        .replace("__DADOS__", dados)
        .replace("__ATUALIZADO__", html.escape(agora.strftime("%d/%m/%Y às %H:%M")))
    )


def gerar(db_path: str = "", saida: str = "") -> int:
    saida = saida or SAIDA
    vagas = carregar_vagas(db_path)
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        f.write(montar_html(vagas))
    return len(vagas)


if __name__ == "__main__":
    total = gerar()
    print(f"docs/index.html gerado com {total} vaga(s).")
