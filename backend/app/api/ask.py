import logging
import re

from fastapi import APIRouter, Form, HTTPException, status

from app.rag import index_service

logger = logging.getLogger(__name__)

router = APIRouter()

_THINK_TAGS = re.compile(r"<think>.*?</think>\s*", flags=re.DOTALL)


def _strip_reasoning(text: str) -> str:
    return _THINK_TAGS.sub("", text).strip()


@router.post("/ask")
async def ask_question(question: str = Form(...)) -> dict[str, object]:
    try:
        query_engine = index_service.get_query_engine()
    except RuntimeError as exc:
        logger.error("Cannot answer question: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Question-answering is not configured: {exc}",
        ) from exc

    if query_engine is None:
        return {"answer": "No documents have been indexed yet.", "sources": []}

    try:
        response = query_engine.query(question)
    except Exception as exc:
        logger.exception("Failed to answer question")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Something went wrong answering your question. Please try again.",
        ) from exc

    sources = sorted(
        {
            node.metadata.get("file_name")
            for node in response.source_nodes
            if node.metadata.get("file_name")
        }
    )
    return {"answer": _strip_reasoning(str(response)), "sources": sources}
