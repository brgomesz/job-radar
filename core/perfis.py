"""Perfis de mercado (Brasil / Internacional) do JobRadar.

Antes disso existiam DOIS programas quase idênticos — main.py e
main_intl.py — cada um com sua própria cópia do ciclo de busca (buscar →
filtrar → checar dedup → notificar antes de salvar → funil por fonte →
alerta de saúde → heartbeat). O que diverge de verdade entre os dois
mercados é só DADO: fontes, termos de busca, cidades aceitas, regra de
cargo. A lógica de execução em si é a mesma — daí valer a pena descrever
cada mercado como um objeto (`Perfil`) e ter um único motor (main.py) que
roda qualquer um dos dois, escolhido em tempo de execução via `--perfil`.

Cada `Perfil` tem uma `chave` curta (usada tanto no argumento --perfil
quanto como sufixo nas chaves da tabela `metadados` — rodízio de termos,
cadência de baixa frequência e heartbeat ficam isolados por perfil, mesmo
os dois perfis rodando na mesma execução do workflow e escrevendo no mesmo
jobs.db).
"""

from dataclasses import dataclass, field

from core.config import (
    KEYWORDS,
    KEYWORDS_CARGO_FORTE,
    KEYWORDS_CARGO_AMBIGUO,
    QUALIFICADORES_DADOS,
    FERRAMENTAS_TITULO,
    QUALIFICADORES_CARGO,
    CIDADES,
    CIDADES_EUROPA_IBERICA,
    ATIVAR_EIXO_IBERICO_BR,
    MERCADOS_REMOTO_ACEITOS,
    TERMOS_BUSCA,
    TERMOS_PRIORITARIOS,
    TERMOS_POR_CICLO,
)
from core.config_intl import (
    KEYWORDS_INTL,
    TERMOS_BUSCA_INTL,
    TERMOS_POR_CICLO_INTL,
    LOCATIONS_INTL,
    DOMINIOS_INDEED_INTL,
    CIDADES_INTL,
    ATIVAR_EIXO_IBERICO,
    MERCADOS_REMOTO_ACEITOS_INTL,
    IDIOMAS_EXIGIDOS_INTL,
)
from core import config_dev as cd
from core.config_dev import (
    KEYWORDS_CARGO_FORTE_DEV,
    KEYWORDS_CARGO_AMBIGUO_DEV,
    CIDADES_DEV,
    MERCADOS_REMOTO_ACEITOS_DEV,
    TERMOS_BUSCA_DEV,
    TERMOS_PRIORITARIOS_DEV,
    TERMOS_POR_CICLO_DEV,
    LOCATIONS_LINKEDIN_DEV,
    LOCATIONS_LINKEDIN_CIDADES_DEV,
)
from core.config_analista import (
    KEYWORDS_CARGO_FORTE_ANALISTA,
    KEYWORDS_CARGO_AMBIGUO_ANALISTA,
    QUALIFICADORES_AREA_ANALISTA,
    TITULOS_EXCLUIDOS_ANALISTA,
    NIVEIS_EXCLUIDOS_ANALISTA,
    NIVEIS_ALVO_ANALISTA,
    CIDADES_ANALISTA,
    MERCADOS_REMOTO_ACEITOS_ANALISTA,
    TERMOS_BUSCA_ANALISTA,
    TERMOS_PRIORITARIOS_ANALISTA,
    TERMOS_POR_CICLO_ANALISTA,
    LOCATIONS_LINKEDIN_ANALISTA,
    LOCATIONS_LINKEDIN_CIDADES_ANALISTA,
    REMOTO_NO_TITULO_ANALISTA,
)
from core.anuncio import RegrasAnuncio, motivo_reprovacao
from core.job import Job, RegrasFiltro
from scrapers.catho import CathoScraper
from scrapers.geekhunter import GeekHunterScraper
from scrapers.gupy import GupyScraper
from scrapers.indeed import IndeedScraper
from scrapers.indeed_intl import IndeedIntlScraper
from scrapers.jobs99 import Jobs99Scraper
from scrapers.linkedin import LinkedInScraper
from scrapers.linkedin_intl import LinkedInIntlScraper
from scrapers.senior import SeniorScraper
from scrapers.solides import SolidesScraper
from scrapers.weworkremotely_intl import WeWorkRemotelyIntlScraper

# "alta" roda TODO ciclo; "baixa" roda só na primeira execução de cada dia
# (ver _fontes_baixa_frequencia_ja_rodaram_hoje em main.py). Existe pra
# fonte de baixo rendimento não pesar no custo de todo ciclo.
FREQUENCIA_ALTA = "alta"
FREQUENCIA_BAIXA = "baixa"


