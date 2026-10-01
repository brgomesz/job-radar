"""Testes do gerador da página pública (web/gerar.py).

A página é commitada e servida pelo GitHub Pages a cada ciclo, sem
ninguém olhando — então o que precisa estar travado é o que quebraria em
silêncio e só apareceria como página em branco:

  - título de vaga com "</script>" fechando a tag no meio do JSON;
  - aspas e acento em nome de empresa;
  - vaga dos perfis antigos (Dados/BI) vazando pra vitrine;
  - marcador do template sobrando por troca de nome.
"""

import json
import re
import sqlite3

import pytest

from web.gerar import carregar_vagas, gerar, montar_html


def _banco(tmp_path, linhas):
    caminho = str(tmp_path / "jobs.db")
    conn = sqlite3.connect(caminho)
    conn.execute(
        """CREATE TABLE vagas_vistas (
            id TEXT, titulo TEXT, empresa TEXT, local TEXT, link TEXT, site TEXT,
            encontrada_em TEXT, relevancia INTEGER, perfil TEXT, modalidade TEXT,
            publicado_em TEXT
        )"""
    )
    conn.executemany(
        "INSERT INTO vagas_vistas (id,titulo,empresa,local,link,site,encontrada_em,"
        "relevancia,perfil,modalidade,publicado_em) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        linhas,
    )
    conn.commit()
    conn.close()
    return caminho


def _linha(titulo, perfil="dev", relevancia=8, empresa="Empresa", quando="2026-08-25T10:00:00"):
    return (
        f"id-{titulo}", titulo, empresa, "Joinville, SC", f"https://x.invalido/{relevancia}",
        "LinkedIn", quando, relevancia, perfil, "Remoto", "há 1 dia",
    )


def test_so_traz_perfis_em_producao(tmp_path):
    db = _banco(tmp_path, [
        _linha("Desenvolvedor Back-end", perfil="dev"),
        _linha("Analista Financeiro", perfil="admin"),
        _linha("Analista de Dados", perfil="brasil"),
        _linha("Data Analyst", perfil="internacional"),
        (None, "Vaga antiga", "X", "", "u", "s", "2026-08-07T00:00:00", 6, None, "", ""),
    ])
    titulos = [v["t"] for v in carregar_vagas(db)]
    assert titulos == ["Desenvolvedor Back-end", "Analista Financeiro"]


def test_ordena_por_nota_e_depois_pela_mais_recente(tmp_path):
    db = _banco(tmp_path, [
        _linha("nota 6", relevancia=6),
        _linha("nota 9 antiga", relevancia=9, quando="2026-08-24T10:00:00"),
        _linha("nota 9 nova", relevancia=9, quando="2026-08-25T10:00:00"),
        _linha("nota 8", relevancia=8),
    ])
    assert [v["t"] for v in carregar_vagas(db)] == [
        "nota 9 nova", "nota 9 antiga", "nota 8", "nota 6",
    ]


def test_titulo_com_fecha_script_nao_quebra_a_pagina(tmp_path):
    """O caso que derrubaria a página inteira: sem escapar "</", esse
    título fecharia o <script> no meio do JSON e nada renderizaria."""
    db = _banco(tmp_path, [_linha("Dev </script><b>oi</b>")])
    pagina = montar_html(carregar_vagas(db))

    assert "</script><b>oi</b>" not in pagina
    assert "<\\/script>" in pagina
    # Um <script> aberto e um fechado: a tag continua íntegra.
    assert pagina.count("</script>") == 1


def test_json_continua_valido_com_aspas_e_acento(tmp_path):
    db = _banco(tmp_path, [_linha('Dev "Pleno"', empresa="Ação & Cia")])
    pagina = montar_html(carregar_vagas(db))

    bruto = re.search(r"const VAGAS = (\[.*?\]);", pagina, re.S).group(1)
    dados = json.loads(bruto.replace("<\\/", "</"))
    assert dados[0]["t"] == 'Dev "Pleno"'
    assert dados[0]["e"] == "Ação & Cia"


def test_nenhum_marcador_do_template_sobra(tmp_path):
    db = _banco(tmp_path, [_linha("Desenvolvedor Back-end")])
    pagina = montar_html(carregar_vagas(db))
    assert "__DADOS__" not in pagina
    assert "__ATUALIZADO__" not in pagina


def test_gerar_escreve_o_arquivo_e_conta_as_vagas(tmp_path):
    db = _banco(tmp_path, [_linha("A"), _linha("B", perfil="admin")])
    saida = tmp_path / "sub" / "index.html"

    assert gerar(db, str(saida)) == 2
    assert "Radar de Vagas" in saida.read_text(encoding="utf-8")


def test_banco_vazio_gera_pagina_valida(tmp_path):
    """Página sem vaga nenhuma ainda tem que ser uma página — não erro."""
    db = _banco(tmp_path, [])
    saida = tmp_path / "index.html"
    assert gerar(db, str(saida)) == 0
    assert "const VAGAS = [];" in saida.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# "achada em": quando a vaga entrou no NOSSO banco
# ---------------------------------------------------------------------------

def test_hora_de_entrada_sai_no_fuso_de_brasilia(tmp_path):
    """O banco guarda UTC (CURRENT_TIMESTAMP do SQLite + runner em UTC).
    Sem converter, uma vaga achada às 7h da manhã apareceria como 10h."""
    db = _banco(tmp_path, [_linha("Dev", quando="2026-08-25T10:12:00")])
    assert carregar_vagas(db)[0]["d"] == "25/08 07:12"


