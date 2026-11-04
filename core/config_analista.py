"""Perfil Analista — dados do perfil `analista`, montado em core/perfis.py.

Mesma separação dos outros perfis: aqui é só DADO (vocabulário de cargo,
qualificador, termo de busca), o motor e o filtro são os mesmos.

Pessoa com 7+ anos em rotinas administrativas e financeiras no mercado
imobiliário (Administração, Joinville/SC). Recorte pedido por ela em
out/2026: em vez de "qualquer analista da área", mira coordenação/
gerência/supervisão administrativa e financeira, operações, contratos e
sales ops — e analista só quando o título traz nível sênior ou o setor
imobiliário/comercial. Era o segundo perfil dela, ao lado do `admin`; o
`admin` foi removido em nov/2026 e este ficou como o único.

Revisado em nov/2026 contra o currículo dela (Gerente Financeira e
Operacional Sênior numa imobiliária; antes, 7 anos de Analista
Administrativo em locação): além de adm-financeiro, operações e
contratos, entram as áreas afins que o currículo sustenta — mercado
imobiliário/locação, RH (MBA em RH; recrutamento e onboarding),
planejamento financeiro (FP&A), contas a pagar/receber e cobrança,
backoffice e office manager. Faixa: pleno a sênior, mais coordenação/
gerência. Local: presencial/híbrido só em Joinville; remoto só quando o
TÍTULO diz (ver REMOTO_NO_TITULO_ANALISTA).
"""

# Cargo forte: aprova SOZINHO pelo título. Variantes de gênero escritas
# uma a uma porque o casamento é por texto ("financeira" não contém
# "financeiro"). O marcador "(a)" ("Coordenador(a) Administrativo(a)") é
# tirado do título antes da comparação (ver _sem_marcador_genero em
# core/job.py), então não precisa de variante própria.
KEYWORDS_CARGO_FORTE_ANALISTA = [
    # --- Coordenação
    "Coordenador Administrativo Financeiro",
    "Coordenadora Administrativa Financeira",
    "Coordenador Administrativo e Financeiro",
    "Coordenadora Administrativa e Financeira",
    "Coordenador Administrativo",
    "Coordenadora Administrativa",
    "Coordenador Financeiro",
    "Coordenadora Financeira",
    "Coordenador de Operações",
    "Coordenadora de Operações",
    "Coordenador de Contratos",
    "Coordenadora de Contratos",
    # --- Gerência
    "Gerente Administrativo Financeiro",
    "Gerente Administrativa Financeira",
    "Gerente Administrativo e Financeiro",
    "Gerente Administrativa e Financeira",
    "Gerente Administrativo",
    "Gerente Administrativa",
    "Gerente Financeiro",
    "Gerente Financeira",
    "Gerente de Operações",
    "Gerente Operacional",
    # --- Supervisão
    "Supervisor Administrativo",
    "Supervisora Administrativa",
    "Supervisor Financeiro",
    "Supervisora Financeira",
    # --- Analista (só os títulos que já são inequívocos)
    "Analista Administrativo Financeiro",
    "Analista Administrativa Financeira",
    "Analista Administrativo e Financeiro",
    "Analista Administrativa e Financeira",
    "Analista de Operações Comerciais",
    # --- Sales Ops e contratos
    "Sales Operations",
    "Sales Ops",
    "Gestor de Contratos",
    "Gestora de Contratos",
    # --- Mercado imobiliário / locação (o setor dela há 8 anos)
    "Gerente Imobiliário",
    "Gerente Imobiliária",
    "Coordenador Imobiliário",
    "Coordenadora Imobiliária",
    "Gerente de Locação",
    "Coordenador de Locação",
    "Coordenadora de Locação",
    "Supervisor de Locação",
    "Supervisora de Locação",
    # --- Gestão de escritório / suporte à diretoria
    "Office Manager",
    "Gerente de Escritório",
    "Coordenador de Backoffice",
    "Coordenadora de Backoffice",
    # --- Planejamento financeiro
    "FP&A",
    # --- RH (MBA em RH; montou recrutamento e onboarding)
    "Coordenador de RH",
    "Coordenadora de RH",
    "Coordenador de Recursos Humanos",
    "Coordenadora de Recursos Humanos",
    "Gerente de RH",
    "Gerente de Recursos Humanos",
    "Business Partner de RH",
    "HR Business Partner",
    "HRBP",
]

