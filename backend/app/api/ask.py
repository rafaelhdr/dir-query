import logging

from fastapi import APIRouter, Depends, Form, HTTPException, status

from app.api.deps import get_workspace_by_slug
from app.db.models import Workspace
from app.services import conversations
from app.services.conversations import ConversationNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/w/{slug}/ask")
async def ask_question(
    question: str = Form(...),
    conversation_id: int | None = Form(None),
    workspace: Workspace = Depends(get_workspace_by_slug),
) -> dict[str, object]:
    try:
        return await conversations.ask(workspace.id, question, conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        ) from exc
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
