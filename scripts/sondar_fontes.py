"""Bancada de fontes: roda as candidatas contra o site de verdade e mostra
o que elas trazem. NÃO grava no banco e NÃO notifica ninguém.

Existe porque fonte nova é a mudança que mais falha em silêncio neste
projeto: um seletor errado devolve zero e o ciclo segue verde, como
aconteceu com o Trampos (6 dias rendendo nada) e com a GeekHunter (151
vagas brutas, 0 aprovadas). Ligar fonte direto no perfil é apostar; rodar
isto antes é medir.

O que o relatório responde, por fonte:
  - o site respondeu? (rede, bloqueio de bot, timeout)
  - o padrão de link acertou? (quantas vagas brutas saíram)
  - os campos vieram? (% com local e com empresa de verdade)
  - sobra alguma coisa depois do filtro de cada perfil?

Uso:
    python -m scripts.sondar_fontes                  # todas, termos padrão
    python -m scripts.sondar_fontes --fonte InfoJobs
    python -m scripts.sondar_fontes --termos "analista financeiro"
    python -m scripts.sondar_fontes --dump           # salva o HTML pra depurar
"""

import argparse
import sys
import time
import traceback

from core.perfis import PERFIL_ADM, PERFIL_AGRO, PERFIL_DEV
from scrapers.nacionais import CANDIDATAS

# Um termo por perfil: o objetivo é saber se a fonte RESPONDE e se o
# extrator ACERTA, não medir volume. Termo de área diferente também expõe
# fonte especializada (portal de TI não devolve nada pra "analista
# financeiro", e isso é informação útil).
TERMOS_PADRAO = [
    "desenvolvedor back-end",
    "analista financeiro",
    "engenheiro agrônomo",
]

PERFIS = [PERFIL_DEV, PERFIL_ADM, PERFIL_AGRO]


def _amostra(vagas, n=3):
    for v in vagas[:n]:
        print(f"      · {v.titulo[:62]}")
        print(f"        {v.empresa[:30]} | {v.local[:28]} | {v.modalidade or '—'} | {v.publicado_em or 'sem data'}")


def sondar(classe, termos, dump=False) -> dict:
    nome = classe.fonte.nome
    print(f"\n{'=' * 62}\n{nome}\n{'=' * 62}")
    print(f"  URL: {classe.fonte.url_busca}")

    inicio = time.time()
    try:
        vagas = classe(termos_busca=termos).buscar_vagas()
    except Exception:
        print(f"  ❌ EXCEÇÃO — a fonte nem chegou a devolver lista:")
        print("     " + traceback.format_exc().strip().replace("\n", "\n     "))
        return {"nome": nome, "brutas": 0, "erro": True}

    duracao = time.time() - inicio
    print(f"  ⏱  {duracao:.0f}s | {len(vagas)} vaga(s) bruta(s)")

    if not vagas:
        # Zero é o resultado que mais engana: pode ser bloqueio, seletor
        # errado ou padrão de link errado. Sem dizer qual, o relatório não
        # serve pra nada.
        print("  ❌ ZERO vagas. Causas prováveis, na ordem:")
        print("     1. padrao_link não bate com o href real do site")
        print("     2. o site bloqueou o acesso automatizado")
        print("     3. a busca não tem resultado pros termos usados")
        print("     Rodar com --dump pra salvar o HTML e conferir.")
        return {"nome": nome, "brutas": 0, "erro": False}

    com_local = sum(1 for v in vagas if v.local and v.local != "Não informado")
    com_empresa = sum(1 for v in vagas if v.empresa and v.empresa != "Não informado")
    print(f"  📍 local extraído: {com_local}/{len(vagas)} ({com_local / len(vagas) * 100:.0f}%)")
    print(f"  🏢 empresa extraída: {com_empresa}/{len(vagas)} ({com_empresa / len(vagas) * 100:.0f}%)")
    _amostra(vagas)

    print("  Depois do filtro de cada perfil:")
    aprovadas_total = 0
    for perfil in PERFIS:
        aprovadas = [v for v in vagas if v.combina_com(perfil.regras)]
        aprovadas_total += len(aprovadas)
        print(f"      {perfil.nome:<26} {len(aprovadas):>3}")
        _amostra(aprovadas, 2)

    return {
        "nome": nome,
        "brutas": len(vagas),
        "aprovadas": aprovadas_total,
        "local_pct": com_local / len(vagas) * 100,
        "segundos": duracao,
        "erro": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sonda fontes candidatas sem tocar em produção")
    parser.add_argument("--fonte", help="Sondar só esta (nome como aparece no relatório)")
    parser.add_argument("--termos", nargs="+", default=TERMOS_PADRAO)
    parser.add_argument("--dump", action="store_true", help="Salvar o HTML de cada busca")
    args = parser.parse_args()

    candidatas = CANDIDATAS
    if args.fonte:
        candidatas = [c for c in CANDIDATAS if args.fonte.lower() in c.fonte.nome.lower()]
        if not candidatas:
            print(f"Nenhuma fonte com '{args.fonte}'. Disponíveis: "
                  + ", ".join(c.fonte.nome for c in CANDIDATAS))
            return 1

    print(f"Sondando {len(candidatas)} fonte(s) com {len(args.termos)} termo(s).")
    print("Nada é gravado no banco e nada é notificado.")

    resultados = [sondar(c, args.termos, args.dump) for c in candidatas]

    print(f"\n{'=' * 62}\nRESUMO\n{'=' * 62}")
    print(f"  {'fonte':<18}{'brutas':>8}{'aprovadas':>11}{'local %':>9}{'seg':>6}")
    for r in resultados:
        if r.get("erro"):
            print(f"  {r['nome']:<18}{'ERRO':>8}")
        elif not r["brutas"]:
            print(f"  {r['nome']:<18}{0:>8}")
        else:
            print(f"  {r['nome']:<18}{r['brutas']:>8}{r['aprovadas']:>11}"
                  f"{r['local_pct']:>8.0f}%{r['segundos']:>6.0f}")

    boas = [r for r in resultados if r.get("brutas")]
    print(f"\n  {len(boas)} de {len(resultados)} fonte(s) responderam com vaga.")
    print("  Promover só as que trouxeram vaga APROVADA — bruta sem aprovada")
    print("  significa que a fonte funciona mas não serve a estes perfis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
