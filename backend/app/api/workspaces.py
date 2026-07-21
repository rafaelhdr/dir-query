from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional
from app.db.models import User, Workspace
from app.db.session import get_session
from app.schemas import WorkspacePublic
from app.services.slug import slugify

router = APIRouter()


def _can_edit(workspace: Workspace, current_user: User | None) -> bool:
    return workspace.owner_user_id is None or (
        current_user is not None and current_user.id == workspace.owner_user_id
    )


def _workspace_public(
    workspace: Workspace, current_user: User | None
) -> WorkspacePublic:
    return WorkspacePublic(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        created_at=workspace.created_at,
        can_edit=_can_edit(workspace, current_user),
    )


@router.post("/workspaces", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    name: str = Form(..., min_length=1),
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> WorkspacePublic:
    slug = slugify(name)
    if not slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name must contain at least one letter or number",
        )

    workspace = Workspace(
        name=name,
        slug=slug,
        owner_user_id=current_user.id if current_user else None,
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
    return _workspace_public(workspace, current_user)


@router.get("/workspaces")
async def list_workspaces(
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> list[WorkspacePublic]:
    result = await session.execute(select(Workspace).order_by(Workspace.created_at.desc()))
    return [
        _workspace_public(workspace, current_user)
        for workspace in result.scalars().all()
    ]


@router.get("/workspaces/{slug}")
async def get_workspace(
    slug: str,
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> WorkspacePublic:
    result = await session.execute(select(Workspace).where(Workspace.slug == slug))
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    return _workspace_public(workspace, current_user)
