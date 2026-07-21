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

from app.api.deps import require_workspace_edit_access
from app.config import MAX_UPLOAD_BYTES, UPLOAD_DIR
from app.db.models import File, Workspace
from app.db.session import get_session
from app.rag import index_service
from app.schemas import UploadPublic

router = APIRouter()

_PATH_SEPARATORS = re.compile(r"[/\\]")


def _sanitize_filename(filename: str) -> str:
    return _PATH_SEPARATORS.sub("_", filename)


@router.post("/w/{slug}/uploads", status_code=status.HTTP_201_CREATED)
async def create_upload(
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
