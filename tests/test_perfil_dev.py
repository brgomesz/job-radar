"""Testes do perfil dev (core/config_dev.py + as duas regras novas de
RegrasFiltro: stacks_excluidas e niveis_excluidos).

Mesma filosofia dos outros arquivos de teste desta base: cada caso trava
uma decisão de filtro que só existe porque foi escolhida de propósito, e
que uma mexida futura nas listas pode desfazer em silêncio. Os três pontos
que mais podem quebrar sem ninguém notar:

  - "java" NÃO pode barrar "JavaScript" (o match é por borda de palavra —
    se alguém trocar por substring crua, todo o perfil morre de uma vez);
  - a stack própria no título perdoa a stack de fora ("Node + Python"),
    MENOS quando a própria só aparece dentro do termo excluído ("React
    Native");
  - vaga sem nível declarado continua passando — o corte de "pleno apenas"
    vale só pro nível ESCRITO no título.

Também cobre o isolamento entre perfis: as regras novas são opcionais, e o
perfil de dados (brasil) não pode ter mudado de comportamento por causa
delas.
"""

import pytest

from core.job import Job
from core.perfis import PERFIL_BR, PERFIL_DEV


def _job(titulo: str, local: str = "Remoto", modalidade: str = "Remoto") -> Job:
    return Job(
        titulo=titulo, empresa="Teste", local=local,
        link="https://teste.invalido/vaga", site="Teste", modalidade=modalidade,
    )


# ---------------------------------------------------------------------------
# Cargo: o que o perfil dev aceita e recusa pelo TÍTULO
# ---------------------------------------------------------------------------

CASOS_CARGO = [
    # Cargo forte genérico — a maioria das vagas reais não traz stack no
    # título, e é justamente por isso que ele é aceito sozinho aqui.
    ("forte-back-end-hifen", "Desenvolvedor Back-end", True),
    ("forte-backend-junto", "Desenvolvedor Backend", True),
    ("forte-backend-ingles", "Backend Developer", True),
    ("forte-full-stack", "Desenvolvedor Full Stack", True),
    ("forte-fullstack-ingles", "Fullstack Engineer", True),
    ("forte-front-end", "Desenvolvedor Front-end", True),
    ("forte-feminino", "Desenvolvedora Back-end", True),
    ("forte-com-stack-no-nome", "Node.js Developer", True),
    ("forte-react", "React Developer", True),

    # Cargo ambíguo: sozinho não basta, precisa da stack junto no título.
    ("ambiguo-sozinho-nao-passa", "Desenvolvedor", False),
    ("ambiguo-com-stack-passa", "Desenvolvedor Node.js", True),
    ("ambiguo-software-engineer-sozinho", "Software Engineer", False),
    ("ambiguo-software-engineer-com-stack", "Software Engineer - TypeScript", True),
    ("ambiguo-analista-sistemas-com-stack", "Analista de Sistemas (API REST)", True),

    # Fora da área: nenhuma palavra de cargo de desenvolvimento.
    ("fora-analista-de-dados", "Analista de Dados", False),
    ("fora-designer", "Designer de Produto", False),
]


@pytest.mark.parametrize(
    "nome,titulo,esperado", CASOS_CARGO, ids=[c[0] for c in CASOS_CARGO]
)
def test_cargo_perfil_dev(nome, titulo, esperado):
    assert _job(titulo).combina_com(PERFIL_DEV.regras) == esperado


# ---------------------------------------------------------------------------
# stacks_excluidas: contrapeso do cargo forte genérico
# ---------------------------------------------------------------------------

