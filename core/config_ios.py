"""Configuração do perfil de vagas para desenvolvimento iOS.

Os termos de busca formam uma rede ampla. A decisão de notificar continua
restrita às regras de título abaixo, para que menções a Swift ou iOS apenas na
descrição não gerem ruído.
"""

# Títulos que identificam diretamente uma função iOS.
KEYWORDS_IOS_FORTE = [
    "iOS Developer",
    "iOS Engineer",
    "iOS Software Engineer",
    "iOS Mobile Developer",
    "Desenvolvedor iOS",
    "Desenvolvedora iOS",
    "Engenheiro iOS",
    "Engenheira iOS",
    "Desenvolvedor de iOS",
    "iPhone Developer",
]

# Títulos genéricos só passam quando acompanhados de uma tecnologia iOS.
KEYWORDS_IOS_AMBIGUO = [
    "Mobile Developer",
    "Mobile Engineer",
    "Software Engineer",
    "Software Developer",
    "Desenvolvedor Mobile",
    "Desenvolvedor de Aplicativos",
    "Swift Developer",
    "Swift Engineer",
]

QUALIFICADORES_IOS = ["ios", "swift", "swiftui", "uikit", "xcode", "iphone", "ipad"]

# Uma tecnologia isolada também não basta: precisa haver indicação de cargo.
FERRAMENTAS_IOS_TITULO = ["Swift", "SwiftUI", "UIKit", "Xcode"]
QUALIFICADORES_CARGO_IOS = [
    "developer", "engineer", "desenvolvedor", "desenvolvedora",
    "engenheiro", "engenheira", "mobile", "software",
]

KEYWORDS_IOS = KEYWORDS_IOS_FORTE + KEYWORDS_IOS_AMBIGUO

TERMOS_IOS_EXTRA = ["swiftui", "uikit", "xcode ios", "iphone app developer"]
TERMOS_BUSCA_IOS = sorted(set(k.lower() for k in KEYWORDS_IOS) | set(TERMOS_IOS_EXTRA))
TERMOS_PRIORITARIOS_IOS = ["ios developer", "desenvolvedor ios", "ios engineer"]
TERMOS_POR_CICLO_IOS = 8

# Remoto em território brasileiro é aceito de qualquer cidade. As demais
# cidades cobrem vagas híbridas/presenciais nos principais polos de tecnologia
# e podem ser ajustadas sem tocar a lógica do filtro.
CIDADES_IOS = [
    "Remoto",
    "São Paulo",
    "Rio de Janeiro",
    "Belo Horizonte",
    "Curitiba",
    "Florianópolis",
    "Porto Alegre",
    "Recife",
    "Brasília",
]

MERCADOS_REMOTO_ACEITOS_IOS = ["Brasil"]
LOCATIONS_LINKEDIN_IOS = ["Brasil"]
LOCATIONS_LINKEDIN_REMOTO_APENAS_IOS: list[str] = []
LOCATIONS_LINKEDIN_CIDADES_IOS = [cidade for cidade in CIDADES_IOS if cidade != "Remoto"]
