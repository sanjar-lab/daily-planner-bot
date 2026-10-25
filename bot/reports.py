"""Weekly / monthly completion reports."""
from __future__ import annotations

import asyncio
import calendar
import datetime as dt
import logging

from . import db, prompts
from .ai import AIError
from .channel import user_theme
from .i18n import t
from .planner import ai_for, local_now
from .render import render_report
from .render.labels import w as word

log = logging.getLogger(__name__)


def period(kind: str, ref: dt.date) -> tuple[dt.date, dt.date]:
    if kind == "month":
        return ref.replace(day=1), ref.replace(day=calendar.monthrange(ref.year, ref.month)[1])
    if kind == "lastweek":
        ref -= dt.timedelta(days=7)
    start = ref - dt.timedelta(days=ref.weekday())
    return start, start + dt.timedelta(days=6)


def _part(start: str | None) -> str:
    if not start:
        return "anytime"
    h = int(start[:2])
    return "morning" if h < 12 else "afternoon" if h < 17 else "evening"


async def build(user, kind: str, ref: dt.date | None = None) -> tuple[bytes, int, str]:
    """Returns (image, completion %, title)."""
    lang = user["lang"]
    today = local_now(user).date()
    ref = ref or today
    start, end = period(kind, ref)
    rows = await db.tasks_between(user["id"], start, end)

    per_day: dict[dt.date, list[int]] = {}
    for r in rows:
        d = per_day.setdefault(r["plan_date"], [0, 0])
        d[1] += 1
        d[0] += r["done"]
    days = [(start + dt.timedelta(i), *per_day.get(start + dt.timedelta(i), [0, 0]))
            for i in range((end - start).days + 1)]

    streak = 0
    for d, done, total in reversed([x for x in days if x[0] <= today]):
        if total and done / total >= 0.6:
            streak += 1
        elif total or streak:
            break
    scored = [(done / total, done, d) for d, done, total in days if total]
    best = max(scored)[2] if scored else None
    high = [r for r in rows if r["priority"] == "high"]
    total = len(rows)
    done = sum(r["done"] for r in rows)
    pct = round(100 * done / total) if total else 0

    insight = ""
    if total:
        parts = {}
        for r in rows:
            p = parts.setdefault(_part(r["start_time"]), [0, 0])
            p[0] += r["done"]
            p[1] += 1
        summary = (
            f"Period {start}..{end}. Done {done}/{total}. High priority done {sum(r['done'] for r in high)}/{len(high)}.\n"
            f"By part of day (done/total): {parts}\n"
            f"Per day: {[(str(d), dn, tt) for d, dn, tt in days if tt]}\n"
            f"Done examples: {[r['title'] for r in rows if r['done']][:12]}\n"
            f"Missed examples: {[r['title'] for r in rows if not r['done']][:12]}")
        try:
            insight = await ai_for(user).text(prompts.report_system(lang), summary, tier="light")
        except AIError as e:
            log.info("report insight failed: %s", e.reason)
        insight = insight or t(lang, "report_fallback", pct=pct)

    data = dict(kind="week" if kind != "month" else "month", start=start, end=end, days=days,
                high_done=sum(r["done"] for r in high), high_total=len(high), streak=streak,
                best_day=best, insight=insight[:400])
    img = await asyncio.to_thread(render_report, data, lang, user_theme(user, today))
    title = word(lang, "weekly" if data["kind"] == "week" else "monthly")
    return img, pct, title
