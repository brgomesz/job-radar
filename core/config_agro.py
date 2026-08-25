"""Perfil agronomia — dados do perfil `agro`, montado em core/perfis.py.

Terceira pessoa deste fork. Mesma separação dos outros perfis: aqui é só
DADO (vocabulário de cargo, área, cidade, termo de busca); o motor e o
filtro são os mesmos.

Origem dos valores: currículo — Agronomia pela UFPR (2022), hoje gerente
de produção do setor de alho semente (Tecnoplanta, Piraquara/PR), com
estágios em assistência técnica a produtores de arroz (Urbano) e no
processo produtivo de fertilizantes (Fertipar, Paranaguá). Técnico em
mecânica pelo IFSC Joinville, inglês avançado.

Os quatro alvos declarados por ele são: assistência técnica ao produtor
rural, RTV (representante técnico de vendas), gerência de qualidade em
fertilizantes e gerência de produção em unidade de beneficiamento de
sementes. As áreas correlatas abaixo saem daí — não são chute: cobrem a
mesma cadeia (insumos, sementes, produção agrícola, qualidade) e os
cargos por onde essas quatro portas costumam ser anunciadas.
"""

# Cargo forte: título que já é inequivocamente da área dele.
#
# Cada grafia precisa estar escrita porque o match tem borda de palavra:
# "agrônomo" não bate "agrônoma", e "RTV" não bate "R.T.V.".
KEYWORDS_CARGO_FORTE_AGRO = [
    # --- Agronomia (formação)
    "Engenheiro Agrônomo",
    "Engenheira Agrônoma",
    "Engenheiro Agronômo",  # grafia errada comum em anúncio
    "Agrônomo",
    "Agrônoma",
    # --- Assistência técnica ao produtor rural (alvo 1)
    "Assistência Técnica Agrícola",
    "Assistente Técnico Agrícola",
    "Assistente Técnico Rural",
    "Consultor Agronômico",
    "Consultora Agronômica",
    "Consultor Agrícola",
    "Consultor Técnico Agrícola",
    "Consultor Técnico Rural",
    "Técnico Agrícola",
    "Técnico Agropecuário",
    # --- RTV / vendas técnicas de insumos (alvo 2)
    "RTV",
    "Representante Técnico de Vendas",
    "Representante Técnico",
    "Representante Comercial Agrícola",
    "Vendedor Técnico Agrícola",
    "Consultor de Vendas Agrícola",
    "Consultor de Insumos",
    "Executivo de Vendas Agrícola",
    # --- Qualidade em fertilizantes (alvo 3)
    "Analista de Qualidade Agrícola",
    "Gerente de Qualidade Agrícola",
    "Analista de Fertilizantes",
    "Analista de Nutrição Vegetal",
    "Consultor de Nutrição Vegetal",
    # --- Sementes / beneficiamento (alvo 4)
    "Unidade de Beneficiamento de Sementes",
    "Beneficiamento de Sementes",
    "Analista de Sementes",
    "Supervisor de Sementes",
    "Coordenador de Sementes",
    "Gerente de Sementes",
    "Produção de Sementes",
    "Analista de Produção Agrícola",
    # --- Produção e operação agrícola (correlatas dos quatro alvos)
    "Gerente de Produção Agrícola",
    "Gerente Agrícola",
    "Gerente de Fazenda",
    "Gestor Agrícola",
    "Supervisor Agrícola",
    "Supervisora Agrícola",
    "Coordenador Agrícola",
    "Coordenadora Agrícola",
    "Encarregado Agrícola",
    "Analista Agrícola",
    "Analista Agronômico",
    "Especialista Agrícola",
    "Planejamento Agrícola",
    "Pesquisador Agrícola",
    "Desenvolvimento de Mercado Agrícola",
]

