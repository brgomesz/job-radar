"""Testes do perfil analista (core/config_analista.py) — coordenação/gerência/
supervisão administrativa e financeira, operações, contratos e sales ops;
analista só com qualificador de nível ou de setor. Só Joinville, sem remoto.

O que este arquivo trava, além do óbvio "cargo certo entra":

  - analista genérico da área NÃO entra sozinho: "Analista Financeiro"
    precisa de nível (sênior/especialista/III) ou setor (imobiliário,
    incorporadora, comercial...) no título;
  - a exclusão é incondicional: assistente, auxiliar, júnior, estágio,
    contábil, fiscal, tributário, controladoria e tesouraria barram até
    cargo forte;
  - a área de fora com o mesmo vocabulário ("Gerente de Operações
    Industriais", num polo industrial como Joinville) continua barrada;
  - Sênior/Especialista/Liderança pontuam como ALVO (no padrão global
    valem -2); Pleno é neutro.
"""

import pytest

from core.job import Job
from core.perfis import PERFIL_ANALISTA, PERFIL_DEV


def _job(
    titulo: str, local: str = "Joinville, SC", modalidade: str = "Presencial"
) -> Job:
    return Job(
        titulo=titulo, empresa="Teste", local=local,
        link="https://teste.invalido/vaga", site="Teste", modalidade=modalidade,
    )


# ---------------------------------------------------------------------------
# Cargo forte: aprova sozinho
# ---------------------------------------------------------------------------

CASOS_CARGO_FORTE = [
    ("coord-adm-fin", "Coordenador Administrativo Financeiro"),
    ("coord-adm-fin-fem", "Coordenadora Administrativa Financeira"),
    ("coord-adm-fin-marcador", "Coordenador(a) Administrativo(a) Financeiro(a)"),
    ("coord-adm", "Coordenadora Administrativa"),
    ("coord-fin", "Coordenador Financeiro"),
    ("coord-operacoes", "Coordenador de Operações"),
    ("coord-contratos", "Coordenadora de Contratos"),
    ("gerente-adm-fin", "Gerente Administrativo e Financeiro"),
    ("gerente-adm", "Gerente Administrativa"),
    ("gerente-fin", "Gerente Financeiro"),
    ("gerente-operacoes", "Gerente de Operações"),
    ("gerente-operacional", "Gerente Operacional"),
    ("supervisor-adm", "Supervisor Administrativo"),
    ("supervisora-fin", "Supervisora Financeira"),
    ("analista-adm-fin", "Analista Administrativo Financeiro"),
    ("analista-op-comerciais", "Analista de Operações Comerciais"),
    ("sales-operations", "Sales Operations Analyst"),
    ("sales-ops", "Sales Ops Specialist"),
    ("gestor-contratos", "Gestora de Contratos"),
]


@pytest.mark.parametrize(
    "nome,titulo", CASOS_CARGO_FORTE, ids=[c[0] for c in CASOS_CARGO_FORTE]
)
def test_cargo_forte_aprova_sozinho(nome, titulo):
    assert _job(titulo).combina_com(PERFIL_ANALISTA.regras)


# ---------------------------------------------------------------------------
# Cargo que só aprova com qualificador
# ---------------------------------------------------------------------------

CASOS_QUALIFICADOR = [
    # Sozinho, não entra
    ("adm-sozinho", "Analista Administrativo", False),
    ("operacoes-sozinho", "Analista de Operações", False),
    ("contratos-sozinho", "Analista de Contratos", False),
    ("financeiro-sozinho", "Analista Financeiro", False),
    ("processos-sozinho", "Analista de Processos", False),
    ("planejamento-sozinho", "Analista de Planejamento", False),
    ("financeiro-pleno", "Analista Financeiro Pleno", False),
    # Com nível
    ("financeiro-senior", "Analista Financeiro Sênior", True),
    ("financeira-sr", "Analista Financeira Sr.", True),
    ("adm-iii", "Analista Administrativo III", True),
    ("contratos-especialista", "Analista de Contratos Especialista", True),
    # Com setor
    ("adm-imobiliaria", "Analista Administrativa - Imobiliária", True),
    ("contratos-incorporadora", "Analista de Contratos (Incorporadora)", True),
    ("processos-construtora", "Analista de Processos - Construtora", True),
    ("planejamento-comercial", "Analista de Planejamento Comercial", True),
    ("operacoes-vendas", "Analista de Operações de Vendas", True),
    ("financeiro-real-estate", "Analista Financeiro Real Estate", True),
    ("adm-sienge", "Analista Administrativo Sienge", True),
    # Nível II não é sênior
    ("financeiro-ii", "Analista Financeiro II", False),
    # Fora do escopo
    ("analista-generico", "Analista Pleno", False),
    ("rh-saiu", "Analista de RH", False),
    ("dev-nao-entra", "Desenvolvedor Back-end", False),
    ("marketing-nao-entra", "Analista de Marketing Sênior", False),
]


