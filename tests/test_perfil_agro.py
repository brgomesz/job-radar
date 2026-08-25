"""Testes do perfil agro (core/config_agro.py) — agronomia, assistência
técnica, RTV, sementes e fertilizantes, em SC e PR.

O que este arquivo trava:

  - os QUATRO cargos que o usuário declarou (assistência técnica ao
    produtor rural, RTV, qualidade em fertilizantes e produção em UBS)
    entram cada um por um caminho diferente do filtro; mexer numa lista
    pode derrubar um deles sem tocar nos outros;
  - a regra de estado: SC e PR inteiros valem, e as fontes escrevem o
    estado de duas formas ("Joinville - SC" e "Joinville, Santa Catarina,
    Brazil"). Se uma das grafias sair da lista, metade do estado some;
  - "campo" ficou FORA dos qualificadores de propósito — se alguém
    adicionar, "Técnico de Campo" de telecom entra junto;
  - liderança pontua como alvo aqui (dois dos quatro cargos são gerência),
    ao contrário do padrão global.
"""

import pytest

from core.job import Job
from core.perfis import PERFIL_ADM, PERFIL_AGRO, PERFIL_DEV


def _job(titulo: str, local: str = "Curitiba - PR", modalidade: str = "Presencial") -> Job:
    return Job(
        titulo=titulo, empresa="Teste", local=local,
        link="https://teste.invalido/vaga", site="Teste", modalidade=modalidade,
    )


# ---------------------------------------------------------------------------
# Os quatro alvos declarados
# ---------------------------------------------------------------------------

CASOS_ALVOS = [
    # 1. Assistência técnica ao produtor rural
    ("assistencia-tecnica", "Assistente Técnico Agrícola", True),
    ("consultor-agronomico", "Consultor Agronômico", True),
    ("engenheiro-agronomo", "Engenheiro Agrônomo", True),
    ("agronoma-feminino", "Engenheira Agrônoma", True),
    # 2. RTV / vendas técnicas
    ("rtv-sigla", "RTV Pleno", True),
    ("representante-tecnico", "Representante Técnico de Vendas", True),
    ("vendedor-tecnico", "Vendedor Técnico Agrícola", True),
    # 3. Qualidade em fertilizantes
    ("qualidade-fertilizantes", "Gerente de Qualidade - Fertilizantes", True),
    ("analista-fertilizantes", "Analista de Fertilizantes", True),
    # 4. Produção / beneficiamento de sementes
    ("ubs", "Gerente de Produção - Beneficiamento de Sementes", True),
    ("analista-sementes", "Analista de Sementes", True),
    ("producao-sementes", "Coordenador de Produção de Sementes", True),

    # Correlatas
    ("supervisor-agricola", "Supervisor Agrícola", True),
    ("gerente-fazenda", "Gerente de Fazenda", True),
    ("tecnico-agricola", "Técnico Agrícola", True),

    # Cargo genérico sem a área junto: não basta.
    ("gerente-qualidade-sozinho", "Gerente de Qualidade", False),
    ("analista-sozinho", "Analista Pleno", False),
    ("coordenador-producao-sozinho", "Coordenador de Produção", False),
    # Fora da área
    ("dev", "Desenvolvedor Back-end", False),
    ("financeiro", "Analista Financeiro", False),
]


@pytest.mark.parametrize("nome,titulo,esperado", CASOS_ALVOS, ids=[c[0] for c in CASOS_ALVOS])
def test_cargo_perfil_agro(nome, titulo, esperado):
    assert _job(titulo).combina_com(PERFIL_AGRO.regras) == esperado


def test_campo_nao_e_qualificador():
    """"Técnico de Campo" e "Analista de Campo" são cargos de telecom,
    energia e pesquisa de mercado. Se "campo" virar qualificador, o radar
    dele enche disso."""
    assert not _job("Técnico de Campo").combina_com(PERFIL_AGRO.regras)
    assert not _job("Analista de Campo").combina_com(PERFIL_AGRO.regras)


