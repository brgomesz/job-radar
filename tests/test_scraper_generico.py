"""Testes do extrator genérico (scrapers/generico.py).

A extração roda sobre âncoras já colhidas da página — dicionário com href,
texto do link e texto do card em volta. Isso é função pura: dá pra testar
sem abrir browser e sem tocar em rede, que é exatamente a parte que
importa, porque é onde mora o risco de uma fonte devolver zero em silêncio.

O que cada grupo trava:
  - o padrão de link é o que separa vaga de menu e rodapé;
  - a localidade sai por PADRÃO "Cidade - UF", não por posição de
    parágrafo, e é ela que decide se a vaga passa no filtro de cidade;
  - UF inventada ("Node - JS", "Pleno/SR") não pode virar localidade.
"""

import pytest

from scrapers.generico import (
    FonteHTML,
    ScraperGenerico,
    extrair_empresa,
    extrair_local,
    extrair_modalidade,
    formatar_termo,
)


class _FonteTeste(ScraperGenerico):
    fonte = FonteHTML(
        nome="Teste",
        base_url="https://portal.invalido",
        url_busca="https://portal.invalido/vagas-de-{termo}",
        padrao_link=r"/vagas/v\d+",
    )


def _ancora(href, texto, caixa=""):
    return {"href": href, "texto": texto, "caixa": caixa}


# ---------------------------------------------------------------------------
# Localidade — o campo de que o filtro depende
# ---------------------------------------------------------------------------

CASOS_LOCAL = [
    ("hifen", "Analista Financeiro\nEmpresa X\nJoinville - SC", "Joinville - SC"),
    ("barra", "Vaga boa\nCuritiba/PR\nefetivo", "Curitiba - PR"),
    ("virgula", "Vaga\nPonta Grossa, PR", "Ponta Grossa - PR"),
    ("nome-composto", "Vaga\nSão José dos Pinhais - PR", "São José dos Pinhais - PR"),
    ("acento", "Vaga\nSão Paulo - SP", "São Paulo - SP"),
    ("uf-minuscula", "Vaga\nBlumenau - sc", "Blumenau - SC"),
    # Lixo grudado antes do nome da cidade
    ("com-salario-antes", "R$ 4.000 | Joinville - SC", "Joinville - SC"),
    # UF que não existe: não pode virar localidade
    ("stack-nao-e-uf", "Desenvolvedor Node - JS\nRemoto", ""),
    ("nivel-nao-e-uf", "Analista Pleno/SR\nHíbrido", ""),
    ("sem-local", "Analista de Dados\nEmpresa Y\nRemoto", ""),
]


@pytest.mark.parametrize("nome,texto,esperado", CASOS_LOCAL, ids=[c[0] for c in CASOS_LOCAL])
def test_extrair_local(nome, texto, esperado):
    assert extrair_local(texto) == esperado


# ---------------------------------------------------------------------------
# Modalidade
# ---------------------------------------------------------------------------

CASOS_MODALIDADE = [
    ("remoto", "Vaga 100% Remoto", "Remoto"),
    ("home-office", "Analista - Home Office", "Remoto"),
    ("hibrido", "Analista\nHíbrido\nJoinville - SC", "Híbrido"),
    ("presencial", "Analista\nPresencial", "Presencial"),
    ("nada", "Analista Financeiro\nJoinville - SC", ""),
    # Remoto ganha de híbrido: o filtro trata híbrido e presencial igual,
    # então o rótulo mais útil pro usuário é o remoto.
    ("remoto-ganha", "Híbrido com trabalho remoto 3x", "Remoto"),
]


@pytest.mark.parametrize("nome,texto,esperado", CASOS_MODALIDADE, ids=[c[0] for c in CASOS_MODALIDADE])
def test_extrair_modalidade(nome, texto, esperado):
    assert extrair_modalidade(texto) == esperado


# ---------------------------------------------------------------------------
# Empresa — heurística, mas não pode devolver rótulo de interface
# ---------------------------------------------------------------------------

def test_empresa_pega_a_linha_util():
    texto = "Analista Financeiro\nTecnoplanta Ltda\nJoinville - SC\nHá 2 dias"
    assert extrair_empresa(texto, "Analista Financeiro", "Joinville - SC") == "Tecnoplanta Ltda"


CASOS_EMPRESA_RUIM = [
    ("so-titulo-e-local", "Analista Financeiro\nJoinville - SC"),
    ("so-rotulos", "Analista Financeiro\nR$ 5.000\nCandidatar-se\nHá 3 dias"),
]


