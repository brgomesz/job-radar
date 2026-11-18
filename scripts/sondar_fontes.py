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

from core.anuncio import motivo_reprovacao
from core.perfis import PERFIL_ANALISTA, PERFIL_DEV_INTL, PERFIL_DEV_JOINVILLE, PERFIL_DEV_REMOTO
from scrapers.nacionais import CANDIDATAS as CANDIDATAS_HTML
from scrapers.remotos import CANDIDATAS_REMOTAS

# HTML (portais e consultorias) e API/feed (vaga remota de fora). As de
# API não têm padrão de link: quando voltam zero, quem explica é o
# `diagnostico` do scraper (URL, status, início da resposta).
CANDIDATAS = CANDIDATAS_HTML + CANDIDATAS_REMOTAS

# Um termo por perfil: o objetivo é saber se a fonte RESPONDE e se o
# extrator ACERTA, não medir volume. Termo de área diferente também expõe
# fonte especializada (portal de TI não devolve nada pra "analista
# financeiro", e isso é informação útil).
TERMOS_PADRAO = [
    "desenvolvedor back-end",
    "coordenador financeiro",
]

# Os perfis do cron (ver jobradar.yml).
PERFIS = [PERFIL_DEV_JOINVILLE, PERFIL_DEV_REMOTO, PERFIL_DEV_INTL, PERFIL_ANALISTA]


def _amostra(vagas, n=3):
    for v in vagas[:n]:
        print(f"      · {v.titulo[:62]}")
        print(f"        {v.empresa[:30]} | {v.local[:28]} | {v.modalidade or '—'} | {v.publicado_em or 'sem data'}")


def _hrefs_encontrados(scraper, n=14):
    """Amostra dos links que a página realmente tem.

    É o que transforma "0 vagas" em conserto: com os hrefs na mão dá pra
    escrever o padrao_link certo. Sem isso, zero é indistinguível de site
    bloqueado.
    """
    vistos, amostra = set(), []
    for a in getattr(scraper, "ultimas_ancoras", []):
        href = (a.get("href") or "").split("?")[0]
        # Âncora sem texto é menu/ícone; a de vaga sempre tem título.
        if not href or href in vistos or len(a.get("texto", "")) < 5:
            continue
        vistos.add(href)
        amostra.append(href)
        if len(amostra) >= n:
            break
    return amostra


def _termos_da_fonte(classe, termos, termos_explicitos: bool) -> list[str]:
    """Fonte de API com termos próprios de sonda usa esses quando ninguém
    passou --termos (os padrões são em português); fonte que lê a
    categoria inteira recebe um termo só, que ela ignora."""
    fonte = classe.fonte
    if getattr(fonte, "usa_termos", True) is False:
        return termos[:1]
    if not termos_explicitos and getattr(fonte, "termos_sonda", ()):
        return list(fonte.termos_sonda)
    return termos


