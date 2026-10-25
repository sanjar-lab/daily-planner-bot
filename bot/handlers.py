"""Telegram handlers: onboarding, plans, checklist, settings, reports, memory."""
from __future__ import annotations

import asyncio
import datetime as dt
import html
import logging
import re
from io import BytesIO
from zoneinfo import ZoneInfo

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    BufferedInputFile, CallbackQuery, ChatAdministratorRights, InlineKeyboardButton,
    InlineKeyboardMarkup, InputMediaPhoto, KeyboardButton, KeyboardButtonRequestChat,
    Message, MessageOriginChannel, ReplyKeyboardMarkup, ReplyKeyboardRemove,
)

from . import db, planner, reports
from .ai import AIError, validate_key
from .channel import caption, checklist, post_plan, refresh_post, user_theme
from .crypto import decrypt, encrypt, mask
from .i18n import LANGS, MENU, menu_action, t
from .render import N_THEMES, render_day
from .render.labels import date_long
from .render.sample import SAMPLE
from .render.themes import PALETTES

log = logging.getLogger(__name__)
router = Router()
private = F.chat.type == "private"
router.message.filter(private)

_locks: dict[int, asyncio.Lock] = {}

TZ_CHOICES = [("Toshkent +5", "Asia/Tashkent"), ("Moskva +3", "Europe/Moscow"), ("Almaty +5", "Asia/Almaty"),
              ("Bishkek +6", "Asia/Bishkek"), ("Istanbul +3", "Europe/Istanbul"), ("Dubai +4", "Asia/Dubai"),
              ("Seoul +9", "Asia/Seoul"), ("London", "Europe/London"), ("Berlin", "Europe/Berlin"),
              ("New York", "America/New_York")]


