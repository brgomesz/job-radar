"""Adaptador PostgREST para a persistência compartilhada do JobRadar."""

import os
import re
import time

import requests


class ConfiguracaoSupabaseInvalida(RuntimeError):
    pass


def _configuracao() -> tuple[str, dict[str, str]]:
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    chave = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not chave:
        raise ConfiguracaoSupabaseInvalida(
            "JOBRADAR_STORAGE=supabase exige SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY."
        )
    return url, {"apikey": chave, "Authorization": f"Bearer {chave}"}


def _requisicao(metodo: str, tabela: str, *, params=None, json=None, headers=None):
    url, cabecalhos = _configuracao()
    cabecalhos.update(headers or {})
    ultima_falha = None
    for tentativa in range(3):
        try:
            resposta = requests.request(
                metodo, f"{url}/rest/v1/{tabela}", params=params, json=json,
                headers=cabecalhos, timeout=15,
            )
            # Erros de cliente não são transitórios; 429/5xx são e merecem
            # uma segunda chance antes de o ciclo falhar e repetir alertas.
            if resposta.status_code == 429 or resposta.status_code >= 500:
                resposta.raise_for_status()
            resposta.raise_for_status()
            return resposta.json() if resposta.content else None
        except requests.RequestException as erro:
            ultima_falha = erro
            if tentativa == 2:
                raise
            time.sleep(0.5 * (2 ** tentativa))
    raise ultima_falha  # pragma: no cover - proteção para o type checker


def verificar_conexao():
    _requisicao("GET", "job_radar_metadados", params={"select": "chave", "limit": "1"})


def ja_vista(job) -> bool:
    for coluna, valor in (("id", job.id), ("chave_secundaria", job.chave_secundaria)):
        if _requisicao("GET", "job_radar_vagas", params={"select": "id", coluna: f"eq.{valor}", "limit": "1"}):
            return True
    return False


def obter_metadado(chave: str) -> str | None:
    linhas = _requisicao("GET", "job_radar_metadados", params={"select": "valor", "chave": f"eq.{chave}", "limit": "1"})
    return linhas[0]["valor"] if linhas else None


def definir_metadado(chave: str, valor: str):
    _requisicao("POST", "job_radar_metadados", json={"chave": chave, "valor": valor}, headers={"Prefer": "resolution=merge-duplicates,return=minimal"})


def salvar_vaga(job, perfil_chave: str = "", digest_pendente: bool = False, exploratoria: bool = False):
    _requisicao("POST", "job_radar_vagas", json={
        "id": job.id, "titulo": job.titulo, "empresa": job.empresa, "local": job.local,
        "link": job.link, "site": job.site, "chave_secundaria": job.chave_secundaria,
        "publicado_em": job.publicado_em, "modalidade": job.modalidade, "relevancia": job.relevancia,
        "perfil": perfil_chave, "digest_pendente": digest_pendente, "exploratoria": exploratoria,
        "situacao": "nova",
    }, headers={"Prefer": "resolution=ignore-duplicates,return=minimal"})


def definir_situacao(id_ou_link: str, situacao: str):
    for coluna in ("id", "link"):
        _requisicao("PATCH", "job_radar_vagas", params={coluna: f"eq.{id_ou_link}"}, json={"situacao": situacao}, headers={"Prefer": "return=minimal"})


def definir_feedback(job_id: str, feedback: str):
    _requisicao("PATCH", "job_radar_vagas", params={"id": f"eq.{job_id}"}, json={"feedback": feedback}, headers={"Prefer": "return=minimal"})


def obter_vagas_pendentes_digest(perfil_chave: str) -> list[tuple]:
    linhas = _requisicao("GET", "job_radar_vagas", params={
        "select": "titulo,empresa,link,relevancia,exploratoria", "perfil": f"eq.{perfil_chave}",
        "digest_pendente": "is.true", "order": "relevancia.desc,encontrada_em.asc",
    })
    return [(l["titulo"], l["empresa"], l["link"], l["relevancia"], l["exploratoria"]) for l in linhas]


def marcar_digest_enviado(perfil_chave: str):
    _requisicao("PATCH", "job_radar_vagas", params={"perfil": f"eq.{perfil_chave}", "digest_pendente": "is.true"}, json={"digest_pendente": False}, headers={"Prefer": "return=minimal"})


def listar_vagas(perfil: str = "", situacao: str = "", site: str = "", busca: str = "", limite: int = 100) -> list[dict]:
    params = {"select": "*", "order": "encontrada_em.desc", "limit": str(max(1, min(limite, 250)))}
    for coluna, valor in (("perfil", perfil), ("situacao", situacao), ("site", site)):
        if valor:
            params[coluna] = f"eq.{valor}"
    if busca:
        # PostgREST usa vírgulas e parênteses como parte da sintaxe de `or`.
        # O filtro veio de um campo de texto do painel, então só termos de
        # busca comuns devem chegar à expressão, nunca operadores novos.
        busca_segura = re.sub(r"[^\wÀ-ÿ -]", "", busca, flags=re.UNICODE).strip()
        if busca_segura:
            params["or"] = f"(titulo.ilike.*{busca_segura}*,empresa.ilike.*{busca_segura}*)"
    return _requisicao("GET", "job_radar_vagas", params=params)


def resumo_painel() -> dict:
    linhas = _requisicao("GET", "job_radar_dashboard_resumo", params={"select": "*"})
    return linhas[0] if linhas else {"total": 0, "novas": 0, "candidaturas": 0, "ultima": None}


def opcoes_filtro_painel(coluna: str) -> list[str]:
    if coluna not in {"perfil", "site"}:
        raise ValueError(f"Coluna de filtro inválida: {coluna}")
    view = "job_radar_dashboard_perfis" if coluna == "perfil" else "job_radar_dashboard_sites"
    linhas = _requisicao("GET", view, params={"select": "valor", "order": "valor"})
    return [linha["valor"] for linha in linhas]


def obter_linhas_relatorio() -> list[tuple[str, str, str | None]]:
    linhas = []
    limite = 1000
    offset = 0
    while True:
        pagina = _requisicao(
            "GET", "job_radar_vagas",
            params={"select": "site,encontrada_em,feedback", "limit": str(limite), "offset": str(offset)},
        )
        linhas.extend(pagina)
        if len(pagina) < limite:
            break
        offset += limite
    return [(linha["site"], linha["encontrada_em"], linha["feedback"]) for linha in linhas]
