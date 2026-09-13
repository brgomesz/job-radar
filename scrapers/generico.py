"""Extrator genérico de card de vaga, para portais brasileiros de HTML.

POR QUE EXISTE, e por que ele não parece com catho.py/solides.py: cada
scraper desta base nasceu de alguém ABRINDO o site, olhando o DOM e
escrevendo o seletor exato ("article", "h2 a", paragrafos[1]). Isso dá o
melhor resultado possível por fonte — e quebra em silêncio quando o site
muda uma classe, devolvendo 0 vaga sem erro nenhum (foi o que aconteceu
com o Trampos, que rendeu zero por 6 dias antes de alguém investigar).

Aqui a aposta é outra: em vez de UM seletor certo, uma cadeia de sinais
que quase todo portal de vaga do Brasil emite, na ordem do mais confiável
pro menos:

  1. O LINK da vaga. Todo portal tem uma URL de detalhe com formato
     reconhecível (/vagas/<id>, /vaga/<slug>, /vaga-de-...). É o sinal mais
     estável que existe: muda muito menos que classe de CSS, porque quebrar
     a URL quebra o SEO do site inteiro.
  2. O TEXTO ÂNCORA do link, que é o título em praticamente todo card.
  3. O TEXTO DO CONTAINER em volta, de onde saem cidade, empresa e data —
     por PADRÃO, não por seletor: "Joinville - SC" é escrito assim em
     qualquer portal brasileiro, com hífen, barra ou vírgula.

O preço é honesto: `empresa` sai pior do que um seletor dedicado sairia (é
heurística sobre texto solto). O que NÃO pode sair pior é `local`, porque
é ele que decide se a vaga passa no filtro de cidade — daí a extração de
localidade ser por regex de "Cidade - UF", e não por posição de parágrafo.

Uma fonte nova aqui é ~10 linhas de configuração (FonteHTML), não um
arquivo de scraper. Ver scrapers/nacionais.py.
"""

import re
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

from core.job import Job, _e_remoto, _normalizar, extrair_data_publicacao, _SIGLAS_UF_BRASIL
from core.logger import get_logger
from scrapers.base import BaseScraper

logger = get_logger()

# "Joinville - SC", "Joinville/SC", "Joinville, SC", "São José dos Pinhais
# - PR". Aceita hífen, barra e vírgula porque os três aparecem em portal
# brasileiro, às vezes no mesmo site em telas diferentes.
#
# A UF é conferida contra a lista real (_SIGLAS_UF_BRASIL) depois do match:
# sem isso, "Node - JS" e "Pleno/SR" viravam localidade.
_PADRAO_CIDADE_UF = re.compile(
    r"([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][\wÁÀÂÃÉÊÍÓÔÕÚÇáàâãéêíóôõúç'’.\- ]{2,40}?)\s*[-/,]\s*([A-Za-z]{2})(?!\w)"
)

# Palavra que, sozinha num card, indica vaga remota. Reaproveita o
# vocabulário de core/job.py (_e_remoto) — não duplica lista aqui.
_ROTULOS_MODALIDADE = ("híbrido", "hibrido", "presencial")


@dataclass
class FonteHTML:
    """Tudo que muda de um portal pro outro.

    `url_busca`: template com {termo} já no formato do site (ver `slug`).
    `padrao_link`: regex do href de uma vaga DE VERDADE. É o que separa o
        card do resto da página (menu, rodapé, "vagas relacionadas").
    `slug`: como o termo entra na URL — "hifen" (analista-de-dados),
        "mais" (analista+de+dados) ou "query" (analista%20de%20dados).
    `seletor_espera`: o que aguardar antes de ler a página. Opcional: sem
        ele, espera a rede sossegar. Um seletor errado aqui não zera a
        fonte — o extrator tenta ler mesmo depois de estourar o tempo.
    """
    nome: str
    url_busca: str
    padrao_link: str
    base_url: str
    slug: str = "hifen"
    seletor_espera: str = ""
    max_paginas: int = 1
    param_pagina: str = ""  # ex: "&page={pagina}" — vazio = não pagina
    espera_extra_s: float = 2.0
    cabecalhos_ignorados: tuple = ()


