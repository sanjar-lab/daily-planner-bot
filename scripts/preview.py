"""Render every template with sample plans into ./previews (dev helper)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot.render import N_THEMES, render_day, render_report, render_task  # noqa: E402

from bot.render.sample import SAMPLE  # noqa: E402

BUSY = dict(SAMPLE, headline="Juda band kun", tasks=SAMPLE["tasks"] * 2 + SAMPLE["tasks"][:2])
LIGHT = dict(SAMPLE, headline="Yengil yakshanba", focus="", tasks=SAMPLE["tasks"][2:5])

if __name__ == "__main__":
    out = Path("previews")
    out.mkdir(exist_ok=True)
    only = [int(a) for a in sys.argv[1:]] or range(N_THEMES)
    for th in only:
        for name, plan, lang in (("std", SAMPLE, "uz"), ("busy", BUSY, "ru"), ("light", LIGHT, "en")):
            t0 = time.perf_counter()
            (out / f"t{th}_{name}.jpg").write_bytes(render_day(plan, lang, th))
            print(f"t{th} {name}: {time.perf_counter() - t0:.2f}s")
        (out / f"t{th}_task_high.jpg").write_bytes(render_task(SAMPLE, 1, "uz", th))
        (out / f"t{th}_task_med.jpg").write_bytes(render_task(SAMPLE, 2, "uz", th))
        import datetime as dt
        days = [(dt.date(2026, 10, 19) + dt.timedelta(i), d, 7) for i, d in enumerate([5, 7, 3, 6, 7, 2, 4])]
        rep = dict(kind="week", start=days[0][0], end=days[-1][0], days=days, high_done=9, high_total=12,
                   streak=4, best_day=days[1][0],
                   insight="Ertalabki vazifalarni deyarli doim bajarasiz, kechki rejalar esa ko‘pincha qoladi. Muhim ishlarni 12:00 gacha qo‘ying.")
        (out / f"t{th}_report.jpg").write_bytes(render_report(rep, "uz", th))
