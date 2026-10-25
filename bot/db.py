"""Postgres (Supabase) access. One small pool, plain SQL."""
from __future__ import annotations

import datetime as dt
import json

import asyncpg

from . import config

pool: asyncpg.Pool | None = None

SCHEMA = """
create table if not exists users (
    id bigint primary key,
    name text,
    lang text not null default 'uz',
    tz text not null default 'Asia/Tashkent',
    gemini_key text,
    groq_key text,
    channel_id bigint,
    channel_title text,
    morning_time text not null default '07:00',
    evening_time text not null default '21:30',
    remind_before int not null default 10,
    reminders boolean not null default true,
    task_cards boolean not null default true,
    morning_post boolean not null default true,
    evening_post boolean not null default true,
    weekly_report boolean not null default true,
    monthly_report boolean not null default true,
    theme_mode int not null default -1,
    state text,
    state_data jsonb not null default '{}'::jsonb,
    last_morning date,
    last_evening date,
    last_weekly date,
    last_monthly date,
    created_at timestamptz not null default now()
);

create table if not exists plans (
    id bigserial primary key,
    user_id bigint not null references users(id) on delete cascade,
    plan_date date not null,
    data jsonb not null,
    theme int not null default 0,
    status text not null default 'draft',
    channel_msg_id bigint,
    created_at timestamptz not null default now()
);
create index if not exists plans_user_date on plans (user_id, plan_date);

create table if not exists tasks (
    id bigserial primary key,
    plan_id bigint not null references plans(id) on delete cascade,
    user_id bigint not null,
    plan_date date not null,
    idx int not null,
    title text not null,
    start_time text,
    priority text not null default 'medium',
    done boolean not null default false,
    done_at timestamptz,
    unique (plan_id, idx)
);
create index if not exists tasks_user_date on tasks (user_id, plan_date);

create table if not exists jobs (
    id bigserial primary key,
    user_id bigint not null references users(id) on delete cascade,
    plan_id bigint not null references plans(id) on delete cascade,
    kind text not null,
    task_idx int,
    run_at timestamptz not null,
    done boolean not null default false
);
create index if not exists jobs_due on jobs (run_at) where not done;

-- v2: custom reminders / focus timers live in jobs without a plan; tasks remember if they were added later
alter table jobs alter column plan_id drop not null;
alter table jobs add column if not exists text text;
alter table tasks add column if not exists added boolean not null default false;

create table if not exists memory (
    user_id bigint not null references users(id) on delete cascade,
    key text not null,
    value text not null,
    category text not null default 'fact',
    updated_at timestamptz not null default now(),
    primary key (user_id, key)
);
"""


async def _init_conn(conn):
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


async def connect():
    global pool
    # statement_cache_size=0 keeps us compatible with Supabase's pgbouncer pooler.
    pool = await asyncpg.create_pool(config.DATABASE_URL, min_size=1, max_size=5,
                                     statement_cache_size=0, init=_init_conn)
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA)


async def close():
    if pool:
        await pool.close()


# ---- users -----------------------------------------------------------------
USER_FIELDS = {
    "name", "lang", "tz", "gemini_key", "groq_key", "channel_id", "channel_title",
    "morning_time", "evening_time", "remind_before", "reminders", "task_cards",
    "morning_post", "evening_post", "weekly_report", "monthly_report", "theme_mode",
    "state", "state_data", "last_morning", "last_evening", "last_weekly", "last_monthly",
}


async def get_user(uid: int) -> asyncpg.Record | None:
    return await pool.fetchrow("select * from users where id = $1", uid)


async def ensure_user(uid: int, name: str | None) -> asyncpg.Record:
    return await pool.fetchrow(
        "insert into users (id, name) values ($1, $2) "
        "on conflict (id) do update set name = coalesce(excluded.name, users.name) returning *",
        uid, name)


async def update_user(uid: int, **fields) -> asyncpg.Record:
    bad = set(fields) - USER_FIELDS
    if bad:
        raise ValueError(f"unknown user fields: {bad}")
    cols = list(fields)
    sets = ", ".join(f"{c} = ${i + 2}" for i, c in enumerate(cols))
    return await pool.fetchrow(f"update users set {sets} where id = $1 returning *",
                               uid, *[fields[c] for c in cols])


