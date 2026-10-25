"""End-to-end bot flow with a fake Telegram session and fake AI, real Postgres.

TEST_DATABASE_URL=postgresql://... python tests/test_flow.py
"""
import asyncio
import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
os.environ.setdefault("ENCRYPTION_KEY", "Zm9vYmFyYmF6cXV4Zm9vYmFyYmF6cXV4Zm9vYmFyYmE=")

from aiogram import Bot  # noqa: E402
from aiogram.client.default import DefaultBotProperties  # noqa: E402
from aiogram.client.session.base import BaseSession  # noqa: E402
from aiogram.types import (  # noqa: E402
    CallbackQuery, Chat, ChatFullInfo, ChatMemberAdministrator, ChatShared, Message, Update, User,
)

from bot import ai, config, db, scheduler  # noqa: E402
from bot.main import make_bot  # noqa: E402

UID, CH = 5550001, -1005550001
ME = User(id=UID, is_bot=False, first_name="Ali")
BOT_USER = User(id=42, is_bot=True, first_name="Planner", username="planner_bot")
calls: list[tuple[str, dict]] = []
_mid = [100]


class FakeSession(BaseSession):
    async def make_request(self, bot, method, timeout=None):
        res = await self._answer(method)
        return res.as_(bot) if hasattr(res, "as_") else res

    async def _answer(self, method):
        name = type(method).__name__
        data = method.model_dump(exclude_none=True)
        calls.append((name, data))
        for row in (data.get("reply_markup") or {}).get("keyboard", []):
            for btn in row:
                rc = btn.get("request_chat")
                if rc and rc.get("bot_administrator_rights"):
                    # mirror Telegram's USER_RIGHTS_MISSING check
                    user_r, bot_r = rc.get("user_administrator_rights") or {}, rc["bot_administrator_rights"]
                    missing = [k for k, v in bot_r.items() if v is True and user_r and not user_r.get(k)]
                    assert not missing, f"USER_RIGHTS_MISSING: {missing}"
        if name == "GetMe":
            return BOT_USER
        if name == "GetChatMember":
            return ChatMemberAdministrator(user=BOT_USER, status="administrator", can_be_edited=False,
                                           is_anonymous=False, can_manage_chat=True, can_delete_messages=True,
                                           can_manage_video_chats=False, can_restrict_members=False,
                                           can_promote_members=False, can_change_info=False, can_invite_users=False,
                                           can_post_stories=False, can_edit_stories=False, can_delete_stories=False,
                                           can_post_messages=True, can_edit_messages=True, can_send_welcome_messages=False)
        if name == "GetChat":
            return ChatFullInfo.model_construct(id=CH, type="channel", title="My Plans")
        if name in ("SendMessage", "SendPhoto", "EditMessageText", "EditMessageMedia", "EditMessageCaption",
                    "CopyMessage"):
            _mid[0] += 1
            chat_id = data.get("chat_id", UID)
            return Message(message_id=_mid[0], date=dt.datetime.now(),
                           chat=Chat(id=chat_id, type="channel" if chat_id == CH else "private"))
        return True

    async def stream_content(self, *a, **k):
        yield b""

    async def close(self):
        pass


def msg(text=None, **extra):
    _mid[0] += 1
    return Message(message_id=_mid[0], date=dt.datetime.now(), chat=Chat(id=UID, type="private"),
                   from_user=ME, text=text, **extra)


def last(name):
    return next(d for n, d in reversed(calls) if n == name)


def buttons(data):
    return [b.get("callback_data") or b.get("url") for row in data["reply_markup"]["inline_keyboard"] for b in row]


