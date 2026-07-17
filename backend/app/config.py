import os
from pathlib import Path

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/data/uploads"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))

HF_HOME = Path(os.getenv("HF_HOME", "/data/hf-cache"))
MINIMAX_LLM_MODEL = os.getenv("MINIMAX_LLM_MODEL", "MiniMax-M2.7")
GEMINI_LLM_MODEL = os.getenv("GEMINI_LLM_MODEL", "gemini-3-flash-preview")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")


def _validate_choice(name: str, value: str, allowed: set[str]) -> str:
    if value not in allowed:
        raise ValueError(
            f"{name}={value!r} is not a valid choice; expected one of {sorted(allowed)}"
        )
    return value


EMBED_PROVIDER = _validate_choice(
    "EMBED_PROVIDER", os.getenv("EMBED_PROVIDER", "cpu"), {"cpu", "gemini"}
)
LLM_PROVIDER = _validate_choice(
    "LLM_PROVIDER", os.getenv("LLM_PROVIDER", "minimax"), {"minimax", "gemini"}
)

POSTGRES_USER = os.getenv("POSTGRES_USER", "understand_your_stuffs")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_DB = os.getenv("POSTGRES_DB", "understand_your_stuffs")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


def _read_secret(name: str) -> str | None:
    secret_file = os.getenv(f"{name}_FILE", f"/run/secrets/{name.lower()}.txt")
    secret_path = Path(secret_file)
    if secret_path.is_file():
        value = secret_path.read_text().strip()
        if value:
            return value
    return os.getenv(name) or None


MINIMAX_API_KEY = _read_secret("MINIMAX_API_KEY")
GOOGLE_API_KEY = _read_secret("GOOGLE_API_KEY")