def formatar_termo(termo: str, estilo: str) -> str:
    limpo = termo.strip().lower()
    if estilo == "mais":
        return limpo.replace(" ", "+")
    if estilo == "query":
        return limpo.replace(" ", "%20")
    return re.sub(r"[^\w\s-]", "", limpo).replace(" ", "-")


def extrair_local(texto: str) -> str:
    """Primeira "Cidade - UF" plausível do texto do card.

    Devolve "" quando não acha — melhor deixar o filtro rejeitar por falta
    de localidade do que inventar uma cidade que o card não disse.
    """
    for cidade, uf in _PADRAO_CIDADE_UF.findall(texto or ""):
        if uf.lower() in _SIGLAS_UF_BRASIL:
            cidade_limpa = " ".join(cidade.split())
            # Corta lixo grudado antes do nome ("R$ 3.000 Joinville - SC").
            cidade_limpa = re.split(r"[|•·\n]", cidade_limpa)[-1].strip()
            if cidade_limpa:
                return f"{cidade_limpa} - {uf.upper()}"
    return ""


def extrair_modalidade(texto: str) -> str:
    """Remoto/Híbrido/Presencial a partir do texto do card, ou "".

    Remoto tem prioridade: card que diz "Híbrido (remoto 3x)" é mais útil
    pro usuário como remoto do que como híbrido, e o filtro de cidade já
    trata híbrido e presencial do mesmo jeito.
    """
    norm = _normalizar(texto or "")
    if _e_remoto(norm):
        return "Remoto"
    for rotulo in _ROTULOS_MODALIDADE:
        if rotulo in norm:
            return "Híbrido" if rotulo.startswith("h") else "Presencial"
    return ""


def extrair_empresa(texto_card: str, titulo: str, local: str) -> str:
    """Melhor palpite de empresa: a primeira linha do card que não é o
    título, não é a localidade e não parece rótulo de interface.

    É heurística e vai errar às vezes — assumido na docstring do módulo. O
    campo é informativo (aparece na notificação e na página); nada do
    filtro depende dele.
    """
    ignorar = {_normalizar(titulo), _normalizar(local)}
    for linha in (texto_card or "").splitlines():
        limpa = linha.strip(" •|·-\t")
        if len(limpa) < 2 or len(limpa) > 80:
            continue
        norm = _normalizar(limpa)
        if norm in ignorar:
            continue
        # Linha que é DATA não é empresa. Reusa o reconhecedor do projeto em
        # vez de uma regex própria: ele já cobre "Há 3 dias", "Publicada em
        # 11/08", "hoje" e "ontem", cada um pego de um site diferente.
        #
        # MEDIDO pelo teste: a versão anterior procurava "há \d" num texto
        # JÁ NORMALIZADO (sem acento), então "Há 3 dias" nunca batia e virava
        # nome de empresa.
        if extrair_data_publicacao(limpa):
            continue
        # Rótulo de interface e faixa salarial também não são empresa.
        if re.search(r"r\$|salari|candidat|publicad|vagas?\b|ver vaga|efetivo|clt|pj\b|confidencial", norm):
            continue
        if _PADRAO_CIDADE_UF.search(limpa):
            continue
        return limpa
    return "Não informado"


