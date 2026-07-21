from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.session import get_session
from app.schemas import TokenResponse
from app.services.auth import authenticate, create_access_token, hash_password_expr

router = APIRouter(prefix="/auth")

_INVALID_CREDENTIALS_DETAIL = "Invalid email or password"


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(token=create_access_token(user.id), email=user.email)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    email: str = Form(..., min_length=1),
    password: str = Form(..., min_length=1),
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    user = User(email=email.strip().lower(), password=hash_password_expr(password))
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from exc
    await session.refresh(user)
    return _token_response(user)


@router.post("/login")
async def login(
    email: str = Form(..., min_length=1),
    password: str = Form(..., min_length=1),
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    user = await authenticate(session, email, password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_INVALID_CREDENTIALS_DETAIL,
        )
    return _token_response(user)
