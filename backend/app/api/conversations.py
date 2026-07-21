from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_workspace_by_slug
from app.db.models import Conversation, Exchange, Workspace
from app.db.session import get_session
from app.schemas import ConversationDetail, ConversationPublic, ExchangePublic

router = APIRouter()


def _conversation_public(conversation: Conversation) -> ConversationPublic:
    return ConversationPublic(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
    )


def _exchange_public(exchange: Exchange) -> ExchangePublic:
    return ExchangePublic(
        id=exchange.id,
        question=exchange.question,
        answer=exchange.answer,
        sources=exchange.sources,
        status=exchange.status,
        created_at=exchange.created_at,
    )


async def _get_workspace_conversation(
    workspace: Workspace, conversation_id: int, session: AsyncSession
) -> Conversation:
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return conversation


@router.get("/w/{slug}/conversations")
async def list_conversations(
    workspace: Workspace = Depends(get_workspace_by_slug),
    session: AsyncSession = Depends(get_session),
) -> dict[str, list[ConversationPublic]]:
    last_activity = (
        select(
            Exchange.conversation_id,
            func.max(Exchange.created_at).label("last_activity"),
        )
        .group_by(Exchange.conversation_id)
        .subquery()
    )

    result = await session.execute(
        select(Conversation)
        .join(last_activity, last_activity.c.conversation_id == Conversation.id)
        .where(Conversation.workspace_id == workspace.id)
        .order_by(last_activity.c.last_activity.desc())
    )
    return {"data": [_conversation_public(c) for c in result.scalars().all()]}


@router.get("/w/{slug}/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    workspace: Workspace = Depends(get_workspace_by_slug),
    session: AsyncSession = Depends(get_session),
) -> ConversationDetail:
    conversation = await _get_workspace_conversation(workspace, conversation_id, session)

    result = await session.execute(
        select(Exchange)
        .where(Exchange.conversation_id == conversation.id)
        .order_by(Exchange.created_at.asc())
    )

    return ConversationDetail(
        **_conversation_public(conversation).model_dump(),
        exchanges=[_exchange_public(e) for e in result.scalars().all()],
    )