# Cargo ambíguo: existe em qualquer setor ("Gerente de Qualidade" há em
# metalurgia, alimentos, farmacêutica). Só conta com um
# QUALIFICADORES_AREA_AGRO junto no título — mesma mecânica dos outros
# perfis. É o que permite cobrir "Gerência de qualidade em fertilizantes"
# sem trazer toda vaga de qualidade industrial de Joinville junto.
KEYWORDS_CARGO_AMBIGUO_AGRO = [
    "Analista",
    "Coordenador",
    "Coordenadora",
    "Supervisor",
    "Supervisora",
    "Gerente",
    "Gestor",
    "Gestora",
    "Consultor",
    "Consultora",
    "Especialista",
    "Encarregado",
    "Encarregada",
    "Representante",
    "Assistente Técnico",
    "Auxiliar Técnico",
    "Técnico",
    "Trainee",
]

# O que confirma que o cargo ambíguo é da área dele.
#
# "campo" NÃO entra, apesar de ser palavra da área ("consultor de campo"):
# "Técnico de Campo" e "Analista de Campo" são cargos comuns de telecom,
# energia e pesquisa de mercado, e o par cargo-ambíguo + "campo" abriria o
# radar pra todos eles.
QUALIFICADORES_AREA_AGRO = [
    "agrícola",
    "agricola",
    "agronômico",
    "agronomico",
    "agronomia",
    "agronegócio",
    "agronegocio",
    "agro",
    "rural",
    "produtor rural",
    "fazenda",
    "lavoura",
    "safra",
    "plantio",
    "colheita",
    "pós-colheita",
    "cultivo",
    "solo",
    "irrigação",
    "sementes",
    "semente",
    "mudas",
    "grãos",
    "graos",
    "soja",
    "milho",
    "trigo",
    "arroz",
    "feijão",
    "hortaliças",
    "fertilizantes",
    "fertilizante",
    "adubo",
    "adubação",
    "nutrição vegetal",
    "nutrição de plantas",
    "defensivos",
    "agroquímicos",
    "insumos agrícolas",
    "insumos",
    "beneficiamento",
    "armazenagem",
    "cooperativa agrícola",
    "revenda agrícola",
]

# Área/produto como núcleo do título ("Analista de Fertilizantes"). Só
# aprova com palavra de cargo junto (QUALIFICADORES_CARGO_AGRO) — espelho
# da regra do cargo ambíguo. Também é o que dá os 2 pontos de "ferramenta
# no título" no score, colocando a vaga que nomeia a especialidade dele
# acima da genérica.
FERRAMENTAS_TITULO_AGRO = [
    "Fertilizantes",
    "Sementes",
    "Defensivos",
    "Insumos Agrícolas",
    "Nutrição Vegetal",
    "Irrigação",
    "Agronegócio",
    "Grãos",
]

QUALIFICADORES_CARGO_AGRO = [
    "analista",
    "coordenador",
    "coordenadora",
    "supervisor",
    "supervisora",
    "gerente",
    "gestor",
    "consultor",
    "consultora",
    "especialista",
    "representante",
    "técnico",
    "tecnico",
    "engenheiro",
    "engenheira",
    "encarregado",
    "assistente",
]

# Rejeição INCONDICIONAL (ver titulos_excluidos em core/job.py). Área de
# fora que usaria o mesmo vocabulário de cargo: "Analista de Sistemas
# Agrícolas" e "Desenvolvedor (agro tech)" são vaga de TI, não de campo.
#
# Curta de propósito: no perfil dele o par cargo-ambíguo + qualificador já
# faz quase todo o trabalho, porque o que define a área ("agrícola",
# "sementes", "fertilizantes") raramente aparece fora dela.
TITULOS_EXCLUIDOS_AGRO = [
    "software",
    "sistemas",
    "desenvolvedor",
    "programador",
    "full stack",
    "telecom",
    "telecomunicações",
]

# Ele tem 3 anos de formado e já é gerente de produção: estágio e trainee
# são passo atrás. Júnior FICA — é como muita vaga de RTV e de assistência
# técnica entra na carreira, e o nível declarado no título nem sempre
# corresponde ao que a empresa aceita.
NIVEIS_EXCLUIDOS_AGRO = [
    "Estágio/Trainee",
]

