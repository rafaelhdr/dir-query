import logging

from fastapi import APIRouter, Depends, Form, HTTPException, status

from app.api.deps import get_workspace_by_slug
from app.db.models import Workspace
from app.rag import index_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/w/{slug}/ask")
async def ask_question(
    question: str = Form(...),
    workspace: Workspace = Depends(get_workspace_by_slug),
) -> dict[str, object]:
    try:
        return await index_service.answer_question(workspace.id, question)
    except RuntimeError as exc:
        logger.error("Cannot answer question: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Question-answering is not configured: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Failed to answer question")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Something went wrong answering your question. Please try again.",
        ) from exc
