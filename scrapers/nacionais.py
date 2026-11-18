"""Fontes nacionais novas, configuradas sobre o ScraperGenerico.

NENHUMA delas está ligada a perfil ainda — ver core/perfis.py. O caminho é:
rodar a bancada (`python -m scripts.sondar_fontes`, ou o workflow
"Sondar fontes"), olhar quantas vagas cada uma traz de verdade, e só então
promover a que rende. É a mesma disciplina que o resto do projeto usa: o
Trampos ficou 6 dias rendendo zero porque entrou sem medição, e a
GeekHunter foi promovida por palpite e entregou 151 brutas -> 0 filtradas.

Por que estas quatro, e não outras:

- VAGAS.COM.BR e INFOJOBS são os dois maiores portais generalistas do país.
  Cobrem as três áreas dos perfis (dev, administrativo, agro) num só lugar.
- TRABALHA BRASIL é o que melhor cobre cidade do interior e vaga
  operacional/técnica — exatamente o buraco dos perfis admin e agro, que
  procuram em Joinville, Piraquara, Ponta Grossa e afins, onde o LinkedIn
  é fraco.
- BNE entra como quarta porque é forte em vaga técnica de indústria e
  agro, e custa pouco somar (a configuração é a parte barata).

Os padrões de URL abaixo vieram da estrutura pública de cada site. Se
algum estiver errado, a sonda mostra "0 vagas" com o HTML na mão pra
corrigir — nenhum deles entra no ciclo de produção antes disso.
"""

from scrapers.generico import FonteHTML, ScraperGenerico


class VagasComScraper(ScraperGenerico):
    fonte = FonteHTML(
        nome="Vagas.com",
        base_url="https://www.vagas.com.br",
        url_busca="https://www.vagas.com.br/vagas-de-{termo}",
        # /vagas/v1234567/analista-de-dados
        padrao_link=r"/vagas/v\d+",
        slug="hifen",
        seletor_espera="[id^=ck], .vaga",
        max_paginas=1,
    )


class InfoJobsScraper(ScraperGenerico):
    fonte = FonteHTML(
        nome="InfoJobs",
        base_url="https://www.infojobs.com.br",
        url_busca="https://www.infojobs.com.br/empregos.aspx?Palabra={termo}",
        # /vaga-de-analista-de-dados-em-joinville__1234567.aspx
        padrao_link=r"/vaga-de-.+__\d+\.aspx",
        slug="mais",
        seletor_espera=".js-vacancyLoad, .vacancy-item",
        max_paginas=1,
    )


class TrabalhaBrasilScraper(ScraperGenerico):
    fonte = FonteHTML(
        nome="Trabalha Brasil",
        base_url="https://www.trabalhabrasil.com.br",
        url_busca="https://www.trabalhabrasil.com.br/vagas-empregos?palavraChave={termo}",
        # /vagas-empregos-em-joinville-sc/analista-de-dados-1234567
        padrao_link=r"/vagas?-empregos?-em-[^/]+/[^/]+-\d+",
        slug="query",
        seletor_espera="#job-list, .job-item",
        max_paginas=1,
    )


class BneScraper(ScraperGenerico):
    fonte = FonteHTML(
        nome="BNE",
        base_url="https://www.bne.com.br",
        url_busca="https://www.bne.com.br/vagas-de-emprego/{termo}",
        padrao_link=r"/vaga/\d+|/vagas?-de-emprego/[^/]+/\d+",
        slug="hifen",
        seletor_espera=".vaga, .card-vaga",
        max_paginas=1,
    )


# --- Consultorias de recrutamento (perfil analista) ---------------------------
#
# Michael Page e Robert Half recrutam justamente gerência e coordenação
# financeira/operacional de média e alta senioridade — o nível da Ana Julia,
# que nos portais generalistas fica afogado em vaga de assistente. Entram
# pelo perfil analista; volume é baixo, rendimento é o que a bancada mede.
#
# O card dessas duas costuma trazer só a cidade, sem UF ("Joinville"), e o
# extrator por "Cidade - UF" deixaria a vaga sem local — `local_sem_uf`
# liga o reconhecimento de cidade conhecida (ver ScraperGenerico).
#
# Os padrões abaixo vêm do formato público de cada site, não de inspeção
# ao vivo (a sessão de desenvolvimento não alcança os sites). Se o padrão
# de link errar, a bancada mostra os hrefs reais da página.

class MichaelPageScraper(ScraperGenerico):
    fonte = FonteHTML(
        nome="Michael Page",
        base_url="https://www.michaelpage.com.br",
        url_busca="https://www.michaelpage.com.br/jobs/{termo}",
        # /job-detail/gerente-financeiro/ref/jn-112026-1234567
        padrao_link=r"/job-detail/[^/]+/ref/",
        slug="hifen",
        seletor_espera="a[href*='/job-detail/']",
        max_paginas=1,
        local_sem_uf=True,
    )


class RobertHalfScraper(ScraperGenerico):
    fonte = FonteHTML(
        nome="Robert Half",
        base_url="https://www.roberthalf.com",
        url_busca="https://www.roberthalf.com/br/pt/jobs?query={termo}",
        # /br/pt/job/joinville-sc/gerente-financeiro/12345-0001234567-ptbr
        padrao_link=r"/br/pt/(?:job|vaga)s?/[^?#]+\d{5,}",
        slug="query",
        seletor_espera="a[href*='/br/pt/job']",
        max_paginas=1,
        espera_extra_s=4.0,
        local_sem_uf=True,
    )


# Ordem da sonda: da mais promissora pra menos, pra quem estiver lendo o
# log parar de ler quando já tiver a resposta.
CANDIDATAS = [
    MichaelPageScraper,
    RobertHalfScraper,
    VagasComScraper,
    InfoJobsScraper,
    TrabalhaBrasilScraper,
    BneScraper,
]
