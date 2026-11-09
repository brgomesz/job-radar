"""Perfis dev (full-stack, foco back-end Node/TypeScript) — dados dos perfis
`dev`, `dev-joinville`, `dev-remoto` e `dev-intl`, montados em
core/perfis.py.

Fica separado de config.py (dados/BI) e config_intl.py pelo mesmo motivo
que aqueles dois são separados entre si: o que muda de um perfil pro outro
é DADO — vocabulário de cargo, stack, cidade, mercado, termo de busca — e
não lógica. O motor (main.py) e o filtro (core/job.py) são os mesmos.

Origem dos valores: currículo do usuário (revisado em nov/2026) —
Desenvolvedor Full-Stack Pleno em Joinville/SC, ~3 anos com JavaScript/
TypeScript. Back-end: Node.js, APIs REST, Prisma, Jest, PostgreSQL, SQL
Server, Supabase. Front-end: React, Next.js, Tailwind, Chakra UI, MUI.
Infra: AWS (Cloud Practitioner, SES), Docker, GitHub Actions, Linux/VPS,
n8n. Inglês intermediário (leitura técnica fluente). NÃO tem: Java,
Kotlin, .NET/C#, PHP, Python, Go, Ruby, Angular, Vue, mobile.

Os quatro perfis dev compartilham a regra de CARGO e de STACK (tudo daqui
até NIVEIS_EXCLUIDOS_DEV); o que muda entre eles é só ONDE a vaga é:
  - dev-joinville: presencial ou híbrido, só em Joinville;
  - dev-remoto:    remoto, empresa brasileira (anúncio em português);
  - dev-intl:      remoto, vaga em inglês / empresa de fora;
  - dev:           o perfil original (remoto + Joinville), que continua no
                   código e na página como "Dev (geral)" — ver core/perfis.py.
"""

# ---------------------------------------------------------------------------
# Cargo (comum aos perfis dev)
# ---------------------------------------------------------------------------

# Cargo forte: título que já é inequivocamente vaga de desenvolvimento na
# faixa do usuário (back, full-stack ou front). Diferente do perfil de
# dados, aqui o cargo forte é GENÉRICO de propósito — a maioria das vagas
# não põe a stack no título ("Desenvolvedor Back-end Pleno" e ponto), e
# exigir stack junto (regra de keywords_ambiguo) descartaria justamente as
# mais comuns. Quem paga o custo dessa abertura é `STACKS_*_EXCLUIDAS_DEV`
# (título) e REGRAS_ANUNCIO_DEV (texto do anúncio).
#
# Cada grafia precisa estar escrita: o match tem borda de palavra, então
# "backend" não bate "back-end" nem "back end", e "desenvolvedora" não bate
# "desenvolvedor". Não é redundância — é a lista de como as fontes de fato
# escrevem.
KEYWORDS_CARGO_FORTE_DEV = [
    # Back-end
    "Desenvolvedor Back-end",
    "Desenvolvedor Backend",
    "Desenvolvedor Back End",
    "Desenvolvedora Back-end",
    "Desenvolvedora Backend",
    "Back-end Developer",
    "Backend Developer",
    "Back End Developer",
    "Back-end Engineer",
    "Backend Engineer",
    "Backend Software Engineer",
    # Full-stack
    "Desenvolvedor Full-Stack",
    "Desenvolvedor Fullstack",
    "Desenvolvedor Full Stack",
    "Desenvolvedora Full-Stack",
    "Desenvolvedora Fullstack",
    "Desenvolvedora Full Stack",
    "Full-Stack Developer",
    "Fullstack Developer",
    "Full Stack Developer",
    "Full-Stack Engineer",
    "Fullstack Engineer",
    "Full Stack Engineer",
    # Front-end (aceito, mas é a terceira preferência do usuário — quem
    # coloca back/full na frente é o score, não o filtro: vaga que nomeia a
    # stack dele no título ganha os pontos de ferramenta e sobe no ranking)
    "Desenvolvedor Front-end",
    "Desenvolvedor Frontend",
    "Desenvolvedor Front End",
    "Desenvolvedora Front-end",
    "Desenvolvedora Frontend",
    "Front-end Developer",
    "Frontend Developer",
    "Front End Developer",
    "Front-end Engineer",
    "Frontend Engineer",
    # Cargo que já traz a stack no nome — não precisa de qualificador
    # nenhum, o título inteiro já é o sinal
    "Desenvolvedor Node",
    "Desenvolvedor Node.js",
    "Node.js Developer",
    "Node Developer",
    "Node.js Engineer",
    "Desenvolvedor JavaScript",
    "JavaScript Developer",
    "Desenvolvedor TypeScript",
    "TypeScript Developer",
    "Desenvolvedor React",
    "React Developer",
    "React Engineer",
    "Desenvolvedor Next.js",
    "Next.js Developer",
    "Desenvolvedor NestJS",
    "NestJS Developer",
]

