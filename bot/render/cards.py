"""Task-start card and report card, styled with the day's palette.

Both are laid out twice (dry run to measure, then for real) so the image is only
as tall as its content, with a 1080px square as the minimum.
"""
from __future__ import annotations

import math

from .canvas import Canvas, F, mix, rgba, text_w, wrap
from .labels import category, date_long, duration, w, weekday_short
from .model import Day, Task, hhmm
from .themes import W, DryCanvas

MIN_CARD = 1080


def _lum(c) -> float:
    r, g, b, _ = rgba(c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _display(P, size):
    # Caveat runs small and Unbounded runs wide — normalize perceived size.
    k = {"Caveat": 1.3, "Unbounded": 0.82}.get(P.display, 1.0)
    return F(P.display, size * k, P.dweight)


def _two_pass(draw, bg) -> bytes:
    h = draw(DryCanvas())
    c = Canvas(W, max(MIN_CARD, math.ceil(h)), bg)
    draw(c)
    return c.to_bytes("JPEG")


def _task_colors(P, priority):
    if priority == "high":
        bg, fg = P.accent, P.on_accent
        return bg, fg, mix(fg, bg, .28), mix(bg, fg, .14)
    if priority == "low":
        return P.soft, P.ink, mix(P.ink, P.soft, .4), mix(P.soft, "#FFFFFF", .55)
    return P.bg, P.ink, P.muted, P.soft


def task_card(P, day: Day, task: Task, lang: str) -> bytes:
    bg, fg, sub, chip_bg = _task_colors(P, task.priority)
    pos = next((i for i, t in enumerate(day.tasks) if t.idx == task.idx), 0)
    M = 88

    def draw(c):
        if c.real:
            ring = mix(bg, fg, .07)
            c.circle(W - 40, 120, 330, None, ring, 56)
            c.circle(W - 40, 120, 150, ring)
        y = 96
        label = w(lang, "now").upper()
        lf = F(P.body, 22, 800)
        lw = text_w(label, lf, 4) + 70
        c.rect(M, y, lw, 52, 26, fg)
        c.circle(M + 28, y + 26, 7, P.accent if task.priority != "high" else bg)
        c.text(M + 46, y + 26, label, lf, bg, anchor="lm", tracking=4)
        c.text(W - M, y + 26, f"{pos + 1}/{day.n}", F(P.body, 26, 800), sub, anchor="rm")
        y += 130

        tf = _display(P, 118)
        start = task.time or "—"
        c.text(M - 4, y + tf.size * 0.82, start, tf, fg, anchor="ls")
        if task.end is not None:
            c.text(M + text_w(start, tf) + 20, y + tf.size * 0.82, f"– {hhmm(task.end)}",
                   _display(P, 46), sub, anchor="ls")
        y += tf.size * 0.82 + 70

        hf = _display(P, 74)
        lines = wrap(task.title, hf, W - 2 * M, 5)
        lh = hf.size * 1.14
        c.lines(M, y, lines, hf, fg, lh)
        y += len(lines) * lh + 24
        if task.note:
            nf = F(P.body, 32, 500)
            nl = wrap(task.note, nf, W - 2 * M, 4)
            c.lines(M, y, nl, nf, sub, 44)
            y += len(nl) * 44
        y += 36

        cf = F(P.body, 22, 800)
        cx = M
        for txt in [w(lang, task.priority), category(lang, task.category), duration(lang, task.minutes)]:
            if not txt:
                continue
            cw = text_w(txt, cf) + 44
            c.rect(cx, y, cw, 54, 27, chip_bg)
            c.text(cx + cw / 2, y + 27, txt, cf, fg, anchor="mm")
            cx += cw + 12
        y += 54

        by = max(y + 110, c.h - 170)
        n = max(1, day.n)
        if n <= 20:
            step = min(44, (W - 2 * M) / n)
            for i in range(n):
                x = M + 9 + i * step
                if i == pos:
                    c.rect(x - 9, by - 9, min(34, step - 8), 18, 9, fg)
                elif i < pos:
                    c.circle(x, by, 9, fg)
                else:
                    c.circle(x, by, 8, None, sub, 2.5)
        else:
            c.rect(M, by - 6, W - 2 * M, 12, 6, mix(bg, fg, .15))
            c.rect(M, by - 6, (W - 2 * M) * (pos + 1) / n, 12, 6, fg)
        nxt = day.tasks[pos + 1] if pos + 1 < day.n else None
        nf = F(P.body, 28, 600)
        if nxt:
            txt = f"{w(lang, 'next')}: {(nxt.time + '  ') if nxt.time else ''}{nxt.title}"
        else:
            txt = w(lang, "last")
        c.text(M, by + 50, wrap(txt, nf, W - 2 * M, 1)[0], nf, sub)
        return by + 170

    return _two_pass(draw, bg)


def report_card(P, data: dict, lang: str) -> bytes:
    """data: kind, start, end (date), days [(date, done, total)], high_done, high_total,
    streak, best_day (date|None), insight (str)."""
    M = 72
    days = data.get("days") or []
    done = sum(d[1] for d in days)
    total = sum(d[2] for d in days)
    pct = round(100 * done / total) if total else 0
    arc_col = P.accent if _lum(P.accent) < 200 else P.ink

    def draw(c):
        y = 80
        c.text(M, y, w(lang, "weekly" if data.get("kind") == "week" else "monthly"),
               _display(P, 60), P.ink)
        y += 96
        s, e = data["start"], data["end"]
        c.text(M, y, f"{date_long(lang, s)} — {date_long(lang, e)}, {e.year}", F(P.body, 28, 600), P.muted)
        y += 80

        cx, cy, r = M + 190, y + 190, 180
        c.circle(cx, cy, r, None, P.line, 34)
        if pct:
            c.arc(cx, cy, r, -90, -90 + 360 * pct / 100, arc_col, 34)
        c.text(cx, cy + 4, f"{pct}%", _display(P, 80), P.ink, anchor="mm")
        c.text(cx, cy + 74, w(lang, "completion"), F(P.body, 22, 700), P.muted, anchor="mm")

        sx = M + 420
        rows = [
            (w(lang, "done"), f"{done}/{total}"),
            (w(lang, "high_done"), f"{data.get('high_done', 0)}/{data.get('high_total', 0)}"),
            (w(lang, "streak"), f"{data.get('streak', 0)} {w(lang, 'days')}"),
            (w(lang, "best_day"), date_long(lang, data["best_day"]) if data.get("best_day") else "—"),
        ]
        ry = y + 10
        for lab, val in rows:
            c.text(sx, ry, lab.upper(), F(P.body, 17, 800), P.muted, tracking=2.5)
            c.text(sx, ry + 28, val, F(P.body, 40, 800), P.ink)
            ry += 94
        y += 420

        ch = 250
        c.rect(M, y, W - 2 * M, ch + 90, 30, P.card)
        n = len(days)
        if n:
            inner = W - 2 * M - 80
            bw = inner / n
            gap = min(18, bw * 0.3)
            rad = min(14, (bw - gap) / 2)
            for i, (d, dn, tot) in enumerate(days):
                x = M + 40 + i * bw
                top = y + 40
                c.rect(x + gap / 2, top, bw - gap, ch - 40, rad, mix(P.soft, P.card, .4))
                if tot and dn:
                    frac = dn / tot
                    hh = max(bw - gap, (ch - 40) * frac)
                    col = arc_col if frac >= 0.7 else mix(arc_col, P.card, .55)
                    c.rect(x + gap / 2, top + ch - 40 - hh, bw - gap, hh, rad, col)
                if n <= 10 or i % 5 == 0 or i == n - 1:
                    lab = weekday_short(lang, d) if n <= 10 else str(d.day)
                    c.text(x + bw / 2, y + ch + 34, lab, F(P.body, 19, 700), P.muted, anchor="mm")
        else:
            c.text(W / 2, y + ch / 2 + 40, w(lang, "no_data"), F(P.body, 28, 600), P.muted, anchor="mm")
        y += ch + 90 + 40

        if data.get("insight"):
            nf = F(P.body, 27, 500)
            lines = wrap(data["insight"], nf, W - 2 * M - 30, 6)
            c.rect(M, y + 4, 6, len(lines) * 39 - 8, 3, arc_col)
            c.lines(M + 30, y, lines, nf, P.ink, 39)
            y += len(lines) * 39
        return y + 80

    return _two_pass(draw, P.bg)
