"""Fontes de vaga 100% remota que publicam API ou feed (JSON/RSS).

NENHUMA delas está ligada a perfil ainda — mesmo caminho das candidatas de
scrapers/nacionais.py: rodar a bancada (workflow "Sondar fontes", ou
`python -m scripts.sondar_fontes`), olhar o que cada uma traz e só então
promover a que render vaga APROVADA.

Por que estas, e por que leitura por API/feed em vez de HTML:

- HIMALAYAS, REMOTIVE e REMOTE OK publicam a lista de vagas em JSON para
  quem quiser consumir (pedindo só crédito e link de volta — o link da vaga
  aponta pro próprio site, e `site` aparece na notificação e na página).
  JSON não quebra quando o site troca uma classe de CSS, que é como as
  fontes deste projeto costumam morrer em silêncio (ver scrapers/generico.py).
- WE WORK REMOTELY RSS: a mesma fonte do WeWorkRemotelyIntlScraper, lida
  pelos feeds RSS por categoria em vez da busca renderizada no navegador.
  Duas vantagens que a busca não tem: o feed traz a REGIÃO em que a vaga
  contrata ("Anywhere in the World", "USA Only"), e não a sede da empresa
  (ver escopo_indefinido em core/job.py); e não precisa de Chromium.

O que nenhuma delas tem é vaga de empresa brasileira: tudo aqui é
`vaga_internacional` (ver _SITES_INTERNACIONAIS em core/job.py), então
servem ao dev-intl, nunca ao dev-remoto.

O filtro de país é o que já existe: `local` sai no formato
"Remote - <regiões>", que é o que extrair_escopo_remoto lê, e o perfil
decide pela lista mercados_remoto_aceitos. Região sem restrição sai como
"Remote - Worldwide" (escopo vazio = aceita).

Os formatos abaixo vieram da documentação pública de cada API. A sessão de
desenvolvimento não alcança nenhum desses sites (bloqueio de rede), então
nada aqui foi visto funcionando ainda — é exatamente o que a bancada mede.
Quando uma fonte devolver zero, `diagnostico` diz o que a resposta trouxe.
"""

import html
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

from core.job import Job, _normalizar
from core.logger import get_logger
from scrapers.base import BaseScraper

logger = get_logger()

TIMEOUT_SEGUNDOS = 30
# Pausa entre chamadas à mesma API: nenhuma delas é feita pra rajada.
PAUSA_ENTRE_CHAMADAS_S = 1.5

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


@dataclass
class FonteAPI:
    """O que a bancada precisa saber de uma fonte por API.

    `url_busca`: só informativo (a bancada imprime).
    `usa_termos`: False quando a fonte é lida inteira numa chamada (por
        categoria) e os termos não mudam nada — o filtro do perfil é que
        separa a vaga.
    `termos_sonda`: termos que a bancada usa quando ninguém passou
        --termos. Os padrões da bancada são em português, e uma API de fora
        com "desenvolvedor back-end" não mede nada.
    """
    nome: str
    url_busca: str
    usa_termos: bool = True
    termos_sonda: tuple = ()


# ---------------------------------------------------------------------------
# Peças comuns
# ---------------------------------------------------------------------------

# Região que declara a vaga aberta pra qualquer país.
_REGIOES_SEM_RESTRICAO = {
    "anywhere", "anywhere in the world", "worldwide", "global", "anywhere (100% remote)",
}
# Palavra que não diz região nenhuma: é pulada, não abre nem restringe.
# "Remote, US" é vaga dos EUA — se "remote" abrisse a vaga, passaria como
# mundial.
_REGIOES_NEUTRAS = {"", "remote", "remoto", "100% remote", "fully remote"}
# "Americas" inclui o Brasil, mas não é país nem bate "latam" em
# extrair_escopo_remoto — sem isto, vaga aberta pras Américas seria barrada
# como mercado não mapeado.
_PADRAO_AMERICAS = re.compile(r"^(north and south )?americas?( only)?$")
# Lista de país muito longa (a Himalayas chega a listar 40) vira ruído na
# notificação; Brasil/LATAM sobem pra frente antes do corte, então o
# escopo que importa nunca é cortado.
_MAX_REGIOES_NO_LOCAL = 8
_PRIORIDADE_REGIAO = ("brazil", "brasil", "latam", "latin america", "americas")


