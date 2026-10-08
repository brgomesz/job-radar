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
import re
import sqlite3
from datetime import datetime, timedelta, timezone

from core.config import DB_PATH

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(_RAIZ, "web", "template.html")
SAIDA = os.path.join(_RAIZ, "docs", "index.html")
# Texto corrido com o anúncio inteiro de cada vaga Dev — feito pra colar
# numa IA. Fica ao lado do index.html (o GitHub Pages serve os dois) e é o
# que a aba "Conteúdo Dev" da página carrega. Arquivo à parte, e não
# embutido no HTML, porque são centenas de KB que só quem abre a aba usa.
SAIDA_CONTEUDO = os.path.join(_RAIZ, "docs", "conteudo-dev.txt")
PERFIL_CONTEUDO = "dev"
# Linha que separa uma vaga da outra no .txt. O template divide o arquivo
# por ela pra montar a lista da aba — mudar aqui exige mudar lá
# (test_pagina_web trava os dois juntos).
SEPARADOR_VAGA = "===== VAGA {n} de {total} ====="
MARCADOR_ANUNCIO = "--- Anúncio ---"

# Espelha o --perfil do workflow. As chaves antigas do banco (brasil,
# internacional e as vagas sem perfil, anteriores ao campo existir) são
# do radar de Dados/BI da autora original e não têm o que fazer nesta
# página — ficam no banco, fora da vitrine.
PERFIS_NA_PAGINA = ("dev", "admin", "agro", "analista")

# Rótulo por perfil. Não importado de core.perfis de propósito: aquele
# módulo carrega todos os scrapers (e o Playwright junto), coisa que um
# gerador de HTML não deveria arrastar só pra ler dois nomes.
ROTULOS = {"dev": "Dev", "admin": "Administrativo", "agro": "Agronomia", "analista": "Analista"}

_FUSO_BR = timezone(timedelta(hours=-3))


def _instante(bruto: str) -> datetime | None:
    """`encontrada_em` cru -> datetime com fuso, ou None se ilegível.

    O banco guarda em UTC sem marcar o fuso (CURRENT_TIMESTAMP do SQLite),
    e em dois formatos: com espaço ("2026-08-25 10:12:00", o do SQLite) e
    com T ("2026-08-25T10:12:00", quando o Python grava). fromisoformat
    aceita os dois; o que ele não faz é assumir UTC, daí o replace.
    """
    if not bruto:
        return None
    try:
        quando = datetime.fromisoformat(bruto)
    except ValueError:
        return None
    return quando.replace(tzinfo=timezone.utc) if quando.tzinfo is None else quando


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
    quando = _instante(bruto)
    if quando is None:
        return ""  # formato inesperado: melhor não mostrar nada do que mentir
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
            # Mesmo instante em epoch, pra página poder ORDENAR e filtrar
            # por período. A string acima não serve pra isso: ela não tem
            # ano ("25/08 07:12"), então comparar duas viradas de ano dá
            # resultado errado, e ordenar texto não é ordenar tempo.
            # 0 = sem data legível (fica fora dos filtros de período).
            "ts": _epoch(l["encontrada_em"] or ""),
            "pub": _rotulo_publicacao(l["publicado_em"] or ""),
            # Data de publicação em epoch, pra página filtrar por ela. É
            # independente de "ts" (quando NÓS achamos): anúncio de julho
            # pode ter entrado no banco ontem.
            "pts": _epoch_publicacao(l["publicado_em"] or "", _instante(l["encontrada_em"] or "")),
        }
        for l in linhas
    ]


