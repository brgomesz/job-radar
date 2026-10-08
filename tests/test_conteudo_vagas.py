"""Testes da captura do anúncio inteiro (aba "Conteúdo Dev").

A captura roda no runner, sem ninguém olhando, e o .txt vai direto pra uma
análise — então o que fica travado aqui é o que estragaria em silêncio:
  - vaga do LinkedIn abrindo a página errada (id mal extraído);
  - requisito em lista virando um parágrafo só;
  - vaga que falhou saindo da fila pra sempre, ou entrando nela de novo
    depois de capturada;
  - o separador do .txt e o do template divergindo (aba vazia).
"""

import re
import sqlite3

import pytest

import database.database as db
from scrapers.conteudo import descricao_jsonld, html_para_texto, url_para_abrir
from web.gerar import (
    MARCADOR_ANUNCIO,
    SEPARADOR_VAGA,
    TEMPLATE,
    carregar_conteudo,
    gerar,
    montar_conteudo_txt,
)

LONGO = "Experiência com Node.js e TypeScript em produção. " * 5


def test_linkedin_abre_endpoint_guest_pelo_id():
    link = "https://br.linkedin.com/jobs/view/software-engineer-back-end-joinville-at-px-4442216252?refId=abc"
    assert url_para_abrir(link, "LinkedIn") == (
        "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4442216252"
    )


def test_outras_fontes_abrem_o_link_original():
    link = "https://vagas.solides.com.br/vaga/83265/desenvolvedor-back-end"
    assert url_para_abrir(link, "Solides") == link


def test_html_preserva_lista_de_requisitos():
    texto = html_para_texto("<p>Requisitos:</p><ul><li>Node.js</li><li>SQL &amp; NoSQL</li></ul>")
    assert texto == "Requisitos:\n\n- Node.js\n- SQL & NoSQL"


def test_jsonld_acha_jobposting_dentro_de_graph():
    script = (
        '{"@context":"https://schema.org","@graph":[{"@type":"Organization","name":"X"},'
        '{"@type":"JobPosting","description":"&lt;p&gt;' + LONGO + '&lt;/p&gt;"}]}'
    )
    assert descricao_jsonld(["isto não é json", script]).startswith("Experiência com Node.js")


def test_jsonld_curto_demais_nao_conta():
    assert descricao_jsonld(['{"@type":"JobPosting","description":"Vaga."}']) == ""


@pytest.fixture
def banco(tmp_path, monkeypatch):
    caminho = str(tmp_path / "jobs.db")
    monkeypatch.setattr(db, "DB_PATH", caminho)
    db.iniciar_db()
    with sqlite3.connect(caminho) as conn:
        conn.executemany(
            "INSERT INTO vagas_vistas (id, titulo, empresa, local, link, site, perfil, "
            "modalidade, publicado_em, encontrada_em) VALUES (?,?,?,?,?,?,?,?,?,?)",
            [
                ("a", "Dev Node Pleno", "Acme", "Joinville, SC", "https://x/a", "Gupy", "dev",
                 "Remoto", "Publicada em: 01/10/2026", "2026-10-01 12:00:00"),
                ("b", "Back-end TS", "Beta", "Brasil", "https://x/b", "LinkedIn", "dev",
                 "", "", "2026-10-02 12:00:00"),
                ("c", "Analista Financeiro", "Gama", "Joinville", "https://x/c", "Gupy", "admin",
                 "", "", "2026-10-03 12:00:00"),
            ],
        )
    return caminho


def test_fila_so_do_perfil_e_mais_recente_primeiro(banco):
    assert [l[0] for l in db.vagas_sem_conteudo("dev", 10, 3)] == ["b", "a"]


def test_capturada_sai_da_fila_e_falha_volta_ate_o_limite(banco):
    db.salvar_conteudo("a", "ok", LONGO, "seletor")
    for _ in range(2):
        db.salvar_conteudo("b", "falhou")
    assert [l[0] for l in db.vagas_sem_conteudo("dev", 10, 3)] == ["b"]
    db.salvar_conteudo("b", "falhou")
    assert db.vagas_sem_conteudo("dev", 10, 3) == []


