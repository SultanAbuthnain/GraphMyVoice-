-- ==========================================================
-- Voice -> Mindmap  |  PostgreSQL schema
-- Owns: sessions, mindmap_nodes, mindmap_edges, notes, tasks
-- Matches the pipeline: Transcription -> Extraction -> Structuring -> Guardrail
-- ==========================================================

create extension if not exists "pgcrypto"; -- for gen_random_uuid()

create type session_status as enum (
  'uploaded',
  'transcribing',
  'extracting',
  'structuring',
  'validating',
  'completed',
  'failed'
);

create type node_type as enum (
  'goal',
  'plan',
  'task',
  'topic',
  'note_ref'
);

-- ----------------------------------------------------------
-- sessions: one row per uploaded recording / processing run
-- ----------------------------------------------------------
create table sessions (
  id            uuid primary key default gen_random_uuid(),
  title         text not null default 'Untitled session',
  status        session_status not null default 'uploaded',
  error_message text,
  audio_url     text not null,           -- storage path/URL of the raw audio
  duration_sec  numeric,
  transcript    text,                    -- raw Whisper transcription (nullable until ready)
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- ----------------------------------------------------------
-- mindmap_nodes: the structured goals/plans/tasks/topics
-- forming the tree the frontend renders with React Flow
-- ----------------------------------------------------------
create table mindmap_nodes (
  id          uuid primary key default gen_random_uuid(),
  session_id  uuid not null references sessions(id) on delete cascade,
  parent_id   uuid references mindmap_nodes(id) on delete cascade,
  type        node_type not null default 'topic',
  label       text not null,
  description text,
  position_x  numeric not null default 0,   -- layout coords cached from last render
  position_y  numeric not null default 0,
  order_index int not null default 0,       -- sibling ordering
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create index idx_mindmap_nodes_session on mindmap_nodes(session_id);
create index idx_mindmap_nodes_parent  on mindmap_nodes(parent_id);

-- ----------------------------------------------------------
-- mindmap_edges: cross-links beyond the parent/child tree
-- (e.g. "depends on", "relates to") extracted by the AI
-- ----------------------------------------------------------
create table mindmap_edges (
  id                uuid primary key default gen_random_uuid(),
  session_id        uuid not null references sessions(id) on delete cascade,
  source_node_id    uuid not null references mindmap_nodes(id) on delete cascade,
  target_node_id    uuid not null references mindmap_nodes(id) on delete cascade,
  relationship_type text not null default 'relates_to',
  created_at        timestamptz not null default now()
);

create index idx_mindmap_edges_session on mindmap_edges(session_id);

-- ----------------------------------------------------------
-- notes: free-text notes, optionally pinned to a node
-- ----------------------------------------------------------
create table notes (
  id         uuid primary key default gen_random_uuid(),
  session_id uuid not null references sessions(id) on delete cascade,
  node_id    uuid references mindmap_nodes(id) on delete set null,
  content    text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_notes_session on notes(session_id);

-- ----------------------------------------------------------
-- tasks: checkbox items, optionally pinned to a node
-- ----------------------------------------------------------
create table tasks (
  id         uuid primary key default gen_random_uuid(),
  session_id uuid not null references sessions(id) on delete cascade,
  node_id    uuid references mindmap_nodes(id) on delete set null,
  title      text not null,
  is_done    boolean not null default false,
  due_date   date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_tasks_session on tasks(session_id);

-- keep updated_at fresh
create or replace function set_updated_at() returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger trg_sessions_updated_at        before update on sessions        for each row execute function set_updated_at();
create trigger trg_mindmap_nodes_updated_at    before update on mindmap_nodes    for each row execute function set_updated_at();
create trigger trg_notes_updated_at            before update on notes            for each row execute function set_updated_at();
create trigger trg_tasks_updated_at            before update on tasks            for each row execute function set_updated_at();
