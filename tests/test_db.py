"""Integration test against a real Postgres: TEST_DATABASE_URL=postgresql://... python tests/test_db.py"""
import asyncio
import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
os.environ.setdefault("ENCRYPTION_KEY", "Zm9vYmFyYmF6cXV4Zm9vYmFyYmF6cXV4Zm9vYmFyYmE=")

from bot import config, db, planner, reports  # noqa: E402

UID = 777000111


async def main():
    config.DATABASE_URL = os.environ["DATABASE_URL"]
    await db.connect()
    await db.connect()  # schema is idempotent
    await db.pool.execute("delete from users where id = $1", UID)

    u = await db.ensure_user(UID, "Test")
    assert u["lang"] == "uz" and u["theme_mode"] == -1
    await db.set_state(UID, "edit:1", {"carry": ["x"]})
    u = await db.update_user(UID, channel_id=-100123, channel_title="Ch", gemini_key="enc")
    assert u["state_data"] == {"carry": ["x"]} and u["state"] == "edit:1"
    assert any(r["id"] == UID for r in await db.active_users())

    today = planner.local_now(u).date()
    plan = planner.normalize({"date": today.isoformat(), "tasks": [
        {"title": "Run", "start": "06:00", "end": "07:00", "priority": "low"},
        {"title": "Ship", "start": "23:58", "priority": "high"},
        {"title": "Call mom"}]}, today)
    pid = await db.create_draft(UID, today, plan, 2)
    pid2 = await db.create_draft(UID, today, plan, 3)  # replaces the previous draft
    assert await db.get_plan(pid) is None and (await db.get_plan(pid2))["data"] == plan

    jobs = [("task_card", 0, dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)),
            ("remind", 1, dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1))]
    assert await db.publish_plan(pid2, UID, today, plan["tasks"], 555, jobs) == []
    # re-publishing another plan for the same day archives the first and returns its message
    pid3 = await db.create_draft(UID, today, plan, 4)
    assert await db.publish_plan(pid3, UID, today, plan["tasks"], 556, jobs) == [555]
    assert (await db.posted_plan(UID, today))["id"] == pid3
    assert len(await db.plan_tasks(pid2)) == 0 and len(await db.plan_tasks(pid3)) == 3

    due = [j for j in await db.take_due_jobs() if j["user_id"] == UID]
    assert [j["kind"] for j in due] == ["task_card"], due
    assert not [j for j in await db.take_due_jobs() if j["user_id"] == UID]

    assert await db.toggle_task(pid3, 0) is True
    assert await db.toggle_task(pid3, 2) is True
    assert await db.toggle_task(pid3, 2) is False
    assert await db.toggle_task(pid3, 99) is None
    rows = await db.tasks_between(UID, today - dt.timedelta(days=7), today)
    assert sum(r["done"] for r in rows) == 1 and len(rows) == 3

    n = await db.save_memory(UID, [{"key": "Work_Hours", "value": "9-18", "category": "work"},
                                   {"key": "goal_ielts", "value": "IELTS 7.5", "category": "goal"},
                                   {"key": "", "value": "skip"}], [])
    assert n == 2
    await db.save_memory(UID, [{"key": "work_hours", "value": "10-19", "category": "work"}], ["goal_ielts"])
    mem = await db.get_memory(UID)
    assert [(m["key"], m["value"]) for m in mem] == [("work_hours", "10-19")], mem
    config.MEMORY_LIMIT = 3
    await db.save_memory(UID, [{"key": f"k{i}", "value": "v", "category": "fact"} for i in range(5)]
                         + [{"key": "g", "value": "goal", "category": "goal"}], [])
    mem = await db.get_memory(UID)
    assert len(mem) == 3 and "g" in [m["key"] for m in mem]

    # report renders with real data (AI insight falls back offline: no keys decrypt)
    u = await db.get_user(UID)
    img, pct, title = await reports.build(u, "week")
    assert img[:2] == b"\xff\xd8" and pct == 33, pct
    img, pct, _ = await reports.build(u, "month")
    Path("previews").mkdir(exist_ok=True)
    Path("previews/db_report_month.jpg").write_bytes(img)

    await db.pool.execute("delete from users where id = $1", UID)
    assert await db.pool.fetchval("select count(*) from plans where user_id = $1", UID) == 0
    await db.close()
    print("PASS db integration")


asyncio.run(main())
