"""Normalizes an AI plan dict into something templates can lay out."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from .canvas import clean

PRIORITIES = ("high", "medium", "low")


def to_min(v) -> int | None:
    if not v or not isinstance(v, str) or ":" not in v:
        return None
    try:
        h, m = v.strip().split(":")[:2]
        h, m = int(h), int(m)
    except ValueError:
        return None
    if 0 <= h <= 24 and 0 <= m < 60:
        return h * 60 + m
    return None


def hhmm(m: int | None) -> str:
    if m is None:
        return ""
    m %= 1440
    return f"{m // 60:02d}:{m % 60:02d}"


@dataclass
class Task:
    idx: int
    title: str
    start: int | None = None
    end: int | None = None
    priority: str = "medium"
    category: str = "other"
    note: str = ""
    done: bool = False
    added: bool = False

    @property
    def minutes(self) -> int | None:
        if self.start is None or self.end is None:
            return None
        d = self.end - self.start
        return d + 1440 if d < 0 else d

    @property
    def time(self) -> str:
        return hhmm(self.start)

    @property
    def range(self) -> str:
        if self.start is None:
            return ""
        return f"{hhmm(self.start)} – {hhmm(self.end)}" if self.end is not None else hhmm(self.start)

    @property
    def part(self) -> str:
        if self.start is None:
            return "anytime"
        if self.start < 12 * 60:
            return "morning"
        if self.start < 17 * 60:
            return "afternoon"
        return "evening"


@dataclass
class Day:
    date: dt.date
    headline: str
    focus: str
    tasks: list[Task] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.tasks)

    @property
    def n_high(self) -> int:
        return sum(t.priority == "high" for t in self.tasks)

    @property
    def planned(self) -> int:
        return sum(t.minutes or 0 for t in self.tasks)

    @property
    def density(self) -> int:
        """0 airy, 1 normal, 2 compact, 3 dense."""
        n = self.n
        return 0 if n <= 4 else 1 if n <= 8 else 2 if n <= 13 else 3

    def parts(self) -> list[tuple[str, list[Task]]]:
        order = ["morning", "afternoon", "evening", "anytime"]
        groups = {k: [t for t in self.tasks if t.part == k] for k in order}
        return [(k, v) for k, v in groups.items() if v]


def build_day(plan: dict) -> Day:
    try:
        date = dt.date.fromisoformat(str(plan.get("date"))[:10])
    except ValueError:
        date = dt.date.today() + dt.timedelta(days=1)
    tasks = []
    for i, t in enumerate(plan.get("tasks") or []):
        title = clean(t.get("title"))
        if not title:
            continue
        pr = str(t.get("priority", "medium")).lower()
        tasks.append(Task(
            idx=int(t.get("idx", i)), title=title, start=to_min(t.get("start")), end=to_min(t.get("end")),
            priority=pr if pr in PRIORITIES else "medium",
            category=str(t.get("category") or "other").lower(),
            note=clean(t.get("note")), done=bool(t.get("done")), added=bool(t.get("added")),
        ))
    timed = sorted((t for t in tasks if t.start is not None), key=lambda t: t.start)
    untimed = [t for t in tasks if t.start is None]
    return Day(date=date, headline=clean(plan.get("headline")), focus=clean(plan.get("focus")),
               tasks=timed + untimed)
