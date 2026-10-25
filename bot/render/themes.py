"""Seven day-plan templates. Each one is a different layout, not just a recolour.

A template is a function (canvas, day, lang) -> content height. It is called twice:
once on a DryCanvas to measure the height, then on a real Canvas of that height.
"""
from __future__ import annotations

import math
from types import SimpleNamespace as NS

from .canvas import F, mix, text_w, wrap
from .labels import category, date_long, duration, month, w, weekday
from .model import Day, hhmm

W = 1080
MIN_H = 1080


class DryCanvas:
    real = False
    w, h = W, 0

    def __getattr__(self, _):
        return lambda *a, **k: 0


PALETTES = [
    NS(name="Editorial", bg="#F5F1EA", ink="#161514", muted="#8A847B", line="#DCD5CA",
       accent="#E2552D", on_accent="#FFFFFF", soft="#ECE5D9", card="#FFFFFF",
       display="PlayfairDisplay", dweight=700, body="Inter"),
    NS(name="Sage", bg="#F1F4EE", ink="#14201A", muted="#76857B", line="#CBD5CC",
       accent="#2F7A57", on_accent="#FFFFFF", soft="#DDE9E0", card="#FFFFFF",
       display="Manrope", dweight=800, body="Manrope"),
    NS(name="Bento", bg="#EFEDE7", ink="#121212", muted="#77736B", line="#DEDAD1",
       accent="#D8F36A", on_accent="#121212", soft="#E4DDFF", card="#FFFFFF",
       display="Unbounded", dweight=700, body="Inter"),
    NS(name="Swiss", bg="#FFFFFF", ink="#0B0B0B", muted="#8C8C8C", line="#E6E6E6",
       accent="#FF3B1F", on_accent="#FFFFFF", soft="#F3F3F1", card="#FFFFFF",
       display="Unbounded", dweight=800, body="Inter"),
    NS(name="Soft", bg="#FFF4EA", ink="#2A1A14", muted="#8E6F63", line="#F1DED2",
       accent="#E0654A", on_accent="#FFFFFF", soft="#FFE3D3", card="#FFFFFF",
       display="Manrope", dweight=800, body="Manrope"),
    NS(name="Notebook", bg="#FBFAF6", ink="#1F2C47", muted="#7D8597", line="#DCD7CC",
       accent="#D1543C", on_accent="#FFFFFF", soft="#FFF0A6", card="#FFFFFF",
       display="Caveat", dweight=700, body="Inter"),
    NS(name="Sunrise", bg="#F7F3EC", ink="#2B1810", muted="#8F7666", line="#EADFD2",
       accent="#FF8552", on_accent="#FFFFFF", soft="#FFE0C2", card="#FFFFFF",
       display="Unbounded", dweight=800, body="Inter"),
]


def _pick(dens: int, *vals):
    return vals[min(dens, len(vals) - 1)]


def _headline(day: Day, lang: str) -> str:
    return day.headline or w(lang, "plan_of_day")


def _short_time(m: int | None) -> str:
    s = hhmm(m)
    return s[1:] if s.startswith("0") else s


def _note(t, lang: str, d: int) -> str:
    """Row note; tasks added to an existing plan always show a '+ Added' marker."""
    if t.added:
        return f"+ {w(lang, 'added')}" + (f" · {t.note}" if t.note else "")
    return t.note if d < 3 else ""


def _nc(t, normal, added):
    return added if t.added else normal


