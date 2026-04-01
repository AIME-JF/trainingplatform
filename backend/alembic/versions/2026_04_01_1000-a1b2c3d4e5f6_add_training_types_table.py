"""add_training_types_table

Revision ID: a1b2c3d4e5f6
Revises: 1a2b3c4d5e6f
Create Date: 2026-04-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 检查 training_types 表是否已存在
    result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'training_types')"))
    table_exists = result.scalar()

    if not table_exists:
        op.create_table(
            'training_types',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('code', sa.String(50), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
            sa.Column('sort_order', sa.Integer(), server_default=sa.text('0'), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_training_types_id', 'training_types', ['id'])
        op.create_index('ix_training_types_code', 'training_types', ['code'], unique=True)
        op.create_unique_constraint('uq_training_types_name', 'training_types', ['name'])

    # 插入默认数据
    result = conn.execute(sa.text("SELECT COUNT(*) FROM training_types"))
    count = result.scalar()
    if count == 0:
        conn.execute(sa.text(
            "INSERT INTO training_types (name, code, description, is_active, sort_order) VALUES "
            "('基础训练', 'basic', '基础训练类型', true, 1), "
            "('专项训练', 'special', '专项训练类型', true, 2), "
            "('晋升培训', 'promotion', '晋升培训类型', true, 3), "
            "('线上培训', 'online', '线上培训类型', true, 4)"
        ))


def downgrade() -> None:
    op.drop_table('training_types')