async def set_state(uid: int, state: str | None, data: dict | None = None):
    await pool.execute("update users set state = $2, state_data = $3 where id = $1",
                       uid, state, data or {})


async def active_users() -> list[asyncpg.Record]:
    return await pool.fetch(
        "select * from users where channel_id is not null and (gemini_key is not null or groq_key is not null)")


# ---- plans & tasks ---------------------------------------------------------
async def create_draft(uid: int, plan_date: dt.date, data: dict, theme: int) -> int:
    async with pool.acquire() as conn, conn.transaction():
        await conn.execute("delete from plans where user_id = $1 and status = 'draft'", uid)
        return await conn.fetchval(
            "insert into plans (user_id, plan_date, data, theme) values ($1, $2, $3, $4) returning id",
            uid, plan_date, data, theme)


async def get_plan(plan_id: int) -> asyncpg.Record | None:
    return await pool.fetchrow("select * from plans where id = $1", plan_id)


async def update_plan(plan_id: int, **fields):
    cols = list(fields)
    sets = ", ".join(f"{c} = ${i + 2}" for i, c in enumerate(cols))
    await pool.execute(f"update plans set {sets} where id = $1", plan_id, *[fields[c] for c in cols])


async def posted_plan(uid: int, plan_date: dt.date) -> asyncpg.Record | None:
    return await pool.fetchrow(
        "select * from plans where user_id = $1 and plan_date = $2 and status = 'posted' "
        "order by id desc limit 1", uid, plan_date)


async def latest_plan(uid: int) -> asyncpg.Record | None:
    return await pool.fetchrow(
        "select * from plans where user_id = $1 order by plan_date desc, id desc limit 1", uid)


async def publish_plan(plan_id: int, uid: int, plan_date: dt.date, tasks: list[dict],
                       channel_msg_id: int, jobs: list[tuple]) -> list[int]:
    """Marks a draft as the posted plan for its date, replacing any earlier one.
    Returns channel message ids of replaced plans (caller may delete them)."""
    async with pool.acquire() as conn, conn.transaction():
        old = await conn.fetch(
            "update plans set status = 'archived' where user_id = $1 and plan_date = $2 "
            "and status = 'posted' and id <> $3 returning id, channel_msg_id", uid, plan_date, plan_id)
        if old:
            await conn.execute("delete from jobs where plan_id = any($1::bigint[])", [r["id"] for r in old])
            await conn.execute("delete from tasks where plan_id = any($1::bigint[])", [r["id"] for r in old])
        await conn.execute("update plans set status = 'posted', channel_msg_id = $2 where id = $1",
                           plan_id, channel_msg_id)
        await _sync_tasks(conn, plan_id, uid, plan_date, tasks)
        await conn.executemany(
            "insert into jobs (user_id, plan_id, kind, task_idx, run_at) values ($1, $2, $3, $4, $5)",
            [(uid, plan_id, kind, idx, run_at) for kind, idx, run_at in jobs])
        return [r["channel_msg_id"] for r in old if r["channel_msg_id"]]


async def _sync_tasks(conn, plan_id, uid, plan_date, tasks):
    """Make the tasks table match the plan, keeping done flags of tasks that stay (same idx)."""
    await conn.execute("delete from tasks where plan_id = $1 and not (idx = any($2::int[]))",
                       plan_id, [t["idx"] for t in tasks])
    await conn.executemany(
        "insert into tasks (plan_id, user_id, plan_date, idx, title, start_time, priority, added) "
        "values ($1, $2, $3, $4, $5, $6, $7, $8) on conflict (plan_id, idx) do update set "
        "title = excluded.title, start_time = excluded.start_time, priority = excluded.priority, "
        "added = excluded.added, plan_date = excluded.plan_date",
        [(plan_id, uid, plan_date, t["idx"], t["title"], t.get("start"), t.get("priority", "medium"),
          bool(t.get("added"))) for t in tasks])


async def update_posted(plan_id: int, uid: int, plan_date: dt.date, data: dict, jobs: list[tuple]):
    """Change a plan that is already in the channel: data, tasks (done kept) and pending jobs."""
    async with pool.acquire() as conn, conn.transaction():
        await conn.execute("update plans set data = $2, plan_date = $3 where id = $1", plan_id, data, plan_date)
        await _sync_tasks(conn, plan_id, uid, plan_date, data["tasks"])
        await conn.execute("delete from jobs where plan_id = $1 and not done", plan_id)
        await conn.executemany(
            "insert into jobs (user_id, plan_id, kind, task_idx, run_at) values ($1, $2, $3, $4, $5)",
            [(uid, plan_id, kind, idx, run_at) for kind, idx, run_at in jobs])


