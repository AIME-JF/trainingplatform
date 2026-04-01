"""add_course_id_to_knowledge_points

Revision ID: a3d174a9a2c7
Revises: a3d174a9a2c6
Create Date: 2026-04-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3d174a9a2c7'
down_revision = 'a3d174a9a2c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查 knowledge_points 表是否有 course_id 列
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'knowledge_points' AND column_name = 'course_id')"))
    column_exists = result.scalar()

    if not column_exists:
        # 给 knowledge_points 表添加 course_id 列
        op.add_column('knowledge_points', sa.Column('course_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_knowledge_points_course_id',
            'knowledge_points', 'courses',
            ['course_id'], ['id']
        )


def downgrade() -> None:
    op.drop_constraint('fk_knowledge_points_course_id', 'knowledge_points', type_='foreignkey')
    op.drop_column('knowledge_points', 'course_id')
