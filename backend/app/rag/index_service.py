import logging
import re
from pathlib import Path

from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.llms import LLM, ChatMessage, MessageRole
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.llms.minimax import MiniMax
from llama_index.readers.file import PDFReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import (
    ASK_HISTORY_LIMIT,
    EMBED_PROVIDER,
    GEMINI_EMBED_MODEL,
    GEMINI_LLM_MODEL,
    GOOGLE_API_KEY,
    HF_HOME,
    LLM_PROVIDER,
    MINIMAX_API_KEY,
    MINIMAX_LLM_MODEL,
    UPLOAD_DIR,
)
from app.db.models import Chunk, Exchange, File, Workspace
from app.db.session import async_session_factory
from app.services import crypto

logger = logging.getLogger(__name__)

TOP_K = 5
NOT_FOUND_ANSWER = "I couldn't find anything related to your question in the uploaded files."

_pdf_reader = PDFReader()
_splitter = SentenceSplitter()
_embed_model: BaseEmbedding | None = None
_THINK_TAGS = re.compile(r"<think>.*?</think>\s*", flags=re.DOTALL)


def _get_embed_model() -> BaseEmbedding:
    global _embed_model
    if _embed_model is None:
        if EMBED_PROVIDER == "gemini":
            if not GOOGLE_API_KEY:
                raise RuntimeError("GOOGLE_API_KEY is not configured")
            _embed_model = GoogleGenAIEmbedding(
                model_name=GEMINI_EMBED_MODEL, api_key=GOOGLE_API_KEY
            )
        else:
            _embed_model = HuggingFaceEmbedding(
                model_name="BAAI/bge-small-en-v1.5",
                cache_folder=str(HF_HOME),
            )
    return _embed_model


def _get_llm(
    key_source: str, key_provider: str | None, encrypted_api_key: str | None
) -> LLM:
    if key_source == "dedicated":
        api_key = crypto.decrypt(encrypted_api_key or "")
        if key_provider == "gemini":
            return GoogleGenAI(model=GEMINI_LLM_MODEL, api_key=api_key)
        return MiniMax(model=MINIMAX_LLM_MODEL, api_key=api_key)

    if LLM_PROVIDER == "gemini":
        if not GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY is not configured")
        return GoogleGenAI(model=GEMINI_LLM_MODEL, api_key=GOOGLE_API_KEY)

    if not MINIMAX_API_KEY:
        raise RuntimeError("MINIMAX_API_KEY is not configured")
    return MiniMax(model=MINIMAX_LLM_MODEL, api_key=MINIMAX_API_KEY)


def _strip_reasoning(text: str) -> str:
    return _THINK_TAGS.sub("", text).strip()


async def index_uploaded_file(file_id: int, path: Path) -> None:
    try:
        documents = _pdf_reader.load_data(file=path)
        nodes = _splitter.get_nodes_from_documents(documents)
        embed_model = _get_embed_model()

        async with async_session_factory() as session:
            for chunk_index, node in enumerate(nodes):
                text = node.get_content()
                embedding = embed_model.get_text_embedding(text)
                session.add(
                    Chunk(
                        file_id=file_id,
                        chunk_index=chunk_index,
                        text=text,
                        embedding=embedding,
                    )
                )

            result = await session.execute(select(File).where(File.id == file_id))
            file = result.scalar_one()
            file.status = "indexed"
            await session.commit()

        logger.info("Indexed uploaded file: %s (%d chunks)", path.name, len(nodes))
    except Exception:
        logger.exception("Failed to index uploaded file: %s", path.name)
        async with async_session_factory() as session:
            result = await session.execute(select(File).where(File.id == file_id))
            file = result.scalar_one_or_none()
            if file is not None:
                file.status = "failed"
                await session.commit()


