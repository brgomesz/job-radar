create table if not exists public.vagas_vistas (
    id text primary key,
    titulo text,
    empresa text,
    local text,
    link text,
    site text,
    encontrada_em timestamptz not null default now(),
    chave_secundaria text,
    publicado_em text,
    modalidade text,
    relevancia integer,
    perfil text,
    digest_pendente boolean not null default false,
    exploratoria boolean not null default false,
    situacao text not null default 'nova',
    feedback text
);

create index if not exists idx_vagas_digest_pendente on public.vagas_vistas (perfil, digest_pendente);
create index if not exists idx_vagas_chave_secundaria on public.vagas_vistas (chave_secundaria);
create index if not exists idx_vagas_painel on public.vagas_vistas (perfil, situacao, encontrada_em desc);

create table if not exists public.metadados (
    chave text primary key,
    valor text
);

-- A Data API não é pública: robô e painel usam a service-role key apenas no servidor.
alter table public.vagas_vistas enable row level security;
alter table public.metadados enable row level security;

create or replace view public.dashboard_resumo with (security_invoker = true) as
select
    count(*) as total,
    count(*) filter (where situacao = 'nova') as novas,
    count(*) filter (where situacao in ('candidatei', 'entrevista', 'proposta')) as candidaturas,
    max(encontrada_em) as ultima
from public.vagas_vistas;

create or replace view public.dashboard_perfis with (security_invoker = true) as
select distinct perfil as valor from public.vagas_vistas
where perfil is not null and perfil <> '';

create or replace view public.dashboard_sites with (security_invoker = true) as
select distinct site as valor from public.vagas_vistas
where site is not null and site <> '';
