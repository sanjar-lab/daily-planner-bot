"""Public rendering API. All functions are CPU-bound; call them via asyncio.to_thread."""
from __future__ import annotations

import math

from .canvas import Canvas
from .cards import report_card, task_card
from .model import build_day
from .themes import MIN_H, PALETTES, TEMPLATES, W, DryCanvas

N_THEMES = len(TEMPLATES)


def theme_for(date, offset: int = 0) -> int:
    """A different template every day of the week; offset lets users reshuffle."""
    return (date.weekday() + offset) % N_THEMES


def render_day(plan: dict, lang: str, theme: int) -> bytes:
    day = build_day(plan)
    tpl = TEMPLATES[theme % N_THEMES]
    h = tpl(DryCanvas(), day, lang)
    c = Canvas(W, max(MIN_H, math.ceil(h)), PALETTES[theme % N_THEMES].bg)
    tpl(c, day, lang)
    return c.to_bytes("JPEG")


def render_task(plan: dict, task_idx: int, lang: str, theme: int) -> bytes:
    day = build_day(plan)
    task = next(t for t in day.tasks if t.idx == task_idx)
    return task_card(PALETTES[theme % N_THEMES], day, task, lang)


def render_report(data: dict, lang: str, theme: int) -> bytes:
    return report_card(PALETTES[theme % N_THEMES], data, lang)