@dataclass
class DefinicaoScraper:
    """Uma fonte dentro de um perfil.

    `kwargs_extras`: além de `termos_busca` (que todo scraper recebe), fonte
    internacional precisa de argumento próprio — `locations=` no
    LinkedInIntlScraper, `dominios=` no IndeedIntlScraper. Fonte do perfil
    BR não precisa de nada extra (LinkedInScraper já traz seus países
    default de config.py), então fica com kwargs_extras vazio.
    """
    classe: type
    frequencia: str
    kwargs_extras: dict = field(default_factory=dict)


@dataclass
class Perfil:
    chave: str  # "brasil" / "internacional" — valor do --perfil e sufixo de chave em metadados
    nome: str  # nome de exibição nos logs/Telegram, ex: "Internacional"
    palavras_monitoradas: list[str]
    paises_pesquisados: list[str] | None  # só o perfil internacional imprime isso no banner
    regras: RegrasFiltro
    regras_eixo_secundario: RegrasFiltro | None
    eixo_secundario_ativo: bool
    eixo_secundario_rotulo: str  # usado só no texto do log ("Nova vaga exploratória (<rótulo>)")
    termos_busca: list[str]
    termos_por_ciclo: int
    definicao_scrapers: list[DefinicaoScraper]
    # Termos fora do rodízio, buscados em TODO ciclo (ver TERMOS_PRIORITARIOS
    # em config.py). Lista vazia = tudo entra no rodízio, que é o
    # comportamento de antes deste campo existir (perfil internacional).
    termos_prioritarios: list[str] = field(default_factory=list)
    max_scrapers_concorrentes: int = 4
    # Reaplica as regras ATUAIS às vagas já salvas do perfil, na página e na
    # captura de anúncios (ver aprovada_pelas_regras_atuais). Ligado quando
    # o filtro do perfil aperta e o histórico antigo deixou de servir.
    refiltrar_historico: bool = False
    # Regra pelo TEXTO do anúncio (ver core/anuncio.py). Com isto, main.py
    # abre o anúncio de toda vaga que iria pro Telegram ANTES de notificar,
    # e a página esconde a vaga cujo anúncio reprova. None = só o título
    # decide (comportamento de antes).
    regras_anuncio: RegrasAnuncio | None = None


# Regra primária: cidade brasileira (Nordeste) ou "Remoto" com mercado
# Brasil/LATAM/Portugal/Espanha aceito (ver Job.escopo_remoto).
_REGRAS_BR = RegrasFiltro(
    keywords_forte=KEYWORDS_CARGO_FORTE,
    keywords_ambiguo=KEYWORDS_CARGO_AMBIGUO,
    qualificadores_dados=QUALIFICADORES_DADOS,
    ferramentas_titulo=FERRAMENTAS_TITULO,
    qualificadores_cargo=QUALIFICADORES_CARGO,
    cidades=CIDADES,
    mercados_remoto_aceitos=MERCADOS_REMOTO_ACEITOS,
)

# Eixo secundário (Ibéria): mesma regra de cargo, cidade europeia em vez de
# brasileira. DESLIGADO — ver ATIVAR_EIXO_IBERICO_BR em config.py: usuário só
# quer vaga remota do mercado internacional, não presencial/híbrida em
# Lisboa/Madrid. Continua definido (não apagado) pra religar fácil depois.
_REGRAS_BR_IBERIA = RegrasFiltro(
    keywords_forte=KEYWORDS_CARGO_FORTE,
    keywords_ambiguo=KEYWORDS_CARGO_AMBIGUO,
    qualificadores_dados=QUALIFICADORES_DADOS,
    ferramentas_titulo=FERRAMENTAS_TITULO,
    qualificadores_cargo=QUALIFICADORES_CARGO,
    cidades=CIDADES_EUROPA_IBERICA,
)

