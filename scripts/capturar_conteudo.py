"""Abre o anúncio de cada vaga aprovada e guarda o texto (descrição,
requisitos, benefícios) em conteudo_vagas — a matéria-prima da aba
"Conteúdo Dev" da página e do arquivo docs/conteudo-dev.txt.

Roda como passo próprio do workflow, DEPOIS do ciclo de busca e ANTES de
salvar o banco. Passo separado (e com continue-on-error) porque nada aqui
pode atrasar ou derrubar a notificação: se o LinkedIn bloquear a leitura do
anúncio, o ciclo de busca já terminou e já avisou o que tinha pra avisar.

Por ciclo abre no máximo --limite vagas (mais recentes primeiro). O
histórico atrasado vai sendo coberto aos poucos: vaga que falhou volta na
fila até MAX_TENTATIVAS; a que a fonte respondeu 404/410 sai da fila.

Uso:
    python -m scripts.capturar_conteudo                 # perfil dev
    python -m scripts.capturar_conteudo --limite 20
"""

import argparse
import time

from playwright.sync_api import sync_playwright

from core.logger import get_logger
from database.database import reabrir_conteudo_bloqueado, salvar_conteudo, vagas_sem_conteudo
from scrapers.conteudo import extrair_da_pagina, parece_bloqueio, url_para_abrir

logger = get_logger()

MAX_TENTATIVAS = 3
# Entre uma vaga e outra. O endpoint guest do LinkedIn rate-limita rápido
# vindo de IP de datacenter; o ciclo não tem pressa nenhuma aqui.
PAUSA_SEGUNDOS = 2.0
# Respostas 429/999 seguidas da mesma fonte: para de bater nela neste run.
# Insistir só piora o bloqueio, e as vagas voltam na fila no próximo ciclo.
MAX_BLOQUEIOS_SEGUIDOS = 3

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def capturar(perfil: str, limite: int) -> dict:
    reabertas = reabrir_conteudo_bloqueado(perfil, parece_bloqueio)
    if reabertas:
        logger.info(f"[conteudo] {reabertas} texto(s) de tela de bloqueio voltaram pra fila.")
    fila = vagas_sem_conteudo(perfil, limite, MAX_TENTATIVAS)
    resumo = {"ok": 0, "falhou": 0, "indisponivel": 0, "pulada": 0}
    if not fila:
        logger.info(f"[conteudo] Nada pendente no perfil {perfil}.")
        return resumo

    logger.info(f"[conteudo] {len(fila)} vaga(s) do perfil {perfil} pra abrir.")
    bloqueios: dict[str, int] = {}

    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        page = navegador.new_page(user_agent=USER_AGENT)
        try:
            for job_id, link, site, titulo in fila:
                if bloqueios.get(site, 0) >= MAX_BLOQUEIOS_SEGUIDOS:
                    resumo["pulada"] += 1
                    continue
                try:
                    resposta = page.goto(url_para_abrir(link, site), timeout=45000)
                    codigo = resposta.status if resposta else 0
                    if codigo in (404, 410):
                        salvar_conteudo(job_id, "indisponivel")
                        resumo["indisponivel"] += 1
                        bloqueios[site] = 0
                        continue
                    if codigo in (429, 999):
                        bloqueios[site] = bloqueios.get(site, 0) + 1
                        salvar_conteudo(job_id, "falhou")
                        resumo["falhou"] += 1
                        logger.warning(f"[conteudo] {site} respondeu {codigo} (bloqueio) em '{titulo}'.")
                        continue
                    try:
                        page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        pass  # página que nunca sossega: lê o que já carregou
                    texto, origem = extrair_da_pagina(page, site)
                except Exception as e:
                    logger.warning(f"[conteudo] Erro abrindo '{titulo}' ({site}): {e}")
                    texto, origem = "", ""

                if texto:
                    salvar_conteudo(job_id, "ok", texto, origem)
                    resumo["ok"] += 1
                    bloqueios[site] = 0
                else:
                    salvar_conteudo(job_id, "falhou")
                    resumo["falhou"] += 1
                    logger.warning(f"[conteudo] Sem texto de anúncio em '{titulo}' ({site}).")
                time.sleep(PAUSA_SEGUNDOS)
        finally:
            navegador.close()

    logger.info(
        f"[conteudo] Perfil {perfil}: {resumo['ok']} capturada(s), {resumo['falhou']} falha(s), "
        f"{resumo['indisponivel']} removida(s) na fonte, {resumo['pulada']} adiada(s) por bloqueio."
    )
    return resumo


def main():
    parser = argparse.ArgumentParser(description="Captura o texto dos anúncios das vagas salvas")
    parser.add_argument("--perfil", default="dev")
    parser.add_argument("--limite", type=int, default=80)
    args = parser.parse_args()
    capturar(args.perfil, args.limite)


if __name__ == "__main__":
    main()
