"""fix missing constraints comments and indexes

Revision ID: ce901f6434c1
Revises: 30b77460a6dd
Create Date: 2026-04-08 16:39:55.321639

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ce901f6434c1'
down_revision: Union[str, None] = '30b77460a6dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _constraint_exists(table: str, name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.table_constraints "
        "WHERE table_name = :table AND constraint_name = :name"
    ), {"table": table, "name": name})
    return result.scalar() is not None


def _index_exists(name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT 1 FROM pg_indexes WHERE indexname = :name"
    ), {"name": name})
    return result.scalar() is not None


def _column_is_nullable(table: str, column: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT is_nullable FROM information_schema.columns "
        "WHERE table_name = :table AND column_name = :column"
    ), {"table": table, "column": column})
    row = result.scalar()
    return row == 'YES'


def upgrade() -> None:
    # === exams: 补齐字段 comments ===
    op.alter_column('exams', 'scene',
               existing_type=sa.VARCHAR(length=30),
               comment='考试场景: training/standalone',
               existing_nullable=True)
    op.alter_column('exams', 'participant_mode',
               existing_type=sa.VARCHAR(length=30),
               comment='参试方式: training_enrollment/excel_import',
               existing_nullable=True)
    op.alter_column('exams', 'purpose',
               existing_type=sa.VARCHAR(length=50),
               comment='用途: admission/completion/quiz/makeup/special/other',
               existing_nullable=True,
               existing_server_default=sa.text("'class_assessment'::character varying"))
    op.alter_column('exams', 'department_ids',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               comment='目标部门ID列表',
               existing_nullable=True)
    op.alter_column('exams', 'police_type_ids',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               comment='目标警种ID列表',
               existing_nullable=True)
    op.alter_column('exams', 'participant_summary',
               existing_type=sa.TEXT(),
               comment='参试对象摘要',
               existing_nullable=True)
    op.alter_column('exams', 'legacy_admission_exam_id',
               existing_type=sa.INTEGER(),
               comment='兼容旧准入考试ID',
               existing_nullable=True)

    # === exams: 补齐 legacy_admission_exam_id 的 unique + FK ===
    if not _constraint_exists('exams', 'uq_exams_legacy_admission_exam_id'):
        op.create_unique_constraint('uq_exams_legacy_admission_exam_id', 'exams', ['legacy_admission_exam_id'])
    if not _constraint_exists('exams', 'fk_exams_legacy_admission_exam'):
        op.create_foreign_key('fk_exams_legacy_admission_exam', 'exams', 'admission_exams', ['legacy_admission_exam_id'], ['id'])

    # === resource_review_tasks: 索引重命名 ===
    if _index_exists('ix_review_task_assignee_status'):
        op.drop_index('ix_review_task_assignee_status', table_name='resource_review_tasks')
    if not _index_exists('ix_review_task_assignee_status_legacy'):
        op.create_index('ix_review_task_assignee_status_legacy', 'resource_review_tasks', ['assignee_user_id', 'status'], unique=False)

    # === resources: 统一 count 字段为 NOT NULL ===
    for col in ('view_count', 'like_count', 'share_count', 'comment_count', 'favorite_count'):
        if _column_is_nullable('resources', col):
            # 先把 NULL 值填为 0
            op.execute(sa.text(f"UPDATE resources SET {col} = 0 WHERE {col} IS NULL"))
            op.alter_column('resources', col, existing_type=sa.INTEGER(), nullable=False)

    # === trainings: 更新 comments + 补齐 entry_exam_id FK ===
    op.alter_column('trainings', 'admission_exam_id',
               existing_type=sa.INTEGER(),
               comment='旧准入考试ID',
               existing_nullable=True)
    op.alter_column('trainings', 'entry_exam_id',
               existing_type=sa.INTEGER(),
               comment='统一入口考试ID',
               existing_nullable=True)
    if not _constraint_exists('trainings', 'fk_trainings_entry_exam'):
        op.create_foreign_key('fk_trainings_entry_exam', 'trainings', 'exams', ['entry_exam_id'], ['id'])


def downgrade() -> None:
    # === trainings ===
    if _constraint_exists('trainings', 'fk_trainings_entry_exam'):
        op.drop_constraint('fk_trainings_entry_exam', 'trainings', type_='foreignkey')
    op.alter_column('trainings', 'entry_exam_id',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_nullable=True)
    op.alter_column('trainings', 'admission_exam_id',
               existing_type=sa.INTEGER(),
               comment='准入考试ID',
               existing_nullable=True)

    # === resources ===
    for col in ('favorite_count', 'comment_count', 'share_count', 'like_count', 'view_count'):
        op.alter_column('resources', col, existing_type=sa.INTEGER(), nullable=True)

    # === resource_review_tasks ===
    if _index_exists('ix_review_task_assignee_status_legacy'):
        op.drop_index('ix_review_task_assignee_status_legacy', table_name='resource_review_tasks')
    if not _index_exists('ix_review_task_assignee_status'):
        op.create_index('ix_review_task_assignee_status', 'resource_review_tasks', ['assignee_user_id', 'status'], unique=False)

    # === exams ===
    if _constraint_exists('exams', 'fk_exams_legacy_admission_exam'):
        op.drop_constraint('fk_exams_legacy_admission_exam', 'exams', type_='foreignkey')
    if _constraint_exists('exams', 'uq_exams_legacy_admission_exam_id'):
        op.drop_constraint('uq_exams_legacy_admission_exam_id', 'exams', type_='unique')

    op.alter_column('exams', 'legacy_admission_exam_id', existing_type=sa.INTEGER(), comment=None, existing_nullable=True)
    op.alter_column('exams', 'participant_summary', existing_type=sa.TEXT(), comment=None, existing_nullable=True)
    op.alter_column('exams', 'police_type_ids', existing_type=postgresql.JSON(astext_type=sa.Text()), comment=None, existing_nullable=True)
    op.alter_column('exams', 'department_ids', existing_type=postgresql.JSON(astext_type=sa.Text()), comment=None, existing_nullable=True)
    op.alter_column('exams', 'purpose', existing_type=sa.VARCHAR(length=50),
               comment='用途: class_assessment/final_assessment/quiz/makeup',
               existing_nullable=True,
               existing_server_default=sa.text("'class_assessment'::character varying"))
    op.alter_column('exams', 'participant_mode', existing_type=sa.VARCHAR(length=30), comment=None, existing_nullable=True)
    op.alter_column('exams', 'scene', existing_type=sa.VARCHAR(length=30), comment=None, existing_nullable=True)
