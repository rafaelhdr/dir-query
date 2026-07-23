import asyncio
import logging

from sqlalchemy import select

from app.db.models import Conversation, Exchange
from app.db.session import async_session_factory
from app.rag import index_service

logger = logging.getLogger(__name__)

TITLE_MAX_LENGTH = 60

# Fire-and-forget generation tasks must be kept alive by a strong reference
# (asyncio only holds a weak one), and must survive the HTTP request/response
# that spawned them so a client disconnect doesn't cut generation short.
_background_tasks: set[asyncio.Task] = set()


class ConversationNotFoundError(Exception):
    pass


def _derive_title(question: str) -> str:
    question = question.strip()
    if len(question) <= TITLE_MAX_LENGTH:
        return question
    return question[: TITLE_MAX_LENGTH - 1].rstrip() + "…"


async def _mark_failed(exchange_id: int) -> None:
    async with async_session_factory() as session:
        exchange_result = await session.execute(
            select(Exchange).where(Exchange.id == exchange_id)
        )
        exchange = exchange_result.scalar_one()
        exchange.status = "failed"
        await session.commit()


async def ask(
    workspace_id: int, question: str, conversation_id: int | None
) -> tuple[int, str, "asyncio.Queue[dict[str, object] | None]"]:
    async with async_session_factory() as session:
        if conversation_id is None:
            conversation = Conversation(
                workspace_id=workspace_id, title=_derive_title(question)
            )
            session.add(conversation)
            await session.flush()
        else:
            result = await session.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.workspace_id == workspace_id,
                )
            )
            conversation = result.scalar_one_or_none()
            if conversation is None:
                raise ConversationNotFoundError(conversation_id)

        exchange = Exchange(
            conversation_id=conversation.id, question=question, status="pending"
        )
        session.add(exchange)
        await session.commit()
        await session.refresh(exchange)

        conversation_id = conversation.id
        title = conversation.title
        exchange_id = exchange.id

    try:
        llm, key_source, used_provider = await index_service.resolve_llm(workspace_id)
    except RuntimeError:
        await _mark_failed(exchange_id)
        raise

    queue: asyncio.Queue[dict[str, object] | None] = asyncio.Queue()

    async def _generate() -> None:
        try:
            async for event in index_service.answer_question(
                llm,
                key_source,
                used_provider,
                workspace_id,
                question,
                conversation_id=conversation_id,
            ):
                await queue.put(event)
                if event["type"] == "final":
                    async with async_session_factory() as session:
                        exchange_result = await session.execute(
                            select(Exchange).where(Exchange.id == exchange_id)
                        )
                        exchange = exchange_result.scalar_one()
                        exchange.answer = str(event["answer"])
                        exchange.sources = event["sources"]
                        exchange.status = "answered"
                        exchange.llm_key_source = event.get("llm_key_source")
                        exchange.llm_provider = event.get("llm_provider")
                        await session.commit()
        except Exception:
            logger.exception("Failed to answer question")
            await _mark_failed(exchange_id)
            await queue.put(
                {
                    "type": "error",
                    "detail": "Something went wrong answering your question. Please try again.",
                }
            )
        finally:
            await queue.put(None)

    task = asyncio.create_task(_generate())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    # Returning the raw queue (not an async generator wrapping it) matters:
    # asyncio.Queue.get() is safely re-callable after a cancelled/timed-out
    # wait_for(), but cancelling a suspended async generator's __anext__()
    # closes the generator for good on the first timeout.
    return conversation_id, title, queue