# ---------------------------------------------------------------------------
# 1. Editorial — warm paper, big serif date, numbered rows with hairlines
# ---------------------------------------------------------------------------
def editorial(c, day: Day, lang: str) -> float:
    P, M, d = PALETTES[0], 80, day.density
    if c.real:
        c.grain(5)
    y = 78
    c.text(M, y, weekday(lang, day.date).upper(), F("Inter", 21, 650), P.ink, tracking=4)
    c.text(W - M, y, f"No. {day.date.timetuple().tm_yday:03d}", F("JetBrainsMono", 20, 500),
           P.muted, anchor="ra")
    y += 46
    c.line(M, y, W - M, y, P.ink, 2)

    num = str(day.date.day)
    day_f = F("PlayfairDisplay", 230, 700)
    base = y + 232
    c.text(M - 8, base, num, day_f, P.ink, anchor="ls")
    nx = M + text_w(num, day_f) + 30
    c.text(nx, base - 96, month(lang, day.date).capitalize(), F("PlayfairDisplay", 60, 600),
           P.ink, anchor="ls")
    c.text(nx, base - 34, str(day.date.year), F("JetBrainsMono", 24, 500), P.muted, anchor="ls")
    y = base + 48

    hf = F("PlayfairDisplay", 58, 600)
    hl = wrap(_headline(day, lang), hf, W - 2 * M, 3)
    c.lines(M, y, hl, hf, P.ink, 70)
    y += len(hl) * 70 + 6
    if day.focus:
        ff = F("Inter", 27, 400)
        fl = wrap(day.focus, ff, W - 2 * M - 34, 2)
        c.rect(M, y + 12, 13, 13, 0, P.accent)
        c.lines(M + 32, y, fl, ff, P.muted, 38)
        y += len(fl) * 38
    y += 42

    c.line(M, y, W - M, y, P.ink, 2)
    sh, cw = 126, (W - 2 * M) / 3
    stats = [(w(lang, "tasks_t"), str(day.n)), (w(lang, "high"), str(day.n_high)),
             (w(lang, "planned"), duration(lang, day.planned) or "—")]
    for i, (lab, val) in enumerate(stats):
        x = M + i * cw + (0 if i == 0 else 30)
        if i:
            c.line(M + i * cw, y + 26, M + i * cw, y + sh - 26, P.line, 2)
        c.text(x, y + 28, lab.upper(), F("Inter", 17, 650), P.muted, tracking=3)
        c.text(x, y + 56, val, F("PlayfairDisplay", 46, 700), P.ink)
    y += sh
    c.line(M, y, W - M, y, P.ink, 2)

    tf = F("Inter", _pick(d, 35, 32, 29, 26), 600)
    nf = F("Inter", _pick(d, 25, 23, 21, 20), 400)
    timef = F("JetBrainsMono", _pick(d, 27, 25, 23, 21), 600)
    endf = F("JetBrainsMono", _pick(d, 21, 20, 19, 18), 400)
    pad = _pick(d, 36, 28, 20, 14)
    tx = M + 214
    tw = W - M - 56 - tx
    for i, t in enumerate(day.tasks):
        tl = wrap(t.title, tf, tw, 3 if d < 2 else 2)
        nl = wrap(_note(t, lang, d), nf, tw, 2 if d < 2 else 1) if _note(t, lang, d) else []
        tlh, nlh = tf.size * 1.24, nf.size * 1.38
        body = len(tl) * tlh + (len(nl) * nlh + 4 if nl else 0)
        left = timef.size * 1.3 + (endf.size * 1.3 if t.end is not None else 0)
        h = max(body, left) + 2 * pad
        ry = y + pad
        c.text(M, ry + 4, f"{i + 1:02d}", F("JetBrainsMono", 19, 500), P.accent)
        if t.start is not None:
            c.text(M + 54, ry, t.time, timef, P.ink)
            if t.end is not None:
                c.text(M + 54, ry + timef.size * 1.3, hhmm(t.end), endf, P.muted)
        else:
            c.text(M + 54, ry, "—", timef, P.muted)
        c.lines(tx, ry - 3, tl, tf, P.ink, tlh)
        if nl:
            c.lines(tx, ry - 3 + len(tl) * tlh + 4, nl, nf, _nc(t, P.muted, P.accent), nlh)
        mx, my = W - M - 12, ry + tf.size * 0.55
        if t.priority == "high":
            c.circle(mx, my, 11, P.accent)
        elif t.priority == "medium":
            c.circle(mx, my, 10, None, P.accent, 3)
        else:
            c.circle(mx, my, 5, P.line)
        y += h
        c.line(M, y, W - M, y, P.line if i < day.n - 1 else P.ink, 1.5 if i < day.n - 1 else 2)

    fy = max(y + 44, c.h - 96)
    c.text(M, fy, f"{w(lang, 'plan_of_day')} · {date_long(lang, day.date)}", F("Inter", 19, 500), P.muted)
    lx = W - M
    for key, kind in (("low", 2), ("medium", 1), ("high", 0)):
        label = w(lang, key)
        lx -= text_w(label, F("Inter", 19, 500))
        c.text(lx, fy, label, F("Inter", 19, 500), P.muted)
        cy = fy + 11
        if kind == 0:
            c.circle(lx - 16, cy, 7, P.accent)
        elif kind == 1:
            c.circle(lx - 16, cy, 6.5, None, P.accent, 2.5)
        else:
            c.circle(lx - 16, cy, 4, P.line)
        lx -= 52
    return fy + 64


