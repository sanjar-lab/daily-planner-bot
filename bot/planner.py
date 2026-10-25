"""Plan creation and editing on top of the AI orchestrator."""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

from . import db, prompts
from .ai import AI
from .crypto import decrypt
from .render.labels import weekday
from .render.model import PRIORITIES, hhmm, to_min


def ai_for(user) -> AI:
    return AI(decrypt(user["gemini_key"]), decrypt(user["groq_key"]))


def local_now(user) -> dt.datetime:
    try:
        tz = ZoneInfo(user["tz"])
    except Exception:
        tz = ZoneInfo("Asia/Tashkent")
    return dt.datetime.now(tz)


def tzinfo(user):
    return local_now(user).tzinfo


async def memory_text(uid: int) -> str:
    rows = await db.get_memory(uid)
    return "\n".join(f"- [{r['category']}] {r['key']}: {r['value']}" for r in rows)


def normalize(plan: dict, default_date: dt.date) -> dict:
    """Validate AI output into the shape the renderer and DB expect."""
    try:
        date = dt.date.fromisoformat(str(plan.get("date"))[:10])
        if abs((date - default_date).days) > 60:
            date = default_date
    except ValueError:
        date = default_date
    tasks = []
    for t in plan.get("tasks") or []:
        if not isinstance(t, dict):
            continue
        title = str(t.get("title") or "").strip()
        if not title:
            continue
        start, end = to_min(t.get("start")), to_min(t.get("end"))
        pr = str(t.get("priority") or "medium").lower()
        tasks.append({
            "added": bool(t.get("added")),
            "title": title[:90],
            "start": hhmm(start) if start is not None else None,
            "end": hhmm(end) if end is not None and start is not None else None,
            "priority": pr if pr in PRIORITIES else "medium",
            "category": str(t.get("category") or "other").lower(),
            "note": str(t.get("note") or "").strip()[:140],
        })
    timed = sorted((t for t in tasks if t["start"]), key=lambda t: t["start"])
    tasks = timed + [t for t in tasks if not t["start"]]
    for i, t in enumerate(tasks):
        t["idx"] = i
    return {
        "date": date.isoformat(),
        "headline": str(plan.get("headline") or "").strip()[:80],
        "focus": str(plan.get("focus") or "").strip()[:140],
        "tasks": tasks[:40],
    }


async def _remember(uid: int, raw: dict) -> int:
    items = [m for m in (raw.get("memory") or []) if isinstance(m, dict)]
    forget = [str(k) for k in (raw.get("forget") or []) if k]
    if not items and not forget:
        return 0
    return await db.save_memory(uid, items, forget)


async def make_plan(user, text: str) -> tuple[dict, int, AI]:
    ai = ai_for(user)
    now = local_now(user)
    today = now.date()
    tomorrow = today + dt.timedelta(days=1)
    carry = (user["state_data"] or {}).get("carry") or []
    system = prompts.plan_system(user["lang"], today.isoformat(), weekday("en", today),
                                 tomorrow.isoformat(), await memory_text(user["id"]), carry)
    raw = await ai.json(system, text, tier="smart")
    plan = normalize(raw, tomorrow)
    learned = await _remember(user["id"], raw)
    return plan, learned, ai


async def edit_plan(user, plan: dict, instruction: str) -> tuple[dict, AI]:
    import json

    ai = ai_for(user)
    user_msg = f"Current plan JSON:\n{json.dumps(plan, ensure_ascii=False)}\n\nInstruction:\n{instruction}"
    raw = await ai.json(prompts.edit_system(user["lang"]), user_msg, tier="smart")
    new = normalize(raw, dt.date.fromisoformat(plan["date"]))
    await _remember(user["id"], raw)
    return new, ai


async def learn_about(user, text: str) -> list[dict]:
    ai = ai_for(user)
    raw = await ai.json(prompts.about_system(user["lang"], await memory_text(user["id"])), text, tier="light")
    await _remember(user["id"], raw)
    return [m for m in (raw.get("memory") or []) if isinstance(m, dict)]


