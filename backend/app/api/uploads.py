import re
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_workspace_by_slug
from app.config import MAX_UPLOAD_BYTES, UPLOAD_DIR
from app.db.models import File, Workspace
from app.db.session import get_session
from app.rag import index_service

router = APIRouter()

_PATH_SEPARATORS = re.compile(r"[/\\]")


def _sanitize_filename(filename: str) -> str:
    return _PATH_SEPARATORS.sub("_", filename)


@router.post("/w/{slug}/uploads", status_code=status.HTTP_201_CREATED)
async def create_upload(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    workspace: Workspace = Depends(get_workspace_by_slug),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str | int]:
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

    workspace_dir = UPLOAD_DIR / str(workspace.id)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4()}-{_sanitize_filename(file.filename)}"
    stored_path = workspace_dir / stored_filename
    stored_path.write_bytes(contents)

    db_file = File(
        workspace_id=workspace.id,
        filename=stored_filename,
        original_name=file.filename,
        status="pending",
    )
    session.add(db_file)
    await session.commit()
    await session.refresh(db_file)

    background_tasks.add_task(index_service.index_uploaded_file, db_file.id, stored_path)

    return {
        "filename": stored_filename,
        "original_filename": file.filename,
        "size": len(contents),
    }
