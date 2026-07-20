"""add unique constraint on files workspace_id original_name

Revision ID: 471e45769e2a
Revises: 52f29471367f
Create Date: 2026-07-19 18:09:51.527554

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '471e45769e2a'
down_revision: Union[str, Sequence[str], None] = '52f29471367f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "uq_files_workspace_id_original_name",
        "files",
        ["workspace_id", "original_name"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_files_workspace_id_original_name", table_name="files")
