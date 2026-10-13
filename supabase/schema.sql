-- Sightra: profiles, sessions, and activity (run in Supabase SQL editor)
-- Service role (Django) bypasses RLS for server-side writes.

create extension if not exists "pgcrypto";

create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text,
  display_name text,
  theme_preference text not null default 'light' check (theme_preference in ('light', 'dark')),
  a11y_preferences jsonb not null default '{}'::jsonb,
  onboarding_completed boolean not null default false,
  last_seen_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.user_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  django_session_key text,
  ip_address text,
  user_agent text,
  device_class text,
  started_at timestamptz not null default now(),
  last_active_at timestamptz not null default now(),
  ended_at timestamptz
);

create index if not exists user_sessions_user_id_idx on public.user_sessions (user_id);
create index if not exists user_sessions_django_session_key_idx on public.user_sessions (django_session_key);

create table if not exists public.user_activity_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users (id) on delete set null,
  session_id uuid references public.user_sessions (id) on delete set null,
  event_type text not null,
  path text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists user_activity_events_user_id_idx on public.user_activity_events (user_id);
create index if not exists user_activity_events_created_at_idx on public.user_activity_events (created_at desc);

alter table public.profiles enable row level security;
alter table public.user_sessions enable row level security;
alter table public.user_activity_events enable row level security;

create policy "Users read own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Users update own profile"
  on public.profiles for update
  using (auth.uid() = id);

create policy "Users read own sessions"
  on public.user_sessions for select
  using (auth.uid() = user_id);

create policy "Users read own activity"
  on public.user_activity_events for select
  using (auth.uid() = user_id);