# ---------------------------------------------------------------------------
# 2. Timeline — sage green, vertical timeline with cards
# ---------------------------------------------------------------------------
def timeline(c, day: Day, lang: str) -> float:
    P, M, d = PALETTES[1], 72, day.density
    y = 82
    c.text(M, y, weekday(lang, day.date).upper(), F("Manrope", 23, 800), P.accent, tracking=3)
    c.text(M, y + 34, date_long(lang, day.date), F("Manrope", 76, 800), P.ink)
    bx, by, br = W - M - 76, 78 + 76, 76
    c.circle(bx, by, br, P.ink)
    c.text(bx, by + 8, str(day.n), F("Manrope", 64, 800), "#FFFFFF", anchor="ms")
    c.text(bx, by + 38, w(lang, "tasks"), F("Manrope", 19, 700), "#A9C3B3", anchor="mm")
    y = 250

    hf = F("Manrope", 36, 700)
    hl = wrap(_headline(day, lang), hf, W - 2 * M, 3)
    c.lines(M, y, hl, hf, mix(P.ink, P.bg, .15), 48)
    y += len(hl) * 48 + 18

    chips = []
    if day.focus:
        chips.append((day.focus, P.soft, P.accent))
    if day.planned:
        chips.append((f"{w(lang, 'planned')}: {duration(lang, day.planned)}", "#FFFFFF", P.ink))
    if day.n_high:
        chips.append((f"{day.n_high} {w(lang, 'high_n')}", "#FFFFFF", P.ink))
    cf = F("Manrope", 23, 700)
    cx, row_h = M, 0
    for text, bg, fg in chips:
        lines = wrap(text, cf, W - 2 * M - 48, 2)
        tw = max(text_w(ln, cf) for ln in lines) + 48
        ch = 30 * len(lines) + 26
        if cx > M and cx + tw > W - M:
            cx, y, row_h = M, y + row_h + 12, 0
        c.rect(cx, y, tw, ch, min(ch / 2, 28), bg)
        c.lines(cx + 24, y + 13, lines, cf, fg, 30)
        cx += tw + 12
        row_h = max(row_h, ch)
    y += row_h + 44

    lx = M + 122
    cardx = lx + 36
    cw = W - M - cardx
    pad = _pick(d, 28, 24, 18, 14)
    gap = _pick(d, 22, 16, 12, 10)
    tf = F("Manrope", _pick(d, 32, 30, 27, 25), 750)
    nf = F("Manrope", _pick(d, 24, 22, 21, 20), 500)
    labf = F("Manrope", 16, 800)
    stf = F("Manrope", _pick(d, 27, 25, 23, 21), 800)
    etf = F("Manrope", _pick(d, 20, 19, 18, 17), 600)
    prev_dot = None
    dots = []
    for t in day.tasks:
        dark = t.priority == "high"
        show_lab = d < 3
        pill = duration(lang, t.minutes)
        pw = text_w(pill, F("Manrope", 18, 800)) + 28 if pill else 0
        tl = wrap(t.title, tf, cw - 2 * pad - (0 if show_lab else pw + 14), 3 if d < 2 else 2)
        nl = wrap(_note(t, lang, d), nf, cw - 2 * pad, 2 if d < 2 else 1) if _note(t, lang, d) else []
        tlh, nlh = tf.size * 1.25, nf.size * 1.38
        h = 2 * pad + (30 if show_lab else 0) + len(tl) * tlh + (len(nl) * nlh + 6 if nl else 0)
        dot_y = y + pad + 12
        if prev_dot is not None:
            c.line(lx, prev_dot, lx, dot_y, P.line, 3)
        prev_dot = dot_y
        if t.start is not None:
            c.text(lx - 30, y + pad - 2, t.time, stf, P.ink, anchor="ra")
            if t.end is not None:
                c.text(lx - 30, y + pad + stf.size * 1.25, hhmm(t.end), etf, P.muted, anchor="ra")
        else:
            c.text(lx - 30, y + pad - 2, "—", stf, P.muted, anchor="ra")
        dots.append((dot_y, t.priority))
        if not dark:
            c.shadow(cardx, y, cw, h, 26, blur=22, color=(20, 40, 30, 22), dy=8)
        c.rect(cardx, y, cw, h, 26, P.ink if dark else P.card)
        fg = "#FFFFFF" if dark else P.ink
        sub = "#AFC2B6" if dark else P.muted
        iy = y + pad
        if show_lab:
            c.text(cardx + pad, iy, category(lang, t.category).upper(), labf,
                   "#8FD3AE" if dark else P.accent, tracking=2.5)
            iy += 30
        if pill:
            px = cardx + cw - pad - pw
            c.rect(px, y + pad - 6, pw, 32, 16, "#24382D" if dark else "#EEF3EE")
            c.text(px + pw / 2, y + pad + 10, pill, F("Manrope", 18, 800), fg, anchor="mm")
        c.lines(cardx + pad, iy - 2, tl, tf, fg, tlh)
        if nl:
            c.lines(cardx + pad, iy - 2 + len(tl) * tlh + 6, nl, nf, _nc(t, sub, "#8FD3AE" if dark else P.accent), nlh)
        y += h + gap
    for dot_y, pr in dots:
        if pr == "high":
            c.circle(lx, dot_y, 17, mix(P.accent, P.bg, .75))
            c.circle(lx, dot_y, 10, P.accent)
        elif pr == "medium":
            c.circle(lx, dot_y, 10, P.bg, P.accent, 4)
        else:
            c.circle(lx, dot_y, 7, P.line)

    fy = max(y + 30, c.h - 90)
    c.text(M, fy, f"{w(lang, 'plan_of_day')} · {day.date.year}", F("Manrope", 19, 700), P.muted)
    c.text(W - M, fy, f"{day.n} {w(lang, 'tasks')}", F("Manrope", 19, 700), P.muted, anchor="ra")
    return fy + 60