# Cargo que só aprova com um QUALIFICADORES_AREA_ANALISTA junto no título:
# "Analista Financeiro" sozinho não entra, "Analista Financeiro Sênior" e
# "Analista Financeiro - Incorporadora" entram. Mesma mecânica de
# "Business Analyst" + "dados" no perfil de dados.
KEYWORDS_CARGO_AMBIGUO_ANALISTA = [
    "Analista Administrativo",
    "Analista Administrativa",
    "Analista de Operações",
    "Analista de Contratos",
    "Analista Financeiro",
    "Analista Financeira",
    "Analista de Processos",
    # Cobre "Analista de Planejamento Financeiro" também (casa por trecho).
    "Analista de Planejamento",
    # --- Áreas afins do currículo (nov/2026)
    "Analista de Locação",
    "Analista de Contas a Pagar",
    "Analista de Contas a Receber",
    "Analista de Cobrança",
    "Analista de Backoffice",
    "Analista de Back Office",
    "Analista de RH",
    "Analista de Recursos Humanos",
    "Analista de Recrutamento",
]

# O que libera o cargo ambíguo acima: nível sênior ou setor imobiliário/
# comercial. Ocupa o campo `qualificadores_dados` de RegrasFiltro (nome
# herdado do primeiro perfil; a função é "o que qualifica esse cargo").
# Plural com "s" já é aceito pelo filtro; "comerciais" não é "comercial"
# + s, por isso vem escrito à parte.
QUALIFICADORES_AREA_ANALISTA = [
    # --- Nível (pleno entrou em nov/2026: a faixa pedida é pleno a sênior,
    # e sem isto "Analista Financeiro Pleno" caía por falta de qualificador)
    "pleno",
    "plena",
    # "II" é o degrau pleno da escada I/II/III (o I é barrado como júnior).
    "ii",
    "sênior",
    "senior",
    "sr",
    "iii",
    "especialista",
    # --- Setor
    "imobiliário",
    "imobiliária",
    "incorporadora",
    "incorporação",
    "construtora",
    "loteadora",
    "real estate",
    # Sienge é o ERP de construtora/incorporadora: no título, é sinal de
    # setor tão forte quanto "construtora". Entrou junto com o termo de
    # busca "sienge" — sem isto, o que essa busca traz cairia quase todo.
    "sienge",
    "comercial",
    "comerciais",
    "vendas",
]

# Sem lista de ferramentas (ver _REGRAS_ANALISTA em core/perfis.py): a
# rota "ferramenta + palavra de cargo" aprovaria "Analista Financeiro
# Pleno Protheus" por fora da regra de qualificador acima.

# Rejeição INCONDICIONAL por termo no título (ver titulos_excluidos em
# core/job.py): nenhum destes passa, em nenhuma combinação — nem cargo
# forte salva.
TITULOS_EXCLUIDOS_ANALISTA = [
    # --- Nível abaixo do alvo (pedido da usuária). niveis_excluidos já
    # barra júnior/estágio DETECTADOS; aqui cobre o resto do vocabulário
    # ("jovem aprendiz", "auxiliar", "assistente") e feminino/plural que a
    # detecção de nível não pega.
    "estágio",
    "estagiário",
    "estagiária",
    "trainee",
    "jovem aprendiz",
    "aprendiz",
    "auxiliar",
    "auxiliares",
    "assistente",
    "júnior",
    "junior",
    "jr",
    # --- Área fora do escopo (pedido da usuária)
    "contábil",
    "contábeis",
    "contabilidade",
    "fiscal",
    "fiscais",
    "tributário",
    "tributária",
    "controladoria",
    "tesouraria",
    # Departamento pessoal / folha (nov/2026): não está no currículo dela e
    # é vizinho do fiscal. "Analista de RH Sênior (Foco em folha)" entrava
    # pela regra de RH.
    "departamento pessoal",
    "dp",
    "folha",
    # --- Área de fora que usa o mesmo vocabulário de cargo. Não vieram no
    # pedido, mas são a proteção que já existia: "Coordenador de
    # Operações" e "Analista de Processos" são cargos dela, mas em
    # Joinville (polo industrial) o falso positivo mais provável é
    # "Gerente de Operações Industriais" / "Analista de Processos de
    # Software". "comercial" e "vendas" SAÍRAM desta lista: agora são
    # qualificadores.
    "sistemas",
    "software",
    "desenvolvimento de software",
    "ti",
    "dados",
    "bi",
    "business intelligence",
    "infraestrutura",
    "redes",
    "suporte técnico",
    "helpdesk",
    "help desk",
    # "industriais" escrito à parte: o plural português não é só "+s".
    "industrial",
    "industriais",
    "produção",
    "manufatura",
    "pcp",
    "qualidade",
    "logística",
    "marketing",
    "engenharia",
    "laboratório",
    "enfermagem",
]