def sondar(classe, termos, dump=False, termos_explicitos=False) -> dict:
    nome = classe.fonte.nome
    print(f"\n{'=' * 62}\n{nome}\n{'=' * 62}")
    print(f"  URL: {classe.fonte.url_busca}")
    termos = _termos_da_fonte(classe, termos, termos_explicitos)
    if getattr(classe.fonte, "usa_termos", True) is False:
        print("  (lê a categoria inteira numa chamada — termos não se aplicam)")
    else:
        print(f"  Termos: {', '.join(termos)}")

    inicio = time.time()
    try:
        scraper = classe(termos_busca=termos)
        vagas = scraper.buscar_vagas()
    except Exception:
        print(f"  ❌ EXCEÇÃO — a fonte nem chegou a devolver lista:")
        print("     " + traceback.format_exc().strip().replace("\n", "\n     "))
        return {"nome": nome, "brutas": 0, "erro": True}

    duracao = time.time() - inicio
    print(f"  ⏱  {duracao:.0f}s | {len(vagas)} vaga(s) bruta(s)")
    diagnostico = getattr(scraper, "diagnostico", [])

    if not vagas and not hasattr(classe.fonte, "padrao_link"):
        print("  ❌ ZERO vagas. O que a fonte respondeu:")
        for linha in diagnostico or ["(nenhuma chamada registrada)"]:
            print(f"     {linha}")
        return {"nome": nome, "brutas": 0, "erro": False}

    if not vagas:
        # Zero é o resultado que mais engana: pode ser bloqueio, seletor
        # errado ou padrão de link errado. Sem dizer qual, o relatório não
        # serve pra nada.
        print(f"  ❌ ZERO vagas com o padrão {classe.fonte.padrao_link!r}.")
        hrefs = _hrefs_encontrados(scraper)
        if hrefs:
            print(f"     A página TEM links ({len(scraper.ultimas_ancoras)} âncoras). Amostra:")
            for h in hrefs:
                print(f"       {h}")
            print("     -> corrigir padrao_link em scrapers/nacionais.py")
        else:
            print("     A página não trouxe link nenhum: bloqueio de bot ou")
            print("     conteúdo que só carrega depois de interação.")
        return {"nome": nome, "brutas": 0, "erro": False}

    com_local = sum(1 for v in vagas if v.local and v.local != "Não informado")
    com_empresa = sum(1 for v in vagas if v.empresa and v.empresa != "Não informado")
    print(f"  📍 local extraído: {com_local}/{len(vagas)} ({com_local / len(vagas) * 100:.0f}%)")
    print(f"  🏢 empresa extraída: {com_empresa}/{len(vagas)} ({com_empresa / len(vagas) * 100:.0f}%)")
    _amostra(vagas)

    descricoes = getattr(scraper, "descricoes", {})
    print("  Depois do filtro de cada perfil:")
    aprovadas_total = 0
    for perfil in PERFIS:
        aprovadas = [v for v in vagas if v.combina_com(perfil.regras)]
        aprovadas_total += len(aprovadas)
        extra = ""
        # A API já entrega o anúncio: dá pra medir aqui quantas passariam
        # também na regra de anúncio (a que barra Java/.NET com título
        # genérico), sem abrir página nenhuma.
        if perfil.regras_anuncio and descricoes and aprovadas:
            com_texto = [v for v in aprovadas if descricoes.get(v.link)]
            passam = [v for v in com_texto
                      if not motivo_reprovacao(v.titulo, descricoes[v.link], perfil.regras_anuncio)]
            extra = f"   (anúncio: {len(passam)} de {len(com_texto)} com texto passam)"
        print(f"      {perfil.nome:<36} {len(aprovadas):>3}{extra}")
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
    parser.add_argument("--termos", nargs="+", default=None)
    parser.add_argument("--dump", action="store_true", help="Salvar o HTML de cada busca")
    args = parser.parse_args()

    candidatas = CANDIDATAS
    if args.fonte:
        candidatas = [c for c in CANDIDATAS if args.fonte.lower() in c.fonte.nome.lower()]
        if not candidatas:
            print(f"Nenhuma fonte com '{args.fonte}'. Disponíveis: "
                  + ", ".join(c.fonte.nome for c in CANDIDATAS))
            return 1

    termos_explicitos = args.termos is not None
    termos = args.termos or TERMOS_PADRAO
    print(f"Sondando {len(candidatas)} fonte(s).")
    print("Nada é gravado no banco e nada é notificado.")

    resultados = [sondar(c, termos, args.dump, termos_explicitos) for c in candidatas]

    print(f"\n{'=' * 62}\nRESUMO\n{'=' * 62}")
    print(f"  {'fonte':<22}{'brutas':>8}{'aprovadas':>11}{'local %':>9}{'seg':>6}")
    for r in resultados:
        if r.get("erro"):
            print(f"  {r['nome']:<22}{'ERRO':>8}")
        elif not r["brutas"]:
            print(f"  {r['nome']:<22}{0:>8}")
        else:
            print(f"  {r['nome']:<22}{r['brutas']:>8}{r['aprovadas']:>11}"
                  f"{r['local_pct']:>8.0f}%{r['segundos']:>6.0f}")

    boas = [r for r in resultados if r.get("brutas")]
    print(f"\n  {len(boas)} de {len(resultados)} fonte(s) responderam com vaga.")
    print("  Promover só as que trouxeram vaga APROVADA — bruta sem aprovada")
    print("  significa que a fonte funciona mas não serve a estes perfis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