# ---------------------------------------------------------------------------
# Localização: SC e PR inteiros, nas duas grafias das fontes
# ---------------------------------------------------------------------------

CASOS_LOCAL = [
    # Sigla (Gupy, Catho, Sólides escrevem assim)
    ("joinville-sigla", "Joinville - SC", True),
    ("piraquara-sigla", "Piraquara - PR", True),
    ("cidade-pequena-sc", "Papanduva - SC", True),
    ("cidade-pequena-pr", "Castro - PR", True),
    # Estado por extenso (o LinkedIn escreve assim)
    ("joinville-extenso", "Joinville, Santa Catarina, Brazil", True),
    ("cascavel-extenso", "Cascavel, Paraná, Brazil", True),
    # Município sem estado nenhum no texto: só as cidades nominais salvam
    ("cidade-sozinha", "Jaraguá do Sul", True),
    ("curitiba-sozinha", "Curitiba", True),
    # Fora dos dois estados
    ("sao-paulo", "Campinas - SP", False),
    ("rio-grande-do-sul", "Passo Fundo, Rio Grande do Sul, Brazil", False),
    ("goias", "Rio Verde - GO", False),
]


@pytest.mark.parametrize("nome,local,esperado", CASOS_LOCAL, ids=[c[0] for c in CASOS_LOCAL])
def test_local_perfil_agro(nome, local, esperado):
    assert _job("Engenheiro Agrônomo", local=local).combina_com(PERFIL_AGRO.regras) == esperado


# ---------------------------------------------------------------------------
# Nível
# ---------------------------------------------------------------------------

def test_estagio_fora_junior_dentro():
    """Ele tem 3 anos de formado e já é gerente: estágio é passo atrás.
    Júnior fica — é como muita vaga de RTV entra na carreira."""
    assert not _job("Estágio em Agronomia").combina_com(PERFIL_AGRO.regras)
    assert _job("Assistente Técnico Agrícola Júnior").combina_com(PERFIL_AGRO.regras)


def test_lideranca_pontua_como_alvo():
    """Dois dos quatro cargos que ele quer são de gerência. No padrão
    global "Liderança" vale -2, o que rebaixaria justamente os alvos."""
    gerente = _job("Gerente de Produção Agrícola", local="Curitiba, Paraná, Brazil")
    pleno = _job("Analista Agrícola Pleno", local="Curitiba, Paraná, Brazil")
    assert gerente.pontuar_relevancia(PERFIL_AGRO.regras) == pleno.pontuar_relevancia(
        PERFIL_AGRO.regras
    )


def test_titulos_excluidos_barram_ti():
    assert not _job("Analista de Sistemas Agrícolas").combina_com(PERFIL_AGRO.regras)
    assert not _job("Desenvolvedor Full Stack - Agronegócio").combina_com(PERFIL_AGRO.regras)


# ---------------------------------------------------------------------------
# Os três perfis não se misturam
# ---------------------------------------------------------------------------

CASOS_CRUZADOS = [
    ("vaga-agro", "Engenheiro Agrônomo", False, False, True),
    ("vaga-dev", "Desenvolvedor Back-end Node.js", True, False, False),
    ("vaga-admin", "Analista Financeiro", False, True, False),
]


@pytest.mark.parametrize(
    "nome,titulo,esp_dev,esp_adm,esp_agro", CASOS_CRUZADOS, ids=[c[0] for c in CASOS_CRUZADOS]
)
def test_perfis_nao_se_misturam(nome, titulo, esp_dev, esp_adm, esp_agro):
    job = _job(titulo, local="Joinville - SC", modalidade="Presencial")
    assert job.combina_com(PERFIL_DEV.regras) == esp_dev
    assert job.combina_com(PERFIL_ADM.regras) == esp_adm
    assert job.combina_com(PERFIL_AGRO.regras) == esp_agro