# Revelo não entrou: o portal de vagas exige login pra navegar, não dá pra
# fazer scraping público de forma confiável.
#
# Trampos SAIU depois de investigar por que rendia 0 notificação em 6 dias
# (~71 vagas brutas/ciclo com 99Jobs). Testei o parâmetro de busca (term=)
# direto na API do site com "analista de dados" e "business intelligence" —
# os dois devolveram a MESMA lista de vagas (Diretor de Arte, SDR,
# Atendimento Publicitário...), nenhuma de dados. A busca do site não
# filtra nada, é sempre o feed genérico recente; a categoria própria
# "Análise e Gestão de Dados" do site tem só 4 vagas no total, contra 226
# de "Emprego" geral (majoritariamente marketing/criação/comercial). O
# vazio vinha da FONTE (site não é de tecnologia/dados) — código do
# scraper continua em scrapers/trampos.py se algum dia mudar.
#
# 99Jobs FICOU: mesma investigação, resultado diferente. A busca por
# "analista de dados" no site retorna vaga de verdade relevante ("Analista
# de Dados Sênior" etc.) — só que presencial/híbrida em São Paulo, fora da
# lista CIDADES e sem sinal de remoto. O vazio aí vem do FILTRO de
# localização (a mesma limitação que afeta o sistema todo), não da fonte —
# remover jogaria fora uma fonte que funciona.
#
# Cadência por fonte: medido em jobradar.log + jobs.db (vagas notificadas /
# vagas brutas retornadas, somado por fonte). Gupy e LinkedIn confirmam o
# que foi medido à parte (Gupy ~2,6%); Catho, GeekHunter e 99Jobs ficam
# abaixo de 1%.
#
# WeWorkRemotelyIntlScraper reaproveitado aqui (não duplicado): é agregador
# de vaga 100% remota que cobre o mercado "remoto internacional" que
# nenhuma das 8 fontes brasileiras alcança — mesmo scraper usado no perfil
# internacional, sem nada daquele perfil hardcoded. Sem medição própria
# ainda pra essa combinação (fonte + termos em português) — FREQUENCIA_BAIXA
# até medir rendimento real.
_SCRAPERS_BR = [
    DefinicaoScraper(GupyScraper, FREQUENCIA_ALTA),        # ~2,6% de rendimento
    DefinicaoScraper(LinkedInScraper, FREQUENCIA_ALTA),     # ~8,5% — a melhor fonte de longe
    DefinicaoScraper(SolidesScraper, FREQUENCIA_ALTA),      # ~1,1%
    # Indeed SAIU dos perfis (codigo continua em scrapers/indeed.py e
    # scrapers/indeed_intl.py, mesmo tratamento que o Trampos recebeu).
    #
    # MEDIDO em 3 ciclos consecutivos de producao (18/08): ZERO vaga bruta,
    # nas duas versoes. O log nao mostra "0 resultado" — mostra timeout na
    # PAGINA 1 de todo termo, em todos os 6 dominios de pais. Isso e
    # bloqueio anti-bot completo, nao ausencia de vaga. O proprio scraper ja
    # avisava do risco: IP de nuvem/datacenter (que e o do GitHub Actions) e
    # o mais bloqueado.
    #
    # Custo medido no relogio do log (os scrapers rodam em PARALELO, entao o
    # que importa e quem termina por ultimo):
    #
    #   Brasil        11m32s — gargalo e o LinkedIn (21:40:55), nao o Indeed
    #                 (21:33:42). Tirar daqui nao encurta o ciclo, so para
    #                 de gastar requisicao a toa.
    #   Internacional 25m42s — LinkedIn Intl termina 21:47:20 e o Indeed Intl
    #                 so 22:06:38. Ele SOZINHO estende o ciclo em 19 minutos,
    #                 entregando zero vaga.
    #
    # Ciclo completo: 37m14s -> ~18m. Sao ~2h30 por dia devolvidas.
    #
    # Pra religar quando/se o Indeed voltar a responder: descomente as duas
    # linhas abaixo (uma aqui, outra em _SCRAPERS_INTL). Nada mais precisa
    # mudar — imports, config e dominios continuam no lugar.
    # DefinicaoScraper(IndeedScraper, FREQUENCIA_ALTA),       # ~1,1%
    DefinicaoScraper(CathoScraper, FREQUENCIA_BAIXA),       # <1%, timeout frequente em headless
    DefinicaoScraper(GeekHunterScraper, FREQUENCIA_BAIXA),  # <1%
    DefinicaoScraper(Jobs99Scraper, FREQUENCIA_BAIXA),      # <1%, fonte confirmada funcionando
    DefinicaoScraper(WeWorkRemotelyIntlScraper, FREQUENCIA_BAIXA),  # nova, sem medição própria
    # MEDIDO ao vivo antes de ligar (3 termos, 398 vagas brutas): rendimento
    # de 0,3% — abaixo da Sólides (1,1%), a fonte mais fraca que ficou. A
    # busca da API casa pedaço de palavra, não o termo: "analista bi" trouxe
    # ANALISTA CONTÁBIL, ANALISTA DE CUSTOS, ANALISTA LOGÍSTICA. E só 1 das
    # 398 era remota — o portal é quase todo presencial, enquanto o remoto é
    # de onde vem a maior parte do volume deste projeto.
    #
    # Entra assim mesmo, e em FREQUENCIA_BAIXA, por três motivos:
    #
    # 1. Custo. 398 vagas em 4 SEGUNDOS, sem navegador. A Sólides gasta
    #    minutos pra render 1,1%. Por vaga útil, a conta favorece a Senior.
    # 2. Cobre a área mais fraca. A única aprovada foi presencial em Natal —
    #    e vaga presencial nas 8 cidades é o que o projeto menos acha (23 em
    #    1.279 no histórico).
    # 3. É a única fonte com data de publicação em 100% dos registros
    #    (398/398), contra praticamente zero nas outras.
    #
    # FREQUENCIA_BAIXA também porque o endpoint só foi testado de máquina
    # doméstica: o robô roda em IP de datacenter, que foi o que derrubou o
    # Indeed. Uma execução por dia mede sem multiplicar requisição.
    #
    # Critério de permanência, pra decidir por número e não por impressão
    # (mesmo critério que manteve o 99Jobs e tirou o Trampos): se numa semana
    # não trouxer vaga relevante das 8 cidades, sai.
    DefinicaoScraper(SeniorScraper, FREQUENCIA_BAIXA),      # 0,3%, mas 4s e cobre cidade
]

