create table if not exists public.job_radar_vagas (
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

create index if not exists idx_job_radar_vagas_digest_pendente on public.job_radar_vagas (perfil, digest_pendente);
create index if not exists idx_job_radar_vagas_chave_secundaria on public.job_radar_vagas (chave_secundaria);
create index if not exists idx_job_radar_vagas_painel on public.job_radar_vagas (perfil, situacao, encontrada_em desc);

create table if not exists public.job_radar_metadados (
    chave text primary key,
    valor text
);

-- A Data API não é pública: robô e painel usam a service-role key apenas no servidor.
alter table public.job_radar_vagas enable row level security;
alter table public.job_radar_metadados enable row level security;

create or replace view public.job_radar_dashboard_resumo with (security_invoker = true) as
select
    count(*) as total,
    count(*) filter (where situacao = 'nova') as novas,
    count(*) filter (where situacao in ('candidatei', 'entrevista', 'proposta')) as candidaturas,
    max(encontrada_em) as ultima
from public.job_radar_vagas;

create or replace view public.job_radar_dashboard_perfis with (security_invoker = true) as
select distinct perfil as valor from public.job_radar_vagas
where perfil is not null and perfil <> '';

create or replace view public.job_radar_dashboard_sites with (security_invoker = true) as
select distinct site as valor from public.job_radar_vagas
where site is not null and site <> '';
