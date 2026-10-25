"""Time-driven work: reminders, task-start cards, morning/evening posts, reports.

Everything is derived from the database, so a restart or a sleeping instance
loses nothing — the next tick catches up (stale items are skipped, not spammed).
"""
from __future__ import annotations

import asyncio
import datetime as dt
import html
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup, ReplyParameters

from . import db, reports
from .i18n import t
from .planner import local_now
from .render import render_task
from .render.model import to_min

log = logging.getLogger(__name__)
_lock = asyncio.Lock()
STALE = dt.timedelta(minutes=20)
WINDOW = 180  # minutes after the configured time during which a daily post may still go out


async def tick(bot: Bot):
    if _lock.locked():
        return
    async with _lock:
        try:
            await run_jobs(bot)
        except Exception:
            log.exception("jobs failed")
        try:
            await run_daily(bot)
        except Exception:
            log.exception("daily failed")


async def loop(bot: Bot, every: int = 30):
    while True:
        await tick(bot)
        await asyncio.sleep(every)


async def _send(coro):
    try:
        return await coro
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        log.warning("send failed: %s", e)


# ---- per-task jobs -----------------------------------------------------------
async def run_jobs(bot: Bot):
    now = dt.datetime.now(dt.timezone.utc)
    for job in await db.take_due_jobs():
        if now - job["run_at"] > STALE:
            continue
        user = await db.get_user(job["user_id"])
        if not user:
            continue
        lang = user["lang"]
        if job["kind"] == "custom":
            await _send(bot.send_message(user["id"], t(lang, "custom_remind", text=html.escape(job["text"] or ""))))
            continue
        if job["kind"] == "focus":
            m = job["text"] or "25"
            await _send(bot.send_message(user["id"], t(lang, "focus_done", m=m), reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=t(lang, "btn_focus_again", m=m), callback_data=f"fo:{m}")]])))
            continue
        plan = await db.get_plan(job["plan_id"]) if job["plan_id"] else None
        if not plan or plan["status"] != "posted":
            continue
        task = next((tk for tk in plan["data"]["tasks"] if tk["idx"] == job["task_idx"]), None)
        if not task:
            continue
        title = html.escape(task["title"])
        if job["kind"] == "remind":
            ref = f"{plan['id']}:{task['idx']}"
            buttons = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=t(lang, "btn_done"), callback_data=f"rk:{ref}"),
                InlineKeyboardButton(text=t(lang, "btn_snooze"), callback_data=f"sn:{ref}")]])
            await _send(bot.send_message(user["id"], t(lang, "remind", min=user["remind_before"], title=title,
                                                       time=task.get("start") or ""), reply_markup=buttons))
        elif job["kind"] == "task_card":
            done = {r["idx"]: r["done"] for r in await db.plan_tasks(plan["id"])}
            if done.get(task["idx"]):
                continue
            img = await asyncio.to_thread(render_task, plan["data"], task["idx"], lang, plan["theme"])
            await _send(bot.send_photo(user["channel_id"], BufferedInputFile(img, "task.jpg"),
                                       caption=t(lang, "card_caption", time=task.get("start") or "", title=title)))


# ---- daily posts ------------------------------------------------------------
def _due(now: dt.datetime, hhmm: str, last: dt.date | None) -> bool:
    m = to_min(hhmm)
    cur = now.hour * 60 + now.minute
    return m is not None and last != now.date() and m <= cur < m + WINDOW


async def run_daily(bot: Bot):
    for user in await db.active_users():
        try:
            now = local_now(user)
            if _due(now, user["morning_time"], user["last_morning"]):
                await db.update_user(user["id"], last_morning=now.date())
                if user["morning_post"]:
                    await morning(bot, user, now.date())
            if _due(now, user["evening_time"], user["last_evening"]):
                await db.update_user(user["id"], last_evening=now.date())
                await evening(bot, user, now.date())
                d = now.date()
                if user["weekly_report"] and d.weekday() == 6 and user["last_weekly"] != d:
                    await db.update_user(user["id"], last_weekly=d)
                    await send_report(bot, user, "week")
                if user["monthly_report"] and (d + dt.timedelta(days=1)).day == 1 and user["last_monthly"] != d:
                    await db.update_user(user["id"], last_monthly=d)
                    await send_report(bot, user, "month")
        except Exception:
            log.exception("daily for user %s failed", user["id"])


async def morning(bot: Bot, user, today: dt.date):
    plan = await db.posted_plan(user["id"], today)
    if not plan:
        return
    lang = user["lang"]
    data = plan["data"]
    first = next((tk for tk in data["tasks"] if tk.get("start")), None)
    text = t(lang, "morning", n=len(data["tasks"]),
             first=t(lang, "first", time=first["start"], title=html.escape(first["title"])) if first else "",
             focus=t(lang, "focus_line", focus=html.escape(data["focus"])) if data.get("focus") else "")
    reply = (ReplyParameters(message_id=plan["channel_msg_id"], allow_sending_without_reply=True)
             if plan["channel_msg_id"] else None)
    await _send(bot.send_message(user["channel_id"], text, reply_parameters=reply))


async def evening(bot: Bot, user, today: dt.date):
    lang = user["lang"]
    plan = await db.posted_plan(user["id"], today)
    tomorrow_plan = await db.posted_plan(user["id"], today + dt.timedelta(days=1))
    if plan:
        tasks = await db.plan_tasks(plan["id"])
        n, done = len(tasks), sum(tk["done"] for tk in tasks)
        left = [tk for tk in tasks if not tk["done"]]
        if user["evening_post"]:
            items = "\n".join(f"▫️ {html.escape(tk['title'])}" for tk in left[:10])
            await _send(bot.send_message(user["channel_id"], t(
                lang, "evening", done=done, n=n, pct=round(100 * done / n) if n else 0,
                left=t(lang, "left", items=items) if left else "")))
        if not tomorrow_plan and user["evening_post"]:
            rows = [[InlineKeyboardButton(text=t(lang, "btn_repeat"), callback_data="repeat")]]
            if left:
                rows.insert(0, [InlineKeyboardButton(text=t(lang, "btn_carry"), callback_data="carry")])
            markup = InlineKeyboardMarkup(inline_keyboard=rows)
            await _send(bot.send_message(user["id"], t(lang, "evening_dm", done=done, n=n), reply_markup=markup))
    elif not tomorrow_plan and user["evening_post"]:
        await _send(bot.send_message(user["id"], t(lang, "ask_plan")))


async def send_report(bot: Bot, user, kind: str):
    img, pct, title = await reports.build(user, kind)
    await _send(bot.send_photo(user["channel_id"], BufferedInputFile(img, "report.jpg"),
                               caption=t(user["lang"], "report_caption", title=title, pct=pct)))
