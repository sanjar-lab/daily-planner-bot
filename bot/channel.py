"""Channel posts: plan photo with an interactive checklist."""
from __future__ import annotations

import asyncio
import html

from aiogram import Bot
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup

from .i18n import t
from .render import render_day, theme_for


def user_theme(user, date) -> int:
    return user["theme_mode"] if user["theme_mode"] >= 0 else theme_for(date)


def _short(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def checklist(plan_id: int, tasks: list) -> InlineKeyboardMarkup:
    rows = []
    for tk in tasks:
        start = tk.get("start") if isinstance(tk, dict) else tk["start_time"]
        mark = "✅" if tk["done"] else "⬜️"
        label = f"{mark} {start + ' · ' if start else ''}{_short(tk['title'], 48)}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"t:{plan_id}:{tk['idx']}")])
    return InlineKeyboardMarkup(inline_keyboard=rows[:100])


def caption(plan: dict, tasks: list, lang: str) -> str:
    n = len(tasks)
    done = sum(1 for tk in tasks if tk["done"])
    pct = round(100 * done / n) if n else 0
    filled = round(pct / 10)
    bar = "▰" * filled + "▱" * (10 - filled)
    parts = []
    if plan.get("headline"):
        parts.append(f"<b>{html.escape(plan['headline'])}</b>")
    if plan.get("focus"):
        parts.append(t(lang, "focus_line", focus=html.escape(plan["focus"])))
    parts.append(f"\n{bar}  {t(lang, 'progress')} {done}/{n} · {pct}%")
    return "\n".join(parts)[:1024]


async def post_plan(bot: Bot, user, plan_id: int, plan: dict, theme: int) -> int:
    img = await asyncio.to_thread(render_day, plan, user["lang"], theme)
    tasks = [dict(tk, done=False) for tk in plan["tasks"]]
    msg = await bot.send_photo(
        user["channel_id"], BufferedInputFile(img, f"plan_{plan['date']}.jpg"),
        caption=caption(plan, tasks, user["lang"]), reply_markup=checklist(plan_id, tasks))
    return msg.message_id
