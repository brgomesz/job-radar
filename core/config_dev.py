"""Perfil dev full-stack (foco back-end Node/TypeScript) — dados do perfil
`dev`, montado em core/perfis.py.

Fica separado de config.py (dados/BI) e config_intl.py pelo mesmo motivo
que aqueles dois são separados entre si: o que muda de um perfil pro outro
é DADO — vocabulário de cargo, stack, cidade, mercado, termo de busca — e
não lógica. O motor (main.py) e o filtro (core/job.py) são os mesmos.

Origem dos valores: currículo do usuário (2 anos em JavaScript/TypeScript,
back-end em Node.js/Prisma/SQL Server/PostgreSQL, front em React/Next.js,
Docker e GitHub Actions), morando em Joinville/SC, inglês B1 (leitura e
escrita técnica fluentes).
"""

# Cargo forte: título que já é inequivocamente vaga de desenvolvimento na
# faixa do usuário (back, full-stack ou front). Diferente do perfil de
# dados, aqui o cargo forte é GENÉRICO de propósito — a maioria das vagas
# não põe a stack no título ("Desenvolvedor Back-end Pleno" e ponto), e
# exigir stack junto (regra de keywords_ambiguo) descartaria justamente as
# mais comuns. Quem paga o custo dessa abertura é `STACKS_EXCLUIDAS_DEV`,
# que barra o "Desenvolvedor Back-end Java" que entraria pela mesma porta.
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
# cargo ambíguo.
#
# Esta lista tem um SEGUNDO papel, além de aprovar: é a "stack própria" que
# perdoa uma stack excluída no mesmo título (ver STACKS_EXCLUIDAS_DEV). Por
# isso ela inclui a stack toda do currículo, não só o que costuma aparecer
# como núcleo de título.
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

# Stack de outro ecossistema: título que nomeia uma destas é descartado, a
# menos que também nomeie uma FERRAMENTAS_TITULO_DEV (ver stacks_excluidas
# em core/job.py). É o contrapeso de ter cargo forte genérico.
#
# "java" não pega "javascript": o match tem borda de palavra, e em
# "javascript" o "java" é seguido de caractere de palavra. Mesma razão pra
# "asp.net" estar escrito além de ".net" — em "asp.net" o ponto vem depois
# de "p", então ".net" sozinho não bate ali.
#
# NÃO entraram, e por quê:
#   "go"     — palavra curta demais, aparece em título como verbo/prefixo
#              em inglês ("Go-to-market", "Golang" já coberto abaixo).
#   "dados"  — barraria "Desenvolvedor Back-end (Plataforma de Dados)", que
#              é vaga de back-end legítima. Vaga de engenharia de dados que
#              escape por aqui cai no digest com score baixo, não notifica
#              na hora.
STACKS_EXCLUIDAS_DEV = [
    # Linguagens/plataformas
    "java",
    ".net",
    "asp.net",
    "dotnet",
    "c#",
    "c++",
    "php",
    "laravel",
    "python",
    "django",
    "ruby",
    "rails",
    "golang",
    "rust",
    "scala",
    "delphi",
    "cobol",
    "abap",
    "sap",
    "salesforce",
    "wordpress",
    "magento",
    "sharepoint",
    "powerbuilder",
    # Front de outro ecossistema
    "angular",
    "angularjs",
    "vue",
    "vuejs",
    "vue.js",
    "svelte",
    # Mobile — outra carreira, não é o que o usuário faz
    "react native",
    "flutter",
    "android",
    "ios",
    "swift",
    "kotlin",
    "mobile",
]

# Nível: o usuário pediu "pleno apenas". Vaga SEM nível declarado no título
# continua passando — é a maioria absoluta dos anúncios, e descartar por
# omissão esvaziaria o radar (ver niveis_excluidos em core/job.py).
NIVEIS_EXCLUIDOS_DEV = [
    "Estágio/Trainee",
    "Júnior",
    "Sênior",
    "Especialista",
    "Liderança",
]

# Remoto (preferência) + Joinville pra presencial/híbrido. Vaga
# presencial/híbrida em qualquer outra cidade é rejeitada — é whitelist,
# não ordenação.
CIDADES_DEV = [
    "Remoto",
    "Joinville",
]

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

# Bloco por ciclo. Menor que o do perfil de dados (10) porque este perfil
# entra num workflow que já roda outros dois — cada termo é uma sessão de
# navegador por fonte, e o ciclo inteiro tem que caber no timeout de 150
# min do jobradar.yml. Com 21 termos e 5 prioritários fixos, uma volta
# completa do rodízio leva 4 ciclos (~12h).
TERMOS_POR_CICLO_DEV = 8

# Uma busca por cidade no LinkedIn, além da nacional (ver
# LOCATIONS_LINKEDIN_CIDADES_PRESENCIAL em config.py): a passada nacional
# não alcança Joinville quando o termo é concorrido em SP/RJ.
LOCATIONS_LINKEDIN_DEV = ["Brazil"]
LOCATIONS_LINKEDIN_CIDADES_DEV = ["Joinville"]
