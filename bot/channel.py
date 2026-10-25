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
        new = " 🆕" if tk.get("added") else ""
        label = f"{mark} {start + ' · ' if start else ''}{_short(tk['title'], 46)}{new}"
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


async def refresh_post(bot: Bot, user, plan_id: int) -> bytes | None:
    """Re-render a posted plan (ticks included) and update the channel message in place.
    Falls back to a fresh post if the old one can't be edited. Returns the image."""
    from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
    from aiogram.types import InputMediaPhoto

    from . import db
    from .planner import with_done

    row = await db.get_plan(plan_id)
    if not row or row["status"] != "posted":
        return None
    tasks = await db.plan_tasks(plan_id)
    view = with_done(row["data"], tasks)
    img = await asyncio.to_thread(render_day, view, user["lang"], row["theme"])
    cap, markup = caption(row["data"], tasks, user["lang"]), checklist(plan_id, tasks)
    try:
        await bot.edit_message_media(
            chat_id=user["channel_id"], message_id=row["channel_msg_id"],
            media=InputMediaPhoto(media=BufferedInputFile(img, "plan.jpg"), caption=cap), reply_markup=markup)
    except (TelegramBadRequest, TelegramForbiddenError):
        msg = await bot.send_photo(user["channel_id"], BufferedInputFile(img, "plan.jpg"),
                                   caption=cap, reply_markup=markup)
        await db.update_plan(plan_id, channel_msg_id=msg.message_id)
    return img