PERFIL_BR = Perfil(
    chave="brasil",
    nome="Brasil",
    palavras_monitoradas=KEYWORDS,
    paises_pesquisados=None,
    regras=_REGRAS_BR,
    regras_eixo_secundario=_REGRAS_BR_IBERIA,
    eixo_secundario_ativo=ATIVAR_EIXO_IBERICO_BR,
    eixo_secundario_rotulo="Ibéria",
    termos_busca=TERMOS_BUSCA,
    termos_por_ciclo=TERMOS_POR_CICLO,
    termos_prioritarios=TERMOS_PRIORITARIOS,
    definicao_scrapers=_SCRAPERS_BR,
    max_scrapers_concorrentes=4,
)


# Regra primária: só remoto ("Remote"/"Remoto" em CIDADES_INTL), mercado
# LATAM/Portugal/Espanha aceito. Sem cargo ambíguo/ferramenta ainda nesse
# perfil — simples de propósito por ser o mais novo dos dois.
#
# idiomas_exigidos: sem mercado declarado, exige espanhol/português/LATAM
# no título (ver IDIOMAS_EXIGIDOS_INTL e comentário em RegrasFiltro) — a
# busca já tentava garantir isso via termo, mas nunca era reconferido na
# vaga em si.
_REGRAS_INTL = RegrasFiltro(
    keywords_forte=KEYWORDS_INTL,
    keywords_ambiguo=[],
    qualificadores_dados=[],
    ferramentas_titulo=[],
    qualificadores_cargo=[],
    cidades=CIDADES_INTL,
    mercados_remoto_aceitos=MERCADOS_REMOTO_ACEITOS_INTL,
    idiomas_exigidos=IDIOMAS_EXIGIDOS_INTL,
)

# Eixo secundário (Ibéria): vaga presencial/híbrida em Portugal/Espanha,
# achada de propósito (LOCATIONS_INTL busca lá) mas que CIDADES_INTL (só
# remoto) rejeitaria. DESLIGADO — mesmo motivo do eixo BR acima.
_REGRAS_INTL_IBERIA = RegrasFiltro(
    keywords_forte=KEYWORDS_INTL,
    keywords_ambiguo=[],
    qualificadores_dados=[],
    ferramentas_titulo=[],
    qualificadores_cargo=[],
    cidades=CIDADES_EUROPA_IBERICA,
)

# As 3 fontes rodam toda vez (FREQUENCIA_ALTA) — perfil novo, sem medição de
# rendimento por fonte ainda que justifique separar em cadência alta/baixa
# como o perfil BR. Ajustar quando/se tiver dado real.
_SCRAPERS_INTL = [
    DefinicaoScraper(LinkedInIntlScraper, FREQUENCIA_ALTA, {"locations": LOCATIONS_INTL}),
    # Indeed Intl desligado — ver MEDIDO em _SCRAPERS_BR. Era o gargalo
    # absoluto do ciclo internacional: 19 dos 25 minutos, zero vaga.
    # DefinicaoScraper(IndeedIntlScraper, FREQUENCIA_ALTA, {"dominios": DOMINIOS_INDEED_INTL}),
    DefinicaoScraper(WeWorkRemotelyIntlScraper, FREQUENCIA_ALTA),
]

PERFIL_INTL = Perfil(
    chave="internacional",
    nome="Internacional",
    palavras_monitoradas=KEYWORDS_INTL,
    paises_pesquisados=LOCATIONS_INTL,
    regras=_REGRAS_INTL,
    regras_eixo_secundario=_REGRAS_INTL_IBERIA,
    eixo_secundario_ativo=ATIVAR_EIXO_IBERICO,
    eixo_secundario_rotulo="Ibéria",
    termos_busca=TERMOS_BUSCA_INTL,
    termos_por_ciclo=TERMOS_POR_CICLO_INTL,
    definicao_scrapers=_SCRAPERS_INTL,
    max_scrapers_concorrentes=3,
)

