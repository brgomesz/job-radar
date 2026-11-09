"""Filtro pelo texto do anúncio (core/anuncio.py) — perfis dev.

Cada caso é um padrão que apareceu nas vagas reais capturadas em nov/2026
(537 anúncios do perfil dev). Os que mais podem quebrar sem ninguém notar:

  - "react native" não pode contar como React;
  - "Node.js" mencionado UMA vez num anúncio inteiro de Java não salva a
    vaga, mas Node como foco principal com Java "complementar" salva;
  - título que já confirma a stack (Node/TypeScript) não é derrubado por
    Python citado como diferencial;
  - anúncio que não cita stack nenhuma passa (não há base pra recusar).
"""

import pytest

from core.anuncio import motivo_reprovacao
from core.perfis import PERFIL_DEV, REGRAS_ANUNCIO_DEV, anuncio_reprovado


def _motivo(titulo, texto):
    return motivo_reprovacao(titulo, texto, REGRAS_ANUNCIO_DEV)


REPROVA = [
    ("backend-dotnet-sem-node", "Desenvolvedor Backend Pleno",
     "Desenvolver e manter APIs em C# e .NET Core. Experiência com Entity Framework e SQL Server."),
    ("fullstack-java-react", "Desenvolvedor(a) Full Stack",
     "Front-end em React e TypeScript. Back-end em Java 17 com Spring Boot e microsserviços."),
    ("backend-java-com-uma-mencao-a-node", "DESENVOLVEDOR BACK END PL",
     "Desenvolver aplicações Backend utilizando Java e Spring Boot. Experiência com Java, "
     "microserviço, APIs (Sprintboot, Node). Tecnologias: Java, Spring Boot, Kafka."),
    ("fullstack-python-fastapi", "Full Stack Developer",
     "We use React and TypeScript on the frontend and Python with FastAPI on the backend. "
     "Strong Python skills required."),
    ("kotlin-sem-stack-propria", "Software Engineer, Backend",
     "You will build services in Kotlin and Java running on the JVM."),
    ("go-maiusculo", "Backend Engineer",
     "Design microservices using Go. Proficiency in Go and PostgreSQL."),
    ("frontend-angular", "Pessoa Desenvolvedora Front-End",
     "Desenvolvimento com Angular 17, TypeScript e RxJS."),
    ("front-react-native-nao-e-react", "Desenvolvedor Front-end",
     "Desenvolvimento de apps com React Native e Flutter para Android e iOS."),
    ("php-laravel", "Desenvolvedor Web Fullstack",
     "Experiência com PHP 8, Laravel e JavaScript."),
]


@pytest.mark.parametrize("nome,titulo,texto", REPROVA, ids=[c[0] for c in REPROVA])
def test_anuncio_de_outra_stack_reprova(nome, titulo, texto):
    assert _motivo(titulo, texto)


APROVA = [
    ("node-react", "Desenvolvedor Full Stack Pleno",
     "Stack: Node.js, NestJS, Prisma, PostgreSQL, React e Next.js."),
    ("node-foco-java-complementar", "FullStack Developer",
     "El rol tendrá foco principal en Node.js, complementado con experiencia en Java/Spring. "
     "Desarrollar servicios backend principalmente con Node.js. Rotar entre Node.js, Java y Go."),
    ("node-com-python-diferencial", "Desenvolvedor Back-end",
     "Requisitos: Node.js e TypeScript. Diferenciais: Python, Go."),
    ("front-react-com-backend-java-da-empresa", "Desenvolvedor Front-end React",
     "Atuar no front em React e TypeScript. Nosso back-end é Java/Spring Boot."),
    ("titulo-confirma-typescript", "Desenvolvedor(a) Full Stack Typescript",
     "Experiência com React. Conhecimento em Python é desejável."),
    ("react-e-react-native", "Desenvolvedor(a) Frontend (React / React Native)",
     "Experiência sólida com React e TypeScript; React Native é um plus."),
    ("sem-stack-nenhuma", "Desenvolvedor Back-end",
     "Vaga para atuar em squad de produto, com metodologias ágeis."),
    ("javascript-nao-e-java", "Desenvolvedor Web",
     "Experiência com JavaScript, HTML e CSS."),
]


@pytest.mark.parametrize("nome,titulo,texto", APROVA, ids=[c[0] for c in APROVA])
def test_anuncio_da_stack_do_usuario_aprova(nome, titulo, texto):
    assert _motivo(titulo, texto) is None


def test_texto_vazio_nao_reprova():
    assert _motivo("Desenvolvedor Backend", "") is None
    assert _motivo("Desenvolvedor Backend", "   ") is None


def test_motivo_nomeia_a_stack():
    assert ".NET" in _motivo("Desenvolvedor Backend", "APIs em C# e .NET 8.")


def test_dev_original_usa_a_regra_e_perfil_sem_regra_nao():
    texto = "APIs em C# e .NET 8."
    assert anuncio_reprovado("dev", "Desenvolvedor Backend", texto)
    assert anuncio_reprovado("analista", "Coordenador Financeiro", texto) is None
    assert PERFIL_DEV.regras_anuncio is REGRAS_ANUNCIO_DEV
