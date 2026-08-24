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

    # Stack de fora ao lado da própria: complemento, não substituto.
    ("node-mais-python-passa", "Desenvolvedor Full Stack (Node + Python)", True),
    ("react-mais-java-passa", "Full Stack Developer - React / Java", True),

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