# ---------------------------------------------------------------------------
# 3. Bento — tiles grid, lime + coral accents
# ---------------------------------------------------------------------------
def bento(c, day: Day, lang: str) -> float:
    P, M, G, R, d = PALETTES[2], 54, 18, 34, day.density
    coral, lilac = "#FF7A59", "#E4DDFF"
    y = M
    w1 = (W - 2 * M - G) * 0.6
    w2 = W - 2 * M - G - w1
    th = 318
    c.rect(M, y, w1, th, R, P.card)
    c.text(M + 36, y + 38, weekday(lang, day.date).upper(), F("Inter", 21, 750), P.muted, tracking=3)
    nf_ = F("Unbounded", 150, 700)
    num = str(day.date.day)
    c.text(M + 30, y + th - 50, num, nf_, P.ink, anchor="ls")
    mx = M + 30 + text_w(num, nf_) + 22
    mon_f = F("Inter", 34, 750)
    mon = month(lang, day.date).capitalize()
    if mx + text_w(mon, mon_f) > M + w1 - 24:
        mon_f = F("Inter", 26, 750)
    c.text(mx, y + th - 108, mon, mon_f, P.ink, anchor="ls")
    c.text(mx, y + th - 60, str(day.date.year), F("Inter", 26, 500), P.muted, anchor="ls")

    x2 = M + w1 + G
    c.rect(x2, y, w2, th, R, P.accent)
    c.text(x2 + 32, y + 38, w(lang, "tasks_t").upper(), F("Inter", 21, 750), P.ink, tracking=3)
    c.text(x2 + 28, y + 220, str(day.n), F("Unbounded", 124, 700), P.ink, anchor="ls")
    meta = f"{day.n_high} {w(lang, 'high_n')}"
    if day.planned:
        meta += f" · {duration(lang, day.planned)}"
    c.text(x2 + 32, y + th - 42, meta, F("Inter", 23, 700), P.ink, anchor="ls")
    y += th + G

    hf = F("Inter", 42, 800)
    ff = F("Inter", 26, 500)
    inner = W - 2 * M - 80
    hl = wrap(_headline(day, lang), hf, inner, 3)
    fl = wrap(day.focus, ff, inner, 3) if day.focus else []
    fh = 40 + 34 + len(hl) * 52 + (len(fl) * 36 + 14 if fl else 0) + 40
    c.rect(M, y, W - 2 * M, fh, R, P.ink)
    c.text(M + 40, y + 40, w(lang, "focus").upper(), F("Inter", 19, 750), P.accent, tracking=3)
    c.lines(M + 40, y + 76, hl, hf, "#FFFFFF", 52)
    if fl:
        c.lines(M + 40, y + 76 + len(hl) * 52 + 14, fl, ff, "#A9A9A3", 36)
    y += fh + G

    def colors(t):
        if t.priority == "high":
            return coral, "#1C0F0A", P.ink, coral, mix("#1C0F0A", coral, .35)
        if t.priority == "low":
            return lilac, P.ink, "#FFFFFF", P.ink, P.muted
        return P.card, P.ink, "#F0EEE8", P.ink, P.muted

    if day.n <= 10:
        tw = (W - 2 * M - G) / 2
        tf = F("Inter", _pick(d, 31, 29, 27), 800)
        nf = F("Inter", _pick(d, 22, 21, 20), 500)
        pf = F("Inter", 19, 800)
        lf = F("Inter", 16, 750)
        pad = 30

        def tile_h(t, width):
            tl = wrap(t.title, tf, width - 2 * pad, 4)
            nl = wrap(_note(t, lang, 0), nf, width - 2 * pad, 3) if _note(t, lang, 0) else []
            return tl, nl, pad + 40 + 20 + len(tl) * tf.size * 1.22 + (
                len(nl) * nf.size * 1.4 + 10 if nl else 0) + 22 + 26 + pad

        i = 0
        tasks = day.tasks
        while i < len(tasks):
            pair = tasks[i:i + 2]
            full = len(pair) == 1
            width = W - 2 * M if full else tw
            laid = [tile_h(t, width) for t in pair]
            rh = max(h for _, _, h in laid)
            for j, (t, (tl, nl, _)) in enumerate(zip(pair, laid)):
                x = M + j * (tw + G)
                bg, fg, pill_bg, pill_fg, sub = colors(t)
                c.rect(x, y, width, rh, R, bg)
                label = t.range or w(lang, "anytime")
                pw = text_w(label, pf) + 30
                c.rect(x + pad, y + pad, pw, 40, 20, pill_bg)
                c.text(x + pad + pw / 2, y + pad + 20, label, pf, pill_fg, anchor="mm")
                ty = y + pad + 40 + 20
                c.lines(x + pad, ty, tl, tf, fg, tf.size * 1.22)
                if nl:
                    c.lines(x + pad, ty + len(tl) * tf.size * 1.22 + 10, nl, nf,
                            _nc(t, sub, "#1C0F0A" if t.priority == "high" else "#5B3FE0"), nf.size * 1.4)
                c.text(x + pad, y + rh - pad - 18, category(lang, t.category).upper(), lf, sub,
                       tracking=2.5, anchor="ls")
                dur = duration(lang, t.minutes)
                if dur:
                    c.text(x + width - pad, y + rh - pad - 18, dur, F("Inter", 18, 700), sub, anchor="rs")
            y += rh + G
            i += 2
    else:
        rows = []
        tf = F("Inter", _pick(d, 28, 28, 27, 25), 650)
        rh = _pick(d, 70, 70, 64, 56)
        for t in day.tasks:
            rows.append(wrap(("+ " if t.added else "") + t.title, tf, W - 2 * M - 300, 1))
        lh = 36 + len(rows) * rh + 20
        c.rect(M, y, W - 2 * M, lh, R, P.card)
        ry = y + 28
        for k, (t, tl) in enumerate(zip(day.tasks, rows)):
            cy = ry + rh / 2
            c.text(M + 36, cy, t.time or "—", F("Inter", 23, 800), P.ink if t.start is not None else P.muted, anchor="lm")
            c.text(M + 160, cy, tl[0], tf, P.ink, anchor="lm")
            col = coral if t.priority == "high" else ("#B9AEF0" if t.priority == "low" else "#CFCBC2")
            c.rect(W - M - 36 - 48, cy - 8, 48, 16, 8, col)
            if k < len(rows) - 1:
                c.line(M + 36, ry + rh, W - M - 36, ry + rh, "#EEEBE4", 1.5)
            ry += rh
        y += lh + G

    fy = max(y + 14, c.h - 80)
    c.text(M + 6, fy, f"{w(lang, 'plan_of_day')} · {date_long(lang, day.date)}", F("Inter", 19, 650), P.muted)
    lx = W - M - 6
    for key, col in (("low", lilac), ("medium", P.card), ("high", coral)):
        lab = w(lang, key)
        lx -= text_w(lab, F("Inter", 19, 650))
        c.text(lx, fy, lab, F("Inter", 19, 650), P.muted)
        c.rect(lx - 30, fy + 3, 20, 20, 6, col, P.line if col == P.card else None, 1.5)
        lx -= 58
    return fy + 60