@pytest.mark.parametrize(
    "nome,titulo,esperado", CASOS_QUALIFICADOR, ids=[c[0] for c in CASOS_QUALIFICADOR]
)
def test_cargo_com_qualificador(nome, titulo, esperado):
    assert _job(titulo).combina_com(PERFIL_ANALISTA.regras) == esperado


# ---------------------------------------------------------------------------
# Exclusões: incondicionais, barram até cargo forte
# ---------------------------------------------------------------------------

CASOS_EXCLUIDO = [
    ("estagio", "Estágio Administrativo Financeiro"),
    ("estagiaria", "Estagiária - Coordenação de Contratos"),
    ("trainee", "Trainee Gerente de Operações"),
    ("jovem-aprendiz", "Jovem Aprendiz Administrativo"),
    ("auxiliar", "Auxiliar Administrativo Financeiro"),
    ("assistente", "Assistente de Coordenador Financeiro"),
    ("junior", "Analista Administrativo Financeiro Júnior"),
    ("jr", "Analista Administrativo Financeiro Jr"),
    ("contabil", "Coordenador Financeiro e Contábil"),
    ("contabilidade", "Gerente de Contabilidade e Financeiro"),
    ("fiscal", "Coordenador Administrativo Fiscal"),
    ("tributario", "Gerente Financeiro e Tributário"),
    ("controladoria", "Coordenador Financeiro e Controladoria"),
    ("tesouraria", "Analista Financeiro Sênior - Tesouraria"),
    # Área de fora com o mesmo vocabulário
    ("operacoes-industriais", "Gerente de Operações Industriais"),
    ("operacoes-logisticas", "Coordenador de Operações Logísticas"),
    ("processos-software", "Analista de Processos de Software Sênior"),
    ("operacoes-ti", "Analista de Operações de TI Sênior"),
]


@pytest.mark.parametrize(
    "nome,titulo", CASOS_EXCLUIDO, ids=[c[0] for c in CASOS_EXCLUIDO]
)
def test_titulos_excluidos(nome, titulo):
    assert not _job(titulo).combina_com(PERFIL_ANALISTA.regras)


# ---------------------------------------------------------------------------
# Senioridade: Sênior/Especialista/Liderança são alvo, Pleno é neutro
# ---------------------------------------------------------------------------

def _score(titulo: str) -> int:
    return _job(titulo).pontuar_relevancia(PERFIL_ANALISTA.regras)


def test_prioridade_pontua_acima_de_pleno():
    senior = _score("Analista Administrativo Financeiro Sênior")
    especialista = _score("Analista Administrativo Financeiro Especialista")
    pleno = _score("Analista Administrativo Financeiro Pleno")

    assert senior == especialista
    assert senior > pleno


@pytest.mark.parametrize("titulo", [
    "Coordenador Financeiro",
    "Supervisora Administrativa",
    "Gerente de Operações",
])
def test_lideranca_pontua_como_senior(titulo):
    assert _job(titulo).senioridade == "Liderança"
    # Os dois são cargo forte; o nível (alvo nos dois) não pode desempatar.
    assert _score(titulo) == _score("Analista Administrativo Financeiro Sênior")


