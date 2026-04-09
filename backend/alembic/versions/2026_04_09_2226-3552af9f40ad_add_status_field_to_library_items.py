"""add status field to library items

Revision ID: 3552af9f40ad
Revises: 8c1d2e3f4a5b
Create Date: 2026-04-09 22:26:58.299393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3552af9f40ad'
down_revision: Union[str, None] = '8c1d2e3f4a5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('library_items', sa.Column('status', sa.String(length=30), nullable=False, server_default='draft', comment='状态: draft/pending_review/reviewing/published/rejected'))
    op.create_index(op.f('ix_library_items_status'), 'library_items', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_library_items_status'), table_name='library_items')
    op.drop_column('library_items', 'status')
