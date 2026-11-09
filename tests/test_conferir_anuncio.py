"""main.py: nos perfis com regras_anuncio (os dev), a vaga que iria pro
Telegram tem o anúncio aberto ANTES de notificar (ver
_notificar_conferindo_anuncio).

MEDIDO (nov/2026): o usuário relatou que só recebia vaga de Java, Kotlin e
stack que nem conhecia. O que estes testes travam:
  - anúncio de outra stack: vaga salva (não volta no próximo ciclo), sem
    mensagem;
  - anúncio que não abriu: notifica do mesmo jeito — falha de leitura não
    pode custar vaga boa;
  - a mesma vaga achada por duas fontes no mesmo ciclo notifica uma vez só
    (ela ainda não está no banco quando a segunda aparece).
"""

import pytest

import main
import scrapers.conteudo as conteudo
from core.job import Job
from core.perfis import PERFIL_DEV_REMOTO

JAVA = "Back-end em Java 17 com Spring Boot. Front em React."
NODE = "Node.js, NestJS e Prisma; React no front."


def _vaga(titulo, slug):
    return Job(titulo=titulo, empresa="Empresa", local="São Paulo, São Paulo, Brazil",
               link=f"https://x.invalido/{slug}", site="LinkedIn", modalidade="Remoto")


@pytest.fixture
def ciclo(monkeypatch):
    estado = {"notificadas": [], "salvas": [], "conteudo": {}, "abertas": []}

    def rodar(vagas, lidos):
        class _Fonte:
            def buscar_vagas(self):
                return list(vagas)

        monkeypatch.setattr(main, "_proximo_bloco_termos", lambda p: ["termo"])
        monkeypatch.setattr(main, "_construir_scrapers", lambda p, t: [_Fonte(), _Fonte()])
        monkeypatch.setattr(main, "ja_vista", lambda v: v.id in {s.id for s in estado["salvas"]})
        monkeypatch.setattr(main, "salvar_vaga", lambda v, **kw: estado["salvas"].append(v))
        monkeypatch.setattr(main, "salvar_conteudo",
                            lambda id_, status, texto="", origem="": estado["conteudo"].__setitem__(id_, status))
        monkeypatch.setattr(main, "notificar_vaga",
                            lambda v, nome: estado["notificadas"].append(v.titulo) or True)
        monkeypatch.setattr(main, "enviar_mensagem", lambda *a, **k: True)
        monkeypatch.setattr(main, "_enviar_heartbeat_diario", lambda *a: None)
        monkeypatch.setattr(main, "_enviar_digest_diario", lambda p: None)

        def ler(itens):
            estado["abertas"].extend(titulo for _, _, _, titulo in itens)
            return {id_: lidos[link.rsplit("/", 1)[1]] for id_, link, _, _ in itens}

        monkeypatch.setattr(conteudo, "ler_anuncios", ler)
        main.ciclo_de_busca(PERFIL_DEV_REMOTO)
        return estado

    return rodar


def test_anuncio_de_outra_stack_nao_notifica(ciclo):
    java = _vaga("Desenvolvedor Full Stack React Pleno", "java")
    node = _vaga("Desenvolvedor Back-end Node.js Pleno", "node")
    falhou = _vaga("Desenvolvedor React Pleno", "falhou")
    for v in (java, node, falhou):
        assert main._vai_pro_telegram(_pontuada(v)), v.titulo

    estado = ciclo([java, node, falhou], {
        "java": ("ok", JAVA, "seletor"),
        "node": ("ok", NODE, "seletor"),
        "falhou": ("falhou", "", ""),
    })

    assert sorted(estado["notificadas"]) == sorted([node.titulo, falhou.titulo])
    # Reprovada também é salva: não pode voltar como "nova" no próximo ciclo.
    assert {v.titulo for v in estado["salvas"]} == {java.titulo, node.titulo, falhou.titulo}
    assert estado["conteudo"] == {java.id: "ok", node.id: "ok", falhou.id: "falhou"}


def test_mesma_vaga_em_duas_fontes_abre_e_notifica_uma_vez(ciclo):
    """_construir_scrapers devolve duas fontes com a mesma lista."""
    node = _vaga("Desenvolvedor Back-end Node.js Pleno", "node")
    estado = ciclo([node], {"node": ("ok", NODE, "seletor")})
    assert estado["abertas"] == [node.titulo]
    assert estado["notificadas"] == [node.titulo]


def test_anuncio_removido_na_fonte_nao_notifica(ciclo):
    node = _vaga("Desenvolvedor Back-end Node.js Pleno", "node")
    estado = ciclo([node], {"node": ("indisponivel", "", "")})
    assert estado["notificadas"] == []
    assert [v.titulo for v in estado["salvas"]] == [node.titulo]


def _pontuada(vaga):
    vaga.relevancia = vaga.pontuar_relevancia(PERFIL_DEV_REMOTO.regras)
    return vaga
