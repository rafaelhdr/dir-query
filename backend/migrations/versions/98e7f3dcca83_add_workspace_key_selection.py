"""add workspace key selection

Revision ID: 98e7f3dcca83
Revises: 9ceea53adb0e
Create Date: 2026-07-22 16:43:33.378608

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98e7f3dcca83'
down_revision: Union[str, Sequence[str], None] = '9ceea53adb0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('exchanges', sa.Column('llm_key_source', sa.String(), nullable=True))
    op.add_column('exchanges', sa.Column('llm_provider', sa.String(), nullable=True))
    op.create_check_constraint(
        'exchanges_llm_key_source_check',
        'exchanges',
        "llm_key_source IS NULL OR llm_key_source IN ('system', 'dedicated')",
    )
    op.create_check_constraint(
        'exchanges_llm_provider_check',
        'exchanges',
        "llm_provider IS NULL OR llm_provider IN ('gemini', 'minimax')",
    )
    op.add_column('workspaces', sa.Column('description', sa.String(), server_default='', nullable=False))
    op.add_column('workspaces', sa.Column('key_source', sa.String(), server_default='system', nullable=False))
    op.add_column('workspaces', sa.Column('key_provider', sa.String(), nullable=True))
    op.add_column('workspaces', sa.Column('encrypted_api_key', sa.String(), nullable=True))
    op.create_check_constraint(
        'workspaces_key_source_check',
        'workspaces',
        "key_source IN ('system', 'dedicated')",
    )
    op.create_check_constraint(
        'workspaces_key_provider_check',
        'workspaces',
        "key_provider IS NULL OR key_provider IN ('gemini', 'minimax')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('workspaces_key_provider_check', 'workspaces', type_='check')
    op.drop_constraint('workspaces_key_source_check', 'workspaces', type_='check')
    op.drop_column('workspaces', 'encrypted_api_key')
    op.drop_column('workspaces', 'key_provider')
    op.drop_column('workspaces', 'key_source')
    op.drop_column('workspaces', 'description')
    op.drop_constraint('exchanges_llm_provider_check', 'exchanges', type_='check')
    op.drop_constraint('exchanges_llm_key_source_check', 'exchanges', type_='check')
    op.drop_column('exchanges', 'llm_provider')
    op.drop_column('exchanges', 'llm_key_source')
