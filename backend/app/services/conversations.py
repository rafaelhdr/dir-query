from sqlalchemy import select

from app.db.models import Conversation, Exchange
from app.db.session import async_session_factory
from app.rag import index_service
from app.schemas import AskResponse

TITLE_MAX_LENGTH = 60


class ConversationNotFoundError(Exception):
    pass


def _derive_title(question: str) -> str:
    question = question.strip()
    if len(question) <= TITLE_MAX_LENGTH:
        return question
    return question[: TITLE_MAX_LENGTH - 1].rstrip() + "…"


async def ask(
    workspace_id: int, question: str, conversation_id: int | None
) -> AskResponse:
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
        result = await index_service.answer_question(
            workspace_id, question, conversation_id=conversation_id
        )
    except Exception:
        async with async_session_factory() as session:
            exchange_result = await session.execute(
                select(Exchange).where(Exchange.id == exchange_id)
            )
            exchange = exchange_result.scalar_one()
            exchange.status = "failed"
            await session.commit()
        raise

    async with async_session_factory() as session:
        exchange_result = await session.execute(
            select(Exchange).where(Exchange.id == exchange_id)
        )
        exchange = exchange_result.scalar_one()
        exchange.answer = str(result["answer"])
        exchange.sources = result["sources"]
        exchange.status = "answered"
        await session.commit()

    return AskResponse(
        conversation_id=conversation_id,
        title=title,
        answer=result["answer"],
        sources=result["sources"],
    )