CASOS_STACK = [
    # O caso que motivou a regra: mesmo cargo forte, stack errada.
    ("java-barra", "Desenvolvedor Back-end Java", False),
    ("dotnet-barra", "Desenvolvedor Back-end .NET", False),
    ("asp-net-barra", "Desenvolvedor ASP.NET", False),
    ("csharp-barra", "Desenvolvedor Full Stack C#", False),
    ("php-barra", "Desenvolvedor PHP", False),
    ("python-barra", "Backend Developer Python", False),
    ("angular-barra", "Desenvolvedor Front-end Angular", False),
    ("vue-barra", "Front-end Developer Vue.js", False),

    # Mobile é outra carreira, não é o que o usuário faz.
    ("flutter-barra", "Desenvolvedor Mobile Flutter", False),
    # "react" está DENTRO de "react native": sem descontar o termo excluído
    # antes de procurar a stack própria, esta vaga se auto-perdoava.
    ("react-native-barra", "Desenvolvedor React Native", False),

    # "java" não pode pegar "javascript" — o match é por borda de palavra.
    # Se este teste quebrar, o perfil inteiro parou de funcionar.
    ("javascript-nao-e-java", "Desenvolvedor JavaScript", True),
    ("javascript-ingles", "JavaScript Developer Pleno", True),

    # Stack de fora ao lado da própria: complemento, não substituto — desde
    # que a própria seja de BACK-END quando a de fora também é.
    ("node-mais-python-passa", "Desenvolvedor Full Stack (Node + Python)", True),
    # MEDIDO (nov/2026): "Java/React" passava pelo React e era o grosso do
    # "só recebo vaga de Java" do usuário. Numa full-stack, o back-end É o
    # Java; o React do título não muda isso.
    ("react-mais-java-barra", "Full Stack Developer - React / Java", False),

    # Sem stack nenhuma no título: passa (é o caso mais comum de todos).
    ("sem-stack-passa", "Desenvolvedor Back-end", True),
]


@pytest.mark.parametrize(
    "nome,titulo,esperado", CASOS_STACK, ids=[c[0] for c in CASOS_STACK]
)
def test_stacks_excluidas(nome, titulo, esperado):
    assert _job(titulo).combina_com(PERFIL_DEV.regras) == esperado


# ---------------------------------------------------------------------------
# niveis_excluidos: "pleno apenas" — mas só pelo nível DECLARADO
# ---------------------------------------------------------------------------

CASOS_NIVEL = [
    ("pleno-passa", "Desenvolvedor Back-end Pleno", True),
    ("pleno-abreviado-passa", "Desenvolvedor Back-end PL", True),
    ("sem-nivel-passa", "Desenvolvedor Back-end", True),
    ("junior-barra", "Desenvolvedor Back-end Júnior", False),
    ("junior-abreviado-barra", "Desenvolvedor Back-end Jr", False),
    ("senior-barra", "Desenvolvedor Back-end Sênior", False),
    ("senior-ingles-barra", "Senior Backend Developer", False),
    ("estagio-barra", "Estágio em Desenvolvimento Back-end", False),
    ("lideranca-barra", "Gerente de Engenharia de Software", False),
    ("especialista-barra", "Especialista Full Stack Developer", False),
]


@pytest.mark.parametrize(
    "nome,titulo,esperado", CASOS_NIVEL, ids=[c[0] for c in CASOS_NIVEL]
)
def test_niveis_excluidos(nome, titulo, esperado):
    assert _job(titulo).combina_com(PERFIL_DEV.regras) == esperado


# ---------------------------------------------------------------------------
# Localização: remoto (com mercado aceito) + Joinville presencial/híbrido
# ---------------------------------------------------------------------------

CASOS_LOCAL = [
    ("remoto-sem-mercado-passa", "Remoto", "Remoto", True),
    ("remoto-brasil-passa", "Remoto (São Paulo, SP)", "Remoto", True),
    ("remoto-portugal-passa", "Remote - Portugal", "Remoto", True),
    ("remoto-eua-passa", "Remote - US", "Remoto", True),
    ("remoto-latam-passa", "Remote - LATAM", "Remoto", True),
    # Mercado que não fala português nem inglês: fora do critério do perfil.
    ("remoto-india-barra", "Remote - India", "Remoto", False),
    ("remoto-alemanha-barra", "Remote - Germany", "Remoto", False),

    ("joinville-presencial-passa", "Joinville, SC", "Presencial", True),
    ("joinville-hibrido-passa", "Joinville, Santa Catarina, Brazil", "Híbrido", True),
    # Presencial em qualquer outra cidade é rejeitado — é whitelist.
    ("sao-paulo-presencial-barra", "São Paulo, SP", "Presencial", False),
    ("recife-presencial-barra", "Recife, PE", "Presencial", False),
]


