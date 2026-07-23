import asyncio
import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.deps import get_workspace_by_slug
from app.db.models import Workspace
from app.services import conversations
from app.services.conversations import ConversationNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()

_HEARTBEAT_SECONDS = 15


def _sse_frame(event_type: str, data: object) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@router.post("/w/{slug}/ask")
async def ask_question(
    question: str = Form(...),
    conversation_id: int | None = Form(None),
    workspace: Workspace = Depends(get_workspace_by_slug),
) -> StreamingResponse:
    try:
        conv_id, title, queue = await conversations.ask(
            workspace.id, question, conversation_id
        )
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

    async def _stream() -> AsyncIterator[str]:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=_HEARTBEAT_SECONDS)
            except TimeoutError:
                yield ": keep-alive\n\n"
                continue

            if event is None:
                return
            if event["type"] == "token":
                yield _sse_frame("token", event["text"])
            elif event["type"] == "final":
                yield _sse_frame(
                    "done",
                    {
                        "conversation_id": conv_id,
                        "title": title,
                        "sources": event["sources"],
                        "answer": event["answer"],
                    },
                )
            elif event["type"] == "error":
                yield _sse_frame("error", {"detail": event["detail"]})

    return StreamingResponse(_stream(), media_type="text/event-stream")