# Alvo largo de propósito: dos quatro cargos que ele quer, dois são de
# gerência. No padrão global "Liderança" vale -2, o que rebaixaria
# justamente "Gerente de Produção" e "Gerente de Qualidade" — os alvos
# declarados dele.
NIVEIS_ALVO_AGRO = [
    "Pleno",
    "Sênior",
    "Especialista",
    "Liderança",
]

# Localização. Ele aceita Santa Catarina e Paraná inteiros, com
# preferência por Joinville e região e por Piraquara/Curitiba e região.
#
# Os dois estados entram como NOME e como SIGLA porque as fontes escrevem
# de formas diferentes: o LinkedIn usa "Joinville, Santa Catarina, Brazil"
# e a Gupy/Catho usam "Joinville - SC". Sem as duas grafias, metade das
# vagas do estado escaparia por causa do formato do texto.
#
# As cidades nominais existem pras fontes que escrevem só o município, sem
# estado nenhum — aí nem o nome nem a sigla do estado aparecem no texto.
CIDADES_AGRO = [
    "Remoto",
    # Estados inteiros (as duas grafias)
    "Santa Catarina",
    "Paraná",
    "SC",
    "PR",
    # --- Joinville e região (norte catarinense)
    "Joinville",
    "Araquari",
    "Guaramirim",
    "Jaraguá do Sul",
    "São Francisco do Sul",
    "Garuva",
    "Schroeder",
    "Barra Velha",
    "Corupá",
    "Massaranduba",
    "São Bento do Sul",
    "Campo Alegre",
    "Rio Negrinho",
    "Mafra",
    "Itapoá",
    # --- Piraquara / Curitiba e região metropolitana
    "Curitiba",
    "Piraquara",
    "São José dos Pinhais",
    "Pinhais",
    "Colombo",
    "Quatro Barras",
    "Campina Grande do Sul",
    "Almirante Tamandaré",
    "Araucária",
    "Fazenda Rio Grande",
    "Campo Largo",
    "Balsa Nova",
    "Contenda",
    "Mandirituba",
    "Tijucas do Sul",
    "Bocaiúva do Sul",
    "Rio Branco do Sul",
    "Lapa",
    "Morretes",
    "Paranaguá",
    "Antonina",
]

# Rotina agronômica é presencial e a legislação de insumos é nacional:
# vaga remota de outro país não se aproveita.
MERCADOS_REMOTO_ACEITOS_AGRO = ["Brasil"]

TERMOS_PRIORITARIOS_AGRO = [
    "engenheiro agrônomo",
    "assistência técnica agrícola",
    "representante técnico de vendas",
    "analista agrícola",
]

TERMOS_BUSCA_AGRO = TERMOS_PRIORITARIOS_AGRO + [
    "consultor agronômico",
    "consultor técnico agrícola",
    "técnico agrícola",
    "vendedor técnico agrícola",
    "gerente de produção agrícola",
    "supervisor agrícola",
    "coordenador agrícola",
    "beneficiamento de sementes",
    "analista de sementes",
    "produção de sementes",
    "analista de fertilizantes",
    "qualidade fertilizantes",
    "nutrição vegetal",
    "insumos agrícolas",
    "agronegócio",
    "gerente agrícola",
]

TERMOS_POR_CICLO_AGRO = 8

# Busca nacional + uma passada por cidade. Curitiba cobre a região
# metropolitana inteira (Piraquara inclusive) no filtro do LinkedIn;
# Joinville cobre o norte catarinense; Ponta Grossa entra porque é o polo
# agrícola do Paraná, onde a maior parte da vaga de campo do estado é
# anunciada — e nenhuma das duas outras alcança.
LOCATIONS_LINKEDIN_AGRO = ["Brazil"]
LOCATIONS_LINKEDIN_CIDADES_AGRO = ["Joinville", "Curitiba", "Ponta Grossa"]