@pytest.mark.parametrize(
    "nome,local,modalidade,esperado", CASOS_LOCAL, ids=[c[0] for c in CASOS_LOCAL]
)
def test_local_perfil_dev(nome, local, modalidade, esperado):
    job = _job("Desenvolvedor Back-end", local=local, modalidade=modalidade)
    assert job.combina_com(PERFIL_DEV.regras) == esperado


# ---------------------------------------------------------------------------
# Isolamento entre perfis: as regras novas são opcionais e o perfil de
# dados não as usa — comportamento dele não pode ter mudado.
# ---------------------------------------------------------------------------

def test_perfil_brasil_nao_usa_regras_novas():
    assert PERFIL_BR.regras.stacks_excluidas is None
    assert PERFIL_BR.regras.niveis_excluidos is None


CASOS_ISOLAMENTO = [
    # Vaga de dados sênior continua entrando no perfil brasil (lá
    # senioridade só pontua, não filtra) e continua fora do perfil dev.
    ("dados-senior", "Analista de Dados Sênior", "Recife, PE", "Presencial", True, False),
    # Vaga de dev não entra no perfil de dados — a exclusão de
    # "desenvolvedor" em QUALIFICADORES_CARGO continua valendo.
    ("dev-node", "Desenvolvedor Back-end Node.js", "Recife, PE", "Presencial", False, False),
]


@pytest.mark.parametrize(
    "nome,titulo,local,modalidade,esperado_br,esperado_dev",
    CASOS_ISOLAMENTO,
    ids=[c[0] for c in CASOS_ISOLAMENTO],
)
def test_isolamento_entre_perfis(nome, titulo, local, modalidade, esperado_br, esperado_dev):
    job = _job(titulo, local=local, modalidade=modalidade)
    assert job.combina_com(PERFIL_BR.regras) == esperado_br
    assert job.combina_com(PERFIL_DEV.regras) == esperado_dev


# ---------------------------------------------------------------------------
# Score: o que decide o que chega NA HORA (limiar 6) e o que vai pro digest
# ---------------------------------------------------------------------------

def test_score_prioriza_stack_propria():
    """Mesma vaga, mesmo nível e mesmo mercado: a que nomeia a stack do
    usuário tem que pontuar mais que a genérica — é isso que coloca
    back-end Node acima de front-end genérico no ranking do digest."""
    com_stack = _job("Desenvolvedor Back-end Node.js Pleno", local="Remoto (Brasil)")
    sem_stack = _job("Desenvolvedor Back-end Pleno", local="Remoto (Brasil)")
    assert com_stack.pontuar_relevancia(PERFIL_DEV.regras) > sem_stack.pontuar_relevancia(
        PERFIL_DEV.regras
    )


# ---------------------------------------------------------------------------
# Revisão de nov/2026 (currículo novo + "só recebo vaga de Java/Kotlin")
# ---------------------------------------------------------------------------

from core.perfis import (  # noqa: E402
    PERFIL_ANALISTA,
    PERFIL_DEV_INTL,
    PERFIL_DEV_JOINVILLE,
    PERFIL_DEV_REMOTO,
    PERFIS,
    SUBPERFIS_DEV,
)

PERFIS_DEV_TODOS = [PERFIL_DEV, PERFIL_DEV_JOINVILLE, PERFIL_DEV_REMOTO, PERFIL_DEV_INTL]