# Cargo ambíguo: existe em qualquer stack e em qualquer área de TI (e às
# vezes fora dela — "Engenheiro" sozinho é engenharia civil). Só conta se o
# título TAMBÉM trouxer um QUALIFICADORES_STACK_DEV junto. Mesma mecânica
# que "Business Analyst" + "dados" no perfil de dados.
KEYWORDS_CARGO_AMBIGUO_DEV = [
    "Desenvolvedor",
    "Desenvolvedora",
    "Developer",
    "Programador",
    "Programadora",
    "Engenheiro de Software",
    "Engenheira de Software",
    "Software Engineer",
    "Software Developer",
    "Analista de Sistemas",
    "Analista Desenvolvedor",
    "Analista Programador",
    "Web Developer",
]

# O que confirma que o cargo ambíguo é da stack do usuário. Ocupa o campo
# `qualificadores_dados` de RegrasFiltro (o nome do campo vem do perfil que
# nasceu primeiro; a função é a mesma — "o que qualifica esse cargo").
QUALIFICADORES_STACK_DEV = [
    "node",
    "node.js",
    "nodejs",
    "javascript",
    "js",
    "typescript",
    "ts",
    "react",
    "reactjs",
    "react.js",
    "next",
    "next.js",
    "nextjs",
    "nest",
    "nestjs",
    "express",
    "prisma",
    "fullstack",
    "full-stack",
    "full stack",
    "backend",
    "back-end",
    "back end",
    "frontend",
    "front-end",
    "front end",
    "api",
    "apis",
    "rest",
    "web",
]

# Ferramenta como núcleo do título ("Desenvolvedor Prisma"). Só aprova com
# palavra de cargo junto (QUALIFICADORES_CARGO_DEV) — espelho da regra de
# cargo ambíguo. Também dá os pontos de "ferramenta" no score: vaga que
# nomeia a stack do currículo sobe no ranking.
FERRAMENTAS_TITULO_DEV = [
    "Node",
    "Node.js",
    "NodeJS",
    "JavaScript",
    "TypeScript",
    "React",
    "ReactJS",
    "Next.js",
    "NextJS",
    "NestJS",
    "Express",
    "Prisma",
    "PostgreSQL",
    "Postgres",
    "SQL Server",
    "Supabase",
    "Tailwind",
    "Chakra UI",
    "Docker",
    "n8n",
]

# Palavra de cargo que confirma que a vaga de ferramenta é de
# desenvolvimento. Aqui "desenvolvedor"/"developer"/"engenheiro" ENTRAM —
# é o oposto exato do perfil de dados (ver QUALIFICADORES_CARGO em
# config.py), onde eles ficam de fora justamente pra manter vaga de dev
# longe do radar.
QUALIFICADORES_CARGO_DEV = [
    "desenvolvedor",
    "desenvolvedora",
    "developer",
    "engenheiro",
    "engenheira",
    "engineer",
    "programador",
    "programadora",
    "dev",
]

# ---------------------------------------------------------------------------
# Stack de fora, no TÍTULO
# ---------------------------------------------------------------------------

