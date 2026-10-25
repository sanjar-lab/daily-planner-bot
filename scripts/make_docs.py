"""Regenerate the README images in docs/images (python scripts/make_docs.py)."""
import datetime as dt
import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot.render import N_THEMES, render_day, render_report, render_task  # noqa: E402
from bot.render.themes import PALETTES  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs" / "images"

PLAN = {
    "date": "2026-10-26",
    "headline": "Deep work and a healthy rhythm",
    "focus": "Ship the planner demo and send it to the client",
    "tasks": [
        {"idx": 0, "title": "Morning run and stretching", "start": "06:30", "end": "07:15", "priority": "medium", "category": "sport", "done": True},
        {"idx": 1, "title": "Build the rendering module", "start": "09:00", "end": "11:30", "priority": "high", "category": "work",
         "note": "7 templates, dynamic height, task cards"},
        {"idx": 2, "title": "Team stand-up", "start": "11:30", "end": "12:00", "priority": "medium", "category": "work"},
        {"idx": 3, "title": "Lunch", "start": "13:00", "end": "14:00", "priority": "low", "category": "rest"},
        {"idx": 4, "title": "Send the demo to the client", "start": "15:00", "end": "15:45", "priority": "high", "category": "work",
         "note": "Video + short written summary"},
        {"idx": 5, "title": "English: 30 new words", "start": "19:00", "end": "19:45", "priority": "medium", "category": "study"},
        {"idx": 6, "title": "Pick up medicine", "priority": "low", "category": "errand"},
    ],
}


def jpg(raw: bytes, width: int) -> Image.Image:
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    return im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)


def save(im: Image.Image, name: str):
    im.save(OUT / name, "JPEG", quality=86, optimize=True, progressive=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    thumbs = []
    for i in range(N_THEMES):
        im = jpg(render_day(PLAN, "en", i), 540)
        save(im, f"template-{i + 1}-{PALETTES[i].name.lower()}.jpg")
        top = Image.new("RGB", (540, 675), im.getpixel((4, im.height - 4)))
        top.paste(im.crop((0, 0, 540, min(675, im.height))), (0, 0))
        thumbs.append(top.resize((360, 450), Image.LANCZOS))

    # showcase: 4 + 3 grid on a soft background
    gap, cols = 24, 4
    w = cols * 360 + (cols + 1) * gap
    h = 2 * 450 + 3 * gap
    sheet = Image.new("RGB", (w, h), "#ECEAE4")
    d = ImageDraw.Draw(sheet)
    for i, th in enumerate(thumbs):
        r, c = divmod(i, cols)
        x = gap + c * (360 + gap) + (0 if r == 0 else (360 + gap) // 2)
        y = gap + r * (450 + gap)
        d.rounded_rectangle([x + 3, y + 5, x + 363, y + 455], 18, fill="#D9D6CE")
        mask = Image.new("L", th.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, 359, 449], 18, fill=255)
        sheet.paste(th, (x, y), mask)
    save(sheet, "showcase.jpg")

    save(jpg(render_task(PLAN, 1, "en", 6), 540), "task-card.jpg")
    added = dict(PLAN, tasks=PLAN["tasks"] + [
        {"idx": 7, "title": "Call mom", "start": "16:30", "priority": "high", "category": "family", "added": True},
        {"idx": 8, "title": "Read 30 minutes", "start": "21:00", "end": "21:30", "priority": "medium",
         "category": "study", "added": True}])
    save(jpg(render_day(added, "en", 5), 540), "added-tasks.jpg")
    days = [(dt.date(2026, 10, 19) + dt.timedelta(i), n, 7) for i, n in enumerate([5, 7, 3, 6, 7, 2, 4])]
    rep = dict(kind="week", start=days[0][0], end=days[-1][0], days=days, high_done=9, high_total=12, streak=4,
               best_day=days[1][0], insight="You finish morning tasks almost every day while evening plans slip. "
                                            "Put your key work before noon.")
    save(jpg(render_report(rep, "en", 2), 540), "report.jpg")
    print("written to", OUT)


if __name__ == "__main__":
    main()