# Perfis dev full-stack (foco back-end Node/TypeScript) — ver
# core/config_dev.py pra origem de cada lista.
#
# Os quatro compartilham a regra de CARGO e de STACK (_regras_dev); só o
# bloco de localização muda. Regras opcionais de RegrasFiltro que só os
# perfis dev usam (nada muda pra brasil/internacional/analista):
#   - stacks_excluidas / stacks_backend_excluidas: o cargo forte é genérico
#     ("Desenvolvedor Back-end"), porque vaga real raramente traz stack no
#     título; essas listas barram Java/.NET/PHP/Angular/mobile no título.
#   - niveis_excluidos + titulos_excluidos: "pleno apenas" — júnior,
#     estágio, sênior, staff, lead e liderança nem notificam. Vaga sem
#     nível declarado continua entrando.
#   - regras_anuncio: o contrapeso que o título não dá — vaga com título
#     genérico cujo anúncio é Java/Kotlin/.NET (ver core/anuncio.py).
REGRAS_ANUNCIO_DEV = RegrasAnuncio(
    proprias_backend=cd.ANUNCIO_BACKEND_PROPRIO,
    proprias_front=cd.ANUNCIO_FRONT_PROPRIO,
    proprias_linguagem=cd.ANUNCIO_LINGUAGEM_PROPRIA,
    familias_backend_alheias=cd.ANUNCIO_FAMILIAS_BACKEND_ALHEIAS,
    alheias_front=cd.ANUNCIO_FRONT_ALHEIO,
    alheias_mobile=cd.ANUNCIO_MOBILE,
    marcas_full_titulo=cd.TITULO_MARCAS_FULL,
    marcas_backend_titulo=cd.TITULO_MARCAS_BACKEND,
    marcas_front_titulo=cd.TITULO_MARCAS_FRONT,
    confirma_backend_titulo=cd.TITULO_CONFIRMA_BACKEND,
    confirma_front_titulo=cd.TITULO_CONFIRMA_FRONT,
)


def _regras_dev(cidades: list[str], **local) -> RegrasFiltro:
    """Cargo e stack comuns aos perfis dev + o bloco de localização de cada
    um (`cidades` e os campos de mercado/modalidade em `local`)."""
    return RegrasFiltro(
        keywords_forte=cd.KEYWORDS_CARGO_FORTE_DEV,
        keywords_ambiguo=cd.KEYWORDS_CARGO_AMBIGUO_DEV,
        qualificadores_dados=cd.QUALIFICADORES_STACK_DEV,
        ferramentas_titulo=cd.FERRAMENTAS_TITULO_DEV,
        qualificadores_cargo=cd.QUALIFICADORES_CARGO_DEV,
        cidades=cidades,
        stacks_excluidas=cd.STACKS_EXCLUIDAS_DEV,
        stacks_perdao=cd.STACKS_PERDAO_DEV,
        stacks_backend_excluidas=cd.STACKS_BACKEND_EXCLUIDAS_DEV,
        stacks_backend_perdao=cd.STACKS_BACKEND_PERDAO_DEV,
        niveis_excluidos=cd.NIVEIS_EXCLUIDOS_DEV,
        titulos_excluidos=cd.TITULOS_EXCLUIDOS_DEV,
        **local,
    )


# --- dev: o perfil original (remoto + Joinville) -----------------------------
#
# SAIU do cron em nov/2026, quando foi dividido nos três perfis abaixo — que
# juntos cobrem exatamente o que ele buscava (Joinville presencial/híbrido +
# remoto Brasil + remoto de fora). Os quatro não podem rodar juntos: o
# jobs.db guarda cada vaga UMA vez só (ja_vista é global, não por perfil),
# então o primeiro a achar uma vaga a tiraria dos outros. Continua aqui:
#   - rodável à mão (`python main.py --perfil dev --once`);
#   - na página, como a opção "Geral" da aba Conteúdo Dev: o histórico dele
#     (552 vagas até nov/2026) mais tudo que os três novos acharem.
_REGRAS_DEV = _regras_dev(CIDADES_DEV, mercados_remoto_aceitos=MERCADOS_REMOTO_ACEITOS_DEV)

# GeekHunter e WeWorkRemotely sobem pra FREQUENCIA_ALTA aqui (no perfil de
# dados as duas são de baixa frequência, por rendimento medido abaixo de
# 1%): as duas são fonte de vaga de TECNOLOGIA, que é exatamente o que este
# perfil procura — o rendimento delas foi medido contra termo de dados/BI,
# não contra "desenvolvedor node".
#
# Catho, Sólides, 99Jobs e Senior ficam em baixa frequência: são portais
# generalistas, mesmo custo por termo e sem sinal de que rendam mais aqui.
# Indeed continua fora (ver MEDIDO em _SCRAPERS_BR — era o gargalo do
# ciclo, com rendimento perto de zero).
_SCRAPERS_DEV = [
    DefinicaoScraper(LinkedInScraper, FREQUENCIA_ALTA, {
        "locations": LOCATIONS_LINKEDIN_DEV,
        # Sem passada de "remoto apenas" em outros países: vaga remota
        # internacional chega pela WeWorkRemotely, sem multiplicar o custo
        # do LinkedIn por país.
        "locations_remoto_apenas": [],
        "locations_cidades_presencial": LOCATIONS_LINKEDIN_CIDADES_DEV,
    }),
    DefinicaoScraper(GupyScraper, FREQUENCIA_ALTA),
    DefinicaoScraper(GeekHunterScraper, FREQUENCIA_ALTA),
    DefinicaoScraper(WeWorkRemotelyIntlScraper, FREQUENCIA_ALTA),
    DefinicaoScraper(SolidesScraper, FREQUENCIA_BAIXA),
    DefinicaoScraper(Jobs99Scraper, FREQUENCIA_BAIXA),
    DefinicaoScraper(CathoScraper, FREQUENCIA_BAIXA),
    DefinicaoScraper(SeniorScraper, FREQUENCIA_BAIXA),
]