# Back-end de outro ecossistema. Título que nomeia uma destas é descartado,
# a menos que nomeie também uma STACKS_BACKEND_PERDAO_DEV (Node) — ver
# stacks_backend_excluidas em core/job.py.
#
# MEDIDO (nov/2026): o perdão antigo era qualquer ferramenta do usuário, e
# "Fullstack Java/React", "Laravel and React Developer", "Desenvolvedor
# Full Stack .NET/React ou Angular" e "Desenvolvedor C# SQL Server"
# passavam pelo React/SQL Server. Numa vaga full-stack o back-end é a
# outra stack; o React não muda isso.
#
# "java" não pega "javascript" (borda de palavra). ".net" bate até grudado
# ("Backend.NET" — ver _padrao_stack em core/job.py). "go" sozinho NÃO
# entra (verbo em inglês, "Go-to-market"): só nas formas abaixo, que são
# como a linguagem aparece em título.
STACKS_BACKEND_EXCLUIDAS_DEV = [
    "java",
    "jvm",
    "spring",
    "spring boot",
    "kotlin",
    "scala",
    ".net",
    "asp.net",
    "dotnet",
    "c#",
    "vb.net",
    "c++",
    "php",
    "laravel",
    "symfony",
    "codeigniter",
    "python",
    "django",
    "flask",
    "fastapi",
    "ruby",
    "rails",
    "golang",
    "(go)",
    "go developer",
    "go engineer",
    "backend go",
    "back-end go",
    "desenvolvedor go",
    "elixir",
    "rust",
    "delphi",
    "cobol",
    "abap",
    "sap",
    "salesforce",
    "apex",
    "advpl",
    "protheus",
    "genexus",
    "clojure",
    "perl",
]

# Só stack de back-end do usuário salva um back-end de fora: "Back-End
# Java/Node" e "Full Stack (Node + Python)" passam; "Java/React" não.
STACKS_BACKEND_PERDAO_DEV = [
    "node",
    "node.js",
    "nodejs",
    "nestjs",
    "nest.js",
    "express",
    "express.js",
]

# Front-end de outro ecossistema, mobile e plataforma fechada. Perdoados
# por qualquer stack do usuário que mude a natureza da vaga (Node, React,
# Next): "Frontend Angular/React" e "Fullstack Node + Vue" passam,
# "Desenvolvedor JavaScript/Angular" não (JavaScript não perdoa mais —
# toda vaga Angular é JavaScript/TypeScript).
STACKS_EXCLUIDAS_DEV = [
    "angular",
    "angularjs",
    "vue",
    "vuejs",
    "vue.js",
    "nuxt",
    "svelte",
    "ember",
    # Mobile — outra carreira, não é o que o usuário faz
    "react native",
    "flutter",
    "dart",
    "android",
    "ios",
    "swift",
    "xamarin",
    "ionic",
    "mobile",
    # Plataforma
    "wordpress",
    "magento",
    "sharepoint",
    "powerbuilder",
]

STACKS_PERDAO_DEV = [
    "node",
    "node.js",
    "nodejs",
    "nestjs",
    "nest.js",
    "express",
    "react",
    "reactjs",
    "react.js",
    "next.js",
    "nextjs",
]

# ---------------------------------------------------------------------------
# Nível e cargos fora da faixa
# ---------------------------------------------------------------------------

# Nível: o usuário pediu "pleno apenas". Vaga SEM nível declarado no título
# continua passando — é a maioria absoluta dos anúncios, e descartar por
# omissão esvaziaria o radar (ver niveis_excluidos em core/job.py).
# "Nível I" é a porta de entrada nas empresas que numeram (I = júnior);
# "Nível IV" fica acima de sênior. II e III passam: dependendo da empresa,
# um dos dois é o pleno.
NIVEIS_EXCLUIDOS_DEV = [
    "Estágio/Trainee",
    "Júnior",
    "Sênior",
    "Especialista",
    "Liderança",
    "Nível I",
    "Nível IV",
]

