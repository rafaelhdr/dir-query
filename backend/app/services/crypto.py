import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import WORKSPACE_KEY_ENCRYPTION_SECRET


def _fernet() -> Fernet:
    if not WORKSPACE_KEY_ENCRYPTION_SECRET:
        raise RuntimeError("WORKSPACE_KEY_ENCRYPTION_SECRET is not configured")
    key = base64.urlsafe_b64encode(
        hashlib.sha256(WORKSPACE_KEY_ENCRYPTION_SECRET.encode()).digest()
    )
    return Fernet(key)


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError("Stored workspace API key could not be decrypted") from exc