def carregar_conteudo(db_path: str = "", perfil: str = PERFIL_CONTEUDO) -> tuple[list[dict], dict]:
    """(vagas com anúncio capturado, contagem) do perfil, mais recentes
    primeiro. Banco sem a tabela conteudo_vagas (anterior à captura) conta
    como nada capturado ainda, não como erro."""
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM vagas_vistas WHERE perfil = ?", (perfil,)
        ).fetchone()[0]
        try:
            linhas = conn.execute(
                """
                SELECT v.titulo, v.empresa, v.local, v.link, v.site, v.modalidade,
                       v.publicado_em, v.encontrada_em, c.texto
                FROM vagas_vistas v JOIN conteudo_vagas c ON c.id = v.id
                WHERE v.perfil = ? AND c.status = 'ok' AND c.texto != ''
                ORDER BY v.encontrada_em DESC
                """,
                (perfil,),
            ).fetchall()
            removidas = conn.execute(
                """
                SELECT COUNT(*) FROM vagas_vistas v JOIN conteudo_vagas c ON c.id = v.id
                WHERE v.perfil = ? AND c.status = 'indisponivel'
                """,
                (perfil,),
            ).fetchone()[0]
        except sqlite3.OperationalError:
            linhas, removidas = [], 0
    finally:
        conn.close()

    vagas = [dict(l) for l in linhas]
    contagem = {
        "total": total,
        "capturadas": len(vagas),
        "removidas": removidas,
        "pendentes": max(total - len(vagas) - removidas, 0),
    }
    return vagas, contagem


def montar_conteudo_txt(vagas: list[dict], contagem: dict, agora: datetime | None = None) -> str:
    agora = agora or datetime.now(_FUSO_BR)
    blocos = [
        "CONTEÚDO DAS VAGAS DE DEV — JobRadar\n"
        f"Gerado em {agora.strftime('%d/%m/%Y às %H:%M')} (Brasília). "
        f"{contagem['capturadas']} vaga(s) com anúncio capturado, de {contagem['total']} "
        "vagas Dev no radar. Mais recentes primeiro.\n"
        "Cada vaga traz o texto do anúncio como a fonte publicou (descrição, "
        "requisitos, diferenciais, benefícios)."
    ]
    for n, v in enumerate(vagas, 1):
        local = v["local"] or "—"
        if v["modalidade"]:
            local = f"{local} ({v['modalidade']})"
        fonte = v["site"] or "—"
        pub = _rotulo_publicacao(v["publicado_em"] or "")
        if pub:
            fonte += f" · publicada {pub}"
        achada = _quando_entrou(v["encontrada_em"] or "")
        if achada:
            fonte += f" · achada {achada}"
        blocos.append(
            SEPARADOR_VAGA.format(n=n, total=len(vagas)) + "\n"
            f"Título: {v['titulo'] or '—'}\n"
            f"Empresa: {v['empresa'] or '—'}\n"
            f"Local: {local}\n"
            f"Fonte: {fonte}\n"
            f"Link: {v['link']}\n"
            f"{MARCADOR_ANUNCIO}\n"
            f"{(v['texto'] or '').strip()}"
        )
    return "\n\n\n".join(blocos) + "\n"


def montar_html(vagas: list[dict], agora: datetime | None = None, conteudo: dict | None = None) -> str:
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
        .replace("__CONTEUDO__", json.dumps(conteudo or {"total": 0, "capturadas": 0, "removidas": 0, "pendentes": 0}))
        .replace("__ATUALIZADO__", html.escape(agora.strftime("%d/%m/%Y às %H:%M")))
    )


