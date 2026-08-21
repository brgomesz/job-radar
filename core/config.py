import os
from dotenv import load_dotenv

load_dotenv()

# Cargo forte: títulos diretos do seu perfil backend sênior
KEYWORDS_CARGO_FORTE = [
    "Desenvolvedor Java",
    "Desenvolvedor Backend",
    "Engenheiro de Software",
    "Software Engineer",
    "Java Developer",
    "Backend Developer",
    "Engenheiro Backend",
    "Desenvolvedor Spring Boot",
    "Arquiteto Java",
    "Especialista Java",
    "Arquiteto de Software",
]

# Cargo ambíguo: títulos genéricos de TI que só contam como match 
# se tiverem qualificadores de backend junto
KEYWORDS_CARGO_AMBIGUO = [
    "Desenvolvedor",
    "Developer",
    "Analista de Sistemas",
    "Engenheiro",
]

# Termo que precisa aparecer junto no título quando o cargo é ambíguo
QUALIFICADORES_DADOS = [
    "java",
    "spring",
    "backend",
    "back-end",
    "microserviços",
    "microservices",
    "api",
    "rest",
]

# Ferramentas ou frameworks que podem aparecer no título
FERRAMENTAS_TITULO = [
    "Spring Boot",
    "Java",
]

# Palavra de cargo que confirma a área técnica de desenvolvimento/engenharia
QUALIFICADORES_CARGO = [
    "desenvolvedor",
    "developer",
    "engenheiro",
    "engineer",
    "analista",
    "especialista",
    "specialist",
    "arquiteto",
    "architect",
]

KEYWORDS = KEYWORDS_CARGO_FORTE + KEYWORDS_CARGO_AMBIGUO

# Termos de busca extras para dar uma rede mais larga nas plataformas
TERMOS_CARGO_EXTRA = [
    "java spring",
    "backend java",
    "desenvolvedor java",
    "engenheiro de software",
]

TERMOS_CARGO = sorted(set(k.lower() for k in KEYWORDS) | set(TERMOS_CARGO_EXTRA))

# Ferramentas e tecnologias do seu stack usadas como buscas complementares
TERMOS_FERRAMENTA = [
    "java",
    "spring boot",
    "microservices",
    "rest api",
    "docker",
]

TERMOS_BUSCA = TERMOS_CARGO + TERMOS_FERRAMENTA

# Termos pesquisados prioritariamente em todos os ciclos (sua busca principal)
TERMOS_PRIORITARIOS = [
    "desenvolvedor java",
    "java developer",
    "backend developer",
    "software engineer",
    "desenvolvedor spring boot",
]

TERMOS_POR_CICLO = 10

# Whitelist de cidades aceitas para vagas híbridas/presenciais + Remoto
# Ajustado para sua localização (Carapicuíba/Grande SP)
CIDADES = [
    "Remoto",
    "São Paulo",
    "Carapicuíba",
    "Barueri",
    "Osasco",
    "Alphaville",
]

CIDADES_EUROPA_IBERICA = [
    "Portugal",
    "Lisboa",
    "Porto",
    "Braga",
    "Espanha",
    "España",
    "Spain",
    "Madrid",
    "Barcelona",
    "Valencia",
]

ATIVAR_EIXO_IBERICO_BR = False

LOCATIONS_LINKEDIN = ["Brazil"]

LOCATIONS_LINKEDIN_REMOTO_APENAS = ["Argentina", "Chile", "Mexico", "Colombia", "Espanha", "Portugal"]

LOCATIONS_LINKEDIN_CIDADES_PRESENCIAL = [c for c in CIDADES if c != "Remoto"]

MERCADOS_REMOTO_ACEITOS = ["Brasil", "LATAM", "Argentina", "Chile", "México", "Colômbia", "Portugal", "Espanha"]

INTERVALO_MINUTOS = int(os.getenv("INTERVALO_MINUTOS", 180))

LIMIAR_DIGEST_IMEDIATO = 7

DIGEST_HORA_UTC = 9

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

_RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.getenv("JOBRADAR_DB_PATH") or os.path.join(_RAIZ_PROJETO, "data", "jobs.db")
