"""UF ambígua (AL/MA/MT/MS/PA/SC) em cidade do INTERIOR, formato "Cidade - UF".

MEDIDO (2026-11-10): a desambiguação Brasil x EUA das 6 siglas que colidem
com estado americano só confirmava Brasil pela CAPITAL. Cidade do interior
no formato das fontes nacionais caía direto em "Estados Unidos":

    "Nova Mutum - MT"  (Sólides, remoto)  -> {"Estados Unidos"}  (Montana)
    "Joinville - SC"   (Sólides, remoto)  -> {"Estados Unidos"}  (South Carolina)
    "Chapecó - SC"     (Sólides)          -> {"Estados Unidos"}

e todo perfil sem "Estados Unidos" em mercados_remoto_aceitos (o de dados
Brasil, o analista) barrava a vaga brasileira remota.

O separador resolve sem base de cidade: no jobs.db, TODO local americano com
sigla ambígua vem com vírgula ("Pittsburgh, PA", "Remoto (Charleston, SC)"),
e TODO local brasileiro das fontes nacionais (Gupy, Sólides, Senior) vem com
hífen. A metade de baixo do arquivo garante que o lado americano não mudou.
"""

import pytest

from core.job import Job, extrair_escopo_remoto
from core.perfis import PERFIL_BR


def _vaga(local: str, modalidade: str = "Remoto", titulo: str = "Analista de Dados") -> Job:
    return Job(
        titulo=titulo,
        empresa="Empresa",
        local=local,
        link="https://exemplo.com/" + local,
        site="Solides",
        modalidade=modalidade,
    )


def test_caso_reportado_nova_mutum_mt():
    """Reprodução exata do bug: Montana no lugar de Mato Grosso."""
    vaga = _vaga("Nova Mutum - MT", titulo="Desenvolvedor Web")
    assert vaga.escopo_remoto == {"Brasil"}


@pytest.mark.parametrize("local", [
    # Formatos REAIS do jobs.db (Sólides/Gupy/Senior).
    "Nova Mutum - MT",
    "Joinville - SC",
    "JOINVILLE - SC",
    "Chapecó - SC",
    # As outras 4 siglas ambíguas, mesmo formato, cidade do interior.
    "Arapiraca - AL",
    "Imperatriz - MA",
    "Dourados - MS",
    "Santarém - PA",
    # Travessão no lugar do hífen e o formato "Remoto (...)".
    "Nova Mutum – MT",
    "Nova Mutum — MT",
    "Remoto (Nova Mutum - MT)",
])
def test_cidade_do_interior_com_hifen_e_brasil(local):
    assert extrair_escopo_remoto(local, "Remoto") == {"Brasil"}


def test_perfil_brasil_aceita_a_vaga_do_interior():
    """O efeito que importa: o perfil que só aceita mercado latino (sem
    "Estados Unidos") deixa de barrar a vaga remota brasileira."""
    assert "Estados Unidos" not in PERFIL_BR.regras.mercados_remoto_aceitos
    assert _vaga("Nova Mutum - MT").combina_com(PERFIL_BR.regras)


# ------------------------------------------- O LADO AMERICANO NÃO MUDA

@pytest.mark.parametrize("local, modalidade", [
    # Formatos REAIS do jobs.db (LinkedIn) — sempre com vírgula.
    ("Pittsburgh, PA", "Remoto"),
    ("Olive Branch, MS", "Remoto"),
    ("Birmingham, AL", "Remoto"),
    ("Greenville, SC", "Remoto"),
    ("Remoto (Boston, MA)", ""),
    ("Remoto (Duncan, SC)", ""),
    # Vale o separador logo ANTES da sigla, não qualquer hífen do texto:
    # aqui o hífen é do nome da cidade e a sigla vem depois de vírgula.
    ("Wilkes-Barre, PA", "Remoto"),
    ("Remoto (Wilkes-Barre, PA)", ""),
    ("Charleston, SC - Remote", "Remoto"),
])
def test_cidade_americana_com_virgula_continua_eua(local, modalidade):
    assert extrair_escopo_remoto(local, modalidade) == {"Estados Unidos"}


def test_vaga_americana_continua_barrada_no_perfil_brasil():
    assert not _vaga("Olive Branch, MS").combina_com(PERFIL_BR.regras)
