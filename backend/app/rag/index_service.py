import logging
import threading
from pathlib import Path

from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.minimax import MiniMax
from llama_index.readers.file import PDFReader

from app.config import HF_HOME, INDEX_DIR, MINIMAX_API_KEY, MINIMAX_LLM_MODEL, UPLOAD_DIR

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_index: VectorStoreIndex | None = None
_pdf_reader = PDFReader()
_embed_model: HuggingFaceEmbedding | None = None


def _get_embed_model() -> HuggingFaceEmbedding:
    global _embed_model
    if _embed_model is None:
        _embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-small-en-v1.5",
            cache_folder=str(HF_HOME),
        )
    return _embed_model


def _uploaded_pdf_names() -> list[str]:
    if not UPLOAD_DIR.exists():
        return []
    return sorted(
        p.name for p in UPLOAD_DIR.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"
    )


def _load_or_create_index() -> VectorStoreIndex:
    embed_model = _get_embed_model()
    if (INDEX_DIR / "docstore.json").is_file():
        storage_context = StorageContext.from_defaults(persist_dir=str(INDEX_DIR))
        return load_index_from_storage(storage_context, embed_model=embed_model)
    return VectorStoreIndex.from_documents([], embed_model=embed_model)


def _index_file(path: Path, index: VectorStoreIndex) -> None:
    documents = _pdf_reader.load_data(file=path)
    for document in documents:
        document.doc_id = path.name
        index.insert(document)


def _persist(index: VectorStoreIndex) -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index.storage_context.persist(persist_dir=str(INDEX_DIR))


def sync_index() -> None:
    global _index
    with _lock:
        try:
            index = _load_or_create_index()
            upload_names = _uploaded_pdf_names()
            already_indexed = set(index.ref_doc_info.keys())
            to_index = [name for name in upload_names if name not in already_indexed]

            logger.info(
                "Startup sync: %d upload(s) found, %d already indexed, %d to index",
                len(upload_names),
                len(upload_names) - len(to_index),
                len(to_index),
            )

            if not to_index:
                logger.info("Startup sync: nothing new to index")
                _index = index
                return

            for name in to_index:
                try:
                    _index_file(UPLOAD_DIR / name, index)
                    logger.info("Startup sync: indexed %s", name)
                except Exception:
                    logger.exception("Startup sync: failed to index %s", name)

            _persist(index)
            _index = index
            logger.info("Startup sync: complete")
        except Exception:
            logger.exception("Startup sync: failed")


def index_uploaded_file(path: Path) -> None:
    global _index
    with _lock:
        try:
            index = _index if _index is not None else _load_or_create_index()
            _index_file(path, index)
            _persist(index)
            _index = index
            logger.info("Indexed uploaded file: %s", path.name)
        except Exception:
            logger.exception("Failed to index uploaded file: %s", path.name)


def get_query_engine() -> BaseQueryEngine | None:
    if _index is None or not _index.ref_doc_info:
        return None
    if not MINIMAX_API_KEY:
        raise RuntimeError("MINIMAX_API_KEY is not configured")
    llm = MiniMax(model=MINIMAX_LLM_MODEL, api_key=MINIMAX_API_KEY)
    return _index.as_query_engine(llm=llm)