# ---------------------------------------------------------------------------
# 4. Swiss — white, black type, red square, tabular rows, big stat footer
# ---------------------------------------------------------------------------
def swiss(c, day: Day, lang: str) -> float:
    P, M, d = PALETTES[3], 64, day.density
    y = 64
    sq = 132
    c.rect(M, y, sq, sq, 0, P.accent)
    c.text(M + sq / 2, y + sq / 2 + 2, str(day.date.day), F("Unbounded", 62, 800), "#FFFFFF", anchor="mm")
    x = M + sq + 28
    wd = weekday(lang, day.date).upper()
    size = 58
    while size > 30 and text_w(wd, F("Unbounded", size, 800)) > W - M - x:
        size -= 2
    c.text(x, y + 2, wd, F("Unbounded", size, 800), P.ink)
    c.text(x, y + sq - 40, f"{month(lang, day.date)} {day.date.year}".lower(), F("Inter", 26, 600), P.muted)
    y += sq + 52

    hf = F("Unbounded", 44, 600)
    hl = wrap(_headline(day, lang), hf, W - 2 * M, 3)
    c.lines(M, y, hl, hf, P.ink, 58)
    y += len(hl) * 58 + 6
    if day.focus:
        ff = F("Inter", 26, 500)
        fl = wrap(day.focus, ff, W - 2 * M - 28, 3)
        c.rect(M, y + 4, 5, len(fl) * 36 - 4, 0, P.accent)
        c.lines(M + 26, y, fl, ff, P.muted, 36)
        y += len(fl) * 36
    y += 44

    c.rect(M, y, W - 2 * M, 10, 0, P.ink)
    y += 10
    hdr = F("Inter", 16, 800)
    c.text(M, y + 20, w(lang, "time").upper(), hdr, P.ink, tracking=3)
    tx = M + 196
    c.text(tx, y + 20, w(lang, "task").upper(), hdr, P.ink, tracking=3)
    c.text(W - M, y + 20, w(lang, "priority").upper(), hdr, P.ink, anchor="ra", tracking=3)
    y += 58
    c.line(M, y, W - M, y, P.ink, 1.5)

    tf = F("Inter", _pick(d, 33, 31, 28, 26), 600)
    nf = F("Inter", _pick(d, 23, 22, 20, 19), 400)
    stf = F("Unbounded", _pick(d, 28, 26, 24, 22), 600)
    etf = F("Inter", _pick(d, 20, 19, 18, 17), 500)
    pad = _pick(d, 30, 24, 18, 13)
    tw = W - M - 90 - tx
    for i, t in enumerate(day.tasks):
        tl = wrap(t.title, tf, tw, 3 if d < 2 else 2)
        nl = wrap(_note(t, lang, d), nf, tw, 2 if d < 2 else 1) if _note(t, lang, d) else []
        tlh, nlh = tf.size * 1.24, nf.size * 1.38
        body = len(tl) * tlh + (len(nl) * nlh + 4 if nl else 0)
        left = stf.size * 1.35 + (etf.size * 1.3 if t.end is not None else 0)
        h = max(body, left) + 2 * pad
        ry = y + pad
        hot = t.priority == "high"
        c.text(M, ry, t.time or "—", stf, P.accent if hot else (P.ink if t.start is not None else P.muted))
        if t.end is not None:
            c.text(M, ry + stf.size * 1.35, hhmm(t.end), etf, P.muted)
        c.lines(tx, ry - 2, tl, tf, P.ink, tlh)
        if nl:
            c.lines(tx, ry - 2 + len(tl) * tlh + 4, nl, nf, _nc(t, P.muted, P.accent), nlh)
        filled = {"high": 3, "medium": 2, "low": 1}[t.priority]
        for b in range(3):
            bx = W - M - 8 - (2 - b) * 15
            col = (P.accent if hot else P.ink) if b < filled else P.line
            c.rect(bx, ry + 2, 8, 26, 0, col)
        y += h
        c.line(M, y, W - M, y, P.ink if i == day.n - 1 else P.line, 1.5)

    y += 40
    fy = max(y, c.h - 250)
    c.rect(M, fy, W - 2 * M, 10, 0, P.ink)
    cw = (W - 2 * M) / 3
    hm = f"{day.planned // 60}:{day.planned % 60:02d}" if day.planned else "—"
    stats = [(f"{day.n:02d}", w(lang, "tasks_t")), (f"{day.n_high:02d}", w(lang, "high")),
             (hm, w(lang, "planned"))]
    for i, (val, lab) in enumerate(stats):
        sx = M + i * cw
        c.text(sx, fy + 40, val, F("Unbounded", 60, 800), P.accent if i == 1 and day.n_high else P.ink)
        c.text(sx, fy + 130, lab.upper(), F("Inter", 16, 800), P.muted, tracking=3)
    c.text(M, fy + 196, f"{w(lang, 'plan_of_day')} — {date_long(lang, day.date)}", F("Inter", 18, 500), P.muted)
    return fy + 250