PERFIL_DEV = Perfil(
    chave="dev",
    nome="Dev Full-Stack",
    palavras_monitoradas=KEYWORDS_CARGO_FORTE_DEV + KEYWORDS_CARGO_AMBIGUO_DEV,
    paises_pesquisados=None,
    regras=_REGRAS_DEV,
    regras_eixo_secundario=None,
    eixo_secundario_ativo=False,
    eixo_secundario_rotulo="",
    termos_busca=TERMOS_BUSCA_DEV,
    termos_por_ciclo=TERMOS_POR_CICLO_DEV,
    termos_prioritarios=TERMOS_PRIORITARIOS_DEV,
    definicao_scrapers=_SCRAPERS_DEV,
    max_scrapers_concorrentes=4,
    # MEDIDO (nov/2026): o filtro apertou (stack de back-end, staff/lead,
    # anúncio) e boa parte do histórico — Java/React, .NET/React, Laravel —
    # deixou de servir. Sem isto continuaria na página.
    refiltrar_historico=True,
    regras_anuncio=REGRAS_ANUNCIO_DEV,
)

# --- dev-joinville: presencial/híbrido, SÓ em Joinville -----------------------
#
# LinkedIn por localidade é a fonte principal: os portais (Gupy, Sólides,
# Catho, Senior, 99Jobs) não filtram por cidade na busca — devolvem o
# Brasil inteiro e Joinville aparece quando aparece; ficam como rede de
# apoio (o filtro recorta a cidade). WeWorkRemotely não entra: só tem vaga
# remota.
PERFIL_DEV_JOINVILLE = Perfil(
    chave="dev-joinville",
    nome="Dev Joinville (presencial/híbrido)",
    palavras_monitoradas=KEYWORDS_CARGO_FORTE_DEV + KEYWORDS_CARGO_AMBIGUO_DEV,
    paises_pesquisados=None,
    regras=_regras_dev(cd.CIDADES_DEV_JOINVILLE, excluir_remoto=True),
    regras_eixo_secundario=None,
    eixo_secundario_ativo=False,
    eixo_secundario_rotulo="",
    termos_busca=cd.TERMOS_BUSCA_DEV_JOINVILLE,
    termos_por_ciclo=cd.TERMOS_POR_CICLO_DEV_JOINVILLE,
    termos_prioritarios=cd.TERMOS_PRIORITARIOS_DEV_JOINVILLE,
    definicao_scrapers=[
        DefinicaoScraper(LinkedInScraper, FREQUENCIA_ALTA, {
            "locations": [],
            "locations_remoto_apenas": [],
            "locations_cidades_presencial": cd.LOCATIONS_LINKEDIN_CIDADES_DEV_JOINVILLE,
            "paginas_cidade": cd.PAGINAS_LINKEDIN_CIDADE_DEV_JOINVILLE,
        }),
        DefinicaoScraper(GupyScraper, FREQUENCIA_ALTA),
        DefinicaoScraper(SolidesScraper, FREQUENCIA_ALTA),
        DefinicaoScraper(CathoScraper, FREQUENCIA_BAIXA),
        DefinicaoScraper(SeniorScraper, FREQUENCIA_BAIXA),
        DefinicaoScraper(Jobs99Scraper, FREQUENCIA_BAIXA),
    ],
    max_scrapers_concorrentes=4,
    refiltrar_historico=True,
    regras_anuncio=REGRAS_ANUNCIO_DEV,
)

