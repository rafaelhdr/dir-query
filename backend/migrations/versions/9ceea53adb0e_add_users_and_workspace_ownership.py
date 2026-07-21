"""add users and workspace ownership

Revision ID: 9ceea53adb0e
Revises: a5f63248171d
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ceea53adb0e'
down_revision: Union[str, Sequence[str], None] = 'a5f63248171d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.add_column(
        "workspaces",
        sa.Column(
            "owner_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.drop_column("workspaces", "owner_email")
    op.drop_column("workspaces", "password")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "workspaces", sa.Column("password", sa.String(), nullable=True)
    )
    op.add_column(
        "workspaces", sa.Column("owner_email", sa.String(), nullable=True)
    )
    op.drop_column("workspaces", "owner_user_id")
    op.drop_table("users")
