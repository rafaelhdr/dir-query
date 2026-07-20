"""split display name and original filename

Revision ID: 4cbea274da12
Revises: 471e45769e2a
Create Date: 2026-07-20 05:57:29.975970

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4cbea274da12'
down_revision: Union[str, Sequence[str], None] = '471e45769e2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("files", sa.Column("original_filename", sa.String(), nullable=True))
    op.execute("UPDATE files SET original_filename = original_name")
    op.alter_column("files", "original_filename", nullable=False)

    op.drop_index("uq_files_workspace_id_original_name", table_name="files")
    op.alter_column("files", "original_name", new_column_name="display_name")

    op.create_index(
        "uq_files_workspace_id_display_name",
        "files",
        ["workspace_id", "display_name"],
        unique=True,
    )
    op.create_index(
        "uq_files_workspace_id_original_filename",
        "files",
        ["workspace_id", "original_filename"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_files_workspace_id_original_filename", table_name="files")
    op.drop_index("uq_files_workspace_id_display_name", table_name="files")

    op.alter_column("files", "display_name", new_column_name="original_name")
    op.create_index(
        "uq_files_workspace_id_original_name",
        "files",
        ["workspace_id", "original_name"],
        unique=True,
    )

    op.drop_column("files", "original_filename")
