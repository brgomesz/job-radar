"""Especificação executável do perfil iOS."""

import pytest

from core.job import Job
from core.perfis import PERFIL_IOS


def vaga(titulo: str, local: str = "São Paulo, SP", modalidade: str = "Híbrido") -> Job:
    return Job(
        titulo=titulo,
        empresa="Empresa Teste",
        local=local,
        link=f"https://exemplo.com/{titulo.replace(' ', '-')}",
        site="Teste",
        modalidade=modalidade,
    )


@pytest.mark.parametrize("titulo", [
    "Senior iOS Developer",
    "iOS Engineer (SwiftUI)",
    "Desenvolvedora iOS Pleno",
    "Software Engineer - iOS",
    "Mobile Developer | Swift",
])
def test_titulos_ios_relevantes_passam(titulo):
    assert vaga(titulo).combina_com(PERFIL_IOS.regras)


@pytest.mark.parametrize("titulo", [
    "Android Developer",
    "Backend Software Engineer",
    "Mobile Developer - Android",
    "Swift Operations Analyst",
    "Product Manager",
])
def test_titulos_sem_sinal_ios_sao_rejeitados(titulo):
    assert not vaga(titulo).combina_com(PERFIL_IOS.regras)


def test_vaga_remota_no_brasil_passa_mesmo_fora_dos_polos():
    assert vaga("iOS Developer", "Remote - Brazil", "Remoto").combina_com(PERFIL_IOS.regras)


def test_vaga_remota_restrita_a_outro_mercado_e_rejeitada():
    assert not vaga("iOS Developer", "Remote - US only", "Remoto").combina_com(PERFIL_IOS.regras)


def test_vaga_presencial_fora_dos_polos_e_rejeitada():
    assert not vaga("iOS Developer", "Salvador, BA", "Presencial").combina_com(PERFIL_IOS.regras)
