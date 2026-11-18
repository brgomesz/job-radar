"""Testes das fontes por API/feed (scrapers/remotos.py) e das consultorias
de scrapers/nacionais.py.

Nada aqui toca rede: a montagem da vaga a partir do item da API é função
pura, e é ela que decide o que o filtro do perfil vai ver — principalmente
`local`, de onde sai o escopo (país) da vaga remota.

O que cada grupo trava:
  - região "qualquer lugar" vira escopo vazio (aceita), região restrita
    vira o país — e "Remote, US" NÃO vira vaga mundial;
  - vaga dessas fontes é internacional: vai pro dev-intl, nunca pro
    dev-remoto;
  - nenhuma candidata está ligada a perfil de produção.
"""

import pytest

from core.job import Job
from core.perfis import PERFIL_DEV_INTL, PERFIL_DEV_REMOTO, PERFIS
from scrapers.generico import FonteHTML, ScraperGenerico, extrair_cidade_conhecida
from scrapers.remotos import (
    CANDIDATAS_REMOTAS,
    data_iso,
    local_remoto,
    montar_job_himalayas,
    montar_job_remoteok,
    montar_job_remotive,
    montar_jobs_wwr_rss,
    texto_limpo,
)


# ---------------------------------------------------------------------------
# Região -> local -> escopo
# ---------------------------------------------------------------------------

CASOS_REGIAO = [
    ("mundo", ["Anywhere in the World"], "Remote - Worldwide", set()),
    ("worldwide", ["Worldwide"], "Remote - Worldwide", set()),
    ("vazio", [], "Remote - Worldwide", set()),
    ("so-remote", ["Remote"], "Remote - Worldwide", set()),
    ("eua", ["USA Only"], "Remote - USA Only", {"Estados Unidos"}),
    # "Remote" não abre a vaga quando vem junto de um país.
    ("remote-us", ["Remote, US"], "Remote - US", {"Estados Unidos"}),
    ("americas", ["Americas Only"], "Remote - Americas (LATAM)", {"LATAM"}),
    ("lista", ["Brazil", "Argentina"], "Remote - Brazil, Argentina", {"Brasil", "Argentina"}),
    ("dict", [{"name": "Brazil"}], "Remote - Brazil", {"Brasil"}),
    ("europa", ["Europe Only"], "Remote - Europe Only", {"Europa"}),
]


@pytest.mark.parametrize("nome,regioes,local,escopo", CASOS_REGIAO, ids=[c[0] for c in CASOS_REGIAO])
def test_local_remoto(nome, regioes, local, escopo):
    assert local_remoto(regioes) == local
    vaga = Job(titulo="Full Stack Developer", empresa="", local=local, link="", site="Himalayas",
               modalidade="Remoto")
    assert vaga.escopo_remoto == escopo


def test_lista_longa_nao_corta_o_brasil():
    """A Himalayas chega a listar dezenas de países. O corte não pode
    levar o Brasil junto — é o país que decide se a vaga serve."""
    paises = ["Germany", "France", "Spain", "Italy", "Poland", "Romania", "Greece",
              "Austria", "Belgium", "Brazil"]
    local = local_remoto(paises)
    assert local.startswith("Remote - Brazil,")
    assert "Brasil" in Job(titulo="x", empresa="", local=local, link="", site="Himalayas",
                           modalidade="Remoto").escopo_remoto


@pytest.mark.parametrize("valor,esperado", [
    (1763424000, "2025-11-18"),
    (1763424000000, "2025-11-18"),
    ("2026-11-17T10:22:05", "2026-11-17"),
    ("Tue, 17 Nov 2026 10:00:00 +0000", "2026-11-17"),
    ("", ""),
    ("lixo", ""),
])
def test_data_iso(valor, esperado):
    assert data_iso(valor) == esperado


def test_texto_limpo_tira_html():
    assert texto_limpo("<p>Node.js &amp; <b>React</b></p>") == "Node.js & React"


# ---------------------------------------------------------------------------
# Montagem por fonte
# ---------------------------------------------------------------------------

