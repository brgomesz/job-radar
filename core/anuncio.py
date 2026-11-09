"""Filtro pelo TEXTO do anúncio (descrição, requisitos), não só pelo título.

Por que existe: o filtro de vaga (Job.combina_com) lê só o título, e o
cargo forte do perfil dev é genérico de propósito ("Desenvolvedor Back-end
Pleno"). MEDIDO (nov/2026), nas 537 vagas dev com anúncio capturado: 119
eram de outra stack — "Desenvolvedor Backend Pleno" que é .NET/C#,
"Desenvolvedor(a) Full Stack" que é Java + React, "Back-end PL" que é Java/
Spring, "Full Stack Developer" que é Python/FastAPI + React. O usuário
relatou "só recebo vaga de Java, Kotlin e coisas que nem sei o que são" —
nenhuma delas dizia isso no título.

Onde entra:
  - main.py: antes de mandar uma vaga pro Telegram, abre o anúncio e passa
    por aqui (ver _conferir_anuncios). Reprovada é salva sem notificar.
  - web/gerar.py: a página e as abas de conteúdo escondem a vaga cujo
    anúncio reprova (o texto é capturado depois, pelo workflow).

Regra (ver motivo_reprovacao):
  1. Anúncio que não cita NADA da stack do usuário, mas cita outra → fora.
  2. Vaga de back-end ou full-stack cujo back-end é de outra linguagem →
     fora. "Outra linguagem" = cita Java/.NET/PHP/Python... e não cita Node
     (ou cita Node uma vez só, contra 3+ menções de UMA outra linguagem:
     "Java, Spring Boot, microsserviços (Spring, Node)").
  3. Vaga de front-end em Angular/Vue/mobile sem React/Next → fora.
  Título que já confirma a stack ("Desenvolvedor Back-end Node.js",
  "Full Stack TypeScript") pula a regra do lado que ele confirma: o
  anúncio pode citar Python como diferencial sem a vaga deixar de ser Node.
  Anúncio que não cita stack nenhuma passa — não há base pra recusar.
"""

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

from core.job import _contem_termo, _normalizar, _padrao_stack, _sem_marcador_genero

# "Go" (a linguagem) só com G maiúsculo e sem hífen dos lados: em texto
# normalizado "go" vira verbo inglês ("go live") e "Go-to-market".
# MEDIDO nas vagas capturadas: as 35 ocorrências de "Go" com essa grafia
# eram todas a linguagem.
_GO_LINGUAGEM = re.compile(r"(?<![\w-])Go(?![\w-])")


@dataclass
class RegrasAnuncio:
    proprias_backend: list[str]
    proprias_front: list[str]
    proprias_linguagem: list[str]
    # {"Java/Kotlin": ["java", "spring boot", ...], ...} — o nome aparece no
    # motivo da reprovação (log e diagnóstico).
    familias_backend_alheias: dict[str, list[str]]
    alheias_front: list[str]
    alheias_mobile: list[str]
    # Título: que tipo de vaga é, e se ele já confirma a stack.
    marcas_full_titulo: list[str]
    marcas_backend_titulo: list[str]
    marcas_front_titulo: list[str]
    confirma_backend_titulo: list[str]
    confirma_front_titulo: list[str]
    # Menções de UMA linguagem de fora que vencem uma única menção ao Node.
    dominancia_minima: int = 3
    # Família onde entra o "Go" com G maiúsculo (ver _GO_LINGUAGEM).
    familia_go: str = "Go"
    _compilado: tuple | None = field(default=None, repr=False, compare=False)

    def classificador(self) -> tuple[re.Pattern, dict[str, str]]:
        """(regex, {termo normalizado: grupo}) — uma alternação com TODOS os
        termos, mais longo primeiro, compilada uma vez só.

        Uma passada pelo texto em vez de uma por lista: a página reavalia
        centenas de anúncios de até 20 mil caracteres a cada ciclo. E o
        "mais longo primeiro" resolve sozinho o caso "react native": na
        mesma posição, ele casa antes de "react", e o trecho conta como
        mobile, não como React (mesmo cuidado que o título tem)."""
        if self._compilado is None:
            grupo_de: dict[str, str] = {}
            def marcar(termos, grupo):
                for t in termos:
                    grupo_de.setdefault(_normalizar(t), grupo)
            marcar(self.proprias_backend, "proprio_back")
            marcar(self.proprias_front, "proprio_front")
            marcar(self.proprias_linguagem, "proprio_lang")
            marcar(self.alheias_front, "alheio_front")
            marcar(self.alheias_mobile, "alheio_mobile")
            for nome, termos in self.familias_backend_alheias.items():
                marcar(termos, "familia:" + nome)
            termos = sorted(grupo_de, key=len, reverse=True)
            regex = re.compile("|".join(_padrao_stack(t) for t in termos))
            self._compilado = (regex, grupo_de)
        return self._compilado