def kb(*rows) -> InlineKeyboardMarkup:
    """Rows of (text, callback_data) pairs; data starting with http becomes a URL button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=txt, url=data) if data.startswith("http")
         else InlineKeyboardButton(text=txt, callback_data=data) for txt, data in row] for row in rows])


KEY_SITES = {"gemini": "https://aistudio.google.com/apikey", "groq": "https://console.groq.com/keys"}


def key_screen(lang: str, provider: str, page: str = "ask", skip: bool = True) -> tuple[str, InlineKeyboardMarkup]:
    """Key request with instruction buttons. page: ask | howto | why."""
    open_btn = [(t(lang, f"btn_open_{provider}"), KEY_SITES[provider])]
    s = "1" if skip else "0"
    if page == "ask":
        rows = [open_btn, [(t(lang, "btn_howto"), f"kh:{provider}:howto:{s}")],
                [(t(lang, "btn_why"), f"kh:{provider}:why:{s}")]]
        if skip:
            rows.append([(t(lang, "skip"), f"skip:{provider}")])
        return t(lang, f"ask_{provider}"), kb(*rows)
    text = t(lang, "howto_" + provider if page == "howto" else "why_keys")
    return text, kb(open_btn, [(t(lang, "btn_back"), f"kh:{provider}:ask:{s}")])


async def ask_key(msg: Message, lang: str, provider: str, skip: bool = True):
    text, markup = key_screen(lang, provider, skip=skip)
    await msg.answer(text, disable_web_page_preview=True, reply_markup=markup)


def theme_name(user) -> str:
    return t(user["lang"], "theme_rotate") if user["theme_mode"] < 0 else PALETTES[user["theme_mode"]].name


async def safe_delete(msg: Message):
    try:
        await msg.delete()
    except TelegramBadRequest:
        pass


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------
async def next_step(msg: Message, user):
    """Ask for whatever setup piece is still missing; returns True when setup is complete."""
    lang = user["lang"]
    if not user["gemini_key"] and not user["groq_key"]:
        if user["state"] == "ask_groq":
            await ask_key(msg, lang, "groq")
            return False
        await db.set_state(user["id"], "ask_gemini")
        await ask_key(msg, lang, "gemini")
        return False
    if user["state"] == "ask_groq":
        await ask_key(msg, lang, "groq")
        return False
    if user["state"] == "ask_tz":
        await ask_tz(msg, lang)
        return False
    if not user["channel_id"]:
        await db.set_state(user["id"], "ask_channel")
        await ask_channel(msg, lang)
        return False
    if user["state"] == "ask_about":
        await msg.answer(t(lang, "ask_about"), reply_markup=kb([(t(lang, "skip"), "skip:about")]))
        return False
    return True


async def ask_tz(msg: Message, lang: str):
    rows = [[(a, f"tz:{b}") for a, b in TZ_CHOICES[i:i + 2]] for i in range(0, len(TZ_CHOICES), 2)]
    await msg.answer(t(lang, "ask_tz"), reply_markup=kb(*rows))


async def ask_channel(msg: Message, lang: str):
    rights = dict(is_anonymous=False, can_manage_chat=False, can_delete_messages=True, can_manage_video_chats=False,
                  can_restrict_members=False, can_promote_members=False, can_change_info=False,
                  can_invite_users=False, can_post_stories=False, can_edit_stories=False,
                  can_delete_stories=False, can_send_welcome_messages=False,
                  can_post_messages=True, can_edit_messages=True)
    button = KeyboardButton(text=t(lang, "btn_pick_channel"), request_chat=KeyboardButtonRequestChat(
        request_id=1, chat_is_channel=True,
        # Telegram requires the user's rights to be a superset of the bot's.
        user_administrator_rights=ChatAdministratorRights(**rights),
        bot_administrator_rights=ChatAdministratorRights(**rights), request_title=True))
    await msg.answer(t(lang, "ask_channel"), reply_markup=ReplyKeyboardMarkup(
        keyboard=[[button]], resize_keyboard=True, one_time_keyboard=True))


@router.message(CommandStart())
async def cmd_start(msg: Message):
    user = await db.get_user(msg.from_user.id)
    if not user:
        user = await db.ensure_user(msg.from_user.id, msg.from_user.first_name)
        await msg.answer(t("uz", "choose_lang"),
                         reply_markup=kb([(v, f"lang:{k}") for k, v in LANGS.items()]))
        return
    if await next_step(msg, user):
        await show_menu(msg, user, t(user["lang"], "ready"))


@router.callback_query(F.data.startswith("lang:"))
async def cb_lang(cq: CallbackQuery):
    lang = cq.data.split(":", 1)[1]
    user = await db.ensure_user(cq.from_user.id, cq.from_user.first_name)
    first_time = not user["gemini_key"] and not user["groq_key"]
    user = await db.update_user(user["id"], lang=lang)
    await cq.answer()
    await safe_delete(cq.message)
    if first_time:
        await cq.message.answer(t(lang, "welcome", name=html.escape(cq.from_user.first_name or "")))
        await next_step(cq.message, user)
    else:
        await cq.message.answer(t(lang, "saved"))
        await show_settings(cq.message, user)


@router.callback_query(F.data.startswith("skip:"))
async def cb_skip(cq: CallbackQuery):
    what = cq.data.split(":", 1)[1]
    user = await db.get_user(cq.from_user.id)
    await cq.answer()
    await cq.message.edit_reply_markup(reply_markup=None)
    if what == "gemini":
        await db.set_state(user["id"], "ask_groq")
    elif what == "groq":
        if not user["gemini_key"] and not user["groq_key"]:
            await db.set_state(user["id"], "ask_gemini")
        else:
            await cq.message.answer(t(user["lang"], "groq_skip_warn"))
            await db.set_state(user["id"], "ask_tz")
    elif what == "about":
        await db.set_state(user["id"], None)
    user = await db.get_user(user["id"])
    if await next_step(cq.message, user):
        await show_menu(cq.message, user, t(user["lang"], "ready"))


@router.callback_query(F.data.startswith("kh:"))
async def cb_key_help(cq: CallbackQuery):
    _, provider, page, skip = cq.data.split(":")
    user = await db.get_user(cq.from_user.id)
    await cq.answer()
    text, markup = key_screen(user["lang"] if user else "uz", provider, page, skip == "1")
    try:
        await cq.message.edit_text(text, disable_web_page_preview=True, reply_markup=markup)
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("tz:"))
async def cb_tz(cq: CallbackQuery):
    await cq.answer()
    await cq.message.edit_reply_markup(reply_markup=None)
    await set_tz(cq.message, await db.get_user(cq.from_user.id), cq.data.split(":", 1)[1])


def parse_tz(text: str) -> str | None:
    text = text.strip()
    m = re.fullmatch(r"(?:utc|gmt)?\s*([+-]?)(\d{1,2})(?::00)?", text, re.I)
    if m:
        h = int(m.group(2))
        if h > 14:
            return None
        sign = "-" if m.group(1) != "-" else "+"  # Etc/GMT signs are inverted
        return "UTC" if h == 0 else f"Etc/GMT{sign}{h}"
    try:
        ZoneInfo(text)
        return text
    except Exception:
        return None


async def set_tz(msg: Message, user, tz: str):
    user = await db.update_user(user["id"], tz=tz)
    now = planner.local_now(user).strftime("%H:%M")
    await msg.answer(t(user["lang"], "tz_ok", tz=tz, time=now))
    onboarding = not user["channel_id"]
    await db.set_state(user["id"], None if not onboarding else "ask_channel")
    user = await db.get_user(user["id"])
    if onboarding:
        await next_step(msg, user)
    else:
        await show_settings(msg, user)


async def save_key(msg: Message, user, provider: str, key: str):
    lang = user["lang"]
    await safe_delete(msg)
    key = key.strip()
    status = await msg.answer(t(lang, "checking"))
    ok = await validate_key(provider, key)
    if ok is False:
        await status.edit_text(t(lang, "key_bad"))
        return
    await db.update_user(user["id"], **{f"{provider}_key": encrypt(key)})
    await status.edit_text(t(lang, "key_ok", mask=mask(key)) + ("" if ok else "\n" + t(lang, "key_unsure")))
    onboarding = not user["channel_id"]
    if user["state"] == "ask_gemini":
        await db.set_state(user["id"], "ask_groq")
    elif user["state"] == "ask_groq":
        await db.set_state(user["id"], "ask_tz")
    else:
        await db.set_state(user["id"], None)
    user = await db.get_user(user["id"])
    if onboarding:
        await next_step(msg, user)


@router.message(F.chat_shared)
async def on_chat_shared(msg: Message, bot: Bot):
    await connect_channel(msg, bot, await db.get_user(msg.from_user.id), msg.chat_shared.chat_id)


@router.message(F.forward_origin.as_("origin"), F.forward_origin.type == "channel")
async def on_forward(msg: Message, bot: Bot, origin: MessageOriginChannel):
    user = await db.get_user(msg.from_user.id)
    if user and user["state"] == "ask_channel":
        await connect_channel(msg, bot, user, origin.chat.id)
    else:
        await on_plan_input(msg, bot)


async def connect_channel(msg: Message, bot: Bot, user, chat_id: int):
    lang = user["lang"]
    try:
        member = await bot.get_chat_member(chat_id, bot.id)
        chat = await bot.get_chat(chat_id)
        ok = member.status == "administrator" and getattr(member, "can_post_messages", False)
    except (TelegramBadRequest, TelegramForbiddenError):
        ok = False
    if not ok:
        await msg.answer(t(lang, "channel_bad"), reply_markup=ReplyKeyboardRemove())
        await ask_channel(msg, lang)
        return
    onboarding = not user["channel_id"]
    user = await db.update_user(user["id"], channel_id=chat_id, channel_title=chat.title)
    await msg.answer(t(lang, "channel_ok", title=html.escape(chat.title or str(chat_id))),
                     reply_markup=ReplyKeyboardRemove())
    if onboarding:
        await db.set_state(user["id"], "ask_about")
        await next_step(msg, await db.get_user(user["id"]))
    else:
        await db.set_state(user["id"], None)
        await show_menu(msg, user)


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------
async def read_input(msg: Message, bot: Bot, user) -> str | None:
    """Text of a message, transcribing voice/audio/video notes."""
    if msg.text or msg.caption:
        return msg.text or msg.caption
    media = msg.voice or msg.audio or msg.video_note
    if not media:
        return None
    status = await msg.answer(t(user["lang"], "listening"))
    buf = BytesIO()
    await bot.download(media, destination=buf)
    mime = getattr(media, "mime_type", None) or ("video/mp4" if msg.video_note else "audio/ogg")
    name = "voice.mp4" if msg.video_note else ("voice.ogg" if msg.voice else (getattr(media, "file_name", None) or "audio.mp3"))
    try:
        text = await planner.ai_for(user).transcribe(buf.getvalue(), mime, name)
    except AIError as e:
        await status.edit_text(t(user["lang"], f"err_{e.reason}"))
        return None
    await status.edit_text(t(user["lang"], "heard", text=html.escape(text[:900])))
    return text


def preview_kb(user, plan_id: int) -> InlineKeyboardMarkup:
    lang = user["lang"]
    return kb([(t(lang, "btn_post"), f"p:post:{plan_id}")],
              [(t(lang, "btn_edit"), f"p:edit:{plan_id}"), (t(lang, "btn_theme"), f"p:theme:{plan_id}")],
              [(t(lang, "btn_cancel"), f"p:cancel:{plan_id}")])


def preview_caption(user, plan: dict, theme: int, learned: int = 0) -> str:
    lang = user["lang"]
    d = dt.date.fromisoformat(plan["date"])
    return t(lang, "preview", date=date_long(lang, d), n=len(plan["tasks"]), theme=PALETTES[theme].name,
             learned=t(lang, "learned_short", n=learned) if learned else "")


async def send_preview(msg: Message, user, plan_id: int, plan: dict, theme: int, learned: int = 0):
    img = await asyncio.to_thread(render_day, plan, user["lang"], theme)
    await msg.answer_photo(BufferedInputFile(img, "preview.jpg"), caption=preview_caption(user, plan, theme, learned),
                           reply_markup=preview_kb(user, plan_id))


def main_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=labels.get(lang, labels["en"])) for _, labels in row] for row in MENU],
        resize_keyboard=True, is_persistent=True, input_field_placeholder="✍️ 🎙")


async def show_menu(msg: Message, user, text: str | None = None):
    await msg.answer(text or t(user["lang"], "menu_hint"), reply_markup=main_menu(user["lang"]))


ONBOARDING = ("ask_gemini", "ask_groq", "ask_tz", "ask_channel")


@router.message(F.text & ~F.text.startswith("/") | F.voice | F.audio | F.video_note)
async def on_plan_input(msg: Message, bot: Bot):
    user = await db.get_user(msg.from_user.id)
    if not user:
        return await cmd_start(msg)
    state = user["state"] or ""
    lang = user["lang"]

    # --- states that expect a specific answer ---
    if state in ("ask_gemini", "ask_groq") or state.startswith("set_key:"):
        if not msg.text:
            return
        provider = "gemini" if state in ("ask_gemini", "set_key:gemini") else "groq"
        return await save_key(msg, user, provider, msg.text)
    if state == "ask_tz":
        tz = parse_tz(msg.text or "")
        return await (set_tz(msg, user, tz) if tz else msg.answer(t(lang, "tz_bad")))
    if state == "ask_channel":
        return await ask_channel(msg, lang)
    if state.startswith("set_time:"):
        m = re.fullmatch(r"\s*(\d{1,2})[:.](\d{2})\s*", msg.text or "")
        if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
            return await msg.answer(t(lang, "time_bad"))
        field = state.split(":", 1)[1] + "_time"
        user = await db.update_user(user["id"], **{field: f"{int(m.group(1)):02d}:{m.group(2)}"})
        await db.set_state(user["id"], None)
        await msg.answer(t(lang, "saved"))
        return await show_times(msg, user)
    if not user["channel_id"] or not (user["gemini_key"] or user["groq_key"]):
        await msg.answer(t(lang, "need_setup"))
        return await next_step(msg, user)

    action = menu_action(msg.text)
    if action:
        if state and state not in ONBOARDING:
            await db.set_state(user["id"], None)
            user = await db.get_user(user["id"])
        return await on_menu(msg, bot, user, action)

    lock = _locks.setdefault(user["id"], asyncio.Lock())
    if lock.locked():
        return await msg.answer(t(lang, "busy"))
    async with lock:
        text = await read_input(msg, bot, user)
        if not text:
            return
        if state == "ask_about" or state == "remember":
            return await learn(msg, user, text)
        if state.startswith("edit:"):
            return await apply_edit(msg, bot, user, int(state.split(":")[1]), text)
        await smart_input(msg, bot, user, text)


# ---------------------------------------------------------------------------
# Chat mode: every free message is routed by the AI
# ---------------------------------------------------------------------------
async def _day_context(user):
    today = planner.local_now(user).date()
    t_row = await db.plan_for(user["id"], today)
    m_row = await db.plan_for(user["id"], today + dt.timedelta(days=1))
    t_done = {r["idx"]: r["done"] for r in await db.plan_tasks(t_row["id"])} if t_row else {}
    return today, t_row, t_done, m_row


async def smart_input(msg: Message, bot: Bot, user, text: str):
    lang = user["lang"]
    status = await msg.answer(t(lang, "thinking"))
    today, t_row, t_done, m_row = await _day_context(user)
    try:
        r = await planner.route(user, text, t_row["data"] if t_row else None, t_done,
                                m_row["data"] if m_row else None)
    except AIError as e:
        return await status.edit_text(t(lang, f"err_{e.reason}"))
    intent = r["intent"]
    reply = html.escape(str(r.get("reply") or ""))[:900]
    try:
        day = dt.date.fromisoformat(str(r.get("date"))[:10])
    except ValueError:
        day = None
    log.info("route %s → %s (%s)", user["id"], intent, day)

    if intent in ("plan", "add", "edit"):
        target = day or (today + dt.timedelta(days=1))
        row = t_row if target == today else m_row if target == today + dt.timedelta(days=1) else \
            await db.plan_for(user["id"], target)
        if not row:
            await safe_delete(status)
            return await create_plan(msg, user, text)
        if intent == "plan":
            await db.set_state(user["id"], user["state"], dict(user["state_data"] or {}, pending=text))
            await safe_delete(status)
            return await msg.answer(t(lang, "plan_exists", date=date_long(lang, row["plan_date"])), reply_markup=kb(
                [(t(lang, "btn_add"), f"pa:add:{row['id']}")], [(t(lang, "btn_replace"), "pa:replace:0")]))
        await safe_delete(status)
        if intent == "add":
            return await apply_add(msg, bot, user, row, text)
        return await apply_edit(msg, bot, user, row["id"], text)

    if intent == "done":
        ids = [int(i) for i in r.get("task_ids") or [] if str(i).lstrip("-").isdigit()]
        target = day or today
        row = t_row if target == today else m_row if target == today + dt.timedelta(days=1) else \
            await db.plan_for(user["id"], target)
        row = row if row and row["status"] == "posted" else None
        if not row or not ids:
            return await status.edit_text(t(lang, "done_none"))
        await db.set_done(row["id"], ids)
        titles = [tk["title"] for tk in row["data"]["tasks"] if tk["idx"] in ids]
        await refresh_post(bot, user, row["id"])
        return await status.edit_text(t(lang, "done_ok", items=html.escape(", ".join(titles))))

    if intent == "remind":
        at = planner.local_to_utc(user, str(r.get("remind_at") or ""))
        rtext = str(r.get("remind_text") or text)[:300]
        if not at or at < dt.datetime.now(dt.timezone.utc):
            return await status.edit_text(t(lang, "remind_bad"))
        await db.add_job(user["id"], "custom", at, rtext)
        when = at.astimezone(planner.tzinfo(user))
        return await status.edit_text(t(lang, "remind_ok", when=f"{date_long(lang, when.date())} {when:%H:%M}",
                                        text=html.escape(rtext)))

    if intent in ("habit", "goal") and isinstance(r.get("memory"), dict) and r["memory"].get("value"):
        mem = dict(r["memory"], category=intent)
        mem["key"] = mem.get("key") or f"{intent}_{int(dt.datetime.now().timestamp())}"
        await db.save_memory(user["id"], [mem], [])
        return await status.edit_text(t(lang, f"{intent}_ok", v=html.escape(str(mem["value"]))))

    await status.edit_text(reply or t(lang, "menu_hint"))


async def create_plan(msg: Message, user, text: str):
    lang = user["lang"]
    status = await msg.answer(t(lang, "thinking"))
    try:
        plan, learned, ai = await planner.make_plan(user, text)
    except AIError as e:
        return await status.edit_text(t(lang, f"err_{e.reason}"))
    if not plan["tasks"]:
        return await status.edit_text(t(lang, "no_tasks"))
    await status.edit_text(t(lang, "designing"))
    theme = user_theme(user, dt.date.fromisoformat(plan["date"]))
    plan_id = await db.create_draft(user["id"], dt.date.fromisoformat(plan["date"]), plan, theme)
    log.info("plan %s for %s via %s", plan_id, user["id"], ai.used)
    await send_preview(msg, user, plan_id, plan, theme, learned)
    await safe_delete(status)


async def save_change(msg: Message, bot: Bot, user, row, plan: dict, ok_text: str):
    """Persist a changed plan: drafts get a new preview, posted plans update the channel in place."""
    date = dt.date.fromisoformat(plan["date"])
    if row["status"] == "draft":
        await db.update_plan(row["id"], data=plan, plan_date=date)
        return await send_preview(msg, user, row["id"], plan, row["theme"])
    done = {r["idx"]: r["done"] for r in await db.plan_tasks(row["id"])}
    jobs = [j for j in planner.schedule(user, plan) if not done.get(j[1])]
    await db.update_posted(row["id"], user["id"], date, plan, jobs)
    img = await refresh_post(bot, user, row["id"])
    tasks = await db.plan_tasks(row["id"])
    if img:
        await msg.answer_photo(BufferedInputFile(img, "plan.jpg"), caption=ok_text,
                               reply_markup=checklist(row["id"], tasks))


async def apply_add(msg: Message, bot: Bot, user, row, text: str):
    lang = user["lang"]
    status = await msg.answer(t(lang, "thinking"))
    try:
        plan = await planner.add_to_plan(user, row["data"], text)
    except AIError as e:
        return await status.edit_text(t(lang, f"err_{e.reason}"))
    n = len(plan["tasks"]) - len(row["data"]["tasks"])
    if n <= 0:
        return await status.edit_text(t(lang, "nothing_added"))
    await safe_delete(status)
    await save_change(msg, bot, user, row, plan,
                      t(lang, "added_ok" if row["status"] == "posted" else "added_draft", n=n))


async def apply_edit(msg: Message, bot: Bot, user, plan_id: int, instruction: str):
    lang = user["lang"]
    row = await db.get_plan(plan_id)
    await db.set_state(user["id"], None)
    if not row or row["user_id"] != user["id"] or row["status"] not in ("draft", "posted"):
        return await msg.answer(t(lang, "expired"))
    status = await msg.answer(t(lang, "thinking"))
    try:
        plan, _ = await planner.edit_plan(user, row["data"], instruction)
    except AIError as e:
        return await status.edit_text(t(lang, f"err_{e.reason}"))
    if not plan["tasks"]:
        return await status.edit_text(t(lang, "no_tasks"))
    plan = planner.reconcile(dict(row["data"], _posted=row["status"] == "posted"), plan)
    await safe_delete(status)
    await save_change(msg, bot, user, row, plan, t(lang, "edited_ok"))


@router.callback_query(F.data.startswith("pa:"))
async def cb_pending(cq: CallbackQuery, bot: Bot):
    _, action, pid = cq.data.split(":")
    user = await db.get_user(cq.from_user.id)
    data = dict(user["state_data"] or {})
    text = data.pop("pending", None)
    await db.set_state(user["id"], user["state"], data)
    await cq.answer()
    await cq.message.edit_reply_markup(reply_markup=None)
    if not text:
        return await cq.message.answer(t(user["lang"], "expired"))
    if action == "replace":
        return await create_plan(cq.message, user, text)
    row = await db.get_plan(int(pid))
    if row:
        await apply_add(cq.message, bot, user, row, text)


async def learn(msg: Message, user, text: str):
    lang = user["lang"]
    onboarding = user["state"] == "ask_about"
    await db.set_state(user["id"], None)
    try:
        items = await planner.learn_about(user, text)
    except AIError as e:
        items = []
        await msg.answer(t(lang, f"err_{e.reason}"))
    if not items and user["state"] == "remember":
        await db.save_memory(user["id"], [{"key": f"note_{int(dt.datetime.now().timestamp())}",
                                           "value": text[:300], "category": "other"}], [])
        items = [{"value": text[:300]}]
    if items:
        lines = "\n".join(f"• {html.escape(str(i.get('value', '')))}" for i in items)
        await msg.answer(t(lang, "learned", items=lines))
    else:
        await msg.answer(t(lang, "nothing_learned"))
    if onboarding:
        await show_menu(msg, user, t(lang, "ready"))


@router.callback_query(F.data.startswith("p:"))
async def cb_preview(cq: CallbackQuery, bot: Bot):
    _, action, pid = cq.data.split(":")
    user = await db.get_user(cq.from_user.id)
    row = await db.get_plan(int(pid))
    lang = user["lang"]
    if not row or row["user_id"] != user["id"] or row["status"] != "draft":
        await cq.answer(t(lang, "expired"), show_alert=True)
        return await cq.message.edit_reply_markup(reply_markup=None)
    plan = row["data"]

    if action == "theme":
        await cq.answer()
        theme = (row["theme"] + 1) % N_THEMES
        await db.update_plan(row["id"], theme=theme)
        img = await asyncio.to_thread(render_day, plan, lang, theme)
        await cq.message.edit_media(
            InputMediaPhoto(media=BufferedInputFile(img, "preview.jpg"), caption=preview_caption(user, plan, theme)),
            reply_markup=preview_kb(user, row["id"]))
    elif action == "edit":
        await cq.answer()
        await db.set_state(user["id"], f"edit:{row['id']}")
        await cq.message.answer(t(lang, "ask_edit"))
    elif action == "cancel":
        await cq.answer(t(lang, "cancelled"))
        await db.update_plan(row["id"], status="cancelled")
        await cq.message.edit_reply_markup(reply_markup=None)
    elif action == "post":
        await cq.answer()
        try:
            msg_id = await post_plan(bot, user, row["id"], plan, row["theme"])
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            log.warning("post failed for %s: %s", user["id"], e)
            return await cq.message.answer(t(lang, "err_post"))
        jobs = planner.schedule(user, plan)
        replaced = await db.publish_plan(row["id"], user["id"], row["plan_date"], plan["tasks"], msg_id, jobs)
        for old in replaced:
            try:
                await bot.delete_message(user["channel_id"], old)
            except (TelegramBadRequest, TelegramForbiddenError):
                pass
        data = dict(user["state_data"] or {})
        if data.pop("carry", None) is not None:
            await db.set_state(user["id"], user["state"], data)
        await cq.message.edit_reply_markup(reply_markup=None)
        await cq.message.answer(t(lang, "posted", jobs=len(jobs)), reply_markup=main_menu(lang))


# ---------------------------------------------------------------------------
# Checklist (works in the channel and in DM copies)
# ---------------------------------------------------------------------------
@router.callback_query(F.data.startswith("t:"))
async def cb_tick(cq: CallbackQuery, bot: Bot):
    _, pid, idx = cq.data.split(":")
    row = await db.get_plan(int(pid))
    if not row:
        return await cq.answer()
    user = await db.get_user(row["user_id"])
    lang = user["lang"]
    if cq.from_user.id != row["user_id"]:
        return await cq.answer(t(lang, "not_owner"), show_alert=True)
    done = await db.toggle_task(row["id"], int(idx))
    if done is None:
        return await cq.answer()
    tasks = await db.plan_tasks(row["id"])
    cap, markup = caption(row["data"], tasks, lang), checklist(row["id"], tasks)
    targets = {(cq.message.chat.id, cq.message.message_id)} if cq.message else set()
    if row["channel_msg_id"] and row["status"] == "posted":
        targets.add((user["channel_id"], row["channel_msg_id"]))
    for chat_id, mid in targets:
        try:
            await bot.edit_message_caption(chat_id=chat_id, message_id=mid, caption=cap, reply_markup=markup)
        except (TelegramBadRequest, TelegramForbiddenError):
            pass
    all_done = all(tk["done"] for tk in tasks)
    await cq.answer(t(lang, "all_done") if all_done and done else t(lang, "ticked" if done else "unticked"),
                    show_alert=bool(all_done and done))


@router.callback_query(F.data.startswith("rk:") | F.data.startswith("sn:"))
async def cb_reminder_action(cq: CallbackQuery, bot: Bot):
    """Buttons under a task reminder: mark done, or snooze 15 minutes."""
    kind, pid, idx = cq.data.split(":")
    user = await db.get_user(cq.from_user.id)
    row = await db.get_plan(int(pid))
    if not row or row["user_id"] != user["id"]:
        return await cq.answer()
    await cq.message.edit_reply_markup(reply_markup=None)
    if kind == "rk":
        await db.set_done(row["id"], [int(idx)])
        await refresh_post(bot, user, row["id"])
        return await cq.answer(t(user["lang"], "ticked"))
    title = next((tk["title"] for tk in row["data"]["tasks"] if tk["idx"] == int(idx)), "")
    await db.add_job(user["id"], "custom", dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=15), title)
    await cq.answer(t(user["lang"], "snoozed"))


@router.callback_query(F.data == "carry")
async def cb_carry(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    today = planner.local_now(user).date()
    row = await db.posted_plan(user["id"], today)
    left = [tk["title"] for tk in await db.plan_tasks(row["id"]) if not tk["done"]] if row else []
    data = dict(user["state_data"] or {}, carry=left)
    await db.set_state(user["id"], user["state"], data)
    await cq.message.edit_reply_markup(reply_markup=None)
    await cq.answer()
    await cq.message.answer(t(user["lang"], "carry_ok", n=len(left)))


@router.callback_query(F.data == "repeat")
async def cb_repeat(cq: CallbackQuery):
    """Copy today's plan to tomorrow as a fresh draft."""
    user = await db.get_user(cq.from_user.id)
    await cq.answer()
    today = planner.local_now(user).date()
    row = await db.plan_for(user["id"], today)
    if not row:
        return await cq.message.answer(t(user["lang"], "no_today_plan"))
    tomorrow = today + dt.timedelta(days=1)
    tasks = [{k: v for k, v in tk.items() if k not in ("added", "done")} for tk in row["data"]["tasks"]]
    plan = planner.normalize(dict(row["data"], date=tomorrow.isoformat(), tasks=tasks), tomorrow)
    theme = user_theme(user, tomorrow)
    pid = await db.create_draft(user["id"], tomorrow, plan, theme)
    await cq.message.answer(t(user["lang"], "repeat_ok"))
    await send_preview(cq.message, user, pid, plan, theme)


