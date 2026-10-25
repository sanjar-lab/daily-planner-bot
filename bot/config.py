import os

from dotenv import load_dotenv

load_dotenv()


def _list(name: str, default: str) -> list[str]:
    return [m.strip() for m in os.getenv(name, default).split(",") if m.strip()]


BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "")

# Webhook mode when a public URL is known (Render sets RENDER_EXTERNAL_URL itself).
PUBLIC_URL = (os.getenv("PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
TICK_KEY = os.getenv("TICK_KEY", "")
PORT = int(os.getenv("PORT", "8080"))
MODE = os.getenv("MODE") or ("webhook" if PUBLIC_URL else "polling")

# Preferred model chains, tried in order. Gemini first, Groq when Gemini is out of quota or failing.
# Whatever else the key can use is discovered at runtime and appended, so renamed or retired
# models don't break the bot.
GEMINI_SMART = _list("GEMINI_SMART", "gemini-3.5-flash,gemini-flash-latest,gemini-3.8-flash")
GEMINI_LIGHT = _list("GEMINI_LIGHT", "gemini-flash-lite-latest,gemini-3.5-flash-lite,gemini-3.5-flash")
GEMINI_AUDIO = _list("GEMINI_AUDIO", "gemini-3.5-flash,gemini-flash-latest,gemini-flash-lite-latest")
GROQ_SMART = _list("GROQ_SMART", "openai/gpt-oss-120b,qwen/qwen3.8-27b,openai/gpt-oss-20b")
GROQ_LIGHT = _list("GROQ_LIGHT", "openai/gpt-oss-20b,qwen/qwen3.8-27b,openai/gpt-oss-120b")
GROQ_STT = _list("GROQ_STT", "whisper-large-v3-turbo,whisper-large-v3")

MEMORY_LIMIT = int(os.getenv("MEMORY_LIMIT", "40"))