async def sync_pending_files() -> None:
    async with async_session_factory() as session:
        result = await session.execute(select(File).where(File.status == "pending"))
        pending_files = result.scalars().all()
        pending = [(f.id, f.workspace_id, f.filename) for f in pending_files]

    logger.info("Startup sync: %d pending file(s) found", len(pending))
    if not pending:
        logger.info("Startup sync: nothing new to index")
        return

    for file_id, workspace_id, filename in pending:
        path = UPLOAD_DIR / str(workspace_id) / filename
        try:
            await index_uploaded_file(file_id, path)
            logger.info("Startup sync: indexed %s", filename)
        except Exception:
            logger.exception("Startup sync: failed to index %s", filename)

    logger.info("Startup sync: complete")


async def _load_history_messages(
    session: AsyncSession, conversation_id: int
) -> list[ChatMessage]:
    result = await session.execute(
        select(Exchange.question, Exchange.answer)
        .where(
            Exchange.conversation_id == conversation_id,
            Exchange.status == "answered",
        )
        .order_by(Exchange.created_at.desc())
        .limit(ASK_HISTORY_LIMIT)
    )
    rows = list(reversed(result.all()))

    messages: list[ChatMessage] = []
    for prior_question, prior_answer in rows:
        messages.append(ChatMessage(role=MessageRole.USER, content=prior_question))
        messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=prior_answer))
    return messages


async def answer_question(
    workspace_id: int, question: str, conversation_id: int | None = None
) -> dict[str, object]:
    async with async_session_factory() as session:
        workspace_result = await session.execute(
            select(
                Workspace.key_source, Workspace.key_provider, Workspace.encrypted_api_key
            ).where(Workspace.id == workspace_id)
        )
        workspace_row = workspace_result.first()

    key_source, key_provider, encrypted_api_key = (
        workspace_row if workspace_row is not None else ("system", None, None)
    )
    used_provider = key_provider if key_source == "dedicated" else LLM_PROVIDER

    llm = _get_llm(key_source, key_provider, encrypted_api_key)

    embed_model = _get_embed_model()
    query_embedding = embed_model.get_query_embedding(question)

    async with async_session_factory() as session:
        result = await session.execute(
            select(Chunk.text, File.display_name, File.filename)
            .join(File, Chunk.file_id == File.id)
            .where(File.workspace_id == workspace_id)
            .order_by(Chunk.embedding.cosine_distance(query_embedding))
            .limit(TOP_K)
        )
        rows = result.all()

        if not rows:
            return {
                "answer": "No documents have been indexed yet.",
                "sources": [],
                "llm_key_source": key_source,
                "llm_provider": used_provider,
            }

        history = (
            await _load_history_messages(session, conversation_id)
            if conversation_id is not None
            else []
        )

    context = "\n\n".join(text for text, _, _ in rows)

    seen_filenames: set[str] = set()
    sources: list[dict[str, str]] = []
    for _, display_name, filename in rows:
        if filename in seen_filenames:
            continue
        seen_filenames.add(filename)
        sources.append(
            {"name": display_name, "url": f"/files/{workspace_id}/{filename}"}
        )
    sources.sort(key=lambda source: source["name"])

    messages = [
        ChatMessage(
            role=MessageRole.SYSTEM,
            content=(
                "Answer the question using only the context below. "
                "If the answer isn't in the context, respond with exactly "
                f'this sentence and nothing else: "{NOT_FOUND_ANSWER}"'
            ),
        ),
        *history,
        ChatMessage(
            role=MessageRole.USER,
            content=f"Context:\n{context}\n\nQuestion: {question}\nAnswer:",
        ),
    ]

    response = await llm.achat(messages)
    answer = _strip_reasoning(str(response.message.content))

    if NOT_FOUND_ANSWER.lower() in answer.lower():
        return {
            "answer": NOT_FOUND_ANSWER,
            "sources": [],
            "llm_key_source": key_source,
            "llm_provider": used_provider,
        }

    return {
        "answer": answer,
        "sources": sources,
        "llm_key_source": key_source,
        "llm_provider": used_provider,
    }