async def show_plan(msg: Message, user, row):
    """A plan in DM: posted plans with their checklist, drafts with the preview buttons."""
    if row["status"] == "draft":
        return await send_preview(msg, user, row["id"], row["data"], row["theme"])
    tasks = await db.plan_tasks(row["id"])
    view = planner.with_done(row["data"], tasks)
    img = await asyncio.to_thread(render_day, view, user["lang"], row["theme"])
    await msg.answer_photo(BufferedInputFile(img, "plan.jpg"), caption=caption(row["data"], tasks, user["lang"]),
                           reply_markup=checklist(row["id"], tasks))


@router.message(Command("today"))
async def cmd_today(msg: Message):
    user = await db.get_user(msg.from_user.id)
    if not user:
        return await cmd_start(msg)
    row = await db.plan_for(user["id"], planner.local_now(user).date())
    if not row:
        return await msg.answer(t(user["lang"], "today_none"))
    await show_plan(msg, user, row)


# ---------------------------------------------------------------------------
# Menu: tomorrow, reminders, focus, goals
# ---------------------------------------------------------------------------
def plan_start_kb(lang: str) -> InlineKeyboardMarkup:
    return kb([(t(lang, "btn_repeat"), "repeat")], [(t(lang, "btn_carry2"), "carry")])


