"""Small drawing toolkit on top of Pillow.

Everything is drawn at SS-times resolution and downscaled at the end, which gives
smooth anti-aliased shapes and crisp text while staying light on CPU and RAM.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"
SS = 2
FALLBACK = "Onest"

_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF️‍⃣]"
)


def clean(s: str | None) -> str:
    s = _EMOJI.sub("", s or "")
    s = s.replace("ʻ", "‘").replace("ʼ", "’").replace("`", "‘")
    return re.sub(r"\s+", " ", s).strip()


def rgba(c, a: int | None = None) -> tuple:
    if c is None:
        return None
    if isinstance(c, str):
        c = c.lstrip("#")
        if len(c) == 3:
            c = "".join(ch * 2 for ch in c)
        t = tuple(int(c[i:i + 2], 16) for i in range(0, len(c), 2))
        c = t if len(t) == 4 else (*t, 255)
    elif len(c) == 3:
        c = (*c, 255)
    if a is not None:
        c = (*c[:3], a)
    return tuple(c)


def mix(c1, c2, t: float) -> tuple:
    """Blend c1 toward c2 by t (0..1). Returns an opaque colour."""
    a, b = rgba(c1), rgba(c2)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


@dataclass(frozen=True)
class F:
    family: str
    size: float
    weight: int = 400


@lru_cache(None)
def _cmap(family: str) -> frozenset:
    return frozenset(TTFont(FONT_DIR / f"{family}.ttf").getBestCmap())


@lru_cache(maxsize=512)
def _load(family: str, size: float, weight: int) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONT_DIR / f"{family}.ttf"), max(1, int(round(size * SS))))
    try:
        vals = []
        for ax in f.get_variation_axes():
            name = ax["name"].decode() if isinstance(ax["name"], bytes) else str(ax["name"])
            lo, hi = ax["minimum"], ax["maximum"]
            if name.lower().startswith("weight"):
                v = weight
            elif name.lower().startswith("optical"):
                v = size * 0.75
            else:
                v = ax.get("default", lo)
            vals.append(max(lo, min(hi, v)))
        f.set_variation_by_axes(vals)
    except OSError:
        pass
    return f


def font(spec: F, text: str = "") -> ImageFont.FreeTypeFont:
    family = spec.family
    if text and any(ord(ch) not in _cmap(family) for ch in text if not ch.isspace()):
        family = FALLBACK
    return _load(family, spec.size, spec.weight)


def text_w(text: str, spec: F, tracking: float = 0) -> float:
    if not text:
        return 0
    return font(spec, text).getlength(text) / SS + tracking * max(0, len(text) - 1)


def wrap(text: str, spec: F, max_w: float, max_lines: int = 0) -> list[str]:
    words = clean(text).split(" ")
    lines: list[str] = []
    cur = ""
    for wd in words:
        if not wd:
            continue
        trial = f"{cur} {wd}".strip()
        if text_w(trial, spec) <= max_w or not cur:
            cur = trial
            # a single word wider than the box: hard-split it
            while text_w(cur, spec) > max_w and len(cur) > 1:
                cut = len(cur)
                while cut > 1 and text_w(cur[:cut], spec) > max_w:
                    cut -= 1
                lines.append(cur[:cut])
                cur = cur[cut:]
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and text_w(last + "…", spec) > max_w:
            last = last[:-1].rstrip()
        lines[-1] = last + "…"
    return lines or [""]


class Canvas:
    real = True

    def __init__(self, w: int, h: int, bg="#ffffff"):
        self.w, self.h = int(w), int(h)
        self.im = Image.new("RGBA", (self.w * SS, self.h * SS), rgba(bg))
        self.dr = ImageDraw.Draw(self.im)

    # ---- primitives -------------------------------------------------------
    @staticmethod
    def _s(v: float) -> int:
        return int(round(v * SS))

    def _box(self, x, y, w, h):
        return [self._s(x), self._s(y), self._s(x + w) - 1, self._s(y + h) - 1]

    def _local(self, x, y, w, h, pad=0):
        """Transparent layer covering a region (for alpha blending)."""
        x0, y0 = self._s(x - pad), self._s(y - pad)
        lw, lh = self._s(w + 2 * pad), self._s(h + 2 * pad)
        return Image.new("RGBA", (max(1, lw), max(1, lh)), (0, 0, 0, 0)), x0, y0

    def _composite(self, layer, x0, y0):
        self.im.alpha_composite(layer, (max(0, x0), max(0, y0)),
                                (max(0, -x0), max(0, -y0)))

    def rect(self, x, y, w, h, r=0, fill=None, outline=None, width=0, corners=None):
        fill, outline = rgba(fill), rgba(outline)
        translucent = (fill and fill[3] < 255) or (outline and outline[3] < 255)
        kw = dict(radius=self._s(r), fill=fill, outline=outline,
                  width=self._s(width) if outline else 0)
        if corners is not None:
            kw["corners"] = corners
        if not translucent:
            self.dr.rounded_rectangle(self._box(x, y, w, h), **kw)
            return
        layer, x0, y0 = self._local(x, y, w, h)
        ImageDraw.Draw(layer).rounded_rectangle([0, 0, layer.width - 1, layer.height - 1], **kw)
        self._composite(layer, x0, y0)

    def circle(self, cx, cy, r, fill=None, outline=None, width=0):
        fill, outline = rgba(fill), rgba(outline)
        box = [self._s(cx - r), self._s(cy - r), self._s(cx + r), self._s(cy + r)]
        if (fill and fill[3] < 255) or (outline and outline[3] < 255):
            layer, x0, y0 = self._local(cx - r, cy - r, 2 * r, 2 * r, pad=1)
            off = self._s(1)
            ImageDraw.Draw(layer).ellipse(
                [off, off, off + self._s(2 * r), off + self._s(2 * r)],
                fill=fill, outline=outline, width=self._s(width) if outline else 0)
            self._composite(layer, x0, y0)
            return
        self.dr.ellipse(box, fill=fill, outline=outline, width=self._s(width) if outline else 0)

    def line(self, x1, y1, x2, y2, fill, width=1):
        self.dr.line([self._s(x1), self._s(y1), self._s(x2), self._s(y2)],
                     fill=rgba(fill), width=max(1, self._s(width)))

    def polyline(self, pts, fill, width=1):
        self.dr.line([(self._s(x), self._s(y)) for x, y in pts], fill=rgba(fill),
                     width=max(1, self._s(width)), joint="curve")

    def arc(self, cx, cy, r, start, end, fill, width):
        box = [self._s(cx - r), self._s(cy - r), self._s(cx + r), self._s(cy + r)]
        self.dr.arc(box, start, end, fill=rgba(fill), width=self._s(width))
        # rounded caps
        for ang in (start, end):
            a = math.radians(ang)
            rr = r - width / 2
            self.circle(cx + rr * math.cos(a), cy + rr * math.sin(a), width / 2, fill=fill)

    def shadow(self, x, y, w, h, r=0, blur=24, color=(0, 0, 0, 30), dy=8):
        pad = blur * 2
        layer, x0, y0 = self._local(x, y + dy, w, h, pad=pad)
        p = self._s(pad)
        ImageDraw.Draw(layer).rounded_rectangle(
            [p, p, p + self._s(w), p + self._s(h)], radius=self._s(r), fill=rgba(color))
        layer = layer.filter(ImageFilter.GaussianBlur(self._s(blur) / 2))
        self._composite(layer, x0, y0)

    def check(self, x, y, size, fill, width=3):
        """Check mark inside a size*size box at (x, y)."""
        self.polyline([(x + size * .22, y + size * .52), (x + size * .42, y + size * .72),
                       (x + size * .78, y + size * .30)], fill, width)

    # ---- text -------------------------------------------------------------
    def text(self, x, y, s, spec: F, fill, anchor="la", tracking: float = 0):
        s = clean(s)
        if not s:
            return 0
        f = font(spec, s)
        fill = rgba(fill)
        if not tracking:
            self.dr.text((self._s(x), self._s(y)), s, font=f, fill=fill, anchor=anchor)
            return text_w(s, spec)
        total = text_w(s, spec, tracking)
        h = anchor[0]
        cx = x - (total if h == "r" else total / 2 if h == "m" else 0)
        for ch in s:
            self.dr.text((self._s(cx), self._s(y)), ch, font=f, fill=fill, anchor="l" + anchor[1])
            cx += f.getlength(ch) / SS + tracking
        return total

    def lines(self, x, y, lines: list[str], spec: F, fill, lh: float, anchor="la"):
        for i, ln in enumerate(lines):
            self.text(x, y + i * lh, ln, spec, fill, anchor=anchor)
        return len(lines) * lh

    # ---- backgrounds --------------------------------------------------------
    def vgradient(self, top, bottom, x=0, y=0, w=None, h=None):
        w, h = w or self.w, h or self.h
        grad = Image.linear_gradient("L").resize((self._s(w), self._s(h)))
        a = Image.new("RGBA", grad.size, rgba(top))
        b = Image.new("RGBA", grad.size, rgba(bottom))
        self.im.paste(Image.composite(b, a, grad), (self._s(x), self._s(y)))

    def blobs(self, blobs: list[tuple], blur: float = 120):
        """Soft colour fields: list of (cx, cy, r, colour). Rendered at low res for speed."""
        k = 8
        small = Image.new("RGBA", (max(1, self.w // k), max(1, self.h // k)), (0, 0, 0, 0))
        d = ImageDraw.Draw(small)
        for cx, cy, r, col in blobs:
            d.ellipse([(cx - r) / k, (cy - r) / k, (cx + r) / k, (cy + r) / k], fill=rgba(col))
        small = small.filter(ImageFilter.GaussianBlur(blur / k))
        self.im.alpha_composite(small.resize(self.im.size, Image.BICUBIC))

    def dots(self, step, r, fill, x0=0, y0=0):
        col = rgba(fill)
        rr = self._s(r)
        y = y0
        while y < self.h:
            x = x0
            while x < self.w:
                cx, cy = self._s(x), self._s(y)
                self.dr.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=col)
                x += step
            y += step

    def grain(self, amount: int = 6):
        noise = Image.effect_noise(self.im.size, 40).convert("L")
        noise = noise.point(lambda v: 128 + (v - 128) * amount // 40)
        overlay = Image.merge("RGBA", [noise, noise, noise, Image.new("L", noise.size, 18)])
        self.im.alpha_composite(overlay)

    # ---- output -------------------------------------------------------------
    def to_bytes(self, fmt: str = "PNG") -> bytes:
        out = self.im.resize((self.w, self.h), Image.LANCZOS).convert("RGB")
        buf = BytesIO()
        if fmt == "JPEG":
            out.save(buf, "JPEG", quality=94, subsampling=0, optimize=True)
        else:
            out.save(buf, "PNG", compress_level=6)
        return buf.getvalue()
