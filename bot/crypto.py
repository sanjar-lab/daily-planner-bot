"""Users' API keys are stored encrypted (Fernet) and only decrypted in memory."""
from cryptography.fernet import Fernet, InvalidToken

from . import config

_fernet = Fernet(config.ENCRYPTION_KEY.encode()) if config.ENCRYPTION_KEY else None


def encrypt(value: str | None) -> str | None:
    if not value:
        return None
    if not _fernet:
        raise RuntimeError("ENCRYPTION_KEY is not set")
    return _fernet.encrypt(value.encode()).decode()


def decrypt(token: str | None) -> str | None:
    if not token or not _fernet:
        return None
    try:
        return _fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        return None


def mask(key: str | None) -> str:
    return f"{key[:4]}…{key[-4:]}" if key and len(key) > 10 else "—"
