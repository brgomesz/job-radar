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

## Perfis de busca

O motor (`main.py`) roda perfis selecionáveis por `--perfil`; cada perfil é
só DADO (`core/config*.py` + `core/perfis.py`), não lógica duplicada.

Dois perfis rodam em produção (cron), os dois notificando no MESMO chat do
Telegram, distinguidos pela linha `Perfil:` da notificação:

- `dev` — full-stack com foco back-end Node/TypeScript, remoto ou
  presencial/híbrido em Joinville/SC, nível pleno apenas.
  Config em `core/config_dev.py`.
- `admin` — administrativo, financeiro, contábil e RH/DP, remoto ou
  Joinville/SC, pleno e sênior. Fiscal e tributário foram excluídos a
  pedido da usuária. Config em `core/config_adm.py`.

- `brasil` / `internacional` — perfis de Dados/BI da autora original do
  projeto. Continuam no código e rodáveis à mão, mas FORA do cron: não
  devem voltar pro workflow sem pedido explícito.

Ao mexer em regra de filtro, rodar `pytest tests/ -v` antes de commitar.