CASOS_STACK_NOV = [
    # Back-end de fora só é perdoado por back-end próprio (Node).
    ("laravel-react-barra", "Laravel and React Developer", False),
    ("dotnet-react-barra", "Desenvolvedor Full Stack .Net/React ou Angular", False),
    ("kotlin-react-barra", "Pessoa Desenvolvedora Full-stack Kotlin/React", False),
    ("python-nextjs-barra", "Desenvolvedor Fullstack (Python + Next.js)", False),
    ("java-node-passa", "Desenvolvedor(a) Back-End Java/Node", True),
    ("go-node-passa", "Pessoa Desenvolvedora Fullstack Go/Node.js - Pleno", True),
    # TypeScript não perdoa back-end de fora (".NET + TypeScript" é .NET).
    ("dotnet-typescript-barra", "Desenvolvedor Fullstack .NET + TypeScript", False),
    # SQL Server (ferramenta do currículo) não perdoa C#.
    ("csharp-sqlserver-barra", "Desenvolvedor Back-end C# SQL Server", False),
    # MEDIDO: ".NET" grudado escapava da borda de palavra.
    ("dotnet-grudado-barra", "Desenvolvedor Backend.NET - TRABALHO REMOTO", False),
    ("go-entre-parenteses-barra", "Backend Engineer (Go) - Remote Work", False),
    # Front de fora: JavaScript não perdoa mais; React/Node sim.
    ("javascript-angular-barra", "Desenvolvedor JavaScript /Angular", False),
    ("angular-react-passa", "Desenvolvedor Front-end Angular/React", True),
    ("node-vue-passa", "Desenvolvedor Full Stack Node + Vue", True),
    ("react-e-react-native-passa", "Desenvolvedor(a) Frontend (React / React Native)", True),
]


@pytest.mark.parametrize(
    "nome,titulo,esperado", CASOS_STACK_NOV, ids=[c[0] for c in CASOS_STACK_NOV]
)
def test_stack_por_camada(nome, titulo, esperado):
    for perfil in (PERFIL_DEV, PERFIL_DEV_REMOTO):
        assert _job(titulo).combina_com(perfil.regras) == esperado, perfil.chave


CASOS_FAIXA = [
    # Staff/Lead/Principal não são nível que _detectar_senioridade conhece —
    # caíam em "Não especificado" e passavam como se fossem pleno.
    ("staff-barra", "Staff Software Engineer - Frontend", False),
    ("staff-backend-barra", "Staff Backend Developer | Remoto", False),
    ("lead-barra", "Lead Front-End Developer (React)", False),
    ("principal-barra", "Principal Full Stack Developer (TypeScript)", False),
    ("nivel-i-barra", "Backend Engineer I", False),
    ("estagiario-barra", "Desenvolvedor BackEnd Node - Estagiário", False),
    ("qa-barra", "Desenvolvedor QA Automação", False),
    ("nivel-ii-passa", "Full Stack Developer II", True),
    ("pl-sr-passa", "Desenvolvedor NodeJS PL/SR", True),
]


@pytest.mark.parametrize("nome,titulo,esperado", CASOS_FAIXA, ids=[c[0] for c in CASOS_FAIXA])
def test_faixa_de_nivel(nome, titulo, esperado):
    assert _job(titulo).combina_com(PERFIL_DEV.regras) == esperado


def test_perfis_dev_compartilham_cargo_e_stack():
    """Os quatro dev mudam só o bloco de localização — a regra de cargo,
    stack e nível é a mesma em todos."""
    campos = (
        "keywords_forte", "keywords_ambiguo", "qualificadores_dados", "ferramentas_titulo",
        "stacks_excluidas", "stacks_backend_excluidas", "niveis_excluidos", "titulos_excluidos",
    )
    for perfil in PERFIS_DEV_TODOS[1:]:
        for campo in campos:
            assert getattr(perfil.regras, campo) == getattr(PERFIL_DEV.regras, campo), (perfil.chave, campo)
        assert perfil.regras_anuncio is PERFIL_DEV.regras_anuncio
        assert perfil.refiltrar_historico


def _vaga(titulo="Desenvolvedor Full Stack", local="Brazil", modalidade="Remoto", site="LinkedIn"):
    return Job(titulo=titulo, empresa="E", local=local, link="https://x.invalido/v",
               site=site, modalidade=modalidade)


