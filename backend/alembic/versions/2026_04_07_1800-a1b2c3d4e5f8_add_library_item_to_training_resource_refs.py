"""add library_item to training_resource_refs

Revision ID: a1b2c3d4e5f8
Revises: 764d58596f22
Create Date: 2026-04-07 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f8'
down_revision: Union[str, None] = '764d58596f22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # training_resource_refs: resource_id nullable + 新增 library_item_id
    op.alter_column('training_resource_refs', 'resource_id', nullable=True)
    op.add_column(
        'training_resource_refs',
        sa.Column('library_item_id', sa.Integer(), nullable=True, comment='知识库资源ID'),
    )
    op.create_foreign_key(
        'fk_training_resource_ref_library_item',
        'training_resource_refs', 'library_items',
        ['library_item_id'], ['id'],
        ondelete='CASCADE',
    )
    op.create_unique_constraint(
        'uq_training_library_item_ref',
        'training_resource_refs',
        ['training_id', 'library_item_id'],
    )
    op.create_index(
        'ix_training_resource_refs_library_item_id',
        'training_resource_refs',
        ['library_item_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_training_resource_refs_library_item_id', table_name='training_resource_refs')
    op.drop_constraint('uq_training_library_item_ref', 'training_resource_refs', type_='unique')
    op.drop_constraint('fk_training_resource_ref_library_item', 'training_resource_refs', type_='foreignkey')
    op.drop_column('training_resource_refs', 'library_item_id')
    op.alter_column('training_resource_refs', 'resource_id', nullable=False)
