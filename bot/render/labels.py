"""Localized words used inside rendered images."""

WEEKDAYS = {
    "uz": ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"],
    "ru": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}
WEEKDAYS_SHORT = {
    "uz": ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"],
    "ru": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}
MONTHS = {
    "uz": ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust",
           "sentabr", "oktabr", "noyabr", "dekabr"],
    "ru": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
           "сентября", "октября", "ноября", "декабря"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
}

WORDS = {
    "uz": {
        "tasks": "vazifa", "tasks_t": "Vazifalar", "high_n": "muhim", "planned": "Rejada",
        "focus": "Fokus", "priority": "Muhimlik", "time": "Vaqt", "task": "Vazifa",
        "high": "Muhim", "medium": "O‘rta", "low": "Past",
        "morning": "Ertalab", "afternoon": "Kunduzi", "evening": "Kechqurun", "anytime": "Istalgan vaqt",
        "now": "Hozir", "next": "Keyingi", "of": "dan", "last": "Kunning oxirgi vazifasi",
        "weekly": "Haftalik hisobot", "monthly": "Oylik hisobot", "done": "Bajarildi",
        "completion": "Bajarilish", "best_day": "Eng yaxshi kun", "streak": "Ketma-ket kunlar",
        "high_done": "Muhimlar", "days": "kun", "plan_of_day": "Kun rejasi", "no_data": "Ma’lumot yo‘q",
        "h": "s", "m": "daq",
    },
    "ru": {
        "tasks": "задач", "tasks_t": "Задачи", "high_n": "важных", "planned": "В плане",
        "focus": "Фокус", "priority": "Приоритет", "time": "Время", "task": "Задача",
        "high": "Важно", "medium": "Средне", "low": "Низко",
        "morning": "Утро", "afternoon": "День", "evening": "Вечер", "anytime": "В любое время",
        "now": "Сейчас", "next": "Далее", "of": "из", "last": "Последняя задача дня",
        "weekly": "Отчёт за неделю", "monthly": "Отчёт за месяц", "done": "Выполнено",
        "completion": "Выполнение", "best_day": "Лучший день", "streak": "Дней подряд",
        "high_done": "Важные", "days": "дн.", "plan_of_day": "План дня", "no_data": "Нет данных",
        "h": "ч", "m": "мин",
    },
    "en": {
        "tasks": "tasks", "tasks_t": "Tasks", "high_n": "high", "planned": "Planned",
        "focus": "Focus", "priority": "Priority", "time": "Time", "task": "Task",
        "high": "High", "medium": "Medium", "low": "Low",
        "morning": "Morning", "afternoon": "Afternoon", "evening": "Evening", "anytime": "Anytime",
        "now": "Now", "next": "Next", "of": "of", "last": "Last task of the day",
        "weekly": "Weekly report", "monthly": "Monthly report", "done": "Done",
        "completion": "Completion", "best_day": "Best day", "streak": "Day streak",
        "high_done": "High priority", "days": "days", "plan_of_day": "Plan of the day", "no_data": "No data",
        "h": "h", "m": "m",
    },
}

CATEGORIES = {
    "uz": {"work": "Ish", "study": "O‘qish", "health": "Salomatlik", "sport": "Sport",
           "personal": "Shaxsiy", "family": "Oila", "errand": "Yumush", "social": "Uchrashuv",
           "rest": "Dam olish", "finance": "Moliya", "other": "Boshqa"},
    "ru": {"work": "Работа", "study": "Учёба", "health": "Здоровье", "sport": "Спорт",
           "personal": "Личное", "family": "Семья", "errand": "Дела", "social": "Встреча",
           "rest": "Отдых", "finance": "Финансы", "other": "Другое"},
    "en": {"work": "Work", "study": "Study", "health": "Health", "sport": "Sport",
           "personal": "Personal", "family": "Family", "errand": "Errand", "social": "Social",
           "rest": "Rest", "finance": "Finance", "other": "Other"},
}


def w(lang: str, key: str) -> str:
    return WORDS.get(lang, WORDS["en"]).get(key, WORDS["en"][key])


def weekday(lang: str, d) -> str:
    return WEEKDAYS.get(lang, WEEKDAYS["en"])[d.weekday()]


def weekday_short(lang: str, d) -> str:
    return WEEKDAYS_SHORT.get(lang, WEEKDAYS_SHORT["en"])[d.weekday()]


MONTHS_NOM_RU = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август",
                 "сентябрь", "октябрь", "ноябрь", "декабрь"]


def month(lang: str, d, standalone: bool = True) -> str:
    """Standalone month name (Russian needs nominative there, genitive inside dates)."""
    if lang == "ru" and standalone:
        return MONTHS_NOM_RU[d.month - 1]
    return MONTHS.get(lang, MONTHS["en"])[d.month - 1]


def date_long(lang: str, d) -> str:
    if lang == "en":
        return f"{month(lang, d, standalone=False)} {d.day}"
    if lang == "uz":
        return f"{d.day}-{month(lang, d, standalone=False)}"
    return f"{d.day} {month(lang, d, standalone=False)}"


def category(lang: str, key: str) -> str:
    table = CATEGORIES.get(lang, CATEGORIES["en"])
    return table.get(key or "other", table["other"])


def duration(lang: str, minutes: int | None) -> str:
    if not minutes:
        return ""
    h, m = divmod(int(minutes), 60)
    hu, mu = w(lang, "h"), w(lang, "m")
    if h and m:
        return f"{h}{hu} {m}{mu}" if lang == "en" else f"{h} {hu} {m} {mu}"
    if h:
        return f"{h}{hu}" if lang == "en" else f"{h} {hu}"
    return f"{m}{mu}" if lang == "en" else f"{m} {mu}"
