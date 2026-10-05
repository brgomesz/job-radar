"""Perfil Analista — dados do perfil `analista`, montado em core/perfis.py.

Mesma separação dos outros perfis: aqui é só DADO (vocabulário de cargo,
qualificador, termo de busca), o motor e o filtro são os mesmos.

Mesma pessoa do perfil `admin` (7+ anos em rotinas administrativas e
financeiras no mercado imobiliário, Administração, Joinville/SC), com
outro recorte, pedido por ela em out/2026: em vez de "qualquer analista da
área", mira coordenação/gerência/supervisão administrativa e financeira,
operações, contratos e sales ops — e analista só quando o título traz
nível sênior ou o setor imobiliário/comercial. O `admin` continua rodando
como estava; os dois perfis convivem.
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
    "Analista de Planejamento",
]

# O que libera o cargo ambíguo acima: nível sênior ou setor imobiliário/
# comercial. Ocupa o campo `qualificadores_dados` de RegrasFiltro (nome
# herdado do primeiro perfil; a função é "o que qualifica esse cargo").
# Plural com "s" já é aceito pelo filtro; "comerciais" não é "comercial"
# + s, por isso vem escrito à parte.
QUALIFICADORES_AREA_ANALISTA = [
    # --- Nível
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
]

# Prioridade da usuária: Sênior, Especialista e Coordenação/Supervisão/
# Gerência ("Liderança" em _detectar_senioridade) pontuam o teto. Pleno
# fica neutro (fora do alvo e fora da penalidade: 0 ponto). No padrão
# global os três valeriam -2.
NIVEIS_ALVO_ANALISTA = [
    "Sênior",
    "Especialista",
    "Liderança",
]

CIDADES_ANALISTA = [
    "Remoto",
    "Joinville",
]

# Só Brasil: rotina administrativa e financeira segue legislação
# nacional — vaga remota de outro país não se aproveita. Vaga
# remota que não declara mercado continua passando (não há base pra
# rejeitar).
MERCADOS_REMOTO_ACEITOS_ANALISTA = ["Brasil"]

TERMOS_PRIORITARIOS_ANALISTA = [
    "coordenador administrativo financeiro",
    "gerente administrativo financeiro",
    "analista administrativo financeiro",
    "analista de operações comerciais",
    "coordenador de contratos",
]

# Prioritários rodam em TODO ciclo; estes entram no rodízio. Com 4 extras
# e TERMOS_POR_CICLO_ANALISTA = 8, na prática também rodam todo ciclo.
TERMOS_BUSCA_ANALISTA = TERMOS_PRIORITARIOS_ANALISTA + [
    "sienge",
    "incorporadora",
    "imobiliária",
    "sales operations",
]

TERMOS_POR_CICLO_ANALISTA = 8

LOCATIONS_LINKEDIN_ANALISTA = ["Brazil"]
LOCATIONS_LINKEDIN_CIDADES_ANALISTA = ["Joinville"]