def test_himalayas():
    vaga = montar_job_himalayas({
        "title": "Senior  Full Stack Engineer",
        "companyName": "Acme",
        "guid": "https://himalayas.app/companies/acme/jobs/full-stack",
        "applicationLink": "https://acme.com/apply",
        "locationRestrictions": ["Brazil", "Mexico"],
        "pubDate": 1763424000,
    })
    assert vaga.titulo == "Senior Full Stack Engineer"
    assert vaga.link == "https://himalayas.app/companies/acme/jobs/full-stack"
    assert vaga.local == "Remote - Brazil, Mexico"
    assert vaga.modalidade == "Remoto"
    assert vaga.site == "Himalayas"


def test_himalayas_sem_guid_usa_link_de_candidatura():
    vaga = montar_job_himalayas({"title": "Dev", "guid": "abc-123", "applicationLink": "https://x.com/a"})
    assert vaga.link == "https://x.com/a"


def test_item_sem_titulo_ou_link_e_descartado():
    assert montar_job_himalayas({"title": "", "guid": "https://h.app/j"}) is None
    assert montar_job_remotive({"title": "Dev", "url": ""}) is None
    assert montar_job_remoteok({"legal": "aviso da API"}) is None


def test_remotive():
    vaga = montar_job_remotive({
        "title": "Node.js Developer",
        "company_name": "Beta",
        "url": "https://remotive.com/remote-jobs/software-dev/node-1",
        "candidate_required_location": "Latin America",
        "publication_date": "2026-11-17T10:22:05",
    })
    assert (vaga.empresa, vaga.local, vaga.publicado_em) == ("Beta", "Remote - Latin America", "2026-11-17")


def test_remoteok():
    vaga = montar_job_remoteok({
        "position": "React Developer",
        "company": "Gamma",
        "url": "https://remoteok.com/remote-jobs/123",
        "location": "",
        "date": "2026-11-16T08:00:00+00:00",
    })
    assert (vaga.local, vaga.publicado_em, vaga.site) == ("Remote - Worldwide", "2026-11-16", "Remote OK")


RSS_WWR = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <item>
    <title>Acme: Full-Stack Developer (Node/React)</title>
    <region>Anywhere in the World</region>
    <link>https://weworkremotely.com/remote-jobs/acme-full-stack?utm=x</link>
    <pubDate>Tue, 17 Nov 2026 10:00:00 +0000</pubDate>
    <description>&lt;p&gt;Node.js e React&lt;/p&gt;</description>
  </item>
  <item>
    <title>Beta: Backend Engineer</title>
    <region>USA Only</region>
    <link>https://weworkremotely.com/remote-jobs/beta-backend</link>
  </item>