def local_remoto(regioes) -> str:
    """Lista de regiões/países em que a vaga contrata -> texto de `local`
    no formato que extrair_escopo_remoto entende."""
    nomes: list[str] = []
    vistos: set[str] = set()
    for bruto in regioes or []:
        if isinstance(bruto, dict):
            bruto = bruto.get("name") or bruto.get("country") or ""
        for parte in re.split(r"[,;/|]", str(bruto)):
            texto = " ".join(parte.split())
            norm = _normalizar(texto)
            if norm in _REGIOES_NEUTRAS:
                continue
            if norm in _REGIOES_SEM_RESTRICAO:
                # Uma região "qualquer lugar" no meio da lista vale pra
                # lista toda: a vaga é aberta.
                return "Remote - Worldwide"
            if _PADRAO_AMERICAS.match(norm):
                texto, norm = "Americas (LATAM)", "americas (latam)"
            if norm not in vistos:
                vistos.add(norm)
                nomes.append(texto)
    if not nomes:
        return "Remote - Worldwide"
    nomes.sort(key=lambda n: not any(p in _normalizar(n) for p in _PRIORIDADE_REGIAO))
    if len(nomes) > _MAX_REGIOES_NO_LOCAL:
        resto = len(nomes) - _MAX_REGIOES_NO_LOCAL
        nomes = nomes[:_MAX_REGIOES_NO_LOCAL] + [f"+{resto}"]
    return "Remote - " + ", ".join(nomes)


def data_iso(valor) -> str:
    """Timestamp unix, ISO ou data de RSS -> "AAAA-MM-DD" (o formato que
    Job.publicacao_antiga e publicado_em_legivel calculam). "" se não der."""
    if valor in (None, ""):
        return ""
    try:
        if isinstance(valor, (int, float)) or str(valor).isdigit():
            numero = float(valor)
            if numero > 1e11:  # milissegundos
                numero /= 1000
            return datetime.fromtimestamp(numero, tz=timezone.utc).date().isoformat()
        texto = str(valor).strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}", texto):
            return texto[:10]
        return parsedate_to_datetime(texto).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return ""


def texto_limpo(conteudo: str) -> str:
    """HTML de descrição -> texto corrido (pra regra de anúncio)."""
    sem_tags = re.sub(r"<[^>]+>", " ", conteudo or "")
    return " ".join(html.unescape(sem_tags).split())


class ScraperAPI(BaseScraper):
    """Base das fontes por API/feed: HTTP simples, sem navegador.

    `diagnostico` guarda uma linha por chamada (URL, status, tamanho, o
    que veio) — é o que a bancada imprime quando a fonte devolve zero.
    `descricoes` guarda o texto do anúncio que a API já entrega junto, por
    link: a bancada usa pra medir quantas aprovadas passariam na regra de
    anúncio do perfil sem abrir página nenhuma.
    """

    fonte: FonteAPI

    def __init__(self, termos_busca: list[str]):
        self.termos_busca = termos_busca
        self.diagnostico: list[str] = []
        self.descricoes: dict[str, str] = {}
        self._sessao = requests.Session()
        self._sessao.headers.update({"User-Agent": _USER_AGENT, "Accept": "application/json, */*"})

    def buscar_vagas(self) -> list[Job]:
        try:
            brutas = self._coletar()
        except requests.RequestException as e:
            self.diagnostico.append(f"erro de rede: {type(e).__name__}: {e}")
            logger.error(f"[{self.fonte.nome}] Erro de rede: {type(e).__name__}")
            brutas = []

        vagas, vistos = [], set()
        for vaga in brutas:
            if vaga.link in vistos:
                continue
            vistos.add(vaga.link)
            vagas.append(vaga)
        logger.info(f"[{self.fonte.nome}] {len(vagas)} vaga(s) encontrada(s) no total")
        return vagas

    def _coletar(self) -> list[Job]:
        raise NotImplementedError

    def _get(self, url: str, params: dict | None = None) -> requests.Response | None:
        """GET com registro no diagnóstico. None quando não deu 200 —
        quem chama decide se tenta outro caminho. Erro de rede também vira
        None: uma chamada que falha (um feed, um termo) não derruba as
        outras da mesma fonte."""
        try:
            resposta = self._sessao.get(url, params=params, timeout=TIMEOUT_SEGUNDOS)
        except requests.RequestException as e:
            self.diagnostico.append(f"GET {url} -> erro de rede: {type(e).__name__}: {e}")
            logger.error(f"[{self.fonte.nome}] Erro de rede em {url}: {type(e).__name__}")
            return None
        tipo = resposta.headers.get("content-type", "?").split(";")[0]
        self.diagnostico.append(
            f"GET {resposta.url} -> {resposta.status_code} ({tipo}, {len(resposta.content)} bytes)"
        )
        if resposta.status_code != 200:
            self.diagnostico.append(f"   início da resposta: {resposta.text[:200]!r}")
            logger.warning(f"[{self.fonte.nome}] HTTP {resposta.status_code} em {url}")
            return None
        return resposta

    def _json(self, url: str, params: dict | None = None):
        resposta = self._get(url, params)
        if resposta is None:
            return None
        try:
            return resposta.json()
        except ValueError:
            # Tela de anti-bot costuma vir com 200 e HTML.
            self.diagnostico.append(f"   não é JSON: {resposta.text[:200]!r}")
            return None

    def _guardar_descricao(self, vaga: Job | None, descricao: str) -> Job | None:
        if vaga and descricao:
            self.descricoes[vaga.link] = texto_limpo(descricao)
        return vaga


