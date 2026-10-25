"""Bot interface strings in Uzbek, Russian and English."""

LANGS = {"uz": "🇺🇿 O‘zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}

T = {
    "choose_lang": {
        "uz": "Tilni tanlang · Выберите язык · Choose language",
        "ru": "Tilni tanlang · Выберите язык · Choose language",
        "en": "Tilni tanlang · Выберите язык · Choose language",
    },
    "welcome": {
        "uz": "👋 <b>Salom, {name}!</b>\n\nMen sizning shaxsiy rejalashtiruvchingizman. Har kuni kechqurun ertangi ishlaringizni "
              "qanday bo‘lsa shunday yozasiz yoki ovozli xabar qilib aytasiz. Men ularni tartibga solaman, chiroyli rasmga "
              "joylayman va kanalingizga checklist bilan tashlayman. Vazifa vaqti kelganda eslataman, hafta va oy oxirida hisobot beraman.\n\n"
              "Sozlash 1 daqiqa oladi. Boshladik 👇",
        "ru": "👋 <b>Привет, {name}!</b>\n\nЯ твой личный планировщик. Каждый вечер ты пишешь или надиктовываешь планы на завтра "
              "как угодно — я структурирую их, оформляю в красивую картинку и публикую в твой канал с чек-листом. "
              "Напоминаю о задачах и присылаю отчёты за неделю и месяц.\n\nНастройка займёт минуту 👇",
        "en": "👋 <b>Hi, {name}!</b>\n\nI'm your personal planner. Every evening you type or voice tomorrow's plans however you like — "
              "I structure them, design a beautiful image and post it to your channel with a checklist. "
              "I remind you when tasks start and send weekly and monthly reports.\n\nSetup takes a minute 👇",
    },
    "ask_gemini": {
        "uz": "<b>1/4 · Gemini API kaliti</b> 🧠\n\nGemini botning asosiy AI'si: rejangizni tushunadi va tartibga soladi. "
              "Kalit <b>bepul</b>, olish 1 daqiqa vaqt oladi.\n\n👇 Saytni oching, kalitni nusxalab <b>shu chatga yuboring</b>. "
              "Qiyin bo'lsa, <b>📖 Qanday olaman?</b> tugmasini bosing.",
        "ru": "<b>1/4 · Ключ Gemini API</b> 🧠\n\nGemini — основной AI бота: понимает и структурирует твой план. "
              "Ключ <b>бесплатный</b>, получить его можно за минуту.\n\n👇 Открой сайт, скопируй ключ и <b>отправь его в этот чат</b>. "
              "Если непонятно, нажми <b>📖 Как получить?</b>",
        "en": "<b>1/4 · Gemini API key</b> 🧠\n\nGemini is the bot's main AI: it understands and structures your plan. "
              "The key is <b>free</b> and takes a minute to get.\n\n👇 Open the site, copy the key and <b>send it to this chat</b>. "
              "Not sure how? Tap <b>📖 How do I get it?</b>",
    },
    "ask_groq": {
        "uz": "<b>2/4 · Groq API kaliti</b> ⚡ (zaxira AI)\n\nGemini limiti tugasa, bot Groq'ga o'tadi va to'xtab qolmaydi. "
              "Groq ovozli xabarlarni ham juda tez taniydi. Kalit <b>bepul</b>.\n\n👇 Kalitni olib <b>shu chatga yuboring</b>. "
              "Hozir xohlamasangiz, o'tkazib yuborishingiz mumkin.",
        "ru": "<b>2/4 · Ключ Groq API</b> ⚡ (резервный AI)\n\nКогда лимит Gemini закончится, бот переключится на Groq и не остановится. "
              "Groq ещё очень быстро распознаёт голосовые. Ключ <b>бесплатный</b>.\n\n👇 Получи ключ и <b>отправь его в этот чат</b>. "
              "Можно и пропустить.",
        "en": "<b>2/4 · Groq API key</b> ⚡ (backup AI)\n\nWhen Gemini's limit runs out, the bot switches to Groq and keeps going. "
              "Groq also transcribes voice messages very fast. The key is <b>free</b>.\n\n👇 Get the key and <b>send it to this chat</b>. "
              "You can skip this for now.",
    },
    "btn_open_gemini": {"uz": "🔗 Google AI Studio'ni ochish", "ru": "🔗 Открыть Google AI Studio", "en": "🔗 Open Google AI Studio"},
    "btn_open_groq": {"uz": "🔗 Groq Console'ni ochish", "ru": "🔗 Открыть Groq Console", "en": "🔗 Open Groq Console"},
    "btn_howto": {"uz": "📖 Qanday olaman? (qadamma-qadam)", "ru": "📖 Как получить? (пошагово)", "en": "📖 How do I get it? (step by step)"},
    "btn_why": {"uz": "❓ Nega kalit kerak?", "ru": "❓ Зачем нужен ключ?", "en": "❓ Why a key?"},
    "btn_back": {"uz": "← Orqaga", "ru": "← Назад", "en": "← Back"},
    "howto_gemini": {
        "uz": "📖 <b>Gemini kalitini olish (1 daqiqa, bepul)</b>\n\n"
              "1️⃣ Pastdagi <b>🔗 Google AI Studio</b> tugmasini bosing\n"
              "2️⃣ Google akkauntingiz (Gmail) bilan kiring\n"
              "3️⃣ <b>Create API key</b> tugmasini bosing. So'rasa, <b>Create project</b> ni tanlang\n"
              "4️⃣ Chiqqan kalit yonidagi 📋 <b>Copy</b> ni bosing (kalit <code>AIza…</code> yoki <code>AQ.…</code> bilan boshlanadi)\n"
              "5️⃣ Shu chatga qaytib, kalitni oddiy xabar qilib yuboring\n\n"
              "✅ Bepul limit bir kishiga bemalol yetadi, karta kerak emas.\n"
              "🔒 Kalit shifrlanib saqlanadi, xabaringiz darhol o'chiriladi.",
        "ru": "📖 <b>Как получить ключ Gemini (1 минута, бесплатно)</b>\n\n"
              "1️⃣ Нажми <b>🔗 Google AI Studio</b> ниже\n"
              "2️⃣ Войди через Google-аккаунт (Gmail)\n"
              "3️⃣ Нажми <b>Create API key</b>. Если попросит, выбери <b>Create project</b>\n"
              "4️⃣ Нажми 📋 <b>Copy</b> рядом с ключом (начинается с <code>AIza…</code> или <code>AQ.…</code>)\n"
              "5️⃣ Вернись сюда и отправь ключ обычным сообщением\n\n"
              "✅ Бесплатного лимита хватает одному человеку с запасом, карта не нужна.\n"
              "🔒 Ключ хранится зашифрованным, сообщение сразу удаляется.",
        "en": "📖 <b>Getting a Gemini key (1 minute, free)</b>\n\n"
              "1️⃣ Tap <b>🔗 Google AI Studio</b> below\n"
              "2️⃣ Sign in with your Google account (Gmail)\n"
              "3️⃣ Tap <b>Create API key</b>. If asked, choose <b>Create project</b>\n"
              "4️⃣ Tap 📋 <b>Copy</b> next to the key (it starts with <code>AIza…</code> or <code>AQ.…</code>)\n"
              "5️⃣ Come back here and send the key as a normal message\n\n"
              "✅ The free tier is plenty for one person, no card needed.\n"
              "🔒 The key is stored encrypted and your message is deleted right away.",
    },
    "howto_groq": {
        "uz": "📖 <b>Groq kalitini olish (1 daqiqa, bepul)</b>\n\n"
              "1️⃣ Pastdagi <b>🔗 Groq Console</b> tugmasini bosing\n"
              "2️⃣ Google yoki GitHub akkaunti bilan kiring\n"
              "3️⃣ <b>Create API Key</b> tugmasini bosing va istalgan nom bering (masalan <code>planner</code>)\n"
              "4️⃣ Kalitni nusxalang (<code>gsk_…</code> bilan boshlanadi). ⚠️ Kalit faqat bir marta ko'rsatiladi\n"
              "5️⃣ Shu chatga kalitni yuboring\n\n"
              "💡 Groq zaxira AI vazifasini bajaradi: Gemini limiti tugasa, bot to'xtab qolmaydi. Ovozli xabarlarni ham juda tez taniydi.",
        "ru": "📖 <b>Как получить ключ Groq (1 минута, бесплатно)</b>\n\n"
              "1️⃣ Нажми <b>🔗 Groq Console</b> ниже\n"
              "2️⃣ Войди через Google или GitHub\n"
              "3️⃣ Нажми <b>Create API Key</b> и дай любое имя (например <code>planner</code>)\n"
              "4️⃣ Скопируй ключ (начинается с <code>gsk_…</code>). ⚠️ Он показывается только один раз\n"
              "5️⃣ Отправь ключ сюда\n\n"
              "💡 Groq — резервный AI: если лимит Gemini закончится, бот продолжит работать. Ещё он очень быстро распознаёт голосовые.",
        "en": "📖 <b>Getting a Groq key (1 minute, free)</b>\n\n"
              "1️⃣ Tap <b>🔗 Groq Console</b> below\n"
              "2️⃣ Sign in with Google or GitHub\n"
              "3️⃣ Tap <b>Create API Key</b> and give it any name (e.g. <code>planner</code>)\n"
              "4️⃣ Copy the key (starts with <code>gsk_…</code>). ⚠️ It's shown only once\n"
              "5️⃣ Send the key here\n\n"
              "💡 Groq is the backup AI: when Gemini's limit runs out the bot keeps working. It also transcribes voice messages very fast.",
    },
    "why_keys": {
        "uz": "❓ <b>Nega kalit kerak?</b>\n\nBot har bir foydalanuvchi uchun uning o'z AI kaliti bilan ishlaydi. Bu uch narsani beradi:\n\n"
              "• <b>Bepul</b>: Gemini va Groq'ning bepul limitlari kundalik rejalashtirishga bemalol yetadi\n"
              "• <b>Limit faqat sizniki</b>: boshqa foydalanuvchilar sizning limitingizni ishlatmaydi\n"
              "• <b>Ishonchli</b>: Gemini asosiy AI, Groq zaxira. Birining limiti tugasa, bot avtomatik ikkinchisiga o'tadi\n\n"
              "🔒 Kalitlar shifrlangan holda saqlanadi. Istalgan payt /settings → 🔑 Kalitlar orqali almashtirasiz yoki o'chirasiz.",
        "ru": "❓ <b>Зачем нужен ключ?</b>\n\nБот работает для каждого пользователя через его собственный AI-ключ. Это даёт три вещи:\n\n"
              "• <b>Бесплатно</b>: бесплатных лимитов Gemini и Groq хватает для ежедневного планирования\n"
              "• <b>Лимит только твой</b>: другие пользователи его не тратят\n"
              "• <b>Надёжно</b>: Gemini — основной AI, Groq — резерв. Если лимит одного закончится, бот сам переключится на другой\n\n"
              "🔒 Ключи хранятся зашифрованными. Сменить или удалить: /settings → 🔑 Ключи.",
        "en": "❓ <b>Why a key?</b>\n\nThe bot runs on each user's own AI key. That gives you three things:\n\n"
              "• <b>Free</b>: Gemini's and Groq's free tiers easily cover daily planning\n"
              "• <b>The limit is yours alone</b>: other users don't spend it\n"
              "• <b>Reliable</b>: Gemini is the main AI, Groq the backup. If one runs out, the bot switches automatically\n\n"
              "🔒 Keys are stored encrypted. Replace or remove them anytime: /settings → 🔑 Keys.",
    },
    "groq_skip_warn": {
        "uz": "⚠️ Groq'siz ham ishlaydi, lekin Gemini limiti tugasa bot javob bermay qoladi. Kalitni keyinroq /settings → 🔑 Kalitlar orqali qo'shishingiz mumkin.",
        "ru": "⚠️ Без Groq тоже работает, но когда лимит Gemini закончится, бот перестанет отвечать. Добавить можно позже: /settings → 🔑 Ключи.",
        "en": "⚠️ Works without Groq, but when Gemini's limit runs out the bot will stop answering. You can add it later: /settings → 🔑 Keys.",
    },
    "checking": {"uz": "🔑 Tekshiryapman…", "ru": "🔑 Проверяю…", "en": "🔑 Checking…"},
    "key_ok": {"uz": "✅ Kalit ishlayapti: <code>{mask}</code>", "ru": "✅ Ключ работает: <code>{mask}</code>",
               "en": "✅ Key works: <code>{mask}</code>"},
    "key_bad": {"uz": "❌ Bu kalit ishlamadi. Tekshirib, qayta yuboring.", "ru": "❌ Ключ не подошёл. Проверь и отправь ещё раз.",
                "en": "❌ That key didn't work. Check it and send again."},
    "key_unsure": {"uz": "⚠️ Hozir tekshira olmadim, lekin saqlab qo‘ydim.", "ru": "⚠️ Не смог проверить сейчас, но сохранил.",
                   "en": "⚠️ Couldn't verify right now, but saved it."},
    "ask_tz": {
        "uz": "<b>3/4 · Vaqt zonasi</b>\n\nEslatmalar to‘g‘ri vaqtda kelishi uchun zonangizni tanlang yoki yozing (masalan <code>Asia/Tashkent</code> yoki <code>+5</code>).",
        "ru": "<b>3/4 · Часовой пояс</b>\n\nВыбери пояс или напиши его (например <code>Europe/Moscow</code> или <code>+3</code>), чтобы напоминания приходили вовремя.",
        "en": "<b>3/4 · Time zone</b>\n\nPick your zone or type it (e.g. <code>Europe/London</code> or <code>+1</code>) so reminders arrive on time.",
    },
    "tz_bad": {"uz": "Bunday zonani tanimadim. Masalan: <code>Asia/Tashkent</code> yoki <code>+5</code>",
               "ru": "Не узнал пояс. Например: <code>Europe/Moscow</code> или <code>+3</code>",
               "en": "Unknown zone. E.g. <code>Europe/London</code> or <code>+1</code>"},
    "tz_ok": {"uz": "🕒 Vaqt zonasi: <b>{tz}</b> (hozir {time})", "ru": "🕒 Часовой пояс: <b>{tz}</b> (сейчас {time})",
              "en": "🕒 Time zone: <b>{tz}</b> (now {time})"},
    "ask_channel": {
        "uz": "<b>4/4 · Kanal</b>\n\nRejalar tushadigan kanalni ulaymiz. Pastdagi <b>📢 Kanalni tanlash</b> tugmasini bosing va kanalingizni tanlang. "
              "Telegram botni o‘zi admin qilib qo‘shadi.\n\nYoki botni kanalga qo‘lda admin qiling va kanaldan istalgan postni shu yerga forward qiling.",
        "ru": "<b>4/4 · Канал</b>\n\nПодключим канал для планов. Нажми <b>📢 Выбрать канал</b> внизу и выбери канал — Telegram сам добавит бота админом.\n\n"
              "Или добавь бота админом вручную и перешли сюда любой пост из канала.",
        "en": "<b>4/4 · Channel</b>\n\nLet's connect the channel for your plans. Tap <b>📢 Pick channel</b> below and choose it — Telegram adds the bot as admin.\n\n"
              "Or add the bot as admin manually and forward any post from the channel here.",
    },
    "btn_pick_channel": {"uz": "📢 Kanalni tanlash", "ru": "📢 Выбрать канал", "en": "📢 Pick channel"},
    "channel_ok": {"uz": "✅ Kanal ulandi: <b>{title}</b>", "ru": "✅ Канал подключён: <b>{title}</b>", "en": "✅ Channel connected: <b>{title}</b>"},
    "channel_bad": {
        "uz": "❌ Bot bu kanalda admin emas yoki post yozish huquqi yo‘q. Botni admin qiling (Post yozish + Tahrirlash) va qayta urinib ko‘ring.",
        "ru": "❌ Бот не админ в этом канале или не может публиковать. Дай права (Публикация + Редактирование) и попробуй снова.",
        "en": "❌ The bot isn't an admin there or can't post. Give it Post + Edit rights and try again.",
    },
    "ask_about": {
        "uz": "🧠 <b>Oxirgi qadam (ixtiyoriy)</b>\n\nO‘zingiz haqingizda qisqacha yozing yoki ayting: ish yoki o‘qish vaqtingiz, doimiy odatlaringiz, "
              "uzoq muddatli maqsadlaringiz. Men faqat rejalashtirish uchun muhimlarini eslab qolaman.",
        "ru": "🧠 <b>Последний шаг (по желанию)</b>\n\nКоротко расскажи о себе текстом или голосом: часы работы или учёбы, постоянные привычки, "
              "долгосрочные цели. Я запомню только то, что важно для планирования.",
        "en": "🧠 <b>Last step (optional)</b>\n\nTell me briefly, by text or voice: work or study hours, regular habits, long-term goals. "
              "I'll remember only what matters for planning.",
    },
    "learned": {"uz": "🧠 Eslab qoldim:\n{items}", "ru": "🧠 Запомнил:\n{items}", "en": "🧠 Got it:\n{items}"},
    "ready": {
        "uz": "🎉 <b>Tayyor!</b>\n\nEndi ertangi rejangizni istalgan ko‘rinishda yozing yoki ovozli xabar yuboring, masalan:\n"
              "<i>«ertaga 9 da ishga, 11 da mijoz bilan call muhim, tushlikdan keyin hisobot, kechqurun zal 1 soat, ingliz tili»</i>\n\n"
              "/settings — sozlamalar · /report — hisobot · /memory — xotira · /help",
        "ru": "🎉 <b>Готово!</b>\n\nТеперь пиши или надиктуй план на завтра как угодно, например:\n"
              "<i>«завтра в 9 на работу, в 11 важный созвон с клиентом, после обеда отчёт, вечером зал час, английский»</i>\n\n"
              "/settings — настройки · /report — отчёт · /memory — память · /help",
        "en": "🎉 <b>All set!</b>\n\nNow type or voice tomorrow's plan however you like, e.g.:\n"
              "<i>“work at 9, important client call at 11, report after lunch, gym 1h in the evening, english”</i>\n\n"
              "/settings · /report · /memory · /help",
    },
    "need_setup": {"uz": "Avval sozlashni tugatamiz 👇", "ru": "Сначала завершим настройку 👇", "en": "Let's finish setup first 👇"},
    "skip": {"uz": "O‘tkazib yuborish →", "ru": "Пропустить →", "en": "Skip →"},
    "thinking": {"uz": "🧠 Rejani tartibga solyapman…", "ru": "🧠 Структурирую план…", "en": "🧠 Structuring your plan…"},
    "listening": {"uz": "🎙 Tinglayapman…", "ru": "🎙 Слушаю…", "en": "🎙 Listening…"},
    "heard": {"uz": "🎙 <i>{text}</i>", "ru": "🎙 <i>{text}</i>", "en": "🎙 <i>{text}</i>"},
    "designing": {"uz": "🎨 Dizayn qilyapman…", "ru": "🎨 Оформляю…", "en": "🎨 Designing…"},
    "preview": {
        "uz": "<b>{date}</b> · {n} ta vazifa · {theme}\n{learned}\nHammasi to‘g‘rimi? Tasdiqlasangiz kanalga joylayman.",
        "ru": "<b>{date}</b> · задач: {n} · {theme}\n{learned}\nВсё верно? После подтверждения опубликую в канал.",
        "en": "<b>{date}</b> · {n} tasks · {theme}\n{learned}\nLooks right? Confirm and I'll post it to your channel.",
    },
    "learned_short": {"uz": "🧠 +{n} ta muhim ma’lumot eslab qolindi\n", "ru": "🧠 Запомнил важного: +{n}\n",
                      "en": "🧠 Remembered +{n} useful facts\n"},
    "btn_post": {"uz": "✅ Kanalga joylash", "ru": "✅ Опубликовать", "en": "✅ Post to channel"},
    "btn_edit": {"uz": "✏️ O‘zgartirish", "ru": "✏️ Изменить", "en": "✏️ Edit"},
    "btn_theme": {"uz": "🎨 Boshqa dizayn", "ru": "🎨 Другой дизайн", "en": "🎨 Another design"},
    "btn_cancel": {"uz": "✖️ Bekor qilish", "ru": "✖️ Отмена", "en": "✖️ Cancel"},
    "ask_edit": {
        "uz": "✏️ Nimani o‘zgartiray? Yozing yoki ayting. Masalan: <i>«tushlikni 13:30 ga sur, sportni o‘chir, hisobotni muhim qil»</i>",
        "ru": "✏️ Что изменить? Напиши или скажи. Например: <i>«обед на 13:30, убери спорт, отчёт сделай важным»</i>",
        "en": "✏️ What should I change? Type or say it, e.g. <i>“move lunch to 13:30, drop gym, make the report high priority”</i>",
    },
    "posted": {"uz": "✅ Kanalga joylandi! {jobs} ta eslatma rejalashtirildi.", "ru": "✅ Опубликовано! Запланировано напоминаний: {jobs}.",
               "en": "✅ Posted! {jobs} reminders scheduled."},
    "cancelled": {"uz": "Bekor qilindi.", "ru": "Отменено.", "en": "Cancelled."},
    "expired": {"uz": "Bu qoralama eskirgan. Rejani qaytadan yuboring.", "ru": "Черновик устарел. Отправь план заново.",
                "en": "This draft expired. Send the plan again."},
    "no_tasks": {"uz": "Bu xabardan vazifa topolmadim 🤔 Ertangi ishlaringizni sanab yozib ko‘ring.",
                 "ru": "Не нашёл задач в сообщении 🤔 Перечисли дела на завтра.",
                 "en": "I couldn't find tasks in that 🤔 Try listing tomorrow's to-dos."},
    "err_quota": {"uz": "⏳ AI limitlari tugadi (Gemini va Groq). Birozdan keyin urinib ko‘ring yoki /settings da Groq kalitini qo‘shing.",
                  "ru": "⏳ Лимиты AI исчерпаны (Gemini и Groq). Попробуй позже или добавь ключ Groq в /settings.",
                  "en": "⏳ AI limits are used up (Gemini and Groq). Try again later or add a Groq key in /settings."},
    "err_invalid_key": {"uz": "🔑 API kalit ishlamayapti. /settings → Kalitlar bo‘limida yangilang.",
                        "ru": "🔑 API-ключ не работает. Обнови его: /settings → Ключи.",
                        "en": "🔑 Your API key stopped working. Update it in /settings → Keys."},
    "err_no_keys": {"uz": "🔑 API kalit kiritilmagan. /settings → Kalitlar.", "ru": "🔑 Нет API-ключа. /settings → Ключи.",
                    "en": "🔑 No API key set. /settings → Keys."},
    "err_failed": {"uz": "😕 AI hozir javob bermadi. Bir daqiqadan keyin qayta yuboring.", "ru": "😕 AI сейчас не ответил. Попробуй через минуту.",
                   "en": "😕 The AI didn't respond. Please try again in a minute."},
    "err_post": {"uz": "❌ Kanalga yubora olmadim. Bot hali ham admin ekanini tekshiring (/settings → Kanal).",
                 "ru": "❌ Не смог отправить в канал. Проверь, что бот всё ещё админ (/settings → Канал).",
                 "en": "❌ Couldn't post to the channel. Check the bot is still an admin (/settings → Channel)."},
    "busy": {"uz": "⏳ Oldingi xabar ustida ishlayapman…", "ru": "⏳ Ещё обрабатываю прошлое сообщение…", "en": "⏳ Still working on your last message…"},
    # channel
    "progress": {"uz": "Bajarildi", "ru": "Выполнено", "en": "Done"},
    "not_owner": {"uz": "Faqat kanal egasi belgilay oladi", "ru": "Отмечать может только владелец", "en": "Only the owner can tick tasks"},
    "all_done": {"uz": "🎉 Hammasi bajarildi! Zo‘r kun!", "ru": "🎉 Всё выполнено! Отличный день!", "en": "🎉 All done! Great day!"},
    "ticked": {"uz": "✅ Belgilandi", "ru": "✅ Отмечено", "en": "✅ Done"},
    "unticked": {"uz": "↩️ Qaytarildi", "ru": "↩️ Снято", "en": "↩️ Unticked"},
    "remind": {"uz": "⏰ {min} daqiqadan keyin: <b>{title}</b> · {time}", "ru": "⏰ Через {min} мин: <b>{title}</b> · {time}",
               "en": "⏰ In {min} min: <b>{title}</b> · {time}"},
    "card_caption": {"uz": "▶️ <b>{time}</b> · {title}", "ru": "▶️ <b>{time}</b> · {title}", "en": "▶️ <b>{time}</b> · {title}"},
    "morning": {
        "uz": "☀️ <b>Xayrli tong!</b> Bugun {n} ta vazifa.\n{first}{focus}",
        "ru": "☀️ <b>Доброе утро!</b> Сегодня задач: {n}.\n{first}{focus}",
        "en": "☀️ <b>Good morning!</b> {n} tasks today.\n{first}{focus}",
    },
    "first": {"uz": "Birinchisi: <b>{time}</b> {title}\n", "ru": "Первая: <b>{time}</b> {title}\n", "en": "First up: <b>{time}</b> {title}\n"},
    "focus_line": {"uz": "🎯 Fokus: {focus}", "ru": "🎯 Фокус: {focus}", "en": "🎯 Focus: {focus}"},
    "evening": {
        "uz": "🌙 <b>Kun yakuni:</b> {done}/{n} bajarildi · {pct}%\n{left}",
        "ru": "🌙 <b>Итог дня:</b> {done}/{n} выполнено · {pct}%\n{left}",
        "en": "🌙 <b>Day wrap-up:</b> {done}/{n} done · {pct}%\n{left}",
    },
    "left": {"uz": "Qolganlar:\n{items}", "ru": "Осталось:\n{items}", "en": "Left:\n{items}"},
    "evening_dm": {
        "uz": "🌙 Bugun: {done}/{n}. Ertangi rejangizni yuboring — yozib yoki ovozli ✍️🎙",
        "ru": "🌙 Сегодня: {done}/{n}. Пришли план на завтра — текстом или голосом ✍️🎙",
        "en": "🌙 Today: {done}/{n}. Send tomorrow's plan — text or voice ✍️🎙",
    },
    "ask_plan": {"uz": "🌙 Ertangi rejangizni yuboring — yozib yoki ovozli ✍️🎙", "ru": "🌙 Пришли план на завтра — текстом или голосом ✍️🎙",
                 "en": "🌙 Send tomorrow's plan — text or voice ✍️🎙"},
    "btn_carry": {"uz": "➡️ Qolganlarni ertaga o‘tkazish", "ru": "➡️ Перенести остаток на завтра", "en": "➡️ Carry the rest to tomorrow"},
    "carry_ok": {"uz": "👌 {n} ta vazifa ertangi rejaga qo‘shiladi.", "ru": "👌 {n} задач(и) добавлю в план на завтра.",
                 "en": "👌 I'll add {n} tasks to tomorrow's plan."},
    # reports
    "report_pick": {"uz": "📊 Qaysi davr uchun hisobot?", "ru": "📊 Отчёт за какой период?", "en": "📊 Report for which period?"},
    "btn_week": {"uz": "Shu hafta", "ru": "Эта неделя", "en": "This week"},
    "btn_lastweek": {"uz": "O‘tgan hafta", "ru": "Прошлая неделя", "en": "Last week"},
    "btn_month": {"uz": "Shu oy", "ru": "Этот месяц", "en": "This month"},
    "btn_share": {"uz": "📢 Kanalga yuborish", "ru": "📢 В канал", "en": "📢 Share to channel"},
    "shared": {"uz": "Kanalga yuborildi ✅", "ru": "Отправлено в канал ✅", "en": "Shared to channel ✅"},
    "report_caption": {"uz": "📊 <b>{title}</b> · {pct}% bajarildi", "ru": "📊 <b>{title}</b> · выполнено {pct}%",
                       "en": "📊 <b>{title}</b> · {pct}% done"},
    "report_fallback": {
        "uz": "Bajarilish {pct}%. Eng muhim 1–2 vazifani kunning birinchi yarmiga qo‘yib ko‘ring.",
        "ru": "Выполнение {pct}%. Попробуй ставить 1–2 главные задачи на первую половину дня.",
        "en": "Completion {pct}%. Try putting your 1–2 key tasks in the first half of the day.",
    },
    # memory
    "memory_title": {"uz": "🧠 <b>Men eslab qolgan ma’lumotlar</b>\nO‘chirish uchun bosing. Qo‘shish: <code>/remember matn</code>",
                     "ru": "🧠 <b>Что я помню</b>\nНажми, чтобы удалить. Добавить: <code>/remember текст</code>",
                     "en": "🧠 <b>What I remember</b>\nTap to delete. Add: <code>/remember text</code>"},
    "memory_empty": {"uz": "🧠 Hozircha hech narsa eslab qolmadim. <code>/remember ish vaqtim 9:00–18:00</code> kabi yozing.",
                     "ru": "🧠 Пока ничего не помню. Напиши, например, <code>/remember работаю 9:00–18:00</code>",
                     "en": "🧠 Nothing remembered yet. Try <code>/remember I work 9:00–18:00</code>"},
    "memory_deleted": {"uz": "O‘chirildi", "ru": "Удалено", "en": "Deleted"},
    "nothing_learned": {"uz": "Muhim yangi ma’lumot topmadim.", "ru": "Не нашёл новой важной информации.", "en": "Nothing new worth remembering."},
    # settings
    "settings": {
        "uz": "⚙️ <b>Sozlamalar</b>\n\nTil: {language}\nKanal: {channel}\nZona: {tz}\nGemini: {gemini} · Groq: {groq}\n"
              "Ertalabki post: {morning} · Kechki: {evening}\nEslatma: {remind}\nShablon: {theme}",
        "ru": "⚙️ <b>Настройки</b>\n\nЯзык: {language}\nКанал: {channel}\nПояс: {tz}\nGemini: {gemini} · Groq: {groq}\n"
              "Утренний пост: {morning} · Вечерний: {evening}\nНапоминание: {remind}\nШаблон: {theme}",
        "en": "⚙️ <b>Settings</b>\n\nLanguage: {language}\nChannel: {channel}\nZone: {tz}\nGemini: {gemini} · Groq: {groq}\n"
              "Morning post: {morning} · Evening: {evening}\nReminder: {remind}\nTemplate: {theme}",
    },
    "s_lang": {"uz": "🌐 Til", "ru": "🌐 Язык", "en": "🌐 Language"},
    "s_keys": {"uz": "🔑 Kalitlar", "ru": "🔑 Ключи", "en": "🔑 Keys"},
    "s_channel": {"uz": "📢 Kanal", "ru": "📢 Канал", "en": "📢 Channel"},
    "s_tz": {"uz": "🕒 Vaqt zonasi", "ru": "🕒 Часовой пояс", "en": "🕒 Time zone"},
    "s_times": {"uz": "⏰ Post vaqtlari", "ru": "⏰ Время постов", "en": "⏰ Post times"},
    "s_notify": {"uz": "🔔 Eslatmalar", "ru": "🔔 Уведомления", "en": "🔔 Notifications"},
    "s_theme": {"uz": "🎨 Shablon", "ru": "🎨 Шаблон", "en": "🎨 Template"},
    "s_back": {"uz": "← Orqaga", "ru": "← Назад", "en": "← Back"},
    "k_gemini": {"uz": "Gemini kalitini almashtirish", "ru": "Сменить ключ Gemini", "en": "Replace Gemini key"},
    "k_groq": {"uz": "Groq kalitini almashtirish", "ru": "Сменить ключ Groq", "en": "Replace Groq key"},
    "k_groq_del": {"uz": "Groq kalitini o‘chirish", "ru": "Удалить ключ Groq", "en": "Remove Groq key"},
    "send_key": {"uz": "Yangi kalitni yuboring:", "ru": "Отправь новый ключ:", "en": "Send the new key:"},
    "t_morning": {"uz": "☀️ Ertalab: {v}", "ru": "☀️ Утро: {v}", "en": "☀️ Morning: {v}"},
    "t_evening": {"uz": "🌙 Kechqurun: {v}", "ru": "🌙 Вечер: {v}", "en": "🌙 Evening: {v}"},
    "ask_time": {"uz": "Vaqtni <b>HH:MM</b> ko‘rinishida yuboring (masalan 07:30).", "ru": "Отправь время в формате <b>HH:MM</b> (например 07:30).",
                 "en": "Send the time as <b>HH:MM</b> (e.g. 07:30)."},
    "time_bad": {"uz": "Format: HH:MM, masalan 21:30", "ru": "Формат: HH:MM, например 21:30", "en": "Format: HH:MM, e.g. 21:30"},
    "n_remind": {"uz": "⏰ Oldindan eslatma (shaxsiy chatga)", "ru": "⏰ Напоминание заранее (в личку)", "en": "⏰ Heads-up reminder (DM)"},
    "n_before": {"uz": "Necha daqiqa oldin: {v}", "ru": "За сколько минут: {v}", "en": "Minutes before: {v}"},
    "n_cards": {"uz": "▶️ Vazifa boshlanganda karta (kanalga)", "ru": "▶️ Карточка при старте задачи (в канал)",
                "en": "▶️ Card when a task starts (channel)"},
    "n_morning": {"uz": "☀️ Ertalabki post", "ru": "☀️ Утренний пост", "en": "☀️ Morning post"},
    "n_evening": {"uz": "🌙 Kechki yakun", "ru": "🌙 Вечерний итог", "en": "🌙 Evening wrap-up"},
    "n_weekly": {"uz": "📊 Haftalik hisobot", "ru": "📊 Отчёт за неделю", "en": "📊 Weekly report"},
    "n_monthly": {"uz": "📈 Oylik hisobot", "ru": "📈 Отчёт за месяц", "en": "📈 Monthly report"},
    "theme_rotate": {"uz": "🔄 Har kuni boshqa", "ru": "🔄 Каждый день разный", "en": "🔄 Different every day"},
    "theme_pick": {"uz": "Shablonni tanlang. Namunalar yuqorida 👆", "ru": "Выбери шаблон. Примеры выше 👆", "en": "Pick a template. Samples above 👆"},
    "saved": {"uz": "✅ Saqlandi", "ru": "✅ Сохранено", "en": "✅ Saved"},
    "on": {"uz": "yoqilgan", "ru": "вкл", "en": "on"},
    "off": {"uz": "o‘chiq", "ru": "выкл", "en": "off"},
    "min_before": {"uz": "{v} daq oldin", "ru": "за {v} мин", "en": "{v} min before"},
    "none": {"uz": "ulanmagan", "ru": "не подключён", "en": "not connected"},
    "today_none": {"uz": "Bugun uchun joylangan reja yo‘q. Rejangizni yuboring ✍️", "ru": "На сегодня плана нет. Пришли его ✍️",
                   "en": "No posted plan for today. Send one ✍️"},
    "help": {
        "uz": "<b>Qanday ishlaydi</b>\n\n1. Ertangi rejani istalgan ko‘rinishda yozing yoki ovozli xabar yuboring (o‘zbek, rus, ingliz).\n"
              "2. Men uni tartibga solaman va rasm ko‘rinishida ko‘rsataman. ✏️ bilan o‘zgartirasiz, ✅ bilan kanalga joylaysiz.\n"
              "3. Kanalda vazifalarni ✅ bilan belgilaysiz. Har bir vazifa boshlanganda karta chiqadi.\n"
              "4. Kechqurun kun yakuni, yakshanba haftalik, oy oxirida oylik hisobot keladi.\n\n"
              "/today — bugungi reja\n/report — hisobot\n/memory — xotira · /remember — eslab qolish\n/templates — shablonlar\n/keys — API kalitlar va yo‘riqnoma\n/settings — sozlamalar\n/cancel — bekor qilish",
        "ru": "<b>Как это работает</b>\n\n1. Пиши или надиктуй план на завтра как угодно (узбекский, русский, английский).\n"
              "2. Я структурирую и покажу картинку. ✏️ — изменить, ✅ — опубликовать в канал.\n"
              "3. В канале отмечай задачи ✅. При старте каждой задачи — карточка.\n"
              "4. Вечером итог дня, в воскресенье отчёт за неделю, в конце месяца — за месяц.\n\n"
              "/today — план на сегодня\n/report — отчёт\n/memory — память · /remember — запомнить\n/templates — шаблоны\n/keys — API-ключи и инструкция\n/settings — настройки\n/cancel — отмена",
        "en": "<b>How it works</b>\n\n1. Type or voice tomorrow's plan any way you like (Uzbek, Russian, English).\n"
              "2. I structure it and show you the image. ✏️ to edit, ✅ to post it to your channel.\n"
              "3. Tick tasks ✅ in the channel. A card appears when each task starts.\n"
              "4. Evening wrap-up daily, weekly report on Sunday, monthly at month end.\n\n"
              "/today — today's plan\n/report — reports\n/memory · /remember\n/templates — templates\n/keys — API keys & how-to\n/settings\n/cancel",
    },
}

COMMANDS = {
    "uz": [("today", "Bugungi reja"), ("report", "Hisobot"), ("memory", "Xotira"), ("templates", "Shablonlar"),
           ("keys", "API kalitlar"), ("settings", "Sozlamalar"), ("help", "Yordam")],
    "ru": [("today", "План на сегодня"), ("report", "Отчёт"), ("memory", "Память"), ("templates", "Шаблоны"),
           ("keys", "API-ключи"), ("settings", "Настройки"), ("help", "Помощь")],
    "en": [("today", "Today's plan"), ("report", "Report"), ("memory", "Memory"), ("templates", "Templates"),
           ("keys", "API keys"), ("settings", "Settings"), ("help", "Help")],
}


def t(lang: str | None, key: str, **kw) -> str:
    entry = T[key]
    s = entry.get(lang or "uz") or entry["en"]
    return s.format(**kw) if kw else s
