from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Workspace
from app.db.session import get_session
from app.services.auth import decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_workspace_by_slug(
    slug: str, session: AsyncSession = Depends(get_session)
) -> Workspace:
    result = await session.execute(select(Workspace).where(Workspace.slug == slug))
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    return workspace


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User | None:
    if credentials is None:
        return None
    try:
        user_id = decode_access_token(credentials.credentials)
    except Exception:
        return None
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_current_user_required(
    current_user: User | None = Depends(get_current_user_optional),
) -> User:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return current_user


async def require_workspace_edit_access(
    workspace: Workspace = Depends(get_workspace_by_slug),
    current_user: User | None = Depends(get_current_user_optional),
) -> Workspace:
    if workspace.owner_user_id is None:
        return workspace
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to edit this workspace",
        )
    if current_user.id != workspace.owner_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the workspace owner can edit this workspace",
        )
    return workspace
