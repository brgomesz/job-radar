"""Testes do perfil analista (core/config_analista.py) — coordenação/gerência/
supervisão administrativa e financeira, operações, contratos e sales ops;
analista só com qualificador de nível ou de setor; áreas afins do currículo
(imobiliário/locação, RH, FP&A, contas a pagar/receber, backoffice).
Presencial/híbrido em Joinville, ou remoto declarado NO TÍTULO.

O que este arquivo trava, além do óbvio "cargo certo entra":

  - analista genérico da área NÃO entra sozinho: "Analista Financeiro"
    precisa de nível (sênior/especialista/III) ou setor (imobiliário,
    incorporadora, comercial...) no título;
  - a exclusão é incondicional: assistente, auxiliar, júnior, estágio,
    contábil, fiscal, tributário, controladoria e tesouraria barram até
    cargo forte;
  - a área de fora com o mesmo vocabulário ("Gerente de Operações
    Industriais", num polo industrial como Joinville) continua barrada;
  - Pleno/Sênior/Especialista/Liderança pontuam como ALVO (no padrão
    global os três últimos valem -2); júnior e "Nível I" nem entram;
  - remoto só conta quando o título declara: a marcação "Remoto" do
    LinkedIn sozinha não basta (MEDIDO: 173 de 188 vagas entravam assim).
"""

import pytest

from core.job import Job
from core.perfis import PERFIL_ANALISTA, PERFIL_DEV


# Padrão em Joinville: os testes de cargo não podem depender da regra de
# local (que tem os próprios testes lá embaixo).
def _job(titulo: str, local: str = "Joinville, SC", modalidade: str = "Presencial") -> Job:
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
    # Áreas afins do currículo (nov/2026)
    ("gerente-fin-operacional", "Gerente Financeira e Operacional"),
    ("gerente-imobiliario", "Gerente Imobiliário"),
    ("coord-locacao", "Coordenadora de Locação"),
    ("gerente-locacao", "Gerente de Locação"),
    ("office-manager", "Office Manager"),
    ("fpa", "Analista de FP&A Sênior"),
    ("coord-rh", "Coordenadora de Recursos Humanos"),
    ("hrbp", "HR Business Partner"),
    ("backoffice", "Coordenador de Backoffice Comercial"),
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
    ("locacao-sozinho", "Analista de Locação", False),
    ("rh-sozinho", "Analista de Recursos Humanos", False),
    # Pleno e II são a faixa pedida (pleno a sênior)
    ("financeiro-pleno", "Analista Financeiro Pleno", True),
    ("financeiro-ii", "Analista Financeiro II", True),
    ("rh-pleno", "Analista de RH Pleno", True),
    ("locacao-imobiliaria", "Analista de Locação - Imobiliária", True),
    ("contas-receber-senior", "Analista de Contas a Receber Sênior", True),
    ("planejamento-fin-pleno", "Analista de Planejamento Financeiro Pleno", True),
    ("recrutamento-senior", "Analista de Recrutamento e Seleção Sênior", True),
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
    # Nível I é o degrau de entrada: júnior com outro nome
    ("financeiro-i", "Analista Financeiro I", False),
    # Fora do escopo
    ("analista-generico", "Analista Pleno", False),
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
# Senioridade: Pleno/Sênior/Especialista/Liderança são todos alvo
# ---------------------------------------------------------------------------

def _score(titulo: str) -> int:
    return _job(titulo).pontuar_relevancia(PERFIL_ANALISTA.regras)


def test_pleno_e_senior_pontuam_igual():
    senior = _score("Analista Administrativo Financeiro Sênior")
    especialista = _score("Analista Administrativo Financeiro Especialista")
    pleno = _score("Analista Administrativo Financeiro Pleno")

    assert senior == especialista == pleno


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

CARGO = "Coordenador Administrativo Financeiro"

CASOS_LOCAL = [
    # Joinville: presencial ou híbrido, título sem nada de especial
    ("joinville-presencial-passa", CARGO, "Joinville, SC", "Presencial", True),
    ("joinville-hibrido-passa", CARGO, "Joinville, Santa Catarina, Brazil", "Híbrido", True),
    ("outra-cidade-barra", CARGO, "Blumenau, SC", "Presencial", False),
    ("sao-paulo-barra", CARGO, "São Paulo, SP", "Presencial", False),
    # MEDIDO: a marcação "Remoto" do LinkedIn (modalidade) sem nada no
    # título era como 173 de 188 vagas entravam — e não eram remotas de
    # verdade. Agora não basta.
    ("remoto-so-na-modalidade-barra", CARGO, "São Paulo, São Paulo, Brazil", "Remoto", False),
    ("remoto-so-no-local-barra", CARGO, "Remoto", "", False),
    # Remoto declarado no título passa, de qualquer lugar do Brasil
    ("titulo-remoto-passa", f"{CARGO} - Remoto", "São Paulo, SP", "", True),
    ("titulo-home-office-passa", f"{CARGO} | Home Office", "Brazil", "Remoto", True),
    ("titulo-100-remoto-passa", f"{CARGO} (100% Remoto)", "Curitiba, PR", "", True),
    ("titulo-remote-passa", "Sales Operations Analyst - Remote Work", "Brazil", "Remoto", True),
    # ...mas não quando o título mistura com híbrido/presencial
    ("titulo-hibrido-remoto-barra", f"{CARGO} - Híbrido/Remoto", "São Paulo, SP", "", False),
    ("titulo-presencial-ou-remoto-barra", f"{CARGO} (Presencial ou Remoto)", "Curitiba, PR", "", False),
    # ...a não ser que seja em Joinville, onde híbrido já vale
    ("titulo-hibrido-joinville-passa", f"{CARGO} - Híbrido/Remoto", "Joinville, SC", "", True),
    # Remoto no título, mas pra outro país: continua barrado (só Brasil)
    ("titulo-remoto-portugal-barra", f"{CARGO} - Remoto", "Remote - Portugal", "Remoto", False),
    ("titulo-remote-eua-barra", "Sales Operations Analyst - Remote", "Remote - US", "Remoto", False),
]


@pytest.mark.parametrize(
    "nome,titulo,local,modalidade,esperado", CASOS_LOCAL, ids=[c[0] for c in CASOS_LOCAL]
)
def test_local_perfil_analista(nome, titulo, local, modalidade, esperado):
    job = _job(titulo, local=local, modalidade=modalidade)
    assert job.combina_com(PERFIL_ANALISTA.regras) == esperado


def test_remoto_pelo_titulo_nao_vaza_pro_perfil_dev():
    """A regra nova é do perfil analista: no dev a modalidade continua
    confirmando remoto."""
    assert PERFIL_DEV.regras.remoto_exige_titulo is None
    job = _job("Desenvolvedor Back-end Node.js", local="Brazil", modalidade="Remoto")
    assert job.combina_com(PERFIL_DEV.regras)


# ---------------------------------------------------------------------------
# Termos de busca
# ---------------------------------------------------------------------------

def test_termos_de_busca():
    assert PERFIL_ANALISTA.termos_prioritarios == [
        "coordenador administrativo financeiro",
        "gerente administrativo financeiro",
        "analista administrativo financeiro",
        "gerente financeiro",
        "coordenador financeiro",
        "analista financeiro remoto",
    ]
    extras = [t for t in PERFIL_ANALISTA.termos_busca if t not in PERFIL_ANALISTA.termos_prioritarios]
    assert len(extras) == 16 and len(set(extras)) == 16
    assert {"gerente de locação", "office manager", "fp&a", "analista de recursos humanos"} <= set(extras)


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
