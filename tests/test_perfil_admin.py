"""Testes do perfil admin (core/config_adm.py) — administrativo,
financeiro, fiscal e RH, Joinville ou remoto, pleno/sênior.

O que este arquivo trava, além do óbvio "cargo certo entra":

  - o falso positivo mais provável deste radar: "processos" e "pessoas"
    são qualificadores legítimos da área, mas existem com outro sentido em
    vaga industrial e de TI (Joinville é polo industrial) — a lista de
    áreas excluídas é o que separa os dois, e é fácil alguém afrouxar isso
    sem perceber ao adicionar um cargo novo;
  - "Assistente"/"Auxiliar" não podem virar porta de entrada: só os
    títulos de assistente nomeados um a um entram, porque o resto é nível
    abaixo do que ela já ocupa;
  - Sênior pontua como ALVO neste perfil (no padrão global vale -2) — se
    niveis_alvo parar de ser respeitado, metade do que ela procura cai no
    ranking sem ninguém notar.
"""

import pytest

from core.job import Job
from core.perfis import PERFIL_ADM, PERFIL_DEV


def _job(titulo: str, local: str = "Remoto", modalidade: str = "Remoto") -> Job:
    return Job(
        titulo=titulo, empresa="Teste", local=local,
        link="https://teste.invalido/vaga", site="Teste", modalidade=modalidade,
    )


# ---------------------------------------------------------------------------
# Cargo
# ---------------------------------------------------------------------------

CASOS_CARGO = [
    # Financeiro
    ("financeiro", "Analista Financeiro", True),
    ("financeira-feminino", "Analista Financeira", True),
    ("contas-a-pagar", "Analista de Contas a Pagar", True),
    ("tesouraria", "Analista de Tesouraria", True),
    ("controladoria", "Analista de Controladoria", True),
    # Contábil fica; fiscal e tributário saíram a pedido da usuária.
    ("contabil", "Analista Contábil", True),
    ("fiscal-barra", "Analista Fiscal", False),
    ("tributario-barra", "Analista Tributário", False),
    # Administrativo
    ("administrativo", "Analista Administrativo", True),
    ("contratos", "Analista de Contratos", True),
    ("assistente-executivo", "Assistente Executiva", True),
    ("coordenador-administrativo", "Coordenadora Administrativa", True),
    # RH / DP (pós em Gestão de Pessoas)
    ("rh", "Analista de RH", True),
    ("recursos-humanos", "Analista de Recursos Humanos", True),
    ("dp", "Analista de Departamento Pessoal", True),
    ("folha", "Analista de Folha de Pagamento", True),
    ("recrutamento", "Analista de Recrutamento e Seleção", True),

    # Cargo ambíguo: sozinho não entra, com a área junto entra.
    ("analista-sozinho-nao", "Analista Pleno", False),
    ("analista-com-area", "Analista Pleno - Financeiro", True),
    ("coordenador-sozinho-nao", "Coordenador", False),
    ("especialista-com-area", "Especialista em Departamento Pessoal", True),

    # "Assistente" e "Auxiliar" não são porta de entrada — só os títulos
    # nomeados um a um na lista forte entram.
    ("auxiliar-generico-nao", "Auxiliar Administrativo", False),
    ("assistente-generico-nao", "Assistente de Operações", False),

    # Fora da área
    ("dev-nao-entra", "Desenvolvedor Back-end", False),
    ("dados-nao-entra", "Analista de Dados", False),
    ("marketing-nao-entra", "Analista de Marketing", False),
]


@pytest.mark.parametrize(
    "nome,titulo,esperado", CASOS_CARGO, ids=[c[0] for c in CASOS_CARGO]
)
def test_cargo_perfil_admin(nome, titulo, esperado):
    assert _job(titulo).combina_com(PERFIL_ADM.regras) == esperado


# ---------------------------------------------------------------------------
# Títulos excluídos: área de fora + fiscal/tributário, sem perdão
# ---------------------------------------------------------------------------

CASOS_TITULO_EXCLUIDO = [
    # "Analista de Processos" é cargo dela; com "Industriais" junto, não é.
    ("processos-sozinho-passa", "Analista de Processos", True),
    ("processos-industriais-barra", "Analista de Processos Industriais", False),
    ("processos-software-barra", "Analista de Processos de Software", False),
    # "pessoas" idem
    ("gestao-de-pessoas-passa", "Analista de Gestão de Pessoas", True),
    # Cargo da área + área de fora no mesmo título
    ("analista-financeiro-ti-barra", "Analista Financeiro de TI", False),
    ("coordenador-qualidade-barra", "Coordenador de Qualidade", False),
    ("analista-comercial-barra", "Analista Comercial", False),
    ("analista-logistica-barra", "Analista de Logística", False),
    # A rejeição é INCONDICIONAL: o ERP no título não salva. Estes dois
    # são exatamente o que passaria se a regra tivesse perdão por
    # ferramenta, e são os dois casos que a usuária não quer ver.
    ("fiscal-com-erp-barra", "Analista Fiscal Protheus", False),
    ("sistemas-com-erp-barra", "Analista de Sistemas Protheus", False),
    # ERP sozinho, sem área de fora, continua entrando normalmente.
    ("financeiro-com-erp-passa", "Analista Financeiro Protheus", True),
]


