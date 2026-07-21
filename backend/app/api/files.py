from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_workspace_by_slug, require_workspace_edit_access
from app.config import UPLOAD_DIR
from app.db.models import File, Workspace
from app.db.session import get_session
from app.schemas import FilePublic

router = APIRouter()


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