async def plan_for(uid: int, plan_date: dt.date) -> asyncpg.Record | None:
    """The posted plan for a date, else the newest draft for it."""
    return await pool.fetchrow(
        "select * from plans where user_id = $1 and plan_date = $2 and status in ('posted', 'draft') "
        "order by (status = 'posted') desc, id desc limit 1", uid, plan_date)


async def plan_tasks(plan_id: int) -> list[asyncpg.Record]:
    return await pool.fetch(
        "select * from tasks where plan_id = $1 order by start_time nulls last, idx", plan_id)


async def set_done(plan_id: int, idxs: list[int]) -> int:
    return len(await pool.fetch(
        "update tasks set done = true, done_at = now() where plan_id = $1 and idx = any($2::int[]) "
        "and not done returning idx", plan_id, idxs))


async def toggle_task(plan_id: int, idx: int) -> bool | None:
    return await pool.fetchval(
        "update tasks set done = not done, done_at = case when done then null else now() end "
        "where plan_id = $1 and idx = $2 returning done", plan_id, idx)


async def tasks_between(uid: int, start: dt.date, end: dt.date) -> list[asyncpg.Record]:
    return await pool.fetch(
        "select t.* from tasks t join plans p on p.id = t.plan_id "
        "where t.user_id = $1 and t.plan_date between $2 and $3 and p.status = 'posted' "
        "order by t.plan_date, t.idx", uid, start, end)


# ---- jobs ------------------------------------------------------------------
async def take_due_jobs(limit: int = 50) -> list[asyncpg.Record]:
    return await pool.fetch(
        "update jobs set done = true where id in ("
        "  select id from jobs where not done and run_at <= now() order by run_at limit $1 "
        "  for update skip locked) returning *", limit)


async def add_job(uid: int, kind: str, run_at: dt.datetime, text: str | None = None,
                  plan_id: int | None = None, task_idx: int | None = None) -> int:
    return await pool.fetchval(
        "insert into jobs (user_id, plan_id, kind, task_idx, run_at, text) values ($1, $2, $3, $4, $5, $6) "
        "returning id", uid, plan_id, kind, task_idx, run_at, text)


async def pending_reminders(uid: int) -> list[asyncpg.Record]:
    return await pool.fetch(
        "select * from jobs where user_id = $1 and not done and kind in ('custom', 'focus') "
        "order by run_at limit 30", uid)


async def delete_job(uid: int, job_id: int):
    await pool.execute("delete from jobs where id = $1 and user_id = $2", job_id, uid)


# ---- memory ----------------------------------------------------------------
async def get_memory(uid: int) -> list[asyncpg.Record]:
    return await pool.fetch(
        "select key, value, category from memory where user_id = $1 order by category, updated_at", uid)


async def save_memory(uid: int, items: list[dict], forget: list[str]) -> int:
    saved = 0
    async with pool.acquire() as conn, conn.transaction():
        if forget:
            await conn.execute("delete from memory where user_id = $1 and key = any($2::text[])", uid, forget)
        for it in items:
            key = str(it.get("key", "")).strip().lower()[:48]
            value = str(it.get("value", "")).strip()[:300]
            if not key or not value:
                continue
            cat = str(it.get("category") or "fact").lower()[:20]
            await conn.execute(
                "insert into memory (user_id, key, value, category) values ($1, $2, $3, $4) "
                "on conflict (user_id, key) do update set value = excluded.value, "
                "category = excluded.category, updated_at = now()", uid, key, value, cat)
            saved += 1
        # keep memory small: drop the stalest non-goal facts beyond the limit
        await conn.execute(
            "delete from memory where user_id = $1 and key in ("
            "  select key from memory where user_id = $1 order by (category = 'goal') desc, updated_at desc "
            "  offset $2)", uid, config.MEMORY_LIMIT)
    return saved


async def delete_memory(uid: int, key: str):
    await pool.execute("delete from memory where user_id = $1 and key = $2", uid, key)