async def on_menu(msg: Message, bot: Bot, user, action: str):
    lang = user["lang"]
    if action == "m_plan":
        return await msg.answer(t(lang, "plan_prompt"), reply_markup=plan_start_kb(lang))
    if action == "m_today":
        return await cmd_today(msg)
    if action == "m_tomorrow":
        row = await db.plan_for(user["id"], planner.local_now(user).date() + dt.timedelta(days=1))
        if not row:
            return await msg.answer(t(lang, "tomorrow_none"), reply_markup=plan_start_kb(lang))
        return await show_plan(msg, user, row)
    if action == "m_remind":
        text, markup = await reminders_view(user)
        return await msg.answer(text, reply_markup=markup)
    if action == "m_focus":
        return await msg.answer(t(lang, "focus_pick"), reply_markup=kb(
            [("25", "fo:25"), ("50", "fo:50"), ("90", "fo:90")]))
    if action == "m_report":
        return await cmd_report(msg)
    if action == "m_goals":
        text, markup = await goals_view(user)
        return await msg.answer(text, reply_markup=markup)
    if action == "m_settings":
        return await show_settings(msg, user)


async def reminders_view(user):
    lang = user["lang"]
    tz = planner.tzinfo(user)
    lines = [t(lang, "reminders_title"), ""]
    lines.append(t(lang, "reminders_auto", m=user["remind_before"]) if user["reminders"] else "🔕")
    rows = []
    jobs = await db.pending_reminders(user["id"])
    if not jobs:
        lines.append("\n" + t(lang, "reminders_empty"))
    for i, j in enumerate(jobs):
        when = j["run_at"].astimezone(tz)
        icon, label = ("🍅", f"{j['text']} min") if j["kind"] == "focus" else ("⏰", j["text"] or "")
        lines.append(f"{i + 1}. {icon} <b>{date_long(lang, when.date())} {when:%H:%M}</b> — {html.escape(label)}")
        rows.append((f"🗑 {i + 1}", f"rd:{j['id']}"))
    return "\n".join(lines)[:4000], kb(*[rows[i:i + 5] for i in range(0, len(rows), 5)]) if rows else None


