from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Workspace
from app.db.session import get_session


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
