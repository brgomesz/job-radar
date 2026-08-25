"""Perfil administrativo/financeiro — dados do perfil `admin`, montado em
core/perfis.py.

Mesma separação dos outros perfis: aqui é só DADO (vocabulário de cargo,
área, cidade, termo de busca), o motor e o filtro são os mesmos.

Origem dos valores: perfil profissional da pessoa que usa este radar —
7+ anos em rotinas administrativas e financeiras no mercado imobiliário
(processos, contratos, fluxo financeiro, controle fiscal), graduação em
Administração e pós em Gestão de Pessoas, morando em Joinville/SC. A pós
em RH é o motivo de o radar cobrir RH/DP além de financeiro e
administrativo: é área correlata que ela pode assumir, não desvio de
escopo.
"""

# Cargo forte: título que já é inequivocamente da área dela. Ao contrário
# do perfil dev, aqui não faz falta um cargo forte genérico tipo
# "Analista" sozinho — o que define a área é o complemento ("Financeiro",
# "de RH", "Fiscal"), e é justamente ele que separa a vaga dela de
# "Analista de Sistemas"/"Analista de Marketing". Cargo sem complemento
# cai na lista ambígua abaixo.
KEYWORDS_CARGO_FORTE_ADM = [
    # --- Financeiro
    "Analista Financeiro",
    "Analista Financeira",
    "Analista de Finanças",
    "Analista Financeiro e Administrativo",
    "Analista Administrativo Financeiro",
    "Analista de Contas a Pagar",
    "Analista de Contas a Receber",
    "Analista de Faturamento",
    "Analista de Tesouraria",
    "Analista de Cobrança",
    "Analista de Crédito e Cobrança",
    "Analista de Custos",
    "Analista de Orçamento",
    "Analista de Planejamento Financeiro",
    "Analista de Controladoria",
    "Assistente Financeiro",
    "Coordenador Financeiro",
    "Coordenadora Financeira",
    "Supervisor Financeiro",
    "Supervisora Financeira",
    # --- Contábil
    #
    # Fiscal e tributário saíram a pedido da usuária: "Analista Fiscal",
    # "Analista Tributário/Tributária" e "Assistente Fiscal" eram daqui.
    # Contábil FICA (não foi pedido pra sair) -- e é por isso que "fiscal"
    # e "tributário" precisaram virar TITULOS_EXCLUIDOS_ADM em vez de só
    # sumirem desta lista: sem a rejeição incondicional, "Analista
    # Contábil e Fiscal" continuaria entrando pelo lado contábil.
    "Analista Contábil",
    "Assistente Contábil",
    # --- Administrativo
    "Analista Administrativo",
    "Analista Administrativa",
    "Analista de Administração",
    "Analista de Processos",
    "Analista de Contratos",
    "Analista de Backoffice",
    "Analista de Back Office",
    "Assistente Executivo",
    "Assistente Executiva",
    "Secretária Executiva",
    "Secretário Executivo",
    "Coordenador Administrativo",
    "Coordenadora Administrativa",
    "Supervisor Administrativo",
    "Supervisora Administrativa",
    "Gestor Administrativo",
    "Gestora Administrativa",
    # --- RH e Departamento Pessoal (pós em Gestão de Pessoas)
    "Analista de RH",
    "Analista de Recursos Humanos",
    "Analista de Departamento Pessoal",
    "Analista de DP",
    "Analista de Folha de Pagamento",
    "Analista de Recrutamento e Seleção",
    "Analista de Recrutamento",
    "Analista de Cargos e Salários",
    "Analista de Treinamento e Desenvolvimento",
    "Analista de Benefícios",
    "Analista de Gestão de Pessoas",
    "Generalista de RH",
    "Business Partner de RH",
    "Assistente de RH",
    "Assistente de Departamento Pessoal",
    "Coordenador de RH",
    "Coordenadora de RH",
    "Analista de Desenvolvimento Organizacional",
    # --- Compras e suprimentos (rotina administrativa correlata)
    "Analista de Compras",
    "Analista de Suprimentos",
]

# Cargo ambíguo: existe em qualquer área da empresa ("Analista Pleno",
# "Coordenador de Operações"). Só conta com um QUALIFICADORES_AREA_ADM
# junto no título — mesma mecânica de "Business Analyst" + "dados" no
# perfil de dados, e de "Desenvolvedor" + "node" no perfil dev.
#
# "Assistente" e "Auxiliar" NÃO entram aqui de propósito: sozinhos eles
# abrem o radar pra vaga de nível inferior ao que ela já ocupa hoje
# (assistente executivo, com 7 anos de casa). Os poucos títulos de
# assistente que interessam de verdade estão nomeados um a um na lista
# forte acima.
KEYWORDS_CARGO_AMBIGUO_ADM = [
    "Analista",
    "Coordenador",
    "Coordenadora",
    "Supervisor",
    "Supervisora",
    "Especialista",
    "Consultor",
    "Consultora",
    "Gerente",
]

# O que confirma que o cargo ambíguo é da área dela. Ocupa o campo
# `qualificadores_dados` de RegrasFiltro (nome herdado do primeiro perfil;
# a função é "o que qualifica esse cargo").
QUALIFICADORES_AREA_ADM = [
    "financeiro",
    "financeira",
    "finanças",
    "administrativo",
    "administrativa",
    "contábil",
    "contabil",
    "controladoria",
    "tesouraria",
    "faturamento",
    "cobrança",
    "crédito",
    "custos",
    "orçamento",
    "contas a pagar",
    "contas a receber",
    "contratos",
    "backoffice",
    "back office",
    "rh",
    "recursos humanos",
    "departamento pessoal",
    "dp",
    "folha de pagamento",
    "recrutamento",
    "seleção",
    "benefícios",
    "cargos e salários",
    "gestão de pessoas",
    "pessoas",
    "compras",
    "suprimentos",
    "processos",
]

