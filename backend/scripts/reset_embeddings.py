"""Reset indexed chunks after changing EMBED_PROVIDER.

Different embedding providers produce vectors in incompatible vector
spaces, so switching EMBED_PROVIDER on a deployment that already has
indexed content requires clearing existing chunks and re-indexing under
the newly configured provider. This script:

1. determines the target embedding dimension by calling the currently
   configured provider (not a hardcoded per-provider table, since the
   specific model in use is itself configurable);
2. clears the `chunks` table and resizes its `embedding` column to that
   dimension;
3. resets previously indexed/failed files back to `pending` so the next
   startup sync re-indexes them automatically.

This is destructive (all chunks are cleared) and has no confirmation
prompt. Usage: uv run python scripts/reset_embeddings.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.db.session import engine  # noqa: E402
from app.rag.index_service import _get_embed_model  # noqa: E402


def _target_dimension() -> int:
    embed_model = _get_embed_model()
    return len(embed_model.get_text_embedding("dimension probe"))


async def reset_embeddings(target_dim: int) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE chunks"))
        await conn.execute(
            text(f"ALTER TABLE chunks ALTER COLUMN embedding TYPE vector({target_dim})")
        )
        await conn.execute(
            text("UPDATE files SET status = 'pending' WHERE status IN ('indexed', 'failed')")
        )


def main() -> None:
    target_dim = _target_dimension()
    asyncio.run(reset_embeddings(target_dim))
    print(
        f"Reset complete: chunks cleared, embedding column resized to "
        f"vector({target_dim}), affected files marked pending for re-indexing."
    )


if __name__ == "__main__":
    main()