# --- dev-remoto: remoto, empresa brasileira -----------------------------------
#
# Vaga em inglês / de empresa de fora vai pro dev-intl (mercado_vaga): os
# dois perfis são disjuntos, então a ordem em que rodam não importa pra
# deduplicação.
PERFIL_DEV_REMOTO = Perfil(
    chave="dev-remoto",
    nome="Dev Remoto (Brasil)",
    palavras_monitoradas=KEYWORDS_CARGO_FORTE_DEV + KEYWORDS_CARGO_AMBIGUO_DEV,
    paises_pesquisados=None,
    regras=_regras_dev(
        cd.CIDADES_DEV_REMOTO,
        mercados_remoto_aceitos=cd.MERCADOS_REMOTO_ACEITOS_DEV_REMOTO,
        mercado_vaga="nacional",
    ),
    regras_eixo_secundario=None,
    eixo_secundario_ativo=False,
    eixo_secundario_rotulo="",
    termos_busca=cd.TERMOS_BUSCA_DEV_REMOTO,
    termos_por_ciclo=cd.TERMOS_POR_CICLO_DEV_REMOTO,
    termos_prioritarios=cd.TERMOS_PRIORITARIOS_DEV_REMOTO,
    definicao_scrapers=[
        DefinicaoScraper(LinkedInScraper, FREQUENCIA_ALTA, {
            "locations": [],
            "locations_remoto_apenas": cd.LOCATIONS_LINKEDIN_REMOTO_DEV_REMOTO,
            "locations_cidades_presencial": [],
            "paginas_remoto": cd.PAGINAS_LINKEDIN_REMOTO_DEV_REMOTO,
        }),
        DefinicaoScraper(GupyScraper, FREQUENCIA_ALTA),
        DefinicaoScraper(GeekHunterScraper, FREQUENCIA_ALTA),
        DefinicaoScraper(SolidesScraper, FREQUENCIA_BAIXA),
        DefinicaoScraper(Jobs99Scraper, FREQUENCIA_BAIXA),
        DefinicaoScraper(CathoScraper, FREQUENCIA_BAIXA),
        DefinicaoScraper(SeniorScraper, FREQUENCIA_BAIXA),
    ],
    max_scrapers_concorrentes=4,
    refiltrar_historico=True,
    regras_anuncio=REGRAS_ANUNCIO_DEV,
)

# --- dev-intl: remoto, vaga em inglês / empresa de fora -----------------------
#
# "Vaga estrangeira" pra quem mora no Brasil = empresa de fora que contrata
# remoto daqui. Ela aparece em dois lugares: no LinkedIn, com local
# "Brazil"/cidade brasileira e título em inglês, e na WeWorkRemotely (só
# vaga remota, quase toda de fora). Ver Job.vaga_internacional.
PERFIL_DEV_INTL = Perfil(
    chave="dev-intl",
    nome="Dev Internacional (remoto)",
    palavras_monitoradas=KEYWORDS_CARGO_FORTE_DEV + KEYWORDS_CARGO_AMBIGUO_DEV,
    paises_pesquisados=None,
    regras=_regras_dev(
        cd.CIDADES_DEV_INTL,
        mercados_remoto_aceitos=cd.MERCADOS_REMOTO_ACEITOS_DEV_INTL,
        mercado_vaga="internacional",
    ),
    regras_eixo_secundario=None,
    eixo_secundario_ativo=False,
    eixo_secundario_rotulo="",
    termos_busca=cd.TERMOS_BUSCA_DEV_INTL,
    termos_por_ciclo=cd.TERMOS_POR_CICLO_DEV_INTL,
    termos_prioritarios=cd.TERMOS_PRIORITARIOS_DEV_INTL,
    definicao_scrapers=[
        DefinicaoScraper(LinkedInScraper, FREQUENCIA_ALTA, {
            "locations": [],
            "locations_remoto_apenas": cd.LOCATIONS_LINKEDIN_REMOTO_DEV_INTL,
            "locations_cidades_presencial": [],
            "paginas_remoto": cd.PAGINAS_LINKEDIN_REMOTO_DEV_INTL,
        }),
        DefinicaoScraper(WeWorkRemotelyIntlScraper, FREQUENCIA_ALTA),
    ],
    max_scrapers_concorrentes=2,
    refiltrar_historico=True,
    regras_anuncio=REGRAS_ANUNCIO_DEV,
)

# Os três que dividem o perfil dev original — a ordem é a das opções da aba
# Conteúdo Dev e a da classificação do histórico dev (ver web/gerar.py).
SUBPERFIS_DEV = ("dev-joinville", "dev-remoto", "dev-intl")

# Perfil Analista — ver core/config_analista.py. Coordenação/gerência/
# supervisão adm-financeira, operações, contratos e sales ops; analista só
# com qualificador de nível ou de setor no título. Portais generalistas
# (onde vaga adm-financeira mora) e as três regras opcionais de
# RegrasFiltro; a rota ferramenta+cargo fica desligada (listas vazias): o
# Sienge, única ferramenta que interessa aqui, é qualificador de setor.
_REGRAS_ANALISTA = RegrasFiltro(
    keywords_forte=KEYWORDS_CARGO_FORTE_ANALISTA,
    keywords_ambiguo=KEYWORDS_CARGO_AMBIGUO_ANALISTA,
    qualificadores_dados=QUALIFICADORES_AREA_ANALISTA,
    ferramentas_titulo=[],
    qualificadores_cargo=[],
    cidades=CIDADES_ANALISTA,
    mercados_remoto_aceitos=MERCADOS_REMOTO_ACEITOS_ANALISTA,
    titulos_excluidos=TITULOS_EXCLUIDOS_ANALISTA,
    niveis_excluidos=NIVEIS_EXCLUIDOS_ANALISTA,
    niveis_alvo=NIVEIS_ALVO_ANALISTA,
    remoto_exige_titulo=REMOTO_NO_TITULO_ANALISTA,
)

