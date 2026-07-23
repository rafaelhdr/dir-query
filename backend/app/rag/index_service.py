import logging
from collections.abc import AsyncIterator
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


_THINK_OPEN = "<think>"
_THINK_CLOSE = "</think>"


class _ReasoningFilter:
    """Removes <think>...</think> reasoning blocks from a token stream as it
    arrives, rather than after the fact. A plain "strip the whole buffer on
    every delta" approach doesn't work while a <think> tag is still open (no
    closing tag yet to match against) — that's exactly the window where an
    unfiltered chunk would leak raw reasoning text to the client. This holds
    back text while inside an unclosed block, and holds back a short tail
    that could be the start of a tag split across chunk boundaries."""

    def __init__(self) -> None:
        self._pending = ""
        self._in_think = False

    def feed(self, delta: str) -> str:
        self._pending += delta
        emitted = []
        while True:
            if self._in_think:
                idx = self._pending.find(_THINK_CLOSE)
                if idx == -1:
                    break
                self._pending = self._pending[idx + len(_THINK_CLOSE) :].lstrip()
                self._in_think = False
                continue

            idx = self._pending.find(_THINK_OPEN)
            if idx == -1:
                hold = 0
                for i in range(1, len(_THINK_OPEN)):
                    if self._pending.endswith(_THINK_OPEN[:i]):
                        hold = i
                        break
                safe_end = len(self._pending) - hold
                if safe_end > 0:
                    emitted.append(self._pending[:safe_end])
                self._pending = self._pending[safe_end:]
                break

            if idx > 0:
                emitted.append(self._pending[:idx])
            self._pending = self._pending[idx + len(_THINK_OPEN) :]
            self._in_think = True

        return "".join(emitted)

    def flush(self) -> str:
        """Releases any leftover text once the stream ends. A still-unclosed
        <think> block at end-of-stream is dropped (nothing after it was ever
        going to be answer text); a dangling partial tag prefix that never
        completed is plain text after all."""
        if self._in_think:
            return ""
        return self._pending


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


async def resolve_llm(workspace_id: int) -> tuple[LLM, str, str | None]:
    """Resolve which LLM/key to use for a workspace, eagerly, so a missing
    API key raises RuntimeError before any streaming response has started
    (see `conversations.ask`)."""
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
    return llm, key_source, used_provider


async def answer_question(
    llm: LLM,
    key_source: str,
    used_provider: str | None,
    workspace_id: int,
    question: str,
    conversation_id: int | None = None,
) -> AsyncIterator[dict[str, object]]:
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
            answer = "No documents have been indexed yet."
            yield {"type": "token", "text": answer}
            yield {
                "type": "final",
                "answer": answer,
                "sources": [],
                "llm_key_source": key_source,
                "llm_provider": used_provider,
            }
            return

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

    response_gen = await llm.astream_chat(messages)

    reasoning_filter = _ReasoningFilter()
    answer_parts: list[str] = []
    async for chunk in response_gen:
        visible = reasoning_filter.feed(chunk.delta or "")
        if visible:
            answer_parts.append(visible)
            yield {"type": "token", "text": visible}

    trailing = reasoning_filter.flush()
    if trailing:
        answer_parts.append(trailing)
        yield {"type": "token", "text": trailing}

    answer = "".join(answer_parts).strip()

    # The final event always carries the authoritative answer text (which
    # can differ slightly from what was streamed above, e.g. when the
    # not-found sentence gets canonicalized below) so the client can do one
    # last corrective render on completion.
    if NOT_FOUND_ANSWER.lower() in answer.lower():
        yield {
            "type": "final",
            "answer": NOT_FOUND_ANSWER,
            "sources": [],
            "llm_key_source": key_source,
            "llm_provider": used_provider,
        }
        return

    yield {
        "type": "final",
        "answer": answer,
        "sources": sources,
        "llm_key_source": key_source,
        "llm_provider": used_provider,
    }
