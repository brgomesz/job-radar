"""Abre o anúncio de uma vaga e devolve o texto dele (descrição, requisitos,
benefícios) — o que os scrapers de busca nunca leem: eles só passam pelo
card da listagem (título, empresa, local).

Usado por scripts/capturar_conteudo.py, depois do ciclo, só nas vagas que
já foram APROVADAS e salvas. Não entra no filtro: serve pra juntar o que o
mercado pede (aba "Conteúdo Dev" da página).

Ordem de extração, da mais limpa pra mais genérica:
  1. seletor próprio da fonte (o bloco da descrição, sem menu nem rodapé);
  2. JSON-LD JobPosting (schema.org) — a maioria dos portais publica pro
     Google for Jobs, e o campo `description` é exatamente o anúncio;
  3. <main>/<article> da página.
Página inteira (<body>) NÃO é fallback de propósito: num muro de login ou
banner de cookie ela devolveria lixo que pareceria conteúdo de vaga, e esse
texto vai direto pra uma análise. Melhor falhar e tentar no próximo ciclo.
"""

import html
import json
import re

# Menos que isso não é anúncio, é casca de página (título + botão).
MIN_CARACTERES = 150
# Teto por vaga: anúncio real raramente passa de 8k; acima disso é página
# que veio com coisa demais junto.
MAX_CARACTERES = 20000

SELETORES_POR_SITE = {
    "LinkedIn": [".show-more-less-html__markup", ".description__text"],
    "Gupy": ['[data-testid="text-section"]', "#job-description", '[class*="JobDescription"]'],
    "We Work Remotely": [
        ".lis-container__job__content__description",
        "#job-listing-show-container",
        ".listing-container",
    ],
    "Catho": ['[class*="job-description"]', '[class*="JobDescription"]', "#job-description"],
    "Solides": ['[class*="description"]', '[class*="Description"]'],
}
SELETORES_GENERICOS = ["main", "article", '[role="main"]']

_LINKEDIN_ID = re.compile(r"(\d{6,})(?:[/?#]|$)")


def url_para_abrir(link: str, site: str) -> str:
    """LinkedIn: em vez da página pública da vaga (pesada e quase sempre
    com muro de login pra IP de datacenter), usa o endpoint "guest" de
    detalhe — o mesmo da família jobs-guest que o LinkedInScraper já usa na
    busca. Devolve só o fragmento com a descrição e os critérios."""
    if site == "LinkedIn":
        caminho = link.split("?", 1)[0]
        achado = _LINKEDIN_ID.search(caminho)
        if achado:
            return f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{achado.group(1)}"
    return link


def html_para_texto(bruto: str) -> str:
    """HTML do JSON-LD -> texto com quebras de linha e marcadores de lista
    preservados (é o que mantém "requisitos" legíveis como lista)."""
    t = bruto or ""
    # JSON-LD às vezes traz o HTML escapado (&lt;p&gt;) — desescapa antes
    # de procurar tag.
    if "&lt;" in t and "<" not in t:
        t = html.unescape(t)
    t = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", t)
    t = re.sub(r"(?i)<br\s*/?>", "\n", t)
    t = re.sub(r"(?i)<li[^>]*>", "\n- ", t)
    t = re.sub(r"(?i)</(p|div|ul|ol|h[1-6]|tr|section)>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    return limpar_texto(html.unescape(t))


def limpar_texto(texto: str) -> str:
    linhas = [re.sub(r"[ \t ]+", " ", l).strip() for l in (texto or "").splitlines()]
    t = "\n".join(linhas)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t[:MAX_CARACTERES]


def descricao_jsonld(scripts: list[str]) -> str:
    """`description` do primeiro JobPosting achado nos <script
    type="application/ld+json"> da página. Aceita objeto solto, lista e
    @graph — os três formatos aparecem em portal real."""
    for bruto in scripts:
        try:
            dado = json.loads(bruto)
        except (ValueError, TypeError):
            continue
        pilha = [dado]
        while pilha:
            item = pilha.pop()
            if isinstance(item, list):
                pilha.extend(item)
            elif isinstance(item, dict):
                tipo = item.get("@type")
                tipos = tipo if isinstance(tipo, list) else [tipo]
                if "JobPosting" in tipos and isinstance(item.get("description"), str):
                    texto = html_para_texto(item["description"])
                    if len(texto) >= MIN_CARACTERES:
                        return texto
                if "@graph" in item:
                    pilha.append(item["@graph"])
    return ""


def _texto_dos_seletores(page, seletores: list[str]) -> str:
    for seletor in seletores:
        try:
            elementos = page.query_selector_all(seletor)
        except Exception:
            continue
        # Gupy divide o anúncio em várias seções com o mesmo seletor
        # (descrição, responsabilidades, requisitos, informações) — junta
        # todas em vez de ficar só com a primeira.
        partes = []
        for el in elementos:
            try:
                partes.append(el.inner_text())
            except Exception:
                continue
        texto = limpar_texto("\n\n".join(p for p in partes if p and p.strip()))
        if len(texto) >= MIN_CARACTERES:
            return texto
    return ""


def _criterios_linkedin(page) -> str:
    """Nível, tipo de contrato, função e setor — a lista que o LinkedIn
    mostra embaixo da descrição. Pequena, mas é justamente o tipo de dado
    que uma análise de mercado quer."""
    linhas = []
    for item in page.query_selector_all(".description__job-criteria-item"):
        try:
            rotulo = item.query_selector(".description__job-criteria-subheader")
            valor = item.query_selector(".description__job-criteria-text")
            if rotulo and valor:
                linhas.append(f"{rotulo.inner_text().strip()}: {valor.inner_text().strip()}")
        except Exception:
            continue
    return "\n".join(linhas)


def extrair_da_pagina(page, site: str) -> tuple[str, str]:
    """(texto, origem) de uma página já carregada; ("", "") se nada serviu."""
    texto = _texto_dos_seletores(page, SELETORES_POR_SITE.get(site, []))
    if texto:
        if site == "LinkedIn":
            criterios = _criterios_linkedin(page)
            if criterios:
                texto = f"{texto}\n\n{criterios}"
        return texto, "seletor"

    try:
        scripts = [
            el.text_content() or ""
            for el in page.query_selector_all('script[type="application/ld+json"]')
        ]
    except Exception:
        scripts = []
    texto = descricao_jsonld(scripts)
    if texto:
        return texto, "json-ld"

    texto = _texto_dos_seletores(page, SELETORES_GENERICOS)
    if texto:
        return texto, "pagina"
    return "", ""
