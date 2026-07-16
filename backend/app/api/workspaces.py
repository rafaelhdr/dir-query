from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Workspace
from app.db.session import get_session
from app.services.slug import slugify

router = APIRouter()


def _workspace_public(workspace: Workspace) -> dict[str, object]:
    return {
        "id": workspace.id,
        "name": workspace.name,
        "slug": workspace.slug,
        "created_at": workspace.created_at.isoformat(),
    }


@router.post("/workspaces", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    name: str = Form(..., min_length=1),
    owner_email: str = Form(..., min_length=1),
    password: str = Form(..., min_length=1),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    slug = slugify(name)
    if not slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name must contain at least one letter or number",
        )

    workspace = Workspace(
        name=name,
        slug=slug,
        owner_email=owner_email,
        password=func.crypt(password, func.gen_salt("bf")),
    )
    session.add(workspace)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A workspace named '{name}' already exists. Please choose a different name.",
        ) from exc

    await session.refresh(workspace)
    return _workspace_public(workspace)


@router.get("/workspaces")
async def list_workspaces(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    result = await session.execute(select(Workspace).order_by(Workspace.created_at.desc()))
    return [_workspace_public(workspace) for workspace in result.scalars().all()]


@router.get("/workspaces/{slug}")
async def get_workspace(
    slug: str, session: AsyncSession = Depends(get_session)
) -> dict[str, object]:
    result = await session.execute(select(Workspace).where(Workspace.slug == slug))
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    return _workspace_public(workspace)