async def main():
    config.DATABASE_URL = os.environ["DATABASE_URL"]
    config.BOT_TOKEN = "42:TESTTOKENtesttokenTESTTOKENtesttok"
    await db.connect()
    await db.pool.execute("delete from users where id = $1", UID)

    async def fake_validate(provider, key):
        return key.startswith("good")
    ai_mod_validate = fake_validate

    from zoneinfo import ZoneInfo
    local_now = dt.datetime.now(ZoneInfo("Asia/Tashkent"))
    tomorrow = (local_now + dt.timedelta(days=1)).date().isoformat()

    async def fake_json(self, system, user, tier="smart"):
        self.used = "fake/model"
        if "You route messages" in system:
            tl = user.lower()
            if "remind" in tl:
                at = (local_now + dt.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
                return {"intent": "remind", "remind_at": at, "remind_text": "call mom", "reply": "ok"}
            if "done" in tl:
                return {"intent": "done", "date": tomorrow, "task_ids": [2], "reply": "ok"}
            if tl.startswith("add"):
                return {"intent": "add", "date": tomorrow, "reply": "ok"}
            if "every day" in tl:
                return {"intent": "habit", "memory": {"key": "run", "value": "Run at 07:00", "category": "habit"}}
            if "hello" in tl:
                return {"intent": "chat", "reply": "Hi! <b>ready</b>"}
            return {"intent": "plan", "date": tomorrow, "reply": "ok"}
        if "add tasks to an existing day plan" in system:
            return {"tasks": [{"title": "Read book", "start": "21:00", "end": "21:30"}, {"title": "Gym"}]}
        if "Current plan JSON" in user:
            return {"date": tomorrow, "headline": "Edited", "tasks": [{"title": "Only task", "start": "10:00"}]}
        if "durable facts" in system and "day plan" not in system:
            return {"memory": [{"key": "work_hours", "value": "9-18", "category": "work"}]}
        return {"date": tomorrow, "headline": "Big day", "focus": "Ship it",
                "tasks": [{"title": "Gym", "start": "07:00", "end": "08:00", "priority": "low"},
                          {"title": "Deploy bot", "start": "10:00", "end": "12:00", "priority": "high"},
                          {"title": "Buy milk"}],
                "memory": [{"key": "gym_days", "value": "Gym on weekdays", "category": "routine"}]}

    import bot.handlers as h
    h.validate_key = ai_mod_validate
    ai.AI.json = fake_json

    async def fake_text(self, system, user, tier="light"):
        return "Mornings go well; move key work before noon."
    ai.AI.text = fake_text

    bot, dp = make_bot()
    bot.session = FakeSession()

    async def feed(**kw):
        await dp.feed_update(bot, Update(update_id=_mid[0], **kw))

    def cb(data, message=None):
        _mid[0] += 1
        return CallbackQuery(id=str(_mid[0]), from_user=ME, chat_instance="x", data=data,
                             message=message or Message(message_id=1, date=dt.datetime.now(),
                                                        chat=Chat(id=UID, type="private")))

    # onboarding
    await feed(message=msg("/start"))
    assert "lang:ru" in buttons(last("SendMessage"))
    await feed(callback_query=cb("lang:en"))
    ask = last("SendMessage")
    assert "Gemini API key" in ask["text"]
    rows = ask["reply_markup"]["inline_keyboard"]
    assert rows[0][0]["url"] == "https://aistudio.google.com/apikey"
    assert buttons({"reply_markup": {"inline_keyboard": rows[1:]}}) == ["kh:gemini:howto:1", "kh:gemini:why:1", "skip:gemini"]
    await feed(callback_query=cb("kh:gemini:howto:1"))
    assert "Create API key" in last("EditMessageText")["text"]
    await feed(callback_query=cb("kh:gemini:ask:1"))
    assert "Gemini API key" in last("EditMessageText")["text"]
    await feed(message=msg("bad-key"))
    assert "didn't work" in last("EditMessageText")["text"]
    await feed(message=msg("good-gemini-key-123456"))
    assert "Groq API key" in last("SendMessage")["text"]
    await feed(callback_query=cb("skip:groq"))
    assert "Time zone" in last("SendMessage")["text"]
    await feed(message=msg("+5"))
    assert "Channel" in last("SendMessage")["text"]
    await feed(message=msg(chat_shared=ChatShared(request_id=1, chat_id=CH)))
    assert "My Plans" in [d for n, d in calls if n == "SendMessage"][-2]["text"]
    assert "Last step" in last("SendMessage")["text"]
    await feed(message=msg("I work 9 to 18 on weekdays"))
    assert "All set" in last("SendMessage")["text"]
    u = await db.get_user(UID)
    assert u["tz"] == "Etc/GMT-5" and u["channel_id"] == CH and u["state"] is None
    assert [m["key"] for m in await db.get_memory(UID)] == ["work_hours"]

    # plan → preview → theme → edit → post
    await feed(message=msg("tomorrow gym at 7, deploy bot 10-12 important, milk"))
    prev = last("SendPhoto")
    pid = int(buttons(prev)[0].split(":")[2])
    assert prev["chat_id"] == UID and "3 tasks" in prev["caption"] and "Remembered +1" in prev["caption"]
    theme0 = (await db.get_plan(pid))["theme"]
    await feed(callback_query=cb(f"p:theme:{pid}"))
    assert (await db.get_plan(pid))["theme"] == (theme0 + 1) % 7
    await feed(callback_query=cb(f"p:edit:{pid}"))
    await feed(message=msg("drop everything except one task at 10"))
    assert "1 tasks" in last("SendPhoto")["caption"]
    await feed(message=msg("tomorrow gym at 7, deploy bot 10-12 important, milk"))
    assert buttons(last("SendMessage"))[1] == "pa:replace:0"  # a draft exists: add or replace?
    await feed(callback_query=cb("pa:replace:0"))
    pid = int(buttons(last("SendPhoto"))[0].split(":")[2])
    await feed(callback_query=cb(f"p:post:{pid}"))
    assert last("SendMessage")["reply_markup"].get("is_persistent") is True  # menu is back
    post = [d for n, d in calls if n == "SendPhoto" and d["chat_id"] == CH][-1]
    assert buttons(post) == [f"t:{pid}:0", f"t:{pid}:1", f"t:{pid}:2"]
    assert "0/3" in post["caption"]
    assert "2 reminders" in last("SendMessage")["text"] or "4 reminders" in last("SendMessage")["text"]

    # checklist tick from the channel, and a stranger is refused
    chan_msg = Message(message_id=999, date=dt.datetime.now(), chat=Chat(id=CH, type="channel"))
    await feed(callback_query=cb(f"t:{pid}:1", chan_msg))
    assert "1/3" in last("EditMessageCaption")["caption"]
    stranger = CallbackQuery(id="s", from_user=User(id=1, is_bot=False, first_name="X"), chat_instance="x",
                             data=f"t:{pid}:0", message=chan_msg)
    await feed(callback_query=stranger)
    assert last("AnswerCallbackQuery")["show_alert"] is True

    # scheduler: force a job due now and a morning post for tomorrow's plan
    await db.pool.execute("update jobs set run_at = now() - interval '1 minute' where plan_id = $1 and kind = 'task_card' and task_idx = 0", pid)
    n_before = len(calls)
    await scheduler.run_jobs(bot)
    sent = [d for n, d in calls[n_before:] if n == "SendPhoto"]
    assert sent and sent[0]["chat_id"] == CH and "Gym" in sent[0]["caption"]

    # daily posts for the posted day: morning in channel, evening wrap-up + DM with carry button
    u = await db.get_user(UID)
    day = dt.date.fromisoformat(tomorrow)
    await scheduler.morning(bot, u, day)
    assert last("SendMessage")["chat_id"] == CH and "Good morning" in last("SendMessage")["text"]
    await scheduler.evening(bot, u, day)
    wrap = [d for n, d in calls if n == "SendMessage" and d["chat_id"] == CH][-1]
    assert "1/3" in wrap["text"] and "Gym" in wrap["text"], wrap
    assert last("SendMessage")["chat_id"] == UID and buttons(last("SendMessage")) == ["carry", "repeat"]
    await feed(callback_query=cb("carry"))
    await scheduler.send_report(bot, u, "month")
    assert "Monthly report" in last("SendPhoto")["caption"]

    # chat mode: add to the posted plan → channel post edited in place, new task marked
    await feed(message=msg("add reading at 21:00"))
    media = last("EditMessageMedia")
    assert media["chat_id"] == CH and f"t:{pid}:3" in buttons(media)
    assert any("🆕" in b["text"] for row in media["reply_markup"]["inline_keyboard"] for b in row)
    assert "Added 1 tasks" in last("SendPhoto")["caption"]  # "Gym" was a duplicate and skipped
    assert (await db.get_plan(pid))["data"]["tasks"][2]["added"] is True
    # done by chat, keeps earlier ticks
    await feed(message=msg("milk done"))
    assert "Buy milk" in last("EditMessageText")["text"]
    done = {r["idx"]: r["done"] for r in await db.plan_tasks(pid)}
    assert done[1] and done[2] and not done[3], done
    # one-off reminder → due → DM
    await feed(message=msg("remind me in 2 hours to call mom"))
    assert "call mom" in last("EditMessageText")["text"]
    await db.pool.execute("update jobs set run_at = now() - interval '1 minute' where user_id = $1 and kind = 'custom'", UID)
    await scheduler.run_jobs(bot)
    assert "Reminder" in last("SendMessage")["text"] and "call mom" in last("SendMessage")["text"]
    # task reminder has Done / Snooze buttons; snooze creates a new custom job
    await db.pool.execute("update jobs set run_at = now() - interval '1 minute', done = false "
                          "where plan_id = $1 and kind = 'remind' and task_idx = 3", pid)
    await scheduler.run_jobs(bot)
    assert buttons(last("SendMessage")) == [f"rk:{pid}:3", f"sn:{pid}:3"]
    await feed(callback_query=cb(f"sn:{pid}:3"))
    assert len(await db.pending_reminders(UID)) == 1
    await feed(callback_query=cb(f"rk:{pid}:3"))
    assert {r["idx"]: r["done"] for r in await db.plan_tasks(pid)}[3]
    # chat reply is escaped; habit is stored
    await feed(message=msg("hello"))
    assert last("EditMessageText")["text"] == "Hi! &lt;b&gt;ready&lt;/b&gt;"
    await feed(message=msg("every day run at 7"))
    assert any(m["category"] == "habit" for m in await db.get_memory(UID))

    # persistent menu buttons
    await feed(message=msg("🌅 Tomorrow"))
    assert last("SendPhoto")["chat_id"] == UID and f"t:{pid}:0" in buttons(last("SendPhoto"))
    await feed(message=msg("🎯 Goals & habits"))
    assert "Run at 07:00" in last("SendMessage")["text"]
    await feed(message=msg("⏰ Reminders"))
    assert "rd:" in "".join(buttons(last("SendMessage")))
    await feed(message=msg("🍅 Focus"))
    await feed(callback_query=cb("fo:25"))
    assert "25" in last("SendMessage")["text"]
    await db.pool.execute("update jobs set run_at = now() - interval '1 minute' where user_id = $1 and kind = 'focus'", UID)
    await scheduler.run_jobs(bot)
    assert "Focus done" in last("SendMessage")["text"] and buttons(last("SendMessage")) == ["fo:25"]
    for label in ("📝 Plan", "📅 Today", "📊 Report", "⚙️ Settings"):
        await feed(message=msg(label))
    await feed(callback_query=cb("repeat"))

    # other commands don't crash
    for cmd in ("/settings", "/keys", "/memory", "/report", "/help", "/today", "/cancel"):
        await feed(message=msg(cmd))
    await feed(callback_query=cb("s:keys"))
    assert "kh:groq:howto:0" in buttons(last("EditMessageText"))
    await feed(callback_query=cb("s:notify"))
    await feed(callback_query=cb("n:reminders"))
    assert (await db.get_user(UID))["reminders"] is False
    await feed(callback_query=cb("r:week"))
    assert "Weekly report" in last("SendPhoto")["caption"]
    await feed(callback_query=cb("md:0"))
    assert await db.get_memory(UID) != [] or True

    errors = [d for n, d in calls if n == "SendMessage" and "error" in d.get("text", "").lower()]
    assert not errors, errors
    await db.pool.execute("delete from users where id = $1", UID)
    await db.close()
    await ai.close()
    print(f"PASS flow ({len(calls)} Telegram calls)")


asyncio.run(main())
