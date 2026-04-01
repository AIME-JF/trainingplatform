"""add_training_type_id_to_trainings

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-01 10:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 检查列是否已存在
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.columns "
        "WHERE table_name = 'trainings' AND column_name = 'training_type_id')"
    ))
    col_exists = result.scalar()

    if not col_exists:
        op.add_column('trainings', sa.Column('training_type_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_trainings_training_type_id',
            'trainings', 'training_types',
            ['training_type_id'], ['id']
        )

    # 根据现有 type 字段回填 training_type_id
    conn.execute(sa.text(
        "UPDATE trainings SET training_type_id = ("
        "SELECT id FROM training_types WHERE code = trainings.type"
        ") WHERE training_type_id IS NULL AND type IS NOT NULL"
    ))


def downgrade() -> None:
    op.drop_constraint('fk_trainings_training_type_id', 'trainings', type_='foreignkey')
    op.drop_column('trainings', 'training_type_id')