# ---------------------------------------------------------------------------
# Himalayas — himalayas.app
# ---------------------------------------------------------------------------

URL_HIMALAYAS_BUSCA = "https://himalayas.app/jobs/api/search"
URL_HIMALAYAS_LISTA = "https://himalayas.app/jobs/api"
# A lista geral devolve no máximo 20 por chamada; 5 páginas = as 100 mais
# recentes, usada só quando a busca por termo não responde.
PAGINAS_HIMALAYAS_LISTA = 5


def montar_job_himalayas(item: dict) -> Job | None:
    titulo = " ".join(str(item.get("title") or "").split())
    link = item.get("guid") or item.get("applicationLink") or ""
    if not isinstance(link, str) or not link.startswith("http"):
        link = item.get("applicationLink") or ""
    if not titulo or not isinstance(link, str) or not link.startswith("http"):
        return None
    return Job(
        titulo=titulo,
        empresa=item.get("companyName") or "Não informado",
        local=local_remoto(item.get("locationRestrictions") or []),
        link=link,
        site="Himalayas",
        publicado_em=data_iso(item.get("pubDate")),
        modalidade="Remoto",
    )


class HimalayasScraper(ScraperAPI):
    """Busca por termo, restrita a vaga que aceita quem mora no Brasil
    (`country=BR`). Se a busca não responder, cai pra lista geral das mais
    recentes e deixa o filtro do perfil escolher."""

    fonte = FonteAPI(
        nome="Himalayas",
        url_busca=f"{URL_HIMALAYAS_BUSCA}?q={{termo}}&country=BR",
        termos_sonda=("full stack developer", "node.js developer"),
    )

    def _coletar(self) -> list[Job]:
        vagas: list[Job] = []
        busca_respondeu = False
        for termo in self.termos_busca:
            logger.info(f"[Himalayas] Buscando: {termo}")
            dados = self._json(URL_HIMALAYAS_BUSCA, {"q": termo, "country": "BR", "sort": "recent"})
            time.sleep(PAUSA_ENTRE_CHAMADAS_S)
            if not isinstance(dados, dict) or not isinstance(dados.get("jobs"), list):
                continue
            busca_respondeu = True
            self.diagnostico.append(f"   '{termo}': {len(dados['jobs'])} item(ns)")
            for item in dados["jobs"]:
                vagas.append(self._guardar_descricao(montar_job_himalayas(item), item.get("description") or item.get("excerpt") or ""))

        if not busca_respondeu:
            self.diagnostico.append("busca por termo não respondeu — lendo a lista geral")
            for pagina in range(PAGINAS_HIMALAYAS_LISTA):
                dados = self._json(URL_HIMALAYAS_LISTA, {"limit": 20, "offset": pagina * 20})
                time.sleep(PAUSA_ENTRE_CHAMADAS_S)
                itens = dados.get("jobs") if isinstance(dados, dict) else None
                if not itens:
                    break
                for item in itens:
                    vagas.append(self._guardar_descricao(montar_job_himalayas(item), item.get("description") or item.get("excerpt") or ""))

        return [v for v in vagas if v]


# ---------------------------------------------------------------------------
# Remotive — remotive.com
# ---------------------------------------------------------------------------

URL_REMOTIVE = "https://remotive.com/api/remote-jobs"


def montar_job_remotive(item: dict) -> Job | None:
    titulo = " ".join(str(item.get("title") or "").split())
    link = item.get("url") or ""
    if not titulo or not str(link).startswith("http"):
        return None
    return Job(
        titulo=titulo,
        empresa=item.get("company_name") or "Não informado",
        local=local_remoto([item.get("candidate_required_location") or ""]),
        link=link,
        site="Remotive",
        publicado_em=data_iso(item.get("publication_date")),
        modalidade="Remoto",
    )


