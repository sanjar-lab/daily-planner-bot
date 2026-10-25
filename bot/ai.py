"""Model orchestration: Gemini first, Groq as fallback, per-user keys.

Each call walks a chain of (provider, model). Rate-limited models are put on a
short cooldown, missing models are skipped for the process lifetime, and an
invalid key skips the whole provider — so the next request goes straight to
something that works.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
import time

import aiohttp

from . import config

log = logging.getLogger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GROQ_URL = "https://api.groq.com/openai/v1"
TIMEOUT = aiohttp.ClientTimeout(total=90)
# Overloaded models can hang for a minute+; give up early and let the chain move on.
GEMINI_TIMEOUT = aiohttp.ClientTimeout(total=35, sock_connect=10)
GROQ_TIMEOUT = aiohttp.ClientTimeout(total=45, sock_connect=10)
BUSY_COOLDOWN = 120

_session: aiohttp.ClientSession | None = None
_cooldown: dict[tuple, float] = {}   # (key_hash, model) -> unix time until which to skip
_missing: set[str] = set()          # models the API says don't exist
_catalog: dict[tuple, tuple[float, list[str]]] = {}  # (provider, key_hash) -> (fetched_at, models)
CATALOG_TTL = 6 * 3600


class AIError(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason  # quota | invalid_key | no_keys | failed


class _Skip(Exception):
    def __init__(self, kind: str, cooldown: float = 0):
        self.kind, self.cooldown = kind, cooldown


def session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(timeout=TIMEOUT)
    return _session


async def close():
    if _session and not _session.closed:
        await _session.close()


def _h(key: str) -> str:
    return hashlib.sha1(key.encode()).hexdigest()[:10]


def _retry_after(resp: aiohttp.ClientResponse, body: str) -> float:
    ra = resp.headers.get("retry-after")
    if ra and ra.replace(".", "").isdigit():
        return float(ra)
    m = re.search(r'"retryDelay":\s*"(\d+)', body)
    if m:
        return float(m.group(1))
    # per-day quota exhausted → don't hammer it for a while
    return 3600 if "PerDay" in body or "per day" in body.lower() else 60


async def _check(resp: aiohttp.ClientResponse) -> dict:
    if resp.status == 200:
        return await resp.json(content_type=None)
    body = await resp.text()
    if resp.status == 429:
        raise _Skip("quota", _retry_after(resp, body))
    if resp.status in (401, 403) or "API_KEY_INVALID" in body or "invalid_api_key" in body:
        raise _Skip("invalid_key")
    if resp.status == 404 or "model_not_found" in body or "does not exist" in body:
        raise _Skip("missing")
    if resp.status == 400 and "decommissioned" in body:
        raise _Skip("missing")
    log.warning("AI HTTP %s: %s", resp.status, body[:300])
    raise _Skip("failed", BUSY_COOLDOWN if resp.status >= 500 else 0)


def parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise
        return json.loads(m.group(0))


# ---- providers -------------------------------------------------------------
async def _gemini(key, model, system, user, want_json, audio=None):
    parts = [{"text": user}]
    if audio:
        data, mime = audio
        parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}})
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"temperature": 0.3 if want_json else 0.6},
    }
    if want_json:
        body["generationConfig"]["responseMimeType"] = "application/json"
    if model.startswith("gemini-3") or model.endswith("-latest"):
        # planning doesn't need deep reasoning; low thinking is ~2x faster
        body["generationConfig"]["thinkingConfig"] = {"thinkingLevel": "low"}
    async with session().post(f"{GEMINI_URL}/{model}:generateContent", json=body,
                              headers={"x-goog-api-key": key}, timeout=GEMINI_TIMEOUT) as r:
        data = await _check(r)
    try:
        cand = data["candidates"][0]
        return "".join(p.get("text", "") for p in cand["content"]["parts"] if not p.get("thought"))
    except (KeyError, IndexError):
        log.warning("Gemini empty response: %s", str(data)[:300])
        raise _Skip("failed")


async def _groq(key, model, system, user, want_json):
    body = {"model": model, "temperature": 0.3 if want_json else 0.6,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    if want_json:
        body["response_format"] = {"type": "json_object"}
    async with session().post(f"{GROQ_URL}/chat/completions", json=body,
                              headers={"Authorization": f"Bearer {key}"}, timeout=GROQ_TIMEOUT) as r:
        data = await _check(r)
    return data["choices"][0]["message"]["content"] or ""


async def _groq_stt(key, model, audio: bytes, filename: str):
    form = aiohttp.FormData()
    form.add_field("file", audio, filename=filename)
    form.add_field("model", model)
    form.add_field("response_format", "json")
    async with session().post(f"{GROQ_URL}/audio/transcriptions", data=form,
                              headers={"Authorization": f"Bearer {key}"}) as r:
        data = await _check(r)
    return data.get("text", "")


# ---- model discovery ---------------------------------------------------------
_GEMINI_RE = re.compile(r"^gemini-(\d+(?:\.\d+)?)-flash(-lite)?(-preview.*)?$")
_GEMINI_SKIP = ("image", "tts", "embedding", "live", "audio", "thinking", "omni")
_GROQ_SKIP = ("whisper", "guard", "orpheus", "tts", "allam", "playai", "compound")


async def _fetch_models(provider: str, key: str) -> list[str]:
    if provider == "gemini":
        async with session().get(f"{GEMINI_URL}?pageSize=200", headers={"x-goog-api-key": key}) as r:
            if r.status != 200:
                return []
            data = await r.json(content_type=None)
        return [m["name"].split("/", 1)[1] for m in data.get("models", [])
                if "generateContent" in m.get("supportedGenerationMethods", [])]
    async with session().get(f"{GROQ_URL}/models", headers={"Authorization": f"Bearer {key}"}) as r:
        if r.status != 200:
            return []
        data = await r.json(content_type=None)
    return [m["id"] for m in data.get("data", []) if m.get("active", True)]


def rank_models(provider: str, names: list[str], tier: str) -> list[str]:
    """Order discovered models best-first for a tier: newest stable flash for smart,
    newest lite for light. Unknown shapes are dropped."""
    if provider == "groq":
        good = [n for n in names if not any(s in n for s in _GROQ_SKIP)]
        size = lambda n: int((re.search(r"(\d+)b\b", n) or re.search(r"(\d+)", n + "0")).group(1))  # noqa: E731
        return sorted(good, key=size, reverse=(tier == "smart"))
    scored = []
    for n in names:
        if any(s in n for s in _GEMINI_SKIP):
            continue
        if n in ("gemini-flash-latest", "gemini-flash-lite-latest"):
            lite = "lite" in n
            scored.append(((lite != (tier == "light")), 0, -999.0, n))
            continue
        m = _GEMINI_RE.match(n)
        if not m:
            continue
        lite, preview = bool(m.group(2)), bool(m.group(3))
        scored.append(((lite != (tier == "light")), int(preview), -float(m.group(1)), n))
    return [n for *_, n in sorted(scored)]


async def discovered(provider: str, key: str, tier: str) -> list[str]:
    ck = (provider, _h(key))
    hit = _catalog.get(ck)
    if not hit or time.time() - hit[0] > CATALOG_TTL:
        try:
            names = await _fetch_models(provider, key)
        except (aiohttp.ClientError, TimeoutError):
            names = []
        if names:
            _catalog[ck] = (time.time(), names)
        hit = _catalog.get(ck, (0, []))
    return rank_models(provider, hit[1], tier)[:4]


def _merge(preferred: list[str], found: list[str]) -> list[str]:
    seen, out = set(), []
    for m in preferred + found:
        if m not in seen and m not in _missing:
            seen.add(m)
            out.append(m)
    return out


# ---- orchestrator ----------------------------------------------------------
class AI:
    def __init__(self, gemini_key: str | None, groq_key: str | None):
        self.gemini_key, self.groq_key = gemini_key, groq_key
        self.used: str = ""  # "provider/model" that answered last

    async def _run(self, chain):
        if not chain:
            raise AIError("no_keys")
        reasons = set()
        dead_keys = set()
        for provider, key, model, call in chain:
            ck = (_h(key), model)
            if key in dead_keys or model in _missing or _cooldown.get(ck, 0) > time.time():
                reasons.add("quota" if _cooldown.get(ck, 0) > time.time() else "failed")
                continue
            try:
                out = await call(key, model)
                self.used = f"{provider}/{model}"
                return out
            except _Skip as s:
                reasons.add(s.kind)
                log.info("AI skip %s/%s: %s", provider, model, s.kind)
                if s.kind == "missing":
                    _missing.add(model)
                elif s.kind == "invalid_key":
                    dead_keys.add(key)
                if s.cooldown:
                    _cooldown[ck] = time.time() + s.cooldown
            except (aiohttp.ClientError, TimeoutError) as e:
                reasons.add("failed")
                _cooldown[ck] = time.time() + BUSY_COOLDOWN
                log.warning("AI unreachable %s/%s: %r", provider, model, e)
            except (json.JSONDecodeError, ValueError) as e:
                reasons.add("failed")
                log.warning("AI bad output %s/%s: %r", provider, model, e)
        for r in ("quota", "invalid_key"):
            if r in reasons:
                raise AIError(r)
        raise AIError("failed")

    async def _models(self, provider: str, tier: str) -> list[str]:
        if provider == "gemini":
            pref = {"smart": config.GEMINI_SMART, "light": config.GEMINI_LIGHT, "audio": config.GEMINI_AUDIO}[tier]
            return _merge(pref, await discovered("gemini", self.gemini_key, "light" if tier == "light" else "smart"))
        pref = config.GROQ_SMART if tier == "smart" else config.GROQ_LIGHT
        return _merge(pref, await discovered("groq", self.groq_key, tier))

    async def _chain(self, tier: str, system: str, user: str, want_json: bool):
        chain = []

        def wrap(fn):
            async def call(key, model):
                text = await fn(key, model, system, user, want_json)
                return parse_json(text) if want_json else text.strip()
            return call

        if self.gemini_key:
            chain += [("gemini", self.gemini_key, m, wrap(_gemini)) for m in await self._models("gemini", tier)]
        if self.groq_key:
            chain += [("groq", self.groq_key, m, wrap(_groq)) for m in await self._models("groq", tier)]
        return chain

    async def json(self, system: str, user: str, tier: str = "smart") -> dict:
        return await self._run(await self._chain(tier, system, user, True))

    async def text(self, system: str, user: str, tier: str = "light") -> str:
        return await self._run(await self._chain(tier, system, user, False))

    async def transcribe(self, audio: bytes, mime: str = "audio/ogg", filename: str = "voice.ogg") -> str:
        prompt = ("Transcribe this voice message verbatim in the language it is spoken "
                  "(Uzbek, Russian, English or mixed). Output only the transcript text.")
        chain = []
        if self.gemini_key:
            async def g(key, model):
                return (await _gemini(key, model, "You are a precise speech-to-text engine.", prompt,
                                      False, audio=(audio, mime))).strip()
            chain += [("gemini", self.gemini_key, m, g) for m in await self._models("gemini", "audio")]
        if self.groq_key:
            async def q(key, model):
                return (await _groq_stt(key, model, audio, filename)).strip()
            chain += [("groq", self.groq_key, m, q) for m in config.GROQ_STT]
        return await self._run(chain)


async def validate_key(provider: str, key: str) -> bool | None:
    """True valid, False rejected, None couldn't tell (network)."""
    try:
        if provider == "gemini":
            url, headers = f"{GEMINI_URL}?pageSize=1", {"x-goog-api-key": key}
        else:
            url, headers = f"{GROQ_URL}/models", {"Authorization": f"Bearer {key}"}
        async with session().get(url, headers=headers) as r:
            if r.status == 200:
                return True
            if r.status in (400, 401, 403):
                return False
            return None
    except aiohttp.ClientError:
        return None