# Ferramenta como núcleo do título ("Analista Protheus"). Só aprova com
# palavra de cargo junto (QUALIFICADORES_CARGO_ADM).
FERRAMENTAS_TITULO_ADM = [
    "Excel",
    "ERP",
    "Totvs",
    "Protheus",
    "Sienge",
    "Omie",
    "Conta Azul",
    "Domínio Sistemas",
    "SAP",
]

# Palavra de cargo que confirma que a vaga de ferramenta é da área dela —
# e não de TI dando suporte ao mesmo sistema ("Desenvolvedor Protheus",
# "Analista de Sistemas SAP" ficam fora justamente por isso).
QUALIFICADORES_CARGO_ADM = [
    "analista",
    "assistente",
    "coordenador",
    "coordenadora",
    "supervisor",
    "supervisora",
    "especialista",
    "gerente",
]

# Rejeição INCONDICIONAL por termo no título (ver titulos_excluidos em
# core/job.py): nenhum destes passa, em nenhuma combinação.
#
# Duas coisas na mesma lista, pelo mesmo motivo:
#
# 1. ÁREA DE FORA que usa o mesmo vocabulário de cargo. "processos" e
#    "pessoas" são qualificadores válidos da área dela, mas aparecem em
#    vaga de tecnologia e de produção industrial com sentido completamente
#    diferente ("Analista de Processos de Software", "Analista de Processos
#    Industriais" — Joinville é polo industrial, esse é o falso positivo
#    mais provável do radar dela).
#
# 2. FISCAL E TRIBUTÁRIO, tirados a pedido da usuária.
#
# Por que incondicional, e não a regra com perdão (stacks_excluidas, que o
# perfil dev usa): lá o perdão existe porque "Full Stack (Node + Python)" é
# vaga boa apesar do Python. Aqui não há caso equivalente — nenhuma vaga
# que ela queira nomeia "sistemas"/"industrial"/"marketing" no título. O
# perdão só abria brecha, e das duas piores maneiras: "Analista Fiscal
# Protheus" (fiscal, que ela não quer) e "Analista de Sistemas Protheus"
# (TI) passariam os dois, porque o ERP no título perdoava a área.
TITULOS_EXCLUIDOS_ADM = [
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
    # "industriais" escrito à parte: o match é por borda de palavra e o
    # plural português não é só "+s" — sem esta linha, "Analista de
    # Processos Industriais" (o falso positivo mais provável do radar dela,
    # num polo industrial como Joinville) passava direto. Pego por
    # tests/test_perfil_admin.py antes de ir pra produção.
    "industrial",
    "industriais",
    "produção",
    "manufatura",
    "pcp",
    "qualidade",
    "logística",
    "marketing",
    "vendas",
    "comercial",
    "engenharia",
    "laboratório",
    "enfermagem",
    # Pedido da usuária (item 2 acima)
    "fiscal",
    "tributário",
    "tributária",
]

# "Pleno / Sênior" pedido pela usuária: estágio, trainee e júnior nem
# notificam. Especialista e liderança (coordenador/gerente) CONTINUAM
# entrando — com 7 anos de área e pós, um "Coordenador Administrativo" é
# passo natural, e barrar por nível declarado seria descartar promoção.
# Vaga sem nível no título passa normalmente (é a maioria).
NIVEIS_EXCLUIDOS_ADM = [
    "Estágio/Trainee",
    "Júnior",
]

# Sênior é ALVO aqui (no padrão global ele vale -2, ver niveis_alvo em
# core/job.py): a usuária quer pleno E sênior, então os dois pontuam o
# teto de senioridade. Júnior sai da lista porque já é excluído acima —
# deixar ele como alvo seria pontuar o que nem chega.
NIVEIS_ALVO_ADM = [
    "Pleno",
    "Sênior",
]

CIDADES_ADM = [
    "Remoto",
    "Joinville",
]

# Só Brasil: rotina administrativa, fiscal e de departamento pessoal é
# legislação nacional — vaga remota de outro país não se aproveita. Vaga
# remota que não declara mercado continua passando (não há base pra
# rejeitar).
MERCADOS_REMOTO_ACEITOS_ADM = ["Brasil"]

TERMOS_PRIORITARIOS_ADM = [
    "analista financeiro",
    "analista administrativo",
    "analista de rh",
    "analista de departamento pessoal",
]

TERMOS_BUSCA_ADM = TERMOS_PRIORITARIOS_ADM + [
    "analista contábil",
    "analista de folha de pagamento",
    "analista de recrutamento e seleção",
    "analista de contas a pagar",
    "analista de contas a receber",
    "analista de faturamento",
    "analista de tesouraria",
    "analista de contratos",
    "analista de custos",
    "analista de controladoria",
    "analista de compras",
    "assistente executivo",
    "coordenador administrativo",
    "analista de gestão de pessoas",
    "analista de processos administrativos",
]

TERMOS_POR_CICLO_ADM = 8

LOCATIONS_LINKEDIN_ADM = ["Brazil"]
LOCATIONS_LINKEDIN_CIDADES_ADM = ["Joinville"]