class RemotiveScraper(ScraperAPI):
    """Uma chamada por execução, na categoria inteira de software. A
    Remotive pede poucas chamadas por dia — buscar termo a termo
    multiplicaria isso sem trazer vaga que a categoria já não traga."""

    fonte = FonteAPI(
        nome="Remotive",
        url_busca=f"{URL_REMOTIVE}?category=software-dev",
        usa_termos=False,
    )

    def _coletar(self) -> list[Job]:
        logger.info("[Remotive] Lendo a categoria software-dev")
        dados = self._json(URL_REMOTIVE, {"category": "software-dev"})
        itens = dados.get("jobs") if isinstance(dados, dict) else None
        if not isinstance(itens, list):
            return []
        self.diagnostico.append(f"   {len(itens)} item(ns) na categoria")
        vagas = [self._guardar_descricao(montar_job_remotive(i), i.get("description") or "") for i in itens]
        return [v for v in vagas if v]


# ---------------------------------------------------------------------------
# Remote OK — remoteok.com
# ---------------------------------------------------------------------------

URL_REMOTEOK = "https://remoteok.com/api"


def montar_job_remoteok(item: dict) -> Job | None:
    titulo = " ".join(str(item.get("position") or "").split())
    link = item.get("url") or ""
    if not titulo or not str(link).startswith("http"):
        return None
    return Job(
        titulo=titulo,
        empresa=item.get("company") or "Não informado",
        local=local_remoto([item.get("location") or ""]),
        link=link,
        site="Remote OK",
        publicado_em=data_iso(item.get("date") or item.get("epoch")),
        modalidade="Remoto",
    )


class RemoteOkScraper(ScraperAPI):
    """Uma chamada: a API devolve as vagas mais recentes de todas as
    áreas, e o primeiro item da lista é o aviso legal (sem `position`), não
    vaga."""

    fonte = FonteAPI(nome="Remote OK", url_busca=URL_REMOTEOK, usa_termos=False)

    def _coletar(self) -> list[Job]:
        logger.info("[Remote OK] Lendo as vagas recentes")
        dados = self._json(URL_REMOTEOK)
        if not isinstance(dados, list):
            return []
        itens = [i for i in dados if isinstance(i, dict) and i.get("position")]
        self.diagnostico.append(f"   {len(itens)} vaga(s) na resposta ({len(dados)} itens)")
        vagas = [self._guardar_descricao(montar_job_remoteok(i), i.get("description") or "") for i in itens]
        return [v for v in vagas if v]


# ---------------------------------------------------------------------------
# We Work Remotely, pelos feeds RSS
# ---------------------------------------------------------------------------

FEEDS_WWR = [
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
]


def montar_jobs_wwr_rss(xml_texto: str) -> list[tuple[Job, str]]:
    """Feed RSS -> [(vaga, descrição)]. O título do item vem como
    "Empresa: Cargo"."""
    try:
        raiz = ET.fromstring(xml_texto)
    except ET.ParseError:
        return []
    saida = []
    for item in raiz.iter("item"):
        def campo(nome):
            return (item.findtext(nome) or "").strip()

        bruto = " ".join(campo("title").split())
        empresa, sep, titulo = bruto.partition(": ")
        if not sep:
            empresa, titulo = "Não informado", bruto
        link = campo("link") or campo("guid")
        if not titulo or not link.startswith("http"):
            continue
        saida.append((Job(
            titulo=titulo,
            empresa=empresa or "Não informado",
            local=local_remoto([campo("region") or campo("country")]),
            link=link.split("?")[0],
            site="We Work Remotely RSS",
            publicado_em=data_iso(campo("pubDate")),
            modalidade="Remoto",
        ), campo("description")))
    return saida


class WeWorkRemotelyRssScraper(ScraperAPI):
    """Os três feeds de programação (full-stack, back-end, front-end). Lê
    a categoria inteira — o feed não tem busca."""

    fonte = FonteAPI(nome="We Work Remotely RSS", url_busca=FEEDS_WWR[0], usa_termos=False)

    def _coletar(self) -> list[Job]:
        vagas: list[Job] = []
        for url in FEEDS_WWR:
            logger.info(f"[We Work Remotely RSS] Lendo {url.rsplit('/', 1)[-1]}")
            resposta = self._get(url)
            time.sleep(PAUSA_ENTRE_CHAMADAS_S)
            if resposta is None:
                continue
            itens = montar_jobs_wwr_rss(resposta.text)
            if not itens:
                self.diagnostico.append(f"   feed sem item legível: {resposta.text[:200]!r}")
            for vaga, descricao in itens:
                vagas.append(self._guardar_descricao(vaga, descricao))
        return vagas


# Ordem da bancada: as que têm API documentada primeiro.
CANDIDATAS_REMOTAS = [
    HimalayasScraper,
    RemotiveScraper,
    RemoteOkScraper,
    WeWorkRemotelyRssScraper,
]