class ScraperGenerico(BaseScraper):
    """Roda uma FonteHTML sobre uma lista de termos."""

    fonte: FonteHTML  # definida na subclasse (ver scrapers/nacionais.py)

    def __init__(self, termos_busca: list[str]):
        self.termos_busca = termos_busca

    def buscar_vagas(self) -> list[Job]:
        vagas: list[Job] = []
        # UM browser para todos os termos, não um por termo: lançar Chromium
        # custa ~1s e os scrapers antigos pagam isso a cada termo (ver
        # catho.py). Com 12 termos por ciclo por fonte, é ~12s de pura
        # inicialização que dá pra não gastar.
        with sync_playwright() as p:
            navegador = p.chromium.launch(headless=True)
            pagina = navegador.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            )
            pagina.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
            )
            try:
                for termo in self.termos_busca:
                    vagas.extend(self._buscar_termo(pagina, termo))
            finally:
                navegador.close()

        logger.info(f"[{self.fonte.nome}] {len(vagas)} vaga(s) encontrada(s) no total")
        return vagas

    def _buscar_termo(self, pagina, termo: str) -> list[Job]:
        logger.info(f"[{self.fonte.nome}] Buscando: {termo}")
        vagas: list[Job] = []
        vistos: set[str] = set()

        for n in range(1, self.fonte.max_paginas + 1):
            url = self.fonte.url_busca.format(termo=formatar_termo(termo, self.fonte.slug))
            if n > 1 and self.fonte.param_pagina:
                url += self.fonte.param_pagina.format(pagina=n)
            elif n > 1:
                break

            try:
                achadas = self._ler_pagina(pagina, url)
            except Exception as e:
                logger.error(f"[{self.fonte.nome}] Erro em '{termo}' (página {n}): {type(e).__name__}")
                break

            novas = [v for v in achadas if v.link not in vistos]
            vistos.update(v.link for v in novas)
            vagas.extend(novas)

            # Página que não trouxe nada novo é fim de resultado — insistir
            # nas seguintes só gastaria requisição.
            if not novas:
                break

        return vagas

    def _ler_pagina(self, pagina, url: str) -> list[Job]:
        pagina.goto(url, timeout=60000, wait_until="domcontentloaded")
        if self.fonte.seletor_espera:
            try:
                pagina.wait_for_selector(self.fonte.seletor_espera, state="attached", timeout=20000)
            except Exception:
                # Seletor de espera errado (ou site mudou) NÃO pode zerar a
                # fonte: o conteúdo pode estar lá mesmo assim. Segue e deixa
                # a extração por link decidir se achou vaga.
                logger.warning(
                    f"[{self.fonte.nome}] Seletor de espera não apareceu — lendo a página assim mesmo."
                )
        if self.fonte.espera_extra_s:
            time.sleep(self.fonte.espera_extra_s)

        return self.extrair_da_pagina(
            pagina.eval_on_selector_all(
                "a[href]",
                """els => els.map(a => {
                    const caixa = a.closest('article, li, [class*=card], [class*=vaga], [class*=job], div');
                    return {
                        href: a.getAttribute('href') || '',
                        texto: (a.innerText || '').trim(),
                        caixa: caixa ? (caixa.innerText || '').trim() : '',
                    };
                })""",
            )
        )

    def extrair_da_pagina(self, ancoras: list[dict]) -> list[Job]:
        """Âncoras cruas -> vagas. Separado da navegação de propósito: é a
        parte que dá pra testar sem abrir browser nenhum (ver
        tests/test_scraper_generico.py)."""
        padrao = re.compile(self.fonte.padrao_link)
        vagas: list[Job] = []
        vistos: set[str] = set()

        for a in ancoras:
            href, titulo, caixa = a.get("href", ""), a.get("texto", ""), a.get("caixa", "")
            if not href or not padrao.search(href):
                continue
            titulo = " ".join(titulo.split())
            # Âncora sem texto (imagem, botão "ver vaga") aponta pra mesma
            # vaga que a âncora do título — descartar aqui evita duplicata.
            if len(titulo) < 5 or len(titulo) > 200:
                continue
            if _normalizar(titulo) in {_normalizar(c) for c in self.fonte.cabecalhos_ignorados}:
                continue

            link = urljoin(self.fonte.base_url, href.split("#")[0])
            if link in vistos:
                continue
            vistos.add(link)

            texto = caixa if len(caixa) > len(titulo) else titulo
            local = extrair_local(texto)
            vagas.append(Job(
                titulo=titulo,
                empresa=extrair_empresa(texto, titulo, local),
                local=local or "Não informado",
                link=link,
                site=self.fonte.nome,
                publicado_em=extrair_data_publicacao(texto),
                modalidade=extrair_modalidade(texto),
            ))

        return vagas
