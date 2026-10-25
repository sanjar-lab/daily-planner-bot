"""Offline tests: normalization, time zones, scheduling, AI fallback chain (mock HTTP)."""
import asyncio
import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ENCRYPTION_KEY", "Zm9vYmFyYmF6cXV4Zm9vYmFyYmF6cXV4Zm9vYmFyYmE=")

from aiohttp import web  # noqa: E402

from bot import ai, config, crypto, planner  # noqa: E402
from bot.handlers import parse_tz  # noqa: E402


def test_normalize():
    raw = {"date": "2026-10-26", "headline": "Day", "tasks": [
        {"title": "B", "start": "14:00", "end": "15:00", "priority": "HIGH"},
        {"title": "", "start": "10:00"},
        {"title": "untimed", "start": None, "priority": "weird"},
        {"title": "A", "start": "9:05", "end": "bad"},
    ]}
    p = planner.normalize(raw, dt.date(2026, 10, 26))
    assert [t["title"] for t in p["tasks"]] == ["A", "B", "untimed"]
    assert p["tasks"][0]["start"] == "09:05" and p["tasks"][0]["end"] is None
    assert p["tasks"][1]["priority"] == "high" and p["tasks"][2]["priority"] == "medium"
    assert [t["idx"] for t in p["tasks"]] == [0, 1, 2]
    assert planner.normalize({"date": "1999-01-01"}, dt.date(2026, 10, 26))["date"] == "2026-10-26"


def test_tz():
    assert parse_tz("+5") == "Etc/GMT-5"
    assert parse_tz("UTC-3") == "Etc/GMT+3"
    assert parse_tz("Asia/Tashkent") == "Asia/Tashkent"
    assert parse_tz("nowhere") is None


def test_schedule():
    user = {"tz": "Asia/Tashkent", "reminders": True, "remind_before": 10, "task_cards": True}
    tomorrow = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).date().isoformat()
    plan = {"date": tomorrow, "tasks": [{"idx": 0, "start": "09:00"}, {"idx": 1, "start": None}]}
    jobs = planner.schedule(user, plan)
    assert [(k, i) for k, i, _ in jobs] == [("remind", 0), ("task_card", 0)]
    assert jobs[1][2].hour == 4  # 09:00 Tashkent == 04:00 UTC
    assert jobs[1][2] - jobs[0][2] == dt.timedelta(minutes=10)


def test_rank_models():
    names = ["gemini-2.5-flash", "gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite",
             "gemini-3-flash-preview", "gemini-3.1-flash-image", "gemini-flash-latest", "gemini-flash-lite-latest",
             "gemini-3.1-pro"]
    smart = ai.rank_models("gemini", names, "smart")
    assert smart[:3] == ["gemini-flash-latest", "gemini-3.8-flash", "gemini-3.5-flash"], smart
    assert "gemini-3.1-flash-image" not in smart and "gemini-3.1-pro" not in smart
    assert ai.rank_models("gemini", names, "light")[0] == "gemini-flash-lite-latest"
    groq = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "whisper-large-v3", "meta-llama/llama-prompt-guard-2-86m",
            "qwen/qwen3.8-27b"]
    assert ai.rank_models("groq", groq, "smart") == ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]
    assert ai._merge(["a", "b"], ["b", "c"]) == ["a", "b", "c"]


def test_webhook_secret():
    import re
    for raw in ("abc_DEF-123", "a+b/c==", ""):
        os.environ["WEBHOOK_SECRET"] = raw
        s = config._webhook_secret()
        assert re.fullmatch(r"[A-Za-z0-9_-]{1,256}", s), s
    os.environ["WEBHOOK_SECRET"] = "abc_DEF-123"
    assert config._webhook_secret() == "abc_DEF-123"


def test_crypto():
    assert crypto.decrypt(crypto.encrypt("secret-key-123")) == "secret-key-123"


async def _fallback():
    hits = []

    async def gemini(req):
        hits.append("gemini:" + req.match_info["m"])
        return web.json_response({"error": {"message": "quota"}}, status=429, headers={"retry-after": "30"})

    async def groq(req):
        body = await req.json()
        hits.append("groq:" + body["model"])
        return web.json_response({"choices": [{"message": {"content": '```json\n{"ok": true}\n```'}}]})

    app = web.Application()
    app.router.add_post("/gem/{m}", gemini)
    app.router.add_post("/groq/chat/completions", groq)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 8765)
    await site.start()
    ai.GEMINI_URL, ai.GROQ_URL = "http://127.0.0.1:8765/gem", "http://127.0.0.1:8765/groq"
    try:
        out = await ai.AI("g-key", "q-key").json("sys json", "user")
        assert out == {"ok": True}, out
        first = list(hits)
        # second call: gemini models are on cooldown, so it goes straight to groq
        hits.clear()
        await ai.AI("g-key", "q-key").json("sys json", "user")
        assert all(h.startswith("groq") for h in hits), hits
        # gemini-only user with quota gone -> AIError("quota")
        try:
            await ai.AI("g-key", None).json("s", "u")
            raise AssertionError("expected quota error")
        except ai.AIError as e:
            assert e.reason == "quota"
        return first
    finally:
        await ai.close()
        await runner.cleanup()


def test_ai_fallback():
    first = asyncio.run(_fallback())
    assert first[0].startswith("gemini") and first[-1] == "groq:" + config.GROQ_SMART[0], first


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
