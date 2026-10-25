# Daily Planner Bot

Telegram bot. Ertangi rejangizni istalgan ko‘rinishda yozasiz yoki ovozli xabar qilib aytasiz. Bot AI yordamida uni tartibga soladi, chiroyli rasm qiladi va kanalingizga checklist bilan joylaydi. Vazifa boshlanganda karta yuboradi, eslatadi, kun, hafta va oy bo‘yicha hisobot beradi. Ko‘p foydalanuvchili: har bir user o‘z Gemini/Groq kalitini va o‘z kanalini ulaydi.

## Imkoniyatlar

- **Matn yoki ovoz** (o‘zbek / rus / ingliz, aralash ham bo‘ladi) → tartibli reja: vaqt, muhimlik, kategoriya.
- **7 ta shablon**: Editorial, Sage, Bento, Swiss, Soft, Notebook, Sunrise. Haftaning har kuni boshqasi chiqadi yoki bittasini doimiy qilib tanlash mumkin. Vazifalar soniga qarab shablon zichligi o‘zi moslashadi.
- **Preview**: ✅ kanalga joylash · ✏️ matn yoki ovoz bilan tahrirlash · 🎨 boshqa dizayn.
- **Kanalda checklist**: tugmalarni faqat egasi bosa oladi, progress caption'da ko‘rinadi.
- **Task-karta**: har bir vazifa boshlanganda kanalga rasm tushadi, uslubi muhimlikka qarab o‘zgaradi. Shaxsiy chatga oldindan eslatma ham keladi.
- **Ertalabki post, kechki yakun**: bajarilmaganlarni ertangi kunga o‘tkazish tugmasi bilan.
- **Haftalik va oylik hisobot**: rasm va AI xulosasi bilan. `/report` orqali istalgan payt so‘rash mumkin.
- **Xotira**: ish vaqti, odatlar va maqsadlar kabi faqat muhim faktlar saqlanadi (`/memory`, `/remember`).
- **AI orkestratsiya**: avval Gemini, limit tugasa yoki xato bersa Groq. Limitga tushgan model vaqtincha chetlab o‘tiladi.
- API kalitlar **shifrlangan** holda saqlanadi, kalit yuborilgan xabar darhol o‘chiriladi.

## Deploy (Render + Supabase, $0)

1. **Bot**: @BotFather → `/newbot` → token oling.
2. **Supabase**: yangi loyiha oching → *Project Settings → Database → Connection string → Transaction pooler* (port 6543). Jadvallar bot ilk ishga tushganda avtomatik yaratiladi.
   ⚠️ `db.<ref>.supabase.co` (direct) manzili faqat IPv6'da ishlaydi va Render'dan ulanmaydi. Doim **pooler** manzilidan foydalaning: `postgres.<ref>@aws-0-<region>.pooler.supabase.com:6543`. `render.yaml` dagi `region` ni bazangizga yaqin qilib tanlang.
3. **Shifrlash kaliti**: `python scripts/gen_key.py`. Uni saqlab qo‘ying va hech qachon o‘zgartirmang.
4. **GitHub**: loyihani repo'ga push qiling.
5. **Render**: *New → Blueprint* → repo'ni tanlang (`render.yaml` ishlatiladi). `BOT_TOKEN`, `DATABASE_URL`, `ENCRYPTION_KEY` qiymatlarini kiriting. `WEBHOOK_SECRET` va `TICK_KEY` avtomatik yaratiladi.
6. **cron-job.org** (bepul): har 5 daqiqada `https://<app>.onrender.com/tick?key=<TICK_KEY>` ga so‘rov yuboradigan job qo‘shing. Bu bepul servisni uyg‘oq ushlab turadi va rejalashtirilgan ishlar o‘z vaqtida bajarilishini kafolatlaydi.

> Render'ning bepul tarifi 15 daqiqa harakatsizlikdan keyin uxlab qoladi. Ping yuborilib turganda uxlamaydi, oylik 750 soat bitta servis uchun yetadi.

## Lokal ishga tushirish

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
cp .env.example .env   # BOT_TOKEN, DATABASE_URL, ENCRYPTION_KEY ni to‘ldiring
python -m bot.main     # PUBLIC_URL bo‘sh bo‘lsa long polling rejimida ishlaydi
```

Shablonlarni namuna ma’lumot bilan ko‘rish: `python scripts/preview.py` → `previews/`.

## Testlar

```bash
python tests/test_core.py                                     # offline: normalize, tz, scheduling, AI fallback
TEST_DATABASE_URL=postgresql://... python tests/test_db.py    # SQL
TEST_DATABASE_URL=postgresql://... python tests/test_flow.py  # butun bot oqimi (soxta Telegram + soxta AI)
```

## Tuzilma

```
bot/
  main.py        webhook server (/webhook, /health, /tick) yoki polling
  handlers.py    onboarding, reja, checklist, sozlamalar, hisobot, xotira
  planner.py     AI orqali reja tuzish va tahrirlash, normalizatsiya, eslatmalarni rejalashtirish
  ai.py          Gemini → Groq orkestratsiyasi, ovozni matnga aylantirish
  prompts.py     AI promptlari
  scheduler.py   eslatma, task-karta, ertalabki/kechki post, hisobotlar
  reports.py     hisobot statistikasi
  channel.py     kanal posti va checklist
  db.py          Postgres sxemasi va so‘rovlar
  i18n.py        uz / ru / en matnlar
  render/        rasm generatsiyasi (Pillow): 7 shablon, task va hisobot kartalari
assets/fonts/    Google Fonts (SIL Open Font License)
```