def test_falha_depois_nao_apaga_texto_capturado(banco):
    db.salvar_conteudo("a", "ok", LONGO, "seletor")
    db.salvar_conteudo("a", "falhou")
    with sqlite3.connect(banco) as conn:
        assert conn.execute("SELECT texto FROM conteudo_vagas WHERE id='a'").fetchone()[0] == LONGO


def test_txt_traz_cabecalho_de_cada_vaga_e_o_anuncio(banco):
    db.salvar_conteudo("a", "ok", LONGO, "seletor")
    db.salvar_conteudo("b", "indisponivel")
    vagas, contagem = carregar_conteudo(banco)
    assert contagem == {"total": 2, "capturadas": 1, "removidas": 1, "pendentes": 0}
    txt = montar_conteudo_txt(vagas, contagem)
    assert SEPARADOR_VAGA.format(n=1, total=1) in txt
    assert "Título: Dev Node Pleno\nEmpresa: Acme\nLocal: Joinville, SC (Remoto)\n" in txt
    assert "publicada 01/10/2026" in txt
    assert f"{MARCADOR_ANUNCIO}\n{LONGO.strip()}" in txt
    assert "Analista Financeiro" not in txt


def test_separador_do_txt_bate_com_o_do_template():
    """A aba divide o .txt com uma regex própria; se o gerador mudar o
    separador sozinho, a aba abre vazia sem erro nenhum."""
    modelo = open(TEMPLATE, encoding="utf-8").read()
    regex_js = re.search(r"const SEPARADOR = /(.+)/m;", modelo).group(1)
    assert re.fullmatch(regex_js, SEPARADOR_VAGA.format(n=12, total=340))
    assert MARCADOR_ANUNCIO in modelo


def test_banco_sem_tabela_de_conteudo_gera_txt_vazio(tmp_path):
    caminho = str(tmp_path / "jobs.db")
    with sqlite3.connect(caminho) as conn:
        conn.execute(
            "CREATE TABLE vagas_vistas (id TEXT, titulo TEXT, empresa TEXT, local TEXT, link TEXT,"
            " site TEXT, encontrada_em TEXT, relevancia INTEGER, perfil TEXT, modalidade TEXT,"
            " publicado_em TEXT)"
        )
    saida = tmp_path / "docs" / "index.html"
    gerar(caminho, str(saida))
    txt = (tmp_path / "docs" / "conteudo-dev.txt").read_text(encoding="utf-8")
    assert "0 vaga(s) com anúncio capturado" in txt
    assert '"capturadas": 0' in saida.read_text(encoding="utf-8")


TELA_ANTIBOT = (
    "weworkremotely.com\nPerforming security verification\n\nThis website uses a security "
    "service to protect against malicious bots. This page is displayed while the website "
    "verifies you are not a bot."
)


def test_tela_de_antibot_nao_conta_como_anuncio():
    from scrapers.conteudo import parece_bloqueio
    assert parece_bloqueio(TELA_ANTIBOT)
    assert not parece_bloqueio(LONGO)
    # Anúncio longo que cita captcha no meio continua valendo.
    assert not parece_bloqueio(LONGO * 10 + " integração com reCAPTCHA ")


def test_texto_de_bloqueio_ja_gravado_volta_pra_fila(banco):
    from scrapers.conteudo import parece_bloqueio
    db.salvar_conteudo("a", "ok", TELA_ANTIBOT, "pagina")
    db.salvar_conteudo("b", "ok", LONGO, "seletor")
    assert db.reabrir_conteudo_bloqueado("dev", parece_bloqueio) == 1
    assert [l[0] for l in db.vagas_sem_conteudo("dev", 10, 3)] == ["a"]
