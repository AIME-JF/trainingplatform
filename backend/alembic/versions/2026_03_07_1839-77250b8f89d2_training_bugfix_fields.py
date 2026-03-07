"""training bugfix fields

Revision ID: 77250b8f89d2
Revises: fcaa5aebe6f6
Create Date: 2026-03-07 18:39:07.641535

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '77250b8f89d2'
down_revision: Union[str, None] = 'fcaa5aebe6f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # training_courses.schedules（存在则跳过）
    if inspector.has_table('training_courses'):
        training_course_columns = {col['name'] for col in inspector.get_columns('training_courses')}
        if 'schedules' not in training_course_columns:
            op.add_column('training_courses', sa.Column('schedules', sa.JSON(), nullable=True, comment='排课清单'))

    # checkin_records.session_key + 约束索引（存在则跳过）
    if inspector.has_table('checkin_records'):
        checkin_columns = {col['name'] for col in inspector.get_columns('checkin_records')}

        if 'session_key' not in checkin_columns:
            op.add_column(
                'checkin_records',
                sa.Column('session_key', sa.String(length=100), nullable=True, server_default=sa.text("'start'"), comment='签到场次标识')
            )

        op.execute("UPDATE checkin_records SET session_key = 'start' WHERE session_key IS NULL")
        op.alter_column(
            'checkin_records',
            'session_key',
            existing_type=sa.String(length=100),
            nullable=False,
            server_default=sa.text("'start'"),
            existing_comment='签到场次标识'
        )

        # 清理可能的历史重复签到数据，避免新增唯一约束失败
        op.execute("""
        WITH ranked AS (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY training_id, user_id, date, session_key
                       ORDER BY id
                   ) AS rn
            FROM checkin_records
        )
        DELETE FROM checkin_records c
        USING ranked r
        WHERE c.id = r.id AND r.rn > 1
        """)

        inspector = inspect(bind)
        unique_constraint_names = {
            uc['name'] for uc in inspector.get_unique_constraints('checkin_records') if uc.get('name')
        }
        if 'uq_checkin_training_user_date_session' not in unique_constraint_names:
            op.create_unique_constraint(
                'uq_checkin_training_user_date_session',
                'checkin_records',
                ['training_id', 'user_id', 'date', 'session_key']
            )

        index_names = {idx['name'] for idx in inspector.get_indexes('checkin_records')}
        if 'ix_checkin_training_date_session' not in index_names:
            op.create_index(
                'ix_checkin_training_date_session',
                'checkin_records',
                ['training_id', 'date', 'session_key'],
                unique=False
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table('checkin_records'):
        index_names = {idx['name'] for idx in inspector.get_indexes('checkin_records')}
        if 'ix_checkin_training_date_session' in index_names:
            op.drop_index('ix_checkin_training_date_session', table_name='checkin_records')

        unique_constraint_names = {
            uc['name'] for uc in inspector.get_unique_constraints('checkin_records') if uc.get('name')
        }
        if 'uq_checkin_training_user_date_session' in unique_constraint_names:
            op.drop_constraint('uq_checkin_training_user_date_session', 'checkin_records', type_='unique')

        checkin_columns = {col['name'] for col in inspector.get_columns('checkin_records')}
        if 'session_key' in checkin_columns:
            op.drop_column('checkin_records', 'session_key')

    if inspector.has_table('training_courses'):
        training_course_columns = {col['name'] for col in inspector.get_columns('training_courses')}
        if 'schedules' in training_course_columns:
            op.drop_column('training_courses', 'schedules')
