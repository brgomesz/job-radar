"""Importa o histórico local de SQLite para a base Supabase configurada.

Uso: JOBRADAR_STORAGE=supabase SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... \
     python scripts/migrar_sqlite_para_supabase.py
"""

import argparse
import sqlite3
import sys
from pathlib import Path

# Executado como `python scripts/...`; nesse modo a raiz do repositório não
# entra automaticamente em sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import DB_PATH
from database import supabase


def _linhas(conn, tabela: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(linha) for linha in conn.execute(f"SELECT * FROM {tabela}").fetchall()]


def _em_lotes(valores: list[dict], tamanho: int = 250):
    for inicio in range(0, len(valores), tamanho):
        yield valores[inicio : inicio + tamanho]


def main():
    parser = argparse.ArgumentParser(description="Migra data/jobs.db para Supabase.")
    parser.add_argument("--dry-run", action="store_true", help="Mostra quantidades sem enviar dados.")
    args = parser.parse_args()

    with sqlite3.connect(DB_PATH) as conn:
        vagas = _linhas(conn, "vagas_vistas")
        metadados = _linhas(conn, "metadados")

    print(f"Encontradas: {len(vagas)} vaga(s) e {len(metadados)} metadado(s).")
    if args.dry_run:
        return

    # O histórico SQLite não tem timezone; tratamos os valores gravados pelo
    # robô como UTC para preservar a ordenação e torná-los timestamptz válidos.
    for vaga in vagas:
        if vaga.get("encontrada_em") and "+" not in vaga["encontrada_em"]:
            vaga["encontrada_em"] = f"{vaga['encontrada_em'].replace(' ', 'T')}+00:00"
        vaga["digest_pendente"] = bool(vaga.get("digest_pendente"))
        vaga["exploratoria"] = bool(vaga.get("exploratoria"))
        vaga["situacao"] = vaga.get("situacao") or "nova"

    for lote in _em_lotes(vagas):
        supabase._requisicao(
            "POST", "job_radar_vagas", json=lote,
            headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
        )
    for lote in _em_lotes(metadados):
        supabase._requisicao(
            "POST", "job_radar_metadados", json=lote,
            headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
        )
    print("Migração concluída.")


if __name__ == "__main__":
    main()
