# Instruções do projeto JobRadar

Memória de longo prazo para o Claude Code neste repositório. Vale para
qualquer sessão, inclusive as iniciadas pela web ou por Actions.

## Regras de Git (obrigatórias)

**PROIBIDO criar branches novas.** Todo trabalho é feito e commitado
direto na `main`, a menos que o usuário peça explicitamente uma branch
naquela conversa. Isso vale inclusive quando a configuração da sessão
sugerir uma branch de trabalho (`claude/...`): a instrução do usuário
prevalece.

- Não criar branch para "isolar" mudança, nem para abrir PR por hábito.
- Não abrir pull request sem pedido explícito.
- Commitar na `main` e dar push na `main`.

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

- `dev` — perfil do usuário (Bruno): full-stack com foco back-end
  Node/TypeScript, remoto ou presencial/híbrido em Joinville/SC, nível
  pleno apenas. Configuração em `core/config_dev.py`.
- `brasil` / `internacional` — perfis de Dados/BI da autora original do
  projeto.

Ao mexer em regra de filtro, rodar `pytest tests/ -v` antes de commitar.