@pytest.mark.parametrize(
    "nome,titulo,esperado", CASOS_TITULO_EXCLUIDO,
    ids=[c[0] for c in CASOS_TITULO_EXCLUIDO],
)
def test_titulos_excluidos(nome, titulo, esperado):
    assert _job(titulo).combina_com(PERFIL_ADM.regras) == esperado


# ---------------------------------------------------------------------------
# Nível: pleno/sênior — e liderança continua entrando
# ---------------------------------------------------------------------------

CASOS_NIVEL = [
    ("pleno-passa", "Analista Financeiro Pleno", True),
    ("senior-passa", "Analista Financeiro Sênior", True),
    ("sem-nivel-passa", "Analista Financeiro", True),
    ("junior-barra", "Analista Financeiro Júnior", False),
    ("jr-barra", "Analista Fiscal Jr", False),
    ("estagio-barra", "Estágio em Departamento Pessoal", False),
    # Promoção natural pra quem tem 7 anos de área e pós: continua entrando.
    ("coordenacao-passa", "Coordenador Administrativo", True),
]


@pytest.mark.parametrize(
    "nome,titulo,esperado", CASOS_NIVEL, ids=[c[0] for c in CASOS_NIVEL]
)
def test_niveis_perfil_admin(nome, titulo, esperado):
    assert _job(titulo).combina_com(PERFIL_ADM.regras) == esperado


def test_senior_e_alvo_neste_perfil():
    """Sênior tem que pontuar igual a Pleno aqui (os dois são o alvo), e
    NÃO pode ser penalizado como é no padrão global."""
    pleno = _job("Analista Financeiro Pleno", local="Remoto (Brasil)")
    senior = _job("Analista Financeiro Sênior", local="Remoto (Brasil)")
    sem_nivel = _job("Analista Financeiro", local="Remoto (Brasil)")

    assert senior.pontuar_relevancia(PERFIL_ADM.regras) == pleno.pontuar_relevancia(
        PERFIL_ADM.regras
    )
    assert senior.pontuar_relevancia(PERFIL_ADM.regras) > sem_nivel.pontuar_relevancia(
        PERFIL_ADM.regras
    )


def test_senior_continua_penalizado_no_perfil_dev():
    """O alvo por perfil não pode ter vazado pro outro radar: no perfil dev
    o padrão global continua valendo (e sênior nem passa no filtro)."""
    assert PERFIL_DEV.regras.niveis_alvo is None
    assert not _job("Senior Backend Developer").combina_com(PERFIL_DEV.regras)


# ---------------------------------------------------------------------------
# Localização
# ---------------------------------------------------------------------------

CASOS_LOCAL = [
    ("remoto-passa", "Remoto", "Remoto", True),
    ("remoto-brasil-passa", "Remoto (Curitiba, PR)", "Remoto", True),
    ("joinville-presencial-passa", "Joinville, SC", "Presencial", True),
    ("joinville-hibrido-passa", "Joinville, Santa Catarina, Brazil", "Híbrido", True),
    ("outra-cidade-barra", "Blumenau, SC", "Presencial", False),
    ("sao-paulo-barra", "São Paulo, SP", "Presencial", False),
    # Rotina fiscal/DP é legislação nacional — remoto de fora não serve.
    ("remoto-portugal-barra", "Remote - Portugal", "Remoto", False),
    ("remoto-eua-barra", "Remote - US", "Remoto", False),
]


@pytest.mark.parametrize(
    "nome,local,modalidade,esperado", CASOS_LOCAL, ids=[c[0] for c in CASOS_LOCAL]
)
def test_local_perfil_admin(nome, local, modalidade, esperado):
    job = _job("Analista Financeiro", local=local, modalidade=modalidade)
    assert job.combina_com(PERFIL_ADM.regras) == esperado


# ---------------------------------------------------------------------------
# Os dois perfis do casal não podem se misturar
# ---------------------------------------------------------------------------

CASOS_CRUZADOS = [
    ("vaga-dela", "Analista Financeiro Pleno", False, True),
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
    assert job.combina_com(PERFIL_ADM.regras) == esperado_adm