def schedule(user, plan: dict) -> list[tuple]:
    """(kind, task_idx, run_at_utc) jobs for a posted plan; past moments are skipped."""
    tz = tzinfo(user)
    date = dt.date.fromisoformat(plan["date"])
    now = dt.datetime.now(dt.timezone.utc)
    jobs = []
    for t in plan["tasks"]:
        m = to_min(t.get("start"))
        if m is None:
            continue
        start = dt.datetime.combine(date, dt.time(m // 60, m % 60), tz).astimezone(dt.timezone.utc)
        if user["reminders"] and user["remind_before"] > 0:
            at = start - dt.timedelta(minutes=user["remind_before"])
            if at > now:
                jobs.append(("remind", t["idx"], at))
        if user["task_cards"] and start > now - dt.timedelta(minutes=2):
            jobs.append(("task_card", t["idx"], start))
    return jobs


# ---- chat routing & changes to existing plans ----------------------------------
def plan_lines(plan: dict | None, done: dict[int, bool] | None = None) -> str:
    if not plan:
        return ""
    done = done or {}
    return "\n".join(f"{t['idx']}: {t.get('start') or '--:--'} {t['title']}{' [done]' if done.get(t['idx']) else ''}"
                     for t in plan["tasks"])


async def route(user, text: str, today_plan, today_done, tomorrow_plan) -> dict:
    now = local_now(user)
    system = prompts.router_system(
        user["lang"], now.strftime("%Y-%m-%d %H:%M (%A)"), plan_lines(today_plan, today_done),
        plan_lines(tomorrow_plan), await memory_text(user["id"]))
    raw = await ai_for(user).json(system, text, tier="light")
    intent = str(raw.get("intent") or "chat").lower()
    raw["intent"] = intent if intent in ("plan", "add", "edit", "done", "remind", "habit", "goal", "chat") else "chat"
    return raw


def merge_added(plan: dict, new_tasks: list[dict]) -> dict:
    """Append new tasks with fresh ids and the 'added' flag, keeping existing ids stable."""
    base = normalize({"date": plan["date"], "tasks": new_tasks}, dt.date.fromisoformat(plan["date"]))["tasks"]
    nxt = max((t["idx"] for t in plan["tasks"]), default=-1) + 1
    old_titles = {t["title"].strip().lower() for t in plan["tasks"]}
    tasks = list(plan["tasks"])
    for t in base:
        if t["title"].strip().lower() in old_titles:
            continue
        tasks.append(dict(t, idx=nxt, added=True))
        nxt += 1
    return dict(plan, tasks=_sorted(tasks))


def reconcile(old: dict, new: dict) -> dict:
    """After an AI edit, give tasks that still exist their old ids (so ticks survive)."""
    by_title = {t["title"].strip().lower(): t for t in old["tasks"]}
    nxt = max((t["idx"] for t in old["tasks"]), default=-1) + 1
    tasks = []
    for t in new["tasks"]:
        prev = by_title.pop(t["title"].strip().lower(), None)
        if prev:
            tasks.append(dict(t, idx=prev["idx"], added=prev.get("added", False)))
        else:
            tasks.append(dict(t, idx=nxt, added=old.get("_posted", False)))
            nxt += 1
    return dict(new, tasks=_sorted(tasks))


def _sorted(tasks: list[dict]) -> list[dict]:
    timed = sorted((t for t in tasks if t.get("start")), key=lambda t: t["start"])
    return timed + [t for t in tasks if not t.get("start")]


async def add_to_plan(user, plan: dict, text: str) -> dict:
    import json

    raw = await ai_for(user).json(
        prompts.add_system(user["lang"]),
        f"Existing plan JSON:\n{json.dumps(plan, ensure_ascii=False)}\n\nUser message:\n{text}", tier="smart")
    return merge_added(plan, [t for t in raw.get("tasks") or [] if isinstance(t, dict)])


def local_to_utc(user, value: str) -> dt.datetime | None:
    try:
        naive = dt.datetime.strptime(value.strip()[:16], "%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return None
    return naive.replace(tzinfo=tzinfo(user)).astimezone(dt.timezone.utc)


def with_done(plan: dict, tasks) -> dict:
    done = {r["idx"]: r["done"] for r in tasks}
    return dict(plan, tasks=[dict(t, done=done.get(t["idx"], False)) for t in plan["tasks"]])