_MARCAS_COMBINANTES = re.compile(r"[\u0300-\u036f]")


def _normalizar_texto(texto: str) -> str:
    """Mesmo resultado de core.job._normalizar pra texto latino, mas sem
    laço em Python caractere a caractere — anúncio tem até 20 mil."""
    return _MARCAS_COMBINANTES.sub("", unicodedata.normalize("NFKD", texto.lower()))


def _tipo_da_vaga(titulo_norm: str, regras: RegrasAnuncio) -> str:
    """"full", "back" ou "front" pelo título. Sem marca nenhuma
    ("Software Engineer", "Desenvolvedor Web") conta como full: o back-end
    é a parte que mais costuma decidir se a vaga serve."""
    tem = lambda termos: any(_contem_termo(_normalizar(t), titulo_norm) for t in termos)  # noqa: E731
    if tem(regras.marcas_full_titulo):
        return "full"
    back, front = tem(regras.marcas_backend_titulo), tem(regras.marcas_front_titulo)
    if back and not front:
        return "back"
    if front and not back:
        return "front"
    return "full"


def motivo_reprovacao(titulo: str, texto: str, regras: RegrasAnuncio) -> str | None:
    """Por que o anúncio não serve — ou None quando serve (ou quando não dá
    pra saber: texto vazio, anúncio sem stack nenhuma)."""
    if not texto or not texto.strip():
        return None

    titulo_norm = _sem_marcador_genero(_normalizar(titulo or ""))

    regex, grupo_de = regras.classificador()
    contagem = Counter(grupo_de[m.group(0)] for m in regex.finditer(_normalizar_texto(texto)))
    go = len(_GO_LINGUAGEM.findall(texto))
    if go:
        contagem["familia:" + regras.familia_go] += go

    proprias_backend = contagem["proprio_back"]
    proprias_front = contagem["proprio_front"]
    proprias_linguagem = contagem["proprio_lang"]
    alheias_front = contagem["alheio_front"]
    alheias_mobile = contagem["alheio_mobile"]
    familias = {
        grupo.split(":", 1)[1]: n for grupo, n in contagem.items()
        if grupo.startswith("familia:") and n
    }

    principal = max(familias, key=familias.get) if familias else ""

    if not (proprias_backend or proprias_front or proprias_linguagem):
        if familias or alheias_front or alheias_mobile:
            citadas = ", ".join(sorted(familias, key=familias.get, reverse=True)) or (
                "Angular/Vue" if alheias_front else "mobile"
            )
            return f"anúncio sem a sua stack (cita {citadas})"
        return None

    tipo = _tipo_da_vaga(titulo_norm, regras)
    confirma = lambda termos: any(_contem_termo(_normalizar(t), titulo_norm) for t in termos)  # noqa: E731

    if tipo in ("back", "full") and familias and not confirma(regras.confirma_backend_titulo):
        if not proprias_backend:
            return f"back-end em {principal}, sem Node"
        if proprias_backend <= 1 and familias[principal] >= regras.dominancia_minima:
            return f"back-end principal em {principal} ({familias[principal]} menções contra 1 de Node)"

    if (
        tipo == "front" and (alheias_front or alheias_mobile)
        and not proprias_front and not confirma(regras.confirma_front_titulo)
    ):
        return "front-end em Angular/Vue/mobile, sem React"

    return None