def test_formato_do_sqlite_com_espaco_tambem_converte(tmp_path):
    """CURRENT_TIMESTAMP grava "YYYY-MM-DD HH:MM:SS", com espaço em vez de
    T -- é o formato da maioria das linhas reais do banco."""
    db = _banco(tmp_path, [_linha("Dev", quando="2026-08-25 00:30:00")])
    assert carregar_vagas(db)[0]["d"] == "24/08 21:30"


@pytest.mark.parametrize("bruto", ["", "ontem", "25/08/2026"])
def test_data_ilegivel_vira_vazio_em_vez_de_erro(tmp_path, bruto):
    """Melhor não mostrar nada do que mostrar hora errada -- e a página
    inteira não pode quebrar por causa de uma linha estranha."""
    db = _banco(tmp_path, [_linha("Dev", quando=bruto)])
    assert carregar_vagas(db)[0]["d"] == ""


def test_pagina_rotula_as_duas_datas(tmp_path):
    """Sem rótulo viravam duas datas soltas na mesma linha."""
    db = _banco(tmp_path, [_linha("Dev")])
    pagina = montar_html(carregar_vagas(db))
    assert "achada ${esc(v.d)}" in pagina or "achada" in pagina
    assert "publicada" in pagina


# ---------------------------------------------------------------------------
# Data de PUBLICAÇÃO (o que a fonte anuncia), para o filtro da página
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta, timezone  # noqa: E402

from web.gerar import _epoch_publicacao  # noqa: E402

_REF = datetime(2026, 9, 13, 12, 0, tzinfo=timezone.utc)


def _data(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%d/%m/%Y")


CASOS_PUBLICACAO = [
    # Formatos conferidos no banco real, um por fonte
    ("iso-linkedin", "2026-07-22", "22/07/2026"),
    ("gupy-com-ano", "Publicada em: 20/08/2026", "20/08/2026"),
    ("gupy-sem-ano", "Publicada em 18/08", "18/08/2026"),
    ("infojobs-dia-mes", "27 ago", "27/08/2026"),
    ("por-extenso", "11 de agosto de 2026", "11/08/2026"),
    # Relativas: contadas a partir de quando NÓS achamos a vaga
    ("relativa-dias", "há 3 dias", "10/09/2026"),
    ("relativa-semanas", "há 2 semanas", "30/08/2026"),
    ("relativa-meses", "Há 1 mês", "14/08/2026"),
    ("hoje", "hoje", "13/09/2026"),
    ("ontem", "ontem", "12/09/2026"),
]


@pytest.mark.parametrize(
    "nome,bruto,esperado", CASOS_PUBLICACAO, ids=[c[0] for c in CASOS_PUBLICACAO]
)
def test_epoch_publicacao(nome, bruto, esperado):
    assert _data(_epoch_publicacao(bruto, _REF)) == esperado


def test_data_sem_ano_na_virada_nao_vai_pro_futuro():
    """Vaga achada em 02/janeiro dizendo "28/12" é de dezembro do ano
    ANTERIOR. Assumir o ano da referência jogaria a publicação 11 meses
    pra frente."""
    ref = datetime(2026, 1, 2, tzinfo=timezone.utc)
    assert _data(_epoch_publicacao("Publicada em 28/12", ref)) == "28/12/2025"


def test_relativa_usa_quando_achamos_nao_agora():
    """A página é regerada a cada ciclo. Calculando "há 2 dias" a partir de
    agora, a MESMA vaga mudaria de data de publicação a cada regeração."""
    antiga = datetime(2026, 1, 10, tzinfo=timezone.utc)
    assert _data(_epoch_publicacao("há 2 dias", antiga)) == "08/01/2026"


@pytest.mark.parametrize("bruto", ["", "em breve", "confira", "R$ 3.000"])
def test_publicacao_ilegivel_vira_zero(bruto):
    """0 deixa a vaga fora de qualquer janela do filtro — dizer que uma
    vaga sem data é das últimas 24h seria inventar."""
    assert _epoch_publicacao(bruto, _REF) == 0


def test_carregar_vagas_traz_plataforma_e_data_de_publicacao(tmp_path):
    """Os dois campos que os filtros novos consomem."""
    db = _banco(tmp_path, [_linha("Dev")])
    v = carregar_vagas(db)[0]
    assert v["s"] == "LinkedIn"
    assert v["pts"] > 0


def test_pagina_tem_os_dois_filtros(tmp_path):
    db = _banco(tmp_path, [_linha("Dev")])
    pagina = montar_html(carregar_vagas(db))
    assert 'id="selPlataforma"' in pagina
    assert 'id="segPublicada"' in pagina


@pytest.mark.parametrize("bruto,esperado", [
    ("Publicada em: 01/10/2026", "01/10/2026"),
    ("Publicada em 18/08", "18/08"),
    ("publicado em: hoje", "hoje"),
    ("2026-09-17", "2026-09-17"),
    ("há 3 dias", "há 3 dias"),
])
def test_rotulo_publicacao_nao_duplica_a_palavra(bruto, esperado):
    """A página escreve "publicada" antes do valor; a Gupy e a Sólides já
    mandam "Publicada em:" embutido, e saía "publicada Publicada em:"."""
    from web.gerar import _rotulo_publicacao
    assert _rotulo_publicacao(bruto) == esperado
