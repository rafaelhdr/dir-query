import logging
import re
from pathlib import Path

from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.llms import LLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.llms.minimax import MiniMax
from llama_index.readers.file import PDFReader
from sqlalchemy import select

from app.config import (
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
from app.db.models import Chunk, File
from app.db.session import async_session_factory

logger = logging.getLogger(__name__)

TOP_K = 5

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


def _get_llm() -> LLM:
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


async def answer_question(workspace_id: int, question: str) -> dict[str, object]:
    llm = _get_llm()

    embed_model = _get_embed_model()
    query_embedding = embed_model.get_query_embedding(question)

    async with async_session_factory() as session:
        result = await session.execute(
            select(Chunk.text, File.original_name)
            .join(File, Chunk.file_id == File.id)
            .where(File.workspace_id == workspace_id)
            .order_by(Chunk.embedding.cosine_distance(query_embedding))
            .limit(TOP_K)
        )
        rows = result.all()

    if not rows:
        return {"answer": "No documents have been indexed yet.", "sources": []}

    context = "\n\n".join(text for text, _ in rows)
    sources = sorted({original_name for _, original_name in rows})

    prompt = (
        "Answer the question using only the context below. "
        "If the answer isn't in the context, say you don't know.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )

    response = await llm.acomplete(prompt)

    return {"answer": _strip_reasoning(str(response)), "sources": sources}
