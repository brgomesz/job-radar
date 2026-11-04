# Instruções do projeto JobRadar

Contexto específico deste repositório. As regras de Git que valem para
qualquer projeto (entre elas: não criar branch nova) ficam nas diretrizes
globais da conta, em ~/.claude/CLAUDE.md — não são repetidas aqui.

## Contexto operacional

- O workflow `.github/workflows/jobradar.yml` roda de 3 em 3h a partir da
  `main` — trabalho que não está na `main` não roda em produção.
- O robô commita `data/jobs.db` na `main` a cada ciclo. Antes de commitar,
  sincronizar (`git pull --rebase origin main`) para não disputar push com
  a execução em andamento.
- `.env` (token e chat_id do Telegram) é ignorado pelo Git e nunca deve ser
  commitado. As credenciais de produção vivem em Secrets do repositório.
- Divisão de entrega: o Telegram manda só o que é urgente (nota >=
  `LIMIAR_DIGEST_IMEDIATO`); a página pública tem TODAS as vagas. O digest
  diário está desligado (`DIGEST_DIARIO_ATIVO`) — chegou a mandar 115 vagas
  num dia só, e a página faz esse papel melhor.
- `docs/index.html` é GERADO (`python -m web.gerar`), nunca editado à mão:
  o workflow o regenera a partir do `jobs.db` a cada ciclo e o GitHub
  Pages o serve. Pra mudar o visual da página, mexer em
  `web/template.html`.
- Abas "Conteúdo Dev" e "Conteúdo Analista" da página: o passo "Capturar
  conteúdo dos anúncios" do workflow (`scripts/capturar_conteudo.py`) abre
  o anúncio de cada vaga `dev` e `analista` salva (até 80 por perfil por
  ciclo, mais recentes primeiro) e guarda o texto na tabela
  `conteudo_vagas`; `web.gerar` junta tudo em `docs/conteudo-<perfil>.txt`
  (lista em `PERFIS_CONTEUDO`), que é o que cada aba carrega. Também GERADO.

## Perfis de busca

O motor (`main.py`) roda perfis selecionáveis por `--perfil`; cada perfil é
só DADO (`core/config*.py` + `core/perfis.py`), não lógica duplicada.

Dois perfis rodam em produção (cron), notificando no MESMO chat do
Telegram, distinguidos pela linha `Perfil:` da notificação:

- `dev` — full-stack com foco back-end Node/TypeScript, remoto ou
  presencial/híbrido em Joinville/SC, nível pleno apenas.
  Config em `core/config_dev.py`.
- `analista` — Ana Julia (Gerente Financeira e Operacional Sênior,
  mercado imobiliário; filtro revisado contra o currículo dela em
  nov/2026). Coordenação/gerência/supervisão adm-financeira, operações,
  contratos, sales ops, imobiliário/locação, RH, FP&A, contas a pagar/
  receber, backoffice e office manager; analista só com nível (pleno, II,
  sênior, III, especialista) ou setor no título. Pleno a sênior: exclui
  júnior, "Nível I", estágio, assistente, auxiliar, contábil, fiscal,
  tributário, controladoria, tesouraria e DP/folha. Local: presencial/
  híbrido SÓ em Joinville; remoto SÓ quando o TÍTULO diz (remoto, home
  office...) — a marcação "Remoto" do LinkedIn não basta
  (`remoto_exige_titulo`). Com `refiltrar_historico`, a página e a captura
  de anúncios reaplicam o filtro atual às vagas já salvas.
  Config em `core/config_analista.py`.

- `admin` (administrativo/financeiro/RH) e `agro` (agronomia) foram
  REMOVIDOS em nov/2026, a pedido — código, config e testes apagados. As
  vagas deles continuam no `jobs.db`, só fora da página.

- `brasil` / `internacional` — perfis de Dados/BI da autora original do
  projeto. Continuam no código e rodáveis à mão, mas FORA do cron: não
  devem voltar pro workflow sem pedido explícito.

Ao mexer em regra de filtro, rodar `pytest tests/ -v` antes de commitar.

## Fontes de vaga

- Fonte NOVA nunca entra direto num perfil. O caminho é: configurar em
  `scrapers/nacionais.py` (sobre o `ScraperGenerico`), rodar a bancada
  (workflow "Sondar fontes", ou `python -m scripts.sondar_fontes`) e
  promover só a que trouxer vaga APROVADA. Fonte que traz vaga bruta mas
  nenhuma aprovada funciona, só não serve a estes perfis.
  `tests/test_scraper_generico.py` avisa se alguma candidata for ligada a
  um perfil sem passar por isso.
- Motivo: fonte ruim falha em SILÊNCIO (devolve zero e o ciclo segue
  verde). Já aconteceu duas vezes — Trampos rendeu zero por 6 dias, e a
  GeekHunter foi promovida por palpite e entregou 151 brutas / 0 aprovadas.
- A sessão de desenvolvimento do Claude não alcança portal de vaga nenhum
  (bloqueio de rede: 403 no CONNECT). Quem tem rede é o runner do GitHub —
  por isso a bancada é um workflow, e não um script para rodar por aqui.