_SCRAPERS_ANALISTA = [
    DefinicaoScraper(LinkedInScraper, FREQUENCIA_ALTA, {
        "locations": LOCATIONS_LINKEDIN_ANALISTA,
        "locations_remoto_apenas": [],
        "locations_cidades_presencial": LOCATIONS_LINKEDIN_CIDADES_ANALISTA,
    }),
    DefinicaoScraper(GupyScraper, FREQUENCIA_ALTA),
    DefinicaoScraper(CathoScraper, FREQUENCIA_ALTA),
    DefinicaoScraper(SolidesScraper, FREQUENCIA_ALTA),
    DefinicaoScraper(Jobs99Scraper, FREQUENCIA_BAIXA),
    DefinicaoScraper(SeniorScraper, FREQUENCIA_BAIXA),
]

PERFIL_ANALISTA = Perfil(
    chave="analista",
    nome="Analista",
    palavras_monitoradas=KEYWORDS_CARGO_FORTE_ANALISTA,
    paises_pesquisados=None,
    regras=_REGRAS_ANALISTA,
    regras_eixo_secundario=None,
    eixo_secundario_ativo=False,
    eixo_secundario_rotulo="",
    termos_busca=TERMOS_BUSCA_ANALISTA,
    termos_por_ciclo=TERMOS_POR_CICLO_ANALISTA,
    termos_prioritarios=TERMOS_PRIORITARIOS_ANALISTA,
    definicao_scrapers=_SCRAPERS_ANALISTA,
    max_scrapers_concorrentes=4,
    # MEDIDO (nov/2026): com o remoto passando a exigir o termo no título,
    # 172 das 188 vagas salvas deixaram de servir — continuariam na página
    # e na aba "Conteúdo Analista" sem isto.
    refiltrar_historico=True,
)

def _job_salvo(titulo: str, local: str, modalidade: str, site: str) -> Job:
    return Job(titulo=titulo or "", empresa="", local=local or "", link="", site=site or "",
               modalidade=modalidade or "")


def anuncio_reprovado(perfil_chave: str, titulo: str, texto_anuncio: str) -> str | None:
    """Motivo pelo qual o anúncio não serve ao perfil (ver core/anuncio.py),
    ou None — também quando o perfil não tem regra de anúncio ou o texto
    ainda não foi capturado."""
    perfil = PERFIS.get(perfil_chave)
    if perfil is None or perfil.regras_anuncio is None or not texto_anuncio:
        return None
    return motivo_reprovacao(titulo or "", texto_anuncio, perfil.regras_anuncio)


def aprovada_pelas_regras_atuais(
    perfil_chave: str, titulo: str, local: str, modalidade: str, site: str = "",
    texto_anuncio: str = "",
) -> bool:
    """A vaga já salva ainda passa no filtro de HOJE do perfil?

    - Título/local: só reavalia perfil com refiltrar_historico; para os
      outros o histórico fica como foi salvo.
    - Anúncio: quando o perfil tem regras_anuncio e o texto já foi
      capturado, o anúncio também precisa passar.
    Chave desconhecida devolve True. Não apaga nada do banco: quem chama só
    deixa de mostrar/abrir a vaga."""
    perfil = PERFIS.get(perfil_chave)
    if perfil is None:
        return True
    if perfil.refiltrar_historico and not _job_salvo(titulo, local, modalidade, site).combina_com(
        perfil.regras
    ):
        return False
    return anuncio_reprovado(perfil_chave, titulo, texto_anuncio) is None


def combina_com_perfil(perfil_chave: str, titulo: str, local: str, modalidade: str, site: str = "") -> bool:
    """A vaga (como está salva no banco) passa na regra de título/local do
    perfil, independente de refiltrar_historico. Usado pra classificar o
    histórico do perfil dev entre os subperfis (ver web/gerar.py)."""
    perfil = PERFIS.get(perfil_chave)
    if perfil is None:
        return False
    return _job_salvo(titulo, local, modalidade, site).combina_com(perfil.regras)


PERFIS = {
    PERFIL_BR.chave: PERFIL_BR,
    PERFIL_INTL.chave: PERFIL_INTL,
    PERFIL_DEV.chave: PERFIL_DEV,
    PERFIL_DEV_JOINVILLE.chave: PERFIL_DEV_JOINVILLE,
    PERFIL_DEV_REMOTO.chave: PERFIL_DEV_REMOTO,
    PERFIL_DEV_INTL.chave: PERFIL_DEV_INTL,
    PERFIL_ANALISTA.chave: PERFIL_ANALISTA,
}
