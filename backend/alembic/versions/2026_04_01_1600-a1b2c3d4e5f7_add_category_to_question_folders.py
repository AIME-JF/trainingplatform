"""add_category_to_question_folders

Revision ID: a1b2c3d4e5f7
Revises: 3654902f12cf
Create Date: 2026-04-01 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = '3654902f12cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'question_folders' AND column_name = 'category')"
    ))
    if not result.scalar():
        op.add_column('question_folders', sa.Column('category', sa.String(50), nullable=True, comment="题库分类"))


def downgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'question_folders' AND column_name = 'category')"
    ))
    if result.scalar():
        op.drop_column('question_folders', 'category')
