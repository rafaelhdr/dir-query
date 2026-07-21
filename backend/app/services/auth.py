import datetime

import jwt
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import config
from app.db.models import User


def _require_secret_key() -> str:
    if not config.JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY is not configured")
    return config.JWT_SECRET_KEY


def hash_password_expr(password: str) -> ColumnElement[str]:
    return func.crypt(password, func.gen_salt("bf"))


async def authenticate(
    session: AsyncSession, email: str, password: str
) -> User | None:
    result = await session.execute(
        select(User).where(
            User.email == email.strip().lower(),
            User.password == func.crypt(password, User.password),
        )
    )
    return result.scalar_one_or_none()


def create_access_token(user_id: int) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + datetime.timedelta(hours=config.JWT_EXPIRES_HOURS),
    }
    return jwt.encode(payload, _require_secret_key(), algorithm=config.JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    payload = jwt.decode(
        token, _require_secret_key(), algorithms=[config.JWT_ALGORITHM]
    )
    return int(payload["sub"])