# (nome, vaga, joinville, remoto, intl)
CASOS_LOCAL_NOVOS = [
    ("joinville-presencial", _vaga(local="Joinville, SC", modalidade="Presencial", site="Solides"),
     True, False, False),
    ("joinville-hibrido-linkedin", _vaga(local="Joinville, Santa Catarina, Brazil", modalidade=""),
     True, False, False),
    # Remota com a SEDE em Joinville no local: não é presencial em Joinville.
    ("joinville-mas-remota-no-titulo",
     _vaga("TypeScript Developer - Remote Work", local="Joinville, Santa Catarina, Brazil", modalidade=""),
     False, False, False),
    ("joinville-mas-modalidade-remoto", _vaga(local="Joinville - SC", modalidade="Remoto", site="Solides"),
     False, True, False),
    ("sao-paulo-presencial", _vaga(local="São Paulo, SP", modalidade="Presencial", site="Gupy"),
     False, False, False),
    # Remota, português, LinkedIn: empresa brasileira.
    ("remota-pt-linkedin", _vaga("Desenvolvedor Back-end Pleno", local="São Paulo, São Paulo, Brazil"),
     False, True, False),
    # Remota, inglês, LinkedIn: empresa de fora / time internacional.
    ("remota-en-linkedin", _vaga("Backend Engineer (Node) - Remote Work", local="Recife, Pernambuco, Brazil"),
     False, False, True),
    # Inglês no cargo, mas português no resto do título: vaga brasileira.
    ("cargo-en-titulo-pt", _vaga("Fullstack Developer Pleno - REMOTO", local="Não informado", site="Gupy"),
     False, True, False),
    # Portal brasileiro é sempre nacional, mesmo com o título todo em inglês.
    ("gupy-titulo-en", _vaga("Full Stack Developer II", local="Não informado", site="Gupy"),
     False, True, False),
    # Escopo declarado de fora do Brasil = internacional.
    ("escopo-latam", _vaga("Desenvolvedor Full Stack", local="Remote - LATAM"),
     False, False, True),
    # We Work Remotely é de fora por definição (o local é a sede).
    ("wwr", _vaga("Full Stack Developer", local="HQ: Ireland (Remote)", site="We Work Remotely"),
     False, False, True),
    ("intl-escopo-india-barra", _vaga("Full Stack Developer", local="Remote - India"),
     False, False, False),
]


@pytest.mark.parametrize(
    "nome,vaga,joinville,remoto,intl", CASOS_LOCAL_NOVOS, ids=[c[0] for c in CASOS_LOCAL_NOVOS]
)
def test_local_dos_perfis_novos(nome, vaga, joinville, remoto, intl):
    assert vaga.combina_com(PERFIL_DEV_JOINVILLE.regras) == joinville
    assert vaga.combina_com(PERFIL_DEV_REMOTO.regras) == remoto
    assert vaga.combina_com(PERFIL_DEV_INTL.regras) == intl


def test_remoto_e_intl_sao_disjuntos():
    """O banco guarda cada vaga uma vez só (ja_vista é global): se os dois
    aceitassem a mesma vaga, quem rodasse primeiro ficaria com ela."""
    for _, vaga, _j, remoto, intl in CASOS_LOCAL_NOVOS:
        assert not (remoto and intl)


def test_wwr_reconstruida_do_banco_nao_e_barrada_pela_sede():
    """MEDIDO (nov/2026): a página reavalia a vaga a partir do banco, onde o
    flag escopo_indefinido não é guardado — "HQ: Ireland" virava escopo."""
    vaga = Job(titulo="Full Stack Developer", empresa="", local="HQ: Ireland (Remote)", link="",
               site="We Work Remotely", modalidade="Remoto")
    assert vaga.escopo_indefinido
    assert vaga.combina_com(PERFIL_DEV.regras)


def test_perfis_novos_no_registro_e_dev_original_continua():
    for chave in ("dev", *SUBPERFIS_DEV, "analista"):
        assert chave in PERFIS
    assert SUBPERFIS_DEV == ("dev-joinville", "dev-remoto", "dev-intl")


def test_regras_novas_sao_opcionais_nos_outros_perfis():
    for perfil in (PERFIL_BR, PERFIL_ANALISTA):
        assert perfil.regras.stacks_backend_excluidas is None
        assert perfil.regras.excluir_remoto is False
        assert perfil.regras.mercado_vaga is None
        assert perfil.regras_anuncio is None
