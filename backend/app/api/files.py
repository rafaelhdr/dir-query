import re
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_workspace_by_slug, require_workspace_edit_access
from app.config import MAX_UPLOAD_BYTES, UPLOAD_DIR
from app.db.models import File, Workspace
from app.db.session import get_session
from app.rag import index_service
from app.schemas import FilePublic, FileRename, UploadPublic

router = APIRouter()

_PATH_SEPARATORS = re.compile(r"[/\\]")


def _sanitize_filename(filename: str) -> str:
    return _PATH_SEPARATORS.sub("_", filename)


def _file_public(file: File) -> FilePublic:
    return FilePublic(
        id=file.id,
        display_name=file.display_name,
        original_filename=file.original_filename,
        status=file.status,
        uploaded_at=file.uploaded_at,
        url=f"/files/{file.workspace_id}/{file.filename}",
    )


async def _get_workspace_file(
    workspace: Workspace, file_id: int, session: AsyncSession
) -> File:
    result = await session.execute(
        select(File).where(File.id == file_id, File.workspace_id == workspace.id)
    )
    file = result.scalar_one_or_none()
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    return file


@router.post("/w/{slug}/files", status_code=status.HTTP_201_CREATED)
async def create_file(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    name: str | None = Form(None),
    workspace: Workspace = Depends(require_workspace_edit_access),
    session: AsyncSession = Depends(get_session),
) -> UploadPublic:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="File exceeds maximum upload size",
        )

    display_name = name.strip() if name and name.strip() else file.filename
    original_filename = file.filename

    existing_display_name = await session.execute(
        select(File.id).where(
            File.workspace_id == workspace.id, File.display_name == display_name
        )
    )
    if existing_display_name.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A file named '{display_name}' already exists in this workspace. "
            "Please choose a different name.",
        )

    existing_original_filename = await session.execute(
        select(File.id).where(
            File.workspace_id == workspace.id,
            File.original_filename == original_filename,
        )
    )
    if existing_original_filename.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A file with the original filename '{original_filename}' "
            "already exists in this workspace.",
        )

    workspace_dir = UPLOAD_DIR / str(workspace.id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4()}-{_sanitize_filename(file.filename)}"
    stored_path = workspace_dir / stored_filename
    stored_path.write_bytes(contents)

    db_file = File(
        workspace_id=workspace.id,
        filename=stored_filename,
        display_name=display_name,
        original_filename=original_filename,
        status="pending",
    )
    session.add(db_file)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        stored_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A file with this name already exists in this workspace.",
        ) from exc
    await session.refresh(db_file)

    background_tasks.add_task(index_service.index_uploaded_file, db_file.id, stored_path)

    return UploadPublic(
        filename=stored_filename,
        display_name=display_name,
        original_filename=original_filename,
        size=len(contents),
    )


@router.get("/w/{slug}/files")
async def list_files(
    workspace: Workspace = Depends(get_workspace_by_slug),
    session: AsyncSession = Depends(get_session),
) -> dict[str, list[FilePublic]]:
    result = await session.execute(
        select(File)
        .where(File.workspace_id == workspace.id)
        .order_by(File.uploaded_at.desc())
    )
    return {"data": [_file_public(file) for file in result.scalars().all()]}


@router.patch("/w/{slug}/files/{file_id}")
async def rename_file(
    file_id: int,
    payload: FileRename,
    workspace: Workspace = Depends(require_workspace_edit_access),
    session: AsyncSession = Depends(get_session),
) -> FilePublic:
    file = await _get_workspace_file(workspace, file_id, session)

    display_name = payload.display_name.strip()
    if not display_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Display name cannot be blank",
        )

    existing_display_name = await session.execute(
        select(File.id).where(
            File.workspace_id == workspace.id,
            File.display_name == display_name,
            File.id != file_id,
        )
    )
    if existing_display_name.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A file named '{display_name}' already exists in this workspace. "
            "Please choose a different name.",
        )

    file.display_name = display_name
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A file with this name already exists in this workspace.",
        ) from exc
    await session.refresh(file)

    return _file_public(file)


@router.delete("/w/{slug}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    workspace: Workspace = Depends(require_workspace_edit_access),
    session: AsyncSession = Depends(get_session),
) -> None:
    file = await _get_workspace_file(workspace, file_id, session)
    stored_path = UPLOAD_DIR / str(workspace.id) / file.filename

    await session.delete(file)
    await session.commit()

    stored_path.unlink(missing_ok=True)
