from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional
from app.db.models import KEY_PROVIDERS, KEY_SOURCES, User, Workspace
from app.db.session import get_session
from app.schemas import WorkspacePublic
from app.services import crypto
from app.services.slug import slugify

router = APIRouter()


def _can_edit(workspace: Workspace, current_user: User | None) -> bool:
    return workspace.owner_user_id is None or (
        current_user is not None and current_user.id == workspace.owner_user_id
    )


def _workspace_public(
    workspace: Workspace, current_user: User | None
) -> WorkspacePublic:
    can_edit = _can_edit(workspace, current_user)
    return WorkspacePublic(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        description=workspace.description,
        created_at=workspace.created_at,
        can_edit=can_edit,
        key_source=workspace.key_source if can_edit else None,
        key_provider=workspace.key_provider if can_edit else None,
    )


@router.post("/workspaces", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    name: str = Form(..., min_length=1),
    description: str = Form(""),
    key_source: str = Form("system"),
    key_provider: str | None = Form(None),
    api_key: str | None = Form(None),
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> WorkspacePublic:
    slug = slugify(name)
    if not slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name must contain at least one letter or number",
        )

    if key_source not in KEY_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"key_source must be one of {KEY_SOURCES}",
        )

    encrypted_api_key: str | None = None
    if key_source == "dedicated":
        if key_provider not in KEY_PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A dedicated key requires a provider, one of {KEY_PROVIDERS}",
            )
        if not api_key or not api_key.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A dedicated key requires a non-empty API key",
            )
        try:
            encrypted_api_key = crypto.encrypt(api_key.strip())
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Cannot store a dedicated API key: {exc}",
            ) from exc
    else:
        key_provider = None

    workspace = Workspace(
        name=name,
        slug=slug,
        description=description,
        owner_user_id=current_user.id if current_user else None,
        key_source=key_source,
        key_provider=key_provider,
        encrypted_api_key=encrypted_api_key,
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