# Rejeição incondicional (sem perdão nenhum) — ver titulos_excluidos em
# core/job.py.
#
# MEDIDO (nov/2026): "Staff Software Engineer - Frontend", "Staff Backend
# Developer", "Lead Front-End Developer (React)" chegavam como se fossem
# pleno — staff/lead/principal não são nível que _detectar_senioridade
# conheça, e caíam em "Não especificado". Os demais são cargo de outra
# área que entra pela palavra "developer"/"engineer" (QA, DevOps, dados).
TITULOS_EXCLUIDOS_DEV = [
    "staff",
    "principal",
    "lead",
    "leader",
    "lider",
    "arquiteto",
    "arquiteta",
    "architect",
    "cto",
    "qa",
    "quality assurance",
    "tester",
    "devops",
    "sre",
    "data engineer",
    "engenheiro de dados",
    "engenheira de dados",
    "machine learning",
    "mlops",
    "instrutor",
    "instrutora",
    "professor",
    "professora",
    "tutor",
    "estagiario",
    "estagiaria",
    "intern",
    "internship",
    "aprendiz",
]

# ---------------------------------------------------------------------------
# Texto do anúncio (core/anuncio.py)
# ---------------------------------------------------------------------------

# Stack do currículo, lida no anúncio inteiro. Separada por camada porque a
# regra muda com o tipo de vaga: numa vaga de back-end/full-stack o que
# importa é o back-end ser Node; numa de front, ser React.
#
# "express" sozinho não entra (verbo em inglês: "express interest"); só
# com o .js. "spring" sozinho também não (estação do ano em inglês).
ANUNCIO_BACKEND_PROPRIO = [
    "node", "node.js", "nodejs", "nestjs", "nest.js", "express.js", "expressjs",
    "fastify", "prisma", "typeorm", "sequelize",
]
ANUNCIO_FRONT_PROPRIO = ["react", "reactjs", "react.js", "next.js", "nextjs"]
ANUNCIO_LINGUAGEM_PROPRIA = ["typescript", "javascript"]

ANUNCIO_FAMILIAS_BACKEND_ALHEIAS = {
    "Java/Kotlin": [
        "java", "kotlin", "spring boot", "spring framework", "spring mvc", "spring cloud",
        "spring data", "spring security", "jvm", "quarkus", "micronaut", "hibernate",
    ],
    ".NET/C#": [".net", "asp.net", "dotnet", "c#", "vb.net", "entity framework", "blazor"],
    "PHP": ["php", "laravel", "symfony", "codeigniter", "cakephp"],
    "Python": ["python", "django", "flask", "fastapi"],
    "Ruby": ["ruby", "rails", "ruby on rails"],
    "Go": ["golang"],  # + "Go" com G maiúsculo, ver _GO_LINGUAGEM em core/anuncio.py
    "Elixir": ["elixir"],
    "outras": [
        "scala", "rust", "c++", "delphi", "cobol", "abap", "clojure", "perl", "groovy",
        "advpl", "genexus",
    ],
}
ANUNCIO_FRONT_ALHEIO = ["angular", "angularjs", "vue", "vue.js", "vuejs", "nuxt", "svelte", "ember"]
ANUNCIO_MOBILE = ["flutter", "dart", "react native", "swift", "swiftui", "android", "ios", "xamarin", "ionic"]

# Tipo da vaga pelo título, e o que no título já confirma a stack.
TITULO_MARCAS_FULL = ["full stack", "full-stack", "fullstack"]
TITULO_MARCAS_BACKEND = ["back-end", "backend", "back end", "api", "apis", "node", "node.js", "nodejs", "nestjs"]
TITULO_MARCAS_FRONT = ["front-end", "frontend", "front end", "react", "next.js", "nextjs", "ui"]
TITULO_CONFIRMA_BACKEND = [
    "node", "node.js", "nodejs", "nestjs", "nest.js", "express", "typescript", "javascript",
]
TITULO_CONFIRMA_FRONT = [
    "react", "reactjs", "react.js", "next.js", "nextjs", "typescript", "javascript",
]

