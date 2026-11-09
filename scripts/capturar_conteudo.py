"""Abre o anúncio de cada vaga aprovada e guarda o texto (descrição,
requisitos, benefícios) em conteudo_vagas — a matéria-prima das abas
"Conteúdo Dev" e "Conteúdo Analista" da página e dos arquivos
docs/conteudo-<perfil>.txt.

Roda como passo próprio do workflow, DEPOIS do ciclo de busca e ANTES de
salvar o banco. Passo separado (e com continue-on-error) porque nada aqui
pode atrasar ou derrubar a notificação: se o LinkedIn bloquear a leitura do
anúncio, o ciclo de busca já terminou e já avisou o que tinha pra avisar.

Por ciclo abre no máximo --limite vagas DE CADA perfil (mais recentes
primeiro). O
histórico atrasado vai sendo coberto aos poucos: vaga que falhou volta na
fila até MAX_TENTATIVAS; a que a fonte respondeu 404/410 sai da fila.

Uso:
    python -m scripts.capturar_conteudo                         # perfil dev
    python -m scripts.capturar_conteudo --perfil dev analista
    python -m scripts.capturar_conteudo --limite 20
"""

import argparse

from core.logger import get_logger
from core.perfis import aprovada_pelas_regras_atuais
from database.database import reabrir_conteudo_bloqueado, salvar_conteudo, vagas_sem_conteudo
from scrapers.conteudo import ler_anuncios, parece_bloqueio

logger = get_logger()

MAX_TENTATIVAS = 3


def capturar(perfil: str, limite: int) -> dict:
    reabertas = reabrir_conteudo_bloqueado(perfil, parece_bloqueio)
    if reabertas:
        logger.info(f"[conteudo] {reabertas} texto(s) de tela de bloqueio voltaram pra fila.")
    # Vaga salva que não passa mais no filtro de hoje do perfil (ver
    # refiltrar_historico em core/perfis.py) não vale a visita: ela nem
    # aparece na página. Filtra antes de cortar no limite, senão o lote do
    # ciclo podia vir inteiro de vagas descartadas.
    fila = [
        (job_id, link, site, titulo)
        for job_id, link, site, titulo, local, modalidade in vagas_sem_conteudo(perfil, None, MAX_TENTATIVAS)
        if aprovada_pelas_regras_atuais(perfil, titulo, local, modalidade, site)
    ][:limite]
    resumo = {"ok": 0, "falhou": 0, "indisponivel": 0, "pulada": 0}
    if not fila:
        logger.info(f"[conteudo] Nada pendente no perfil {perfil}.")
        return resumo

    logger.info(f"[conteudo] {len(fila)} vaga(s) do perfil {perfil} pra abrir.")
    # Abre e lê (scrapers/conteudo.py); aqui só grava. Vaga "pulada" (fonte
    # que bloqueou neste run) não conta tentativa — volta inteira no
    # próximo ciclo.
    for job_id, (status, texto, origem) in ler_anuncios(fila).items():
        resumo[status] += 1
        if status != "pulada":
            salvar_conteudo(job_id, status, texto, origem)

    logger.info(
        f"[conteudo] Perfil {perfil}: {resumo['ok']} capturada(s), {resumo['falhou']} falha(s), "
        f"{resumo['indisponivel']} removida(s) na fonte, {resumo['pulada']} adiada(s) por bloqueio."
    )
    return resumo


def main():
    parser = argparse.ArgumentParser(description="Captura o texto dos anúncios das vagas salvas")
    parser.add_argument("--perfil", nargs="+", default=["dev"])
    parser.add_argument("--limite", type=int, default=80, help="máximo de vagas abertas POR perfil")
    args = parser.parse_args()
    for perfil in args.perfil:
        # Um perfil que quebre não impede o seguinte de rodar.
        try:
            capturar(perfil, args.limite)
        except Exception as e:
            logger.error(f"[conteudo] Captura do perfil {perfil} interrompida: {e}")


if __name__ == "__main__":
    main()