@router.callback_query(F.data.startswith("rd:"))
async def cb_reminder_delete(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    await db.delete_job(user["id"], int(cq.data.split(":")[1]))
    await cq.answer(t(user["lang"], "reminder_deleted"))
    text, markup = await reminders_view(user)
    await cq.message.edit_text(text, reply_markup=markup)


@router.callback_query(F.data.startswith("fo:"))
async def cb_focus(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    minutes = int(cq.data.split(":")[1])
    end = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=minutes)
    job_id = await db.add_job(user["id"], "focus", end, str(minutes))
    await cq.answer()
    local_end = end.astimezone(planner.tzinfo(user))
    await cq.message.answer(t(user["lang"], "focus_started", m=minutes, end=f"{local_end:%H:%M}"),
                            reply_markup=kb([(t(user["lang"], "btn_cancel_focus"), f"fs:{job_id}")]))


@router.callback_query(F.data.startswith("fs:"))
async def cb_focus_stop(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    await db.delete_job(user["id"], int(cq.data.split(":")[1]))
    await cq.answer(t(user["lang"], "cancelled"))
    await cq.message.edit_reply_markup(reply_markup=None)


async def goals_view(user):
    lang = user["lang"]
    rows = await db.get_memory(user["id"])
    goals = [r for r in rows if r["category"] == "goal"]
    habits = [r for r in rows if r["category"] == "habit"]
    if not goals and not habits:
        return f"{t(lang, 'goals_title')}\n\n{t(lang, 'goals_empty')}", None
    lines, buttons, n = [], [], 0
    for title, items, icon in ((t(lang, "goals_title"), goals, "🎯"), (t(lang, "habits_title"), habits, "🔁")):
        if not items:
            continue
        lines += ["", title]
        for r in items:
            n += 1
            lines.append(f"{n}. {html.escape(r['value'])}")
            buttons.append((f"🗑 {icon}{n}", f"gd:{r['key'][:50]}"))
    return "\n".join(lines).strip()[:4000], kb(*[buttons[i:i + 4] for i in range(0, len(buttons), 4)])


@router.callback_query(F.data.startswith("gd:"))
async def cb_goal_delete(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    await db.delete_memory(user["id"], cq.data.split(":", 1)[1])
    await cq.answer(t(user["lang"], "memory_deleted"))
    text, markup = await goals_view(user)
    await cq.message.edit_text(text, reply_markup=markup)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
@router.message(Command("report"))
async def cmd_report(msg: Message):
    user = await db.get_user(msg.from_user.id)
    if not user:
        return await cmd_start(msg)
    lang = user["lang"]
    await msg.answer(t(lang, "report_pick"), reply_markup=kb(
        [(t(lang, "btn_week"), "r:week"), (t(lang, "btn_lastweek"), "r:lastweek")],
        [(t(lang, "btn_month"), "r:month")]))


@router.callback_query(F.data.startswith("r:"))
async def cb_report(cq: CallbackQuery):
    kind = cq.data.split(":")[1]
    user = await db.get_user(cq.from_user.id)
    await cq.answer()
    status = await cq.message.answer(t(user["lang"], "designing"))
    img, pct, title = await reports.build(user, kind)
    await status.delete()
    await cq.message.answer_photo(
        BufferedInputFile(img, "report.jpg"), caption=t(user["lang"], "report_caption", title=title, pct=pct),
        reply_markup=kb([(t(user["lang"], "btn_share"), "share")]))


@router.callback_query(F.data == "share")
async def cb_share(cq: CallbackQuery, bot: Bot):
    user = await db.get_user(cq.from_user.id)
    try:
        await bot.copy_message(user["channel_id"], cq.message.chat.id, cq.message.message_id)
        await cq.message.edit_reply_markup(reply_markup=None)
        await cq.answer(t(user["lang"], "shared"))
    except (TelegramBadRequest, TelegramForbiddenError):
        await cq.answer(t(user["lang"], "err_post"), show_alert=True)


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------
async def memory_view(user):
    rows = await db.get_memory(user["id"])
    lang = user["lang"]
    if not rows:
        return t(lang, "memory_empty"), None
    lines = [t(lang, "memory_title"), ""]
    buttons = []
    for i, r in enumerate(rows):
        lines.append(f"{i + 1}. <b>{html.escape(r['category'])}</b> · {html.escape(r['value'])}")
        buttons.append((f"🗑 {i + 1}", f"md:{i}"))
    rows_kb = [buttons[i:i + 5] for i in range(0, len(buttons), 5)]
    return "\n".join(lines)[:4000], kb(*rows_kb)


@router.message(Command("memory"))
async def cmd_memory(msg: Message):
    user = await db.get_user(msg.from_user.id)
    if not user:
        return await cmd_start(msg)
    text, markup = await memory_view(user)
    await msg.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("md:"))
async def cb_memory_delete(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    rows = await db.get_memory(user["id"])
    i = int(cq.data.split(":")[1])
    if i < len(rows):
        await db.delete_memory(user["id"], rows[i]["key"])
    await cq.answer(t(user["lang"], "memory_deleted"))
    text, markup = await memory_view(user)
    await cq.message.edit_text(text, reply_markup=markup)


@router.message(Command("remember"))
async def cmd_remember(msg: Message, command: CommandObject):
    user = await db.get_user(msg.from_user.id)
    if not user:
        return await cmd_start(msg)
    if command.args:
        await db.set_state(user["id"], "remember")
        return await learn(msg, await db.get_user(user["id"]), command.args)
    await db.set_state(user["id"], "remember")
    await msg.answer(t(user["lang"], "ask_about"))


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
def onoff(user, field) -> str:
    return "✅" if user[field] else "▫️"


async def show_settings(msg: Message, user, edit: bool = False):
    lang = user["lang"]
    remind = t(lang, "min_before", v=user["remind_before"]) if user["reminders"] else t(lang, "off")
    text = t(lang, "settings", language=LANGS[lang], channel=html.escape(user["channel_title"] or t(lang, "none")),
             tz=user["tz"], gemini=mask(decrypt(user["gemini_key"])), groq=mask(decrypt(user["groq_key"])),
             morning=user["morning_time"], evening=user["evening_time"], remind=remind, theme=theme_name(user))
    markup = kb([(t(lang, "s_lang"), "s:lang"), (t(lang, "s_keys"), "s:keys")],
                [(t(lang, "s_channel"), "s:channel"), (t(lang, "s_tz"), "s:tz")],
                [(t(lang, "s_times"), "s:times"), (t(lang, "s_notify"), "s:notify")],
                [(t(lang, "s_theme"), "s:theme")])
    if edit:
        try:
            return await msg.edit_text(text, reply_markup=markup)
        except TelegramBadRequest:
            pass
    await msg.answer(text, reply_markup=markup)


async def show_times(msg: Message, user, edit: bool = False):
    lang = user["lang"]
    markup = kb([(t(lang, "t_morning", v=user["morning_time"]), "st:morning")],
                [(t(lang, "t_evening", v=user["evening_time"]), "st:evening")],
                [(t(lang, "s_back"), "s:main")])
    text = t(lang, "s_times")
    if edit:
        return await msg.edit_text(text, reply_markup=markup)
    await msg.answer(text, reply_markup=markup)


def notify_kb(user) -> InlineKeyboardMarkup:
    lang = user["lang"]
    return kb([(f"{onoff(user, 'reminders')} {t(lang, 'n_remind')}", "n:reminders")],
              [(t(lang, "n_before", v=user["remind_before"]), "n:before")],
              [(f"{onoff(user, 'task_cards')} {t(lang, 'n_cards')}", "n:task_cards")],
              [(f"{onoff(user, 'morning_post')} {t(lang, 'n_morning')}", "n:morning_post"),
               (f"{onoff(user, 'evening_post')} {t(lang, 'n_evening')}", "n:evening_post")],
              [(f"{onoff(user, 'weekly_report')} {t(lang, 'n_weekly')}", "n:weekly_report"),
               (f"{onoff(user, 'monthly_report')} {t(lang, 'n_monthly')}", "n:monthly_report")],
              [(t(lang, "s_back"), "s:main")])


def theme_kb(user) -> InlineKeyboardMarkup:
    lang = user["lang"]
    mark = lambda i: "● " if user["theme_mode"] == i else ""  # noqa: E731
    rows = [[(mark(-1) + t(lang, "theme_rotate"), "th:-1")]]
    names = [(f"{mark(i)}{i + 1}. {p.name}", f"th:{i}") for i, p in enumerate(PALETTES)]
    rows += [names[i:i + 2] for i in range(0, len(names), 2)]
    rows.append([(t(lang, "s_back"), "s:main")])
    return kb(*rows)


@router.message(Command("settings"))
async def cmd_settings(msg: Message):
    user = await db.get_user(msg.from_user.id)
    if not user:
        return await cmd_start(msg)
    await db.set_state(user["id"], None)
    await show_settings(msg, user)


@router.callback_query(F.data.startswith("s:"))
async def cb_settings(cq: CallbackQuery):
    page = cq.data.split(":")[1]
    user = await db.get_user(cq.from_user.id)
    lang = user["lang"]
    await cq.answer()
    if page == "main":
        await show_settings(cq.message, user, edit=True)
    elif page == "lang":
        await cq.message.edit_text(t(lang, "choose_lang"), reply_markup=kb([(v, f"lang:{k}") for k, v in LANGS.items()]))
    elif page == "keys":
        await keys_page(cq.message, user, edit=True)
    elif page == "channel":
        await db.set_state(user["id"], "ask_channel")
        await ask_channel(cq.message, lang)
    elif page == "tz":
        await db.set_state(user["id"], "ask_tz")
        await ask_tz(cq.message, lang)
    elif page == "times":
        await show_times(cq.message, user, edit=True)
    elif page == "notify":
        await cq.message.edit_text(t(lang, "s_notify"), reply_markup=notify_kb(user))
    elif page == "theme":
        await cq.message.edit_text(t(lang, "theme_pick"), reply_markup=theme_kb(user))


async def keys_page(msg: Message, user, edit: bool):
    lang = user["lang"]
    rows = [[(t(lang, "k_gemini"), "sk:gemini")], [(t(lang, "k_groq"), "sk:groq")]]
    if user["groq_key"] and user["gemini_key"]:
        rows.append([(t(lang, "k_groq_del"), "sk:groq_del")])
    rows += [[(t(lang, "btn_howto") + " · Gemini", "kh:gemini:howto:0")],
             [(t(lang, "btn_howto") + " · Groq", "kh:groq:howto:0")],
             [(t(lang, "s_back"), "s:main")]]
    text = (f"{t(lang, 's_keys')}\n\nGemini: <code>{mask(decrypt(user['gemini_key']))}</code>\n"
            f"Groq: <code>{mask(decrypt(user['groq_key']))}</code>")
    if edit:
        return await msg.edit_text(text, reply_markup=kb(*rows))
    await msg.answer(text, reply_markup=kb(*rows))


@router.message(Command("keys"))
async def cmd_keys(msg: Message):
    user = await db.get_user(msg.from_user.id)
    if not user:
        return await cmd_start(msg)
    await keys_page(msg, user, edit=False)


@router.callback_query(F.data.startswith("sk:"))
async def cb_keys(cq: CallbackQuery):
    what = cq.data.split(":")[1]
    user = await db.get_user(cq.from_user.id)
    await cq.answer()
    if what == "groq_del":
        user = await db.update_user(user["id"], groq_key=None)
        return await show_settings(cq.message, user, edit=True)
    await db.set_state(user["id"], f"set_key:{what}")
    await ask_key(cq.message, user["lang"], what, skip=False)


@router.callback_query(F.data.startswith("st:"))
async def cb_time(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    await db.set_state(user["id"], f"set_time:{cq.data.split(':')[1]}")
    await cq.answer()
    await cq.message.answer(t(user["lang"], "ask_time"))


@router.callback_query(F.data.startswith("n:"))
async def cb_notify(cq: CallbackQuery):
    field = cq.data.split(":")[1]
    user = await db.get_user(cq.from_user.id)
    if field == "before":
        steps = [5, 10, 15, 30, 60]
        cur = user["remind_before"]
        user = await db.update_user(user["id"], remind_before=steps[(steps.index(cur) + 1) % len(steps)]
                                    if cur in steps else 10)
    else:
        user = await db.update_user(user["id"], **{field: not user[field]})
    await cq.answer(t(user["lang"], "saved"))
    await cq.message.edit_reply_markup(reply_markup=notify_kb(user))


@router.callback_query(F.data.startswith("th:"))
async def cb_theme(cq: CallbackQuery):
    user = await db.update_user(cq.from_user.id, theme_mode=int(cq.data.split(":")[1]))
    await cq.answer(t(user["lang"], "saved"))
    await cq.message.edit_reply_markup(reply_markup=theme_kb(user))


@router.message(Command("templates"))
async def cmd_templates(msg: Message):
    user = await db.get_user(msg.from_user.id)
    if not user:
        return await cmd_start(msg)
    row = await db.latest_plan(user["id"])
    plan = row["data"] if row else SAMPLE
    imgs = await asyncio.gather(*[asyncio.to_thread(render_day, plan, user["lang"], i) for i in range(N_THEMES)])
    media = [InputMediaPhoto(media=BufferedInputFile(img, f"t{i}.jpg"), caption=f"{i + 1}. {PALETTES[i].name}")
             for i, img in enumerate(imgs)]
    await msg.answer_media_group(media)
    await msg.answer(t(user["lang"], "theme_pick"), reply_markup=theme_kb(user))


@router.message(Command("help"))
async def cmd_help(msg: Message):
    user = await db.get_user(msg.from_user.id)
    if user and user["channel_id"]:
        return await show_menu(msg, user, t(user["lang"], "help"))
    await msg.answer(t(user["lang"] if user else "uz", "help"))


@router.message(Command("cancel"))
async def cmd_cancel(msg: Message):
    user = await db.get_user(msg.from_user.id)
    if user:
        await db.set_state(user["id"], None)
        if user["channel_id"]:
            return await show_menu(msg, user, t(user["lang"], "cancelled"))
        await msg.answer(t(user["lang"], "cancelled"), reply_markup=ReplyKeyboardRemove())