# Formatos de `publicado_em` que as fontes de fato usam, conferidos no
# banco: ISO do LinkedIn ("2026-07-22"), "Publicada em: 20/08/2026" e
# "Publicada em 18/08" (sem ano) da Gupy/Sólides, "há N dias|semanas|
# meses|anos" de várias, "hoje"/"ontem", e "27 ago" do InfoJobs.
_PUB_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_PUB_DMA = re.compile(r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?")
_PUB_RELATIVA = re.compile(r"h[áa]\s+(\d+)\s*(dia|semana|m[êe]s|mes|ano)", re.I)
_PUB_DIA_MES = re.compile(
    r"(\d{1,2})\s*(?:de\s+)?(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)", re.I
)
_MESES = {m: i for i, m in enumerate(
    ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"], 1
)}
_DIAS_POR_UNIDADE = {"dia": 1, "semana": 7, "mes": 30, "mês": 30, "mes_": 30, "ano": 365}


def _epoch_publicacao(bruto: str, referencia: datetime | None) -> int:
    """`publicado_em` (o que a FONTE anuncia) em epoch, ou 0 se ilegível.

    Data relativa ("há 28 dias") é resolvida contra `referencia` — o
    instante em que NÓS achamos a vaga —, não contra agora. A diferença
    importa e cresce: uma vaga achada em agosto dizendo "há 2 dias" foi
    publicada em agosto, e calcular isso a partir de hoje a jogaria semanas
    pra frente. Como a página é regerada a cada ciclo, o valor calculado a
    partir de agora também MUDARIA a cada regeração, para a mesma vaga.

    0 (ilegível ou vazio) fica fora de qualquer janela do filtro: dizer que
    uma vaga sem data é das últimas 24h seria inventar.
    """
    texto = (bruto or "").strip()
    if not texto:
        return 0
    base = referencia or datetime.now(timezone.utc)

    iso = _PUB_ISO.search(texto)
    if iso:
        try:
            return int(datetime(*map(int, iso.groups()), tzinfo=timezone.utc).timestamp())
        except ValueError:
            return 0

    rel = _PUB_RELATIVA.search(texto)
    if rel:
        unidade = _normalizar_unidade(rel.group(2))
        return int((base - timedelta(days=int(rel.group(1)) * _DIAS_POR_UNIDADE[unidade])).timestamp())

    norm = texto.lower()
    if "hoje" in norm or "agora" in norm:
        return int(base.timestamp())
    if "ontem" in norm:
        return int((base - timedelta(days=1)).timestamp())

    dma = _PUB_DMA.search(texto)
    if dma:
        dia, mes, ano = dma.group(1), dma.group(2), dma.group(3)
        return _montar_data(int(dia), int(mes), ano, base)

    dia_mes = _PUB_DIA_MES.search(texto)
    if dia_mes:
        return _montar_data(int(dia_mes.group(1)), _MESES[dia_mes.group(2).lower()[:3]], None, base)

    return 0


def _normalizar_unidade(bruta: str) -> str:
    u = bruta.lower()
    return "mes" if u.startswith("m") else u


def _montar_data(dia: int, mes: int, ano: str | None, base: datetime) -> int:
    """Monta a data; sem ano, usa o que NÃO joga a publicação no futuro.

    "Publicada em 18/08" não diz o ano. Assumir o ano da referência erra
    na virada: vaga achada em 02/janeiro dizendo "28/12" é de dezembro do
    ano anterior, não de dezembro do ano que vem.
    """
    if ano:
        a = int(ano)
        a += 2000 if a < 100 else 0
    else:
        a = base.year
    try:
        data = datetime(a, mes, dia, tzinfo=timezone.utc)
    except ValueError:
        return 0
    if not ano and data > base + timedelta(days=1):
        try:
            data = datetime(a - 1, mes, dia, tzinfo=timezone.utc)
        except ValueError:
            return 0
    return int(data.timestamp())


def _rotulo_publicacao(bruto: str) -> str:
    """Texto da data como vai pra página. Tira o "Publicada em:" que a Gupy
    e a Sólides já trazem embutido — a página põe o rótulo "publicada"
    antes do valor, e sem isso sai "publicada Publicada em: 01/10/2026"."""
    return re.sub(r"^\s*publicad[oa]\s*(em)?\s*:?\s*", "", bruto or "", flags=re.I).strip()


def _epoch(bruto: str) -> int:
    """Segundos desde 1970 (UTC) — 0 quando a data não é legível."""
    quando = _instante(bruto)
    return int(quando.timestamp()) if quando else 0


def gerar(db_path: str = "", saida: str = "") -> int:
    saida = saida or SAIDA
    # Sempre ao lado do index.html: a aba carrega o .txt por caminho relativo.
    saida_conteudo = os.path.join(os.path.dirname(saida), os.path.basename(SAIDA_CONTEUDO))
    vagas = carregar_vagas(db_path)
    com_conteudo, contagem = carregar_conteudo(db_path)
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        f.write(montar_html(vagas, conteudo=contagem))
    with open(saida_conteudo, "w", encoding="utf-8") as f:
        f.write(montar_conteudo_txt(com_conteudo, contagem))
    return len(vagas)


if __name__ == "__main__":
    total = gerar()
    print(f"docs/index.html gerado com {total} vaga(s); docs/conteudo-dev.txt junto.")