</channel></rss>"""


def test_wwr_rss():
    itens = montar_jobs_wwr_rss(RSS_WWR)
    assert [(v.empresa, v.titulo, v.local) for v, _ in itens] == [
        ("Acme", "Full-Stack Developer (Node/React)", "Remote - Worldwide"),
        ("Beta", "Backend Engineer", "Remote - USA Only"),
    ]
    assert itens[0][0].link == "https://weworkremotely.com/remote-jobs/acme-full-stack"
    assert itens[0][0].publicado_em == "2026-11-17"
    # Região de contratação é escopo de verdade aqui (diferente da busca
    # antiga, cujo `local` era a sede da empresa).
    assert itens[1][0].escopo_remoto == {"Estados Unidos"}


def test_rss_quebrado_nao_derruba():
    assert montar_jobs_wwr_rss("<html>Performing security verification</html") == []


# ---------------------------------------------------------------------------
# Perfil: tudo isso é vaga internacional
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("site", ["Himalayas", "Remotive", "Remote OK", "We Work Remotely RSS"])
def test_fontes_remotas_vao_pro_dev_intl_e_nao_pro_dev_remoto(site):
    vaga = Job(titulo="Full Stack Developer", empresa="Acme", local="Remote - Worldwide",
               link="https://x", site=site, modalidade="Remoto")
    assert vaga.vaga_internacional
    assert vaga.combina_com(PERFIL_DEV_INTL.regras)
    assert not vaga.combina_com(PERFIL_DEV_REMOTO.regras)


def test_dev_intl_barra_regiao_fora_da_lista():
    vaga = Job(titulo="Full Stack Developer", empresa="Acme", local=local_remoto(["Europe Only"]),
               link="https://x", site="Himalayas", modalidade="Remoto")
    assert not vaga.combina_com(PERFIL_DEV_INTL.regras)


# ---------------------------------------------------------------------------
# Cidade sem UF (consultorias)
# ---------------------------------------------------------------------------

def test_cidade_conhecida_sem_uf():
    assert extrair_cidade_conhecida("Gerente Financeiro\nJoinville\nPermanente") == "Joinville - SC"
    assert extrair_cidade_conhecida("Gerente Financeiro\nSão Paulo") == ""


class _ConsultoriaTeste(ScraperGenerico):
    fonte = FonteHTML(
        nome="Teste", base_url="https://c.invalido", url_busca="https://c.invalido/{termo}",
        padrao_link=r"/job-detail/", local_sem_uf=True,
    )


class _PortalTeste(ScraperGenerico):
    fonte = FonteHTML(
        nome="Teste", base_url="https://p.invalido", url_busca="https://p.invalido/{termo}",
        padrao_link=r"/job-detail/",
    )


def test_local_sem_uf_so_vale_pra_fonte_que_pede():
    ancora = {"href": "/job-detail/gerente/ref/1", "texto": "Gerente Financeiro",
              "caixa": "Gerente Financeiro\nJoinville\nPermanente"}
    assert _ConsultoriaTeste([]).extrair_da_pagina([ancora])[0].local == "Joinville - SC"
    assert _PortalTeste([]).extrair_da_pagina([ancora])[0].local == "Não informado"


# ---------------------------------------------------------------------------
# As candidatas continuam FORA de produção
# ---------------------------------------------------------------------------

def test_candidatas_remotas_nao_estao_em_nenhum_perfil():
    """Mesma trava de tests/test_scraper_generico.py, pras fontes de API:
    entram no ciclo só depois de medidas pela bancada."""
    candidatas = {c.__name__ for c in CANDIDATAS_REMOTAS}
    for perfil in PERFIS.values():
        usados = {d.classe.__name__ for d in perfil.definicao_scrapers}
        assert not (usados & candidatas), (
            f"O perfil '{perfil.chave}' já usa {usados & candidatas}. "
            "Rodar scripts/sondar_fontes.py antes de promover, e atualizar este teste."
        )


def test_bancada_conhece_todas_as_candidatas():
    from scripts.sondar_fontes import CANDIDATAS
    from scrapers.nacionais import CANDIDATAS as HTML

    assert set(HTML) | set(CANDIDATAS_REMOTAS) == set(CANDIDATAS)


def test_erro_de_rede_num_feed_nao_derruba_os_outros(monkeypatch):
    """Um feed fora do ar (ou um termo que estoura) tira só aquela
    chamada; a fonte devolve o que os outros trouxeram."""
    import requests

    from scrapers import remotos

    monkeypatch.setattr(remotos, "PAUSA_ENTRE_CHAMADAS_S", 0)

    class _Resposta:
        status_code, url, content = 200, "https://wwr", b"x"
        headers = {"content-type": "application/rss+xml"}
        text = RSS_WWR

    chamadas = []

    def falso_get(url, params=None, timeout=None):
        chamadas.append(url)
        if len(chamadas) == 1:
            raise requests.ConnectionError("fora do ar")
        return _Resposta()

    scraper = remotos.WeWorkRemotelyRssScraper([])
    monkeypatch.setattr(scraper._sessao, "get", falso_get)
    vagas = scraper.buscar_vagas()
    assert len(chamadas) == len(remotos.FEEDS_WWR)
    assert len(vagas) == 2  # os dois feeds que responderam trazem as mesmas 2 vagas
    assert any("erro de rede" in linha for linha in scraper.diagnostico)