# Estágio, trainee e júnior nem notificam (pedido da usuária: "penalizar").
# Como não chegam ao ranking, a penalidade vira exclusão — reforçada pelos
# termos em TITULOS_EXCLUIDOS_ANALISTA.
NIVEIS_EXCLUIDOS_ANALISTA = [
    "Estágio/Trainee",
    "Júnior",
    # "Analista Financeiro I" é o degrau de entrada da escada I/II/III —
    # júnior com outro nome. II (pleno) e III (sênior) continuam.
    "Nível I",
]

# Faixa pedida: pleno a sênior, mais Especialista e Coordenação/
# Supervisão/Gerência ("Liderança" em _detectar_senioridade) — todos
# pontuam o teto. No padrão global Sênior/Especialista/Liderança valeriam -2.
NIVEIS_ALVO_ANALISTA = [
    "Pleno",
    "Sênior",
    "Especialista",
    "Liderança",
]

# Presencial/híbrido só em Joinville. "Remoto" aqui liga a rota de vaga
# remota, mas com REMOTO_NO_TITULO_ANALISTA abaixo ela só vale quando o
# título declara — a marcação "Remoto" do LinkedIn não basta.
CIDADES_ANALISTA = [
    "Remoto",
    "Joinville",
]

# Termos que tornam uma vaga "expressamente remota" (ver
# remoto_exige_titulo em core/job.py). Título que também diz híbrido ou
# presencial não conta.
REMOTO_NO_TITULO_ANALISTA = [
    "remoto",
    "remota",
    "home office",
    "home-office",
    "homeoffice",
    "teletrabalho",
    "trabalho de casa",
    "100% online",
    "remote",
]

# Só Brasil: rotina administrativa e financeira segue legislação
# nacional — vaga remota de outro país não se aproveita. Vaga
# remota que não declara mercado continua passando (não há base pra
# rejeitar).
MERCADOS_REMOTO_ACEITOS_ANALISTA = ["Brasil"]

# Os cargos mais próximos do currículo, em TODO ciclo. Os dois com
# "remoto" existem porque remoto só vale com o termo no título: a busca
# com a palavra junto traz justamente esses anúncios pra cima.
TERMOS_PRIORITARIOS_ANALISTA = [
    "coordenador administrativo financeiro",
    "gerente administrativo financeiro",
    "analista administrativo financeiro",
    "gerente financeiro",
    "coordenador financeiro",
    "analista financeiro remoto",
]

# Rodízio: 16 termos em blocos de TERMOS_POR_CICLO_ANALISTA = 8 — cada um
# roda a cada 2 ciclos (6h).
TERMOS_BUSCA_ANALISTA = TERMOS_PRIORITARIOS_ANALISTA + [
    "analista administrativo remoto",
    "analista de operações comerciais",
    "coordenador de contratos",
    "analista de contratos",
    "gerente de locação",
    "analista de locação",
    "gerente operacional",
    "office manager",
    "fp&a",
    "analista de recursos humanos",
    "coordenador de rh",
    "sales operations",
    "sienge",
    "incorporadora",
    "imobiliária",
    "home office financeiro",
]

TERMOS_POR_CICLO_ANALISTA = 8

LOCATIONS_LINKEDIN_ANALISTA = ["Brazil"]
LOCATIONS_LINKEDIN_CIDADES_ANALISTA = ["Joinville"]