# ---------------------------------------------------------------------------
# Onde a vaga é — um bloco por perfil
# ---------------------------------------------------------------------------

# Mercados aceitos quando a vaga remota DECLARA escopo geográfico. O
# critério do usuário é "país que fale português ou inglês" — os rótulos
# abaixo são os que extrair_escopo_remoto sabe devolver (ver
# _MERCADOS_REMOTO em core/job.py); escrever um país que não esteja
# mapeado lá não teria efeito nenhum.
#
# "LATAM" entra mesmo sendo majoritariamente hispanofalante porque o Brasil
# está dentro dele: "Remote - LATAM" é justamente o rótulo que empresa
# americana usa pra contratar brasileiro, e o anúncio é em inglês.
#
# Vaga remota que NÃO declara mercado nenhum continua passando (não há base
# pra rejeitar) — é o comportamento padrão do filtro.
MERCADOS_REMOTO_ACEITOS_DEV = [
    "Brasil",
    "LATAM",
    "Portugal",
    "Estados Unidos",
    "Canadá",
    "Reino Unido",
    "Angola",
    "Moçambique",
    "Cabo Verde",
]

# --- dev (original): remoto + Joinville --------------------------------------
CIDADES_DEV = [
    "Remoto",
    "Joinville",
]

# Termos que rodam em TODO ciclo, fora do rodízio — os que definem o perfil
# (mesma ideia de TERMOS_PRIORITARIOS em config.py).
TERMOS_PRIORITARIOS_DEV = [
    "desenvolvedor back-end",
    "desenvolvedor full stack",
    "node.js",
    "typescript",
    "react",
]

# Rede ampla de busca. Separada das KEYWORDS pelo mesmo motivo do perfil de
# dados: aqui é o que se PESQUISA em cada site; o filtro de título é quem
# decide o que entra.
TERMOS_BUSCA_DEV = TERMOS_PRIORITARIOS_DEV + [
    "backend developer",
    "back-end developer",
    "fullstack developer",
    "full stack developer",
    "desenvolvedor javascript",
    "desenvolvedor typescript",
    "desenvolvedor node",
    "desenvolvedor react",
    "desenvolvedor front-end",
    "frontend developer",
    "software engineer node",
    "nestjs",
    "next.js",
    "prisma orm",
    "api rest node",
    "desenvolvedor web",
]

TERMOS_POR_CICLO_DEV = 8

# Uma busca por cidade no LinkedIn, além da nacional (ver
# LOCATIONS_LINKEDIN_CIDADES_PRESENCIAL em config.py): a passada nacional
# não alcança Joinville quando o termo é concorrido em SP/RJ.
LOCATIONS_LINKEDIN_DEV = ["Brazil"]
LOCATIONS_LINKEDIN_CIDADES_DEV = ["Joinville"]

# --- dev-joinville: presencial/híbrido, SÓ Joinville -------------------------
# Whitelist de uma cidade só, sem "Remoto": vaga remota é rejeitada mesmo
# com local em Joinville (excluir_remoto — o LinkedIn mostra a sede da
# empresa no local de vaga remota).
CIDADES_DEV_JOINVILLE = ["Joinville"]

# Joinville tem poucas vagas de dev por semana (11 em 2,5 meses no
# histórico do perfil dev), então o termo é LARGO de propósito: a busca do
# LinkedIn por localidade já recorta a cidade, e quem decide o que é da
# stack é o filtro. Termo estreito ("desenvolvedor node") só acharia o que
# o termo largo já acha.
TERMOS_PRIORITARIOS_DEV_JOINVILLE = [
    "desenvolvedor",
    "programador",
    "desenvolvedor full stack",
    "engenheiro de software",
]
TERMOS_BUSCA_DEV_JOINVILLE = TERMOS_PRIORITARIOS_DEV_JOINVILLE + [
    "desenvolvedor back-end",
    "desenvolvedor front-end",
    "desenvolvedor node",
    "desenvolvedor react",
    "desenvolvedor javascript",
    "typescript",
    "software engineer",
    "developer",
    "desenvolvedor web",
    "analista desenvolvedor",
]
TERMOS_POR_CICLO_DEV_JOINVILLE = 4
LOCATIONS_LINKEDIN_CIDADES_DEV_JOINVILLE = ["Joinville"]
# Páginas da busca por cidade no LinkedIn. No perfil dev era 1 (a cidade
# era uma passada extra); aqui ela é a busca principal.
PAGINAS_LINKEDIN_CIDADE_DEV_JOINVILLE = 3