# ---------------------------------------------------------------------------
# 5. Soft — warm colour fields, frosted cards grouped by part of day
# ---------------------------------------------------------------------------
def soft(c, day: Day, lang: str) -> float:
    P, M, d = PALETTES[4], 64, day.density
    if c.real:
        H = c.h
        c.blobs([(150, 230, 430, "#FFC4A3"), (980, 120, 380, "#FFB3CC"),
                 (930, H * 0.52, 440, "#FFE19B"), (90, H * 0.74, 420, "#CFE5FF"),
                 (760, H * 0.97, 400, "#FFC4A3")], blur=150)
    y = 84
    c.text(M, y, weekday(lang, day.date).upper(), F("Manrope", 23, 800), P.accent, tracking=3)
    c.text(M, y + 36, date_long(lang, day.date), F("Manrope", 84, 800), P.ink)
    y += 160
    hf = F("Manrope", 36, 750)
    hl = wrap(_headline(day, lang), hf, W - 2 * M, 3)
    c.lines(M, y, hl, hf, P.ink, 48)
    y += len(hl) * 48 + 4
    if day.focus:
        ff = F("Manrope", 26, 600)
        fl = wrap(day.focus, ff, W - 2 * M, 3)
        c.lines(M, y + 6, fl, ff, P.muted, 36)
        y += len(fl) * 36 + 6
    y += 30

    pf = F("Manrope", 23, 800)
    px = M
    for txt in [f"{day.n} {w(lang, 'tasks')}", f"{day.n_high} {w(lang, 'high_n')}",
                duration(lang, day.planned)]:
        if not txt:
            continue
        pw = text_w(txt, pf) + 44
        c.rect(px, y, pw, 58, 29, (255, 255, 255, 200))
        c.text(px + pw / 2, y + 29, txt, pf, P.ink, anchor="mm")
        px += pw + 12
    y += 58 + 44

    tf = F("Manrope", _pick(d, 31, 29, 27, 25), 750)
    nf = F("Manrope", _pick(d, 23, 22, 20, 19), 500)
    pad = _pick(d, 26, 22, 17, 13)
    rx = M + 28 + 132
    tw = W - M - 28 - rx
    for part, tasks in day.parts():
        c.text(M + 6, y, w(lang, part).upper(), F("Manrope", 20, 800), P.ink, tracking=3)
        c.text(W - M - 6, y, str(len(tasks)), F("Manrope", 20, 800), P.muted, anchor="ra")
        y += 40
        laid = []
        for t in tasks:
            tag = t.priority == "high"
            tl = wrap(t.title, tf, tw - (120 if tag else 0), 3 if d < 2 else 2)
            nl = wrap(_note(t, lang, d), nf, tw, 2 if d < 2 else 1) if _note(t, lang, d) else []
            body = len(tl) * tf.size * 1.25 + (len(nl) * nf.size * 1.38 + 4 if nl else 0)
            laid.append((t, tl, nl, max(body, 64 if t.end is not None else 40) + 2 * pad))
        ch = sum(h for *_, h in laid) + 16
        c.rect(M, y, W - 2 * M, ch, 36, (255, 255, 255, 178))
        ry = y + 8
        for k, (t, tl, nl, h) in enumerate(laid):
            iy = ry + pad
            lab = t.time or "··"
            c.rect(M + 24, iy - 4, 112, 42, 21, "#FFFFFF")
            c.text(M + 80, iy + 17, lab, F("Manrope", 22, 800), P.ink, anchor="mm")
            if t.end is not None:
                c.text(M + 80, iy + 62, hhmm(t.end), F("Manrope", 19, 700), P.muted, anchor="mm")
            c.lines(rx, iy - 2, tl, tf, P.ink, tf.size * 1.25)
            if nl:
                c.lines(rx, iy - 2 + len(tl) * tf.size * 1.25 + 4, nl, nf, _nc(t, P.muted, P.accent), nf.size * 1.38)
            if t.priority == "high":
                tag = w(lang, "high")
                tgw = text_w(tag, F("Manrope", 17, 800)) + 26
                c.rect(W - M - 24 - tgw, iy - 2, tgw, 34, 17, P.accent)
                c.text(W - M - 24 - tgw / 2, iy + 15, tag, F("Manrope", 17, 800), "#FFFFFF", anchor="mm")
            elif t.priority == "low":
                c.circle(W - M - 34, iy + 15, 6, mix(P.muted, "#FFFFFF", .45))
            if k < len(laid) - 1:
                c.line(M + 24, ry + h, W - M - 24, ry + h, (241, 222, 210, 255), 1.5)
            ry += h
        y += ch + 30

    fy = max(y + 6, c.h - 84)
    c.text(M + 6, fy, f"{w(lang, 'plan_of_day')} · {date_long(lang, day.date)}", F("Manrope", 19, 700), P.muted)
    return fy + 60