@pytest.mark.parametrize("nome,texto", CASOS_EMPRESA_RUIM, ids=[c[0] for c in CASOS_EMPRESA_RUIM])
def test_empresa_nao_inventa(nome, texto):
    """Rótulo de interface e faixa salarial não são nome de empresa — na
    dúvida, "Não informado"."""
    assert extrair_empresa(texto, "Analista Financeiro", "Joinville - SC") == "Não informado"


# ---------------------------------------------------------------------------
# Padrão de link — separa vaga de menu, rodapé e "vagas relacionadas"
# ---------------------------------------------------------------------------

def test_so_link_de_vaga_vira_job():
    ancoras = [
        _ancora("/vagas/v1234567", "Desenvolvedor Back-end", "Desenvolvedor Back-end\nACME\nJoinville - SC"),
        _ancora("/sobre-nos", "Sobre nós"),
        _ancora("/vagas-de-analista", "Vagas de analista"),
        _ancora("https://facebook.com/portal", "Facebook"),
    ]
    vagas = _FonteTeste([]).extrair_da_pagina(ancoras)
    assert [v.titulo for v in vagas] == ["Desenvolvedor Back-end"]
    assert vagas[0].link == "https://portal.invalido/vagas/v1234567"
    assert vagas[0].local == "Joinville - SC"
    assert vagas[0].site == "Teste"


def test_mesma_vaga_em_duas_ancoras_entra_uma_vez():
    """Card costuma ter dois links pra mesma vaga (título e botão). Sem
    deduplicar por link, a fonte reporta o dobro do que achou."""
    ancoras = [
        _ancora("/vagas/v99", "Analista Financeiro", "Analista Financeiro\nX\nCuritiba - PR"),
        _ancora("/vagas/v99#candidatar", "Analista Financeiro", "Analista Financeiro\nX\nCuritiba - PR"),
    ]
    assert len(_FonteTeste([]).extrair_da_pagina(ancoras)) == 1


def test_ancora_sem_titulo_util_e_ignorada():
    """Link de imagem ou botão "Ver" aponta pra vaga mas não tem título."""
    ancoras = [_ancora("/vagas/v1", ""), _ancora("/vagas/v2", "Ver")]
    assert _FonteTeste([]).extrair_da_pagina(ancoras) == []


def test_vaga_sem_local_nao_e_descartada_pelo_extrator():
    """Quem decide por localidade é o filtro do perfil, não o scraper — a
    vaga sai daqui com "Não informado" e é o filtro que rejeita."""
    vagas = _FonteTeste([]).extrair_da_pagina([_ancora("/vagas/v7", "Analista de Dados", "Analista de Dados\nACME")])
    assert vagas[0].local == "Não informado"


# ---------------------------------------------------------------------------
# Formato do termo na URL
# ---------------------------------------------------------------------------

CASOS_SLUG = [
    ("hifen", "hifen", "analista-de-dados"),
    ("mais", "mais", "analista+de+dados"),
    ("query", "query", "analista%20de%20dados"),
]


@pytest.mark.parametrize("nome,estilo,esperado", CASOS_SLUG, ids=[c[0] for c in CASOS_SLUG])
def test_formatar_termo(nome, estilo, esperado):
    assert formatar_termo("Analista de Dados", estilo) == esperado


def test_slug_hifen_tira_pontuacao():
    """"next.js" e "node.js" viram parte da URL — ponto quebra caminho em
    alguns portais."""
    assert formatar_termo("Next.js", "hifen") == "nextjs"


# ---------------------------------------------------------------------------
# As candidatas continuam FORA de produção
# ---------------------------------------------------------------------------

def test_candidatas_nao_estao_em_nenhum_perfil():
    """Fonte nova só entra no ciclo depois de medida pela sonda. Se alguém
    ligar uma sem medir, este teste avisa."""
    from core.perfis import PERFIS
    from scrapers.nacionais import CANDIDATAS

    candidatas = {c.__name__ for c in CANDIDATAS}
    for perfil in PERFIS.values():
        usados = {d.classe.__name__ for d in perfil.definicao_scrapers}
        assert not (usados & candidatas), (
            f"O perfil '{perfil.chave}' já usa {usados & candidatas}. "
            "Rodar scripts/sondar_fontes.py antes de promover, e atualizar este teste."
        )
