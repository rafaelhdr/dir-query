import re
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, status

from app.config import MAX_UPLOAD_BYTES, UPLOAD_DIR
from app.rag import index_service

router = APIRouter()

_PATH_SEPARATORS = re.compile(r"[/\\]")


def _sanitize_filename(filename: str) -> str:
    return _PATH_SEPARATORS.sub("_", filename)


@router.post("/uploads", status_code=status.HTTP_201_CREATED)
async def create_upload(
    file: UploadFile, background_tasks: BackgroundTasks
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

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4()}-{_sanitize_filename(file.filename)}"
    stored_path = UPLOAD_DIR / stored_filename
    stored_path.write_bytes(contents)

    background_tasks.add_task(index_service.index_uploaded_file, stored_path)

    return {
        "filename": stored_filename,
        "original_filename": file.filename,
        "size": len(contents),
    }