# ---------------------------------------------------------------------------
# 6. Notebook — dotted paper, handwritten headline, checkboxes, marker highlight
# ---------------------------------------------------------------------------
def notebook(c, day: Day, lang: str) -> float:
    P, d = PALETTES[5], day.density
    M, R = 150, W - 72
    if c.real:
        c.dots(40, 2, P.line, 20, 20)
        c.line(112, 0, 112, c.h, "#F2ABA2", 2.5)
    y = 82
    c.text(M, y, f"{weekday(lang, day.date)}, {date_long(lang, day.date)}", F("Caveat", 48, 700), P.accent)
    y += 74
    hf = F("Caveat", 98, 700)
    hl = wrap(_headline(day, lang), hf, R - M, 3)
    c.lines(M, y, hl, hf, P.ink, 92)
    y += len(hl) * 92 + 6
    sw = min(R - M, max(text_w(ln, hf) for ln in hl))
    pts = [(M + i * 4, y + 5 * math.sin(i * 4 / 44 * 2 * math.pi)) for i in range(int(sw // 4) + 1)]
    c.polyline(pts, P.accent, 4)
    y += 34
    if day.focus:
        ff = F("Inter", 26, 500)
        fl = wrap("→ " + day.focus, ff, R - M, 3)
        c.lines(M, y, fl, ff, P.muted, 37)
        y += len(fl) * 37
    y += 48

    tf = F("Inter", _pick(d, 33, 31, 28, 26), 600)
    nf = F("Inter", _pick(d, 23, 22, 20, 19), 400)
    gap = _pick(d, 34, 26, 18, 12)
    timef = F("Caveat", _pick(d, 40, 38, 34, 32), 700)
    tx = M + 62
    tw = R - tx - 170
    for t in day.tasks:
        tl = wrap(t.title, tf, tw, 3 if d < 2 else 2)
        nl = wrap(_note(t, lang, d), nf, tw, 2 if d < 2 else 1) if _note(t, lang, d) else []
        tlh, nlh = tf.size * 1.3, nf.size * 1.38
        c.rect(M, y + 2, 36, 36, 9, P.card, P.ink, 3)
        if t.done:
            c.check(M, y + 2, 36, P.accent, 4)
        if t.priority == "high":
            for k, ln in enumerate(tl):
                lw = text_w(ln, tf)
                c.rect(tx - 8, y + k * tlh + tf.size * 0.42, lw + 16, tf.size * 0.72, 6, P.soft)
        c.lines(tx, y - 2, tl, tf, P.ink, tlh)
        if t.priority == "high":
            c.text(tx + text_w(tl[-1], tf) + 16, y - 6 + (len(tl) - 1) * tlh, "!", F("Caveat", 44, 700), P.accent)
        if nl:
            c.lines(tx, y - 2 + len(tl) * tlh + 2, nl, nf, _nc(t, P.muted, P.accent), nlh)
        if t.start is not None:
            c.text(R, y - 6, _short_time(t.start), timef, P.accent, anchor="ra")
            if t.end is not None:
                c.text(R, y + timef.size * 0.9, "– " + _short_time(t.end), F("Caveat", timef.size * 0.78, 700),
                       P.muted, anchor="ra")
        h = max(len(tl) * tlh + (len(nl) * nlh + 2 if nl else 0), 44 + (30 if t.end is not None else 0))
        y += h + gap

    fy = max(y + 30, c.h - 120)
    summary = f"{day.n} {w(lang, 'tasks')} · {day.n_high} {w(lang, 'high_n')}"
    if day.planned:
        summary += f" · {duration(lang, day.planned)}"
    c.text(M, fy, summary, F("Caveat", 46, 700), P.ink)
    c.line(M, fy + 64, M + min(R - M, text_w(summary, F("Caveat", 46, 700))), fy + 60, P.accent, 3)
    return fy + 110


# ---------------------------------------------------------------------------
# 7. Sunrise — retro sun block on top, ticket-style task rows
# ---------------------------------------------------------------------------
def sunrise(c, day: Day, lang: str) -> float:
    P, M, d = PALETTES[6], 64, day.density
    sun = P.accent
    med, low = "#FFD5AE", "#ECE5DA"
    hf = F("Inter", 34, 750)
    hl = wrap(_headline(day, lang), hf, 560, 3)
    tb = max(540, 362 + len(hl) * 46 + 64)
    c.rect(0, 0, W, tb, 0, P.soft)
    scx, scy, sr = W - 228, tb - 6, 178
    c.circle(scx, scy, sr, sun)
    for k, (off, th) in enumerate(((34, 12), (72, 9), (104, 6), (130, 4))):
        c.rect(scx - sr - 4, tb - off - th, 2 * sr + 8, th, 0, P.soft)
    c.rect(0, tb, W, 400, 0, P.bg)
    y = 72
    c.text(M, y, weekday(lang, day.date).upper(), F("Unbounded", 24, 600), "#9A5530", tracking=3)
    dn = F("Unbounded", 168, 800)
    c.text(M - 6, y + 236, str(day.date.day), dn, P.ink, anchor="ls")
    mx = M + text_w(str(day.date.day), dn) + 18
    c.text(mx, y + 168, month(lang, day.date).capitalize(), F("Inter", 36, 750), P.ink, anchor="ls")
    c.text(mx, y + 222, str(day.date.year), F("Inter", 28, 500), "#9A7560", anchor="ls")
    c.lines(M, 362, hl, hf, "#4A2A1C", 46)
    y = tb + 44

    chf = F("Inter", 23, 800)
    cx = M
    for txt in [f"{day.n} {w(lang, 'tasks')}", f"{day.n_high} {w(lang, 'high_n')}", duration(lang, day.planned)]:
        if not txt:
            continue
        cw = text_w(txt, chf) + 44
        c.rect(cx, y, cw, 60, 30, P.card, P.line, 2)
        c.text(cx + cw / 2, y + 30, txt, chf, P.ink, anchor="mm")
        cx += cw + 12
    y += 60 + 28
    if day.focus:
        ff = F("Inter", 26, 500)
        fl = wrap(day.focus, ff, W - 2 * M, 3)
        c.lines(M, y, fl, ff, P.muted, 37)
        y += len(fl) * 37 + 10
    y += 26

    stub = 178
    tf = F("Inter", _pick(d, 31, 29, 27, 25), 700)
    nf = F("Inter", _pick(d, 23, 22, 20, 19), 400)
    pad = _pick(d, 28, 24, 18, 14)
    gap = _pick(d, 18, 16, 12, 10)
    bx = M + stub + 32
    tw = W - M - 30 - bx
    for t in day.tasks:
        tl = wrap(t.title, tf, tw, 3 if d < 2 else 2)
        nl = wrap(_note(t, lang, d), nf, tw, 2 if d < 2 else 1) if _note(t, lang, d) else []
        lab = d < 3
        tlh, nlh = tf.size * 1.25, nf.size * 1.38
        h = 2 * pad + (28 if lab else 0) + len(tl) * tlh + (len(nl) * nlh + 4 if nl else 0)
        h = max(h, 112 if t.end is not None else 84)
        c.shadow(M, y, W - 2 * M, h, 24, blur=18, color=(90, 50, 20, 20), dy=6)
        col = {"high": sun, "medium": med, "low": low}[t.priority]
        fg = "#FFFFFF" if t.priority == "high" else P.ink
        c.rect(M, y, stub, h, 24, col, corners=(True, False, False, True))
        c.rect(M + stub, y, W - 2 * M - stub, h, 24, P.card, corners=(False, True, True, False))
        for py in (y, y + h):
            c.circle(M + stub, py, 11, P.bg)
        for dy in range(int(y + 22), int(y + h - 18), 16):
            c.line(M + stub, dy, M + stub, dy + 7, mix(P.line, P.ink, .25), 2)
        if t.start is not None:
            c.text(M + stub / 2, y + pad + 4, t.time, F("Inter", _pick(d, 32, 30, 27, 25), 800), fg, anchor="ma")
            if t.end is not None:
                c.text(M + stub / 2, y + pad + 48, hhmm(t.end), F("Inter", 21, 600),
                       mix(fg, col, .3), anchor="ma")
        else:
            c.text(M + stub / 2, y + h / 2, "··", F("Inter", 30, 800), fg, anchor="mm")
        iy = y + pad
        if lab:
            c.text(bx, iy, category(lang, t.category).upper(), F("Inter", 16, 800), P.muted, tracking=2.5)
            iy += 28
        c.lines(bx, iy - 2, tl, tf, P.ink, tlh)
        if nl:
            c.lines(bx, iy - 2 + len(tl) * tlh + 4, nl, nf, _nc(t, P.muted, "#D9542B"), nlh)
        y += h + gap

    fy = max(y + 30, c.h - 86)
    c.text(M, fy, f"{w(lang, 'plan_of_day')} · {date_long(lang, day.date)}", F("Inter", 19, 650), P.muted)
    return fy + 60


TEMPLATES = [editorial, timeline, bento, swiss, soft, notebook, sunrise]
