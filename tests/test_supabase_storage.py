import pytest

from core.job import Job
from database import supabase


class Resposta:
    content = b"[]"
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return []


def configurar(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://abc.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "segredo")


def test_configuracao_exige_credenciais(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    with pytest.raises(supabase.ConfiguracaoSupabaseInvalida):
        supabase.verificar_conexao()


def test_salvar_vaga_usa_upsert_que_ignora_duplicata(monkeypatch):
    configurar(monkeypatch)
    chamadas = []

    def requisicao(*args, **kwargs):
        chamadas.append((args, kwargs))
        return Resposta()

    monkeypatch.setattr(supabase.requests, "request", requisicao)
    vaga = Job("iOS Developer", "Acme", "Remote - Brazil", "https://example.com/1", "LinkedIn")
    supabase.salvar_vaga(vaga, "ios", digest_pendente=True)

    args, kwargs = chamadas[0]
    assert args[:2] == ("POST", "https://abc.supabase.co/rest/v1/vagas_vistas")
    assert kwargs["json"]["perfil"] == "ios"
    assert kwargs["json"]["digest_pendente"] is True
    assert kwargs["headers"]["Prefer"] == "resolution=ignore-duplicates,return=minimal"


def test_digest_pendente_respeita_perfil_e_ordem(monkeypatch):
    configurar(monkeypatch)
    capturada = {}

    def requisicao(*args, **kwargs):
        capturada.update(kwargs)
        return Resposta()

    monkeypatch.setattr(supabase.requests, "request", requisicao)
    assert supabase.obter_vagas_pendentes_digest("ios") == []
    assert capturada["params"]["perfil"] == "eq.ios"
    assert capturada["params"]["digest_pendente"] == "is.true"
    assert capturada["params"]["order"] == "relevancia.desc,encontrada_em.asc"


def test_busca_remove_operadores_do_postgrest(monkeypatch):
    configurar(monkeypatch)
    capturada = {}

    def requisicao(*args, **kwargs):
        capturada.update(kwargs)
        return Resposta()

    monkeypatch.setattr(supabase.requests, "request", requisicao)
    supabase.listar_vagas(busca="iOS),site.eq.segredo")
    assert capturada["params"]["or"] == "(titulo.ilike.*iOSsiteeqsegredo*,empresa.ilike.*iOSsiteeqsegredo*)"