def test_senior_continua_penalizado_no_perfil_dev():
    """O alvo por perfil não pode ter vazado pro outro radar: no perfil dev
    o padrão global continua valendo (e sênior nem passa no filtro)."""
    assert PERFIL_DEV.regras.niveis_alvo is None
    assert not _job("Senior Backend Developer").combina_com(PERFIL_DEV.regras)


# ---------------------------------------------------------------------------
# Localização
# ---------------------------------------------------------------------------

# Remoto saiu do perfil (pedido da usuária): o que chegava como remoto
# era, na maioria, vaga presencial que o filtro f_WT=2 do LinkedIn deixou
# passar — o caso "linkedin-sp-marcado-remoto" é um deles, real.
CASOS_LOCAL = [
    ("joinville-presencial-passa", "Joinville, SC", "Presencial", True),
    ("joinville-hibrido-passa", "Joinville, Santa Catarina, Brazil", "Híbrido", True),
    ("joinville-remoto-passa", "Joinville, Santa Catarina, Brazil", "Remoto", True),
    ("remoto-barra", "Remoto", "Remoto", False),
    ("remoto-brasil-barra", "Remoto (Curitiba, PR)", "Remoto", False),
    ("linkedin-sp-marcado-remoto", "São Paulo, São Paulo, Brazil", "Remoto", False),
    ("outra-cidade-barra", "Blumenau, SC", "Presencial", False),
    ("sao-paulo-barra", "São Paulo, SP", "Presencial", False),
    ("remoto-portugal-barra", "Remote - Portugal", "Remoto", False),
    ("remoto-eua-barra", "Remote - US", "Remoto", False),
]


@pytest.mark.parametrize(
    "nome,local,modalidade,esperado", CASOS_LOCAL, ids=[c[0] for c in CASOS_LOCAL]
)
def test_local_perfil_analista(nome, local, modalidade, esperado):
    job = _job("Coordenador Administrativo Financeiro", local=local, modalidade=modalidade)
    assert job.combina_com(PERFIL_ANALISTA.regras) == esperado


# ---------------------------------------------------------------------------
# Termos de busca
# ---------------------------------------------------------------------------

def test_linkedin_so_busca_joinville():
    """Sem a passada nacional (que traz a f_WT=2 "remota"): só a busca
    por cidade, em Joinville."""
    (linkedin,) = [
        d for d in PERFIL_ANALISTA.definicao_scrapers
        if d.classe.__name__ == "LinkedInScraper"
    ]
    assert linkedin.kwargs_extras["locations"] == []
    assert linkedin.kwargs_extras["locations_remoto_apenas"] == []
    assert linkedin.kwargs_extras["locations_cidades_presencial"] == ["Joinville"]


def test_termos_de_busca():
    assert PERFIL_ANALISTA.termos_prioritarios == [
        "coordenador administrativo financeiro",
        "gerente administrativo financeiro",
        "analista administrativo financeiro",
        "analista de operações comerciais",
        "coordenador de contratos",
    ]
    extras = [t for t in PERFIL_ANALISTA.termos_busca if t not in PERFIL_ANALISTA.termos_prioritarios]
    assert extras == ["sienge", "incorporadora", "imobiliária", "sales operations"]


# ---------------------------------------------------------------------------
# Não pode pegar vaga do perfil dev, nem o dev pegar a dele
# ---------------------------------------------------------------------------

CASOS_CRUZADOS = [
    ("vaga-dela", "Coordenadora Administrativa Financeira", False, True),
    ("vaga-dele", "Desenvolvedor Back-end Node.js Pleno", True, False),
    ("nenhum-dos-dois", "Analista de Dados Pleno", False, False),
]


@pytest.mark.parametrize(
    "nome,titulo,esperado_dev,esperado_adm",
    CASOS_CRUZADOS,
    ids=[c[0] for c in CASOS_CRUZADOS],
)
def test_perfis_nao_se_misturam(nome, titulo, esperado_dev, esperado_adm):
    job = _job(titulo, local="Joinville, SC", modalidade="Híbrido")
    assert job.combina_com(PERFIL_DEV.regras) == esperado_dev
    assert job.combina_com(PERFIL_ANALISTA.regras) == esperado_adm
