"""create workspaces files chunks

Revision ID: 52f29471367f
Revises:
Create Date: 2026-07-16 16:32:11.575245

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '52f29471367f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "workspaces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("owner_email", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("slug", name="uq_workspaces_slug"),
    )

    op.create_table(
        "files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.Integer(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("original_name", sa.String(), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=False),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "status", sa.String(), nullable=False, server_default="pending"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'indexed', 'failed')",
            name="files_status_check",
        ),
    )
    op.create_index("ix_files_workspace_id", "files", ["workspace_id"])

    op.create_table(
        "chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "file_id",
            sa.Integer(),
            sa.ForeignKey("files.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_chunks_file_id", "chunks", ["file_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_chunks_file_id", table_name="chunks")
    op.drop_table("chunks")
    op.drop_index("ix_files_workspace_id", table_name="files")
    op.drop_table("files")
    op.drop_table("workspaces")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
    op.execute("DROP EXTENSION IF EXISTS vector")