# --- dev-remoto: remoto, empresa brasileira ----------------------------------
CIDADES_DEV_REMOTO = ["Remoto"]
# Sem lista de mercados (None): quem separa Brasil de fora aqui é
# mercado_vaga="nacional" (ver Job.vaga_internacional) — vaga do LinkedIn
# com escopo de fora ("Remote - LATAM") ou título em inglês vai pro
# dev-intl. Lista ["Brasil"] aqui barrava vaga brasileira por escopo mal
# lido: MEDIDO "Nova Mutum - MT" (Sólides) sai como Estados Unidos
# (MT = Montana) em extrair_escopo_remoto.
MERCADOS_REMOTO_ACEITOS_DEV_REMOTO = None

TERMOS_PRIORITARIOS_DEV_REMOTO = [
    "desenvolvedor full stack",
    "desenvolvedor back-end",
    "desenvolvedor node",
    "desenvolvedor react",
    "typescript",
]
TERMOS_BUSCA_DEV_REMOTO = TERMOS_PRIORITARIOS_DEV_REMOTO + [
    "desenvolvedor backend node.js",
    "desenvolvedor fullstack node react",
    "desenvolvedor javascript",
    "desenvolvedor typescript",
    "desenvolvedor front-end react",
    "desenvolvedor next.js",
    "desenvolvedor nestjs",
    "node.js",
    "react",
    "engenheiro de software node",
    "programador node",
    "desenvolvedor web",
]
TERMOS_POR_CICLO_DEV_REMOTO = 6
# Só a passada de remoto (f_WT=2) do LinkedIn: a nacional sem filtro só
# traria presencial, que este perfil descarta.
LOCATIONS_LINKEDIN_REMOTO_DEV_REMOTO = ["Brazil"]
PAGINAS_LINKEDIN_REMOTO_DEV_REMOTO = 3

# --- dev-intl: remoto, vaga em inglês / empresa de fora ----------------------
CIDADES_DEV_INTL = ["Remoto"]
# Mesmo critério do perfil dev original ("país que fale português ou
# inglês"), mais escopo vazio (vaga remota "anywhere").
MERCADOS_REMOTO_ACEITOS_DEV_INTL = MERCADOS_REMOTO_ACEITOS_DEV

# Em inglês: é como a empresa de fora anuncia, inclusive quando publica a
# vaga no LinkedIn com local "Brazil". "latam" no termo puxa as vagas que
# contratam explicitamente da América Latina.
TERMOS_PRIORITARIOS_DEV_INTL = [
    "full stack developer",
    "node.js developer",
    "backend developer node",
    "react developer",
    "typescript developer",
]
TERMOS_BUSCA_DEV_INTL = TERMOS_PRIORITARIOS_DEV_INTL + [
    "full stack engineer",
    "backend engineer",
    "software engineer node",
    "frontend developer react",
    "next.js developer",
    "nestjs developer",
    "javascript developer",
    "full stack developer latam",
    "remote developer latam",
    "mid-level full stack",
]
TERMOS_POR_CICLO_DEV_INTL = 5
# Passada de remoto do LinkedIn no Brasil: é onde empresa estrangeira que
# contrata brasileiro publica (local "Brazil"/"São Paulo", título em
# inglês). Busca em país de fora (EUA, Canadá) não entra: a vaga remota de
# lá quase sempre exige residência, e cada país multiplica o custo.
LOCATIONS_LINKEDIN_REMOTO_DEV_INTL = ["Brazil"]
PAGINAS_LINKEDIN_REMOTO_DEV_INTL = 3
