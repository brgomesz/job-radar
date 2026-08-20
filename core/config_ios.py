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

# Aceita vagas remotas no Brasil e no exterior. Para modalidade presencial ou
# híbrida, a única cidade de interesse é Joinville.
CIDADES_IOS = [
    "Remoto",
    "Joinville",
]

# None preserva vagas remotas sem limitação de país: Brasil e mercado
# internacional. A restrição geográfica só continua valendo para vagas não
# remotas, via CIDADES_IOS.
MERCADOS_REMOTO_ACEITOS_IOS = None
LOCATIONS_LINKEDIN_IOS = ["Brasil"]
# Países internacionais consultados no LinkedIn somente com o filtro nativo
# de remoto. We Work Remotely complementa a cobertura global.
LOCATIONS_LINKEDIN_REMOTO_APENAS_IOS = [
    "Spain", "Portugal", "Mexico", "Colombia", "Argentina", "Chile",
]
LOCATIONS_LINKEDIN_CIDADES_IOS = [cidade for cidade in CIDADES_IOS if cidade != "Remoto"]
