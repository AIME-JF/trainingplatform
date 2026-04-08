"""unify exam management core

Revision ID: b6c7d8e9f0a1
Revises: a1b2c3d4e5f8
Create Date: 2026-04-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6c7d8e9f0a1'
down_revision: Union[str, None] = 'a1b2c3d4e5f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('exams', sa.Column('scene', sa.String(length=30), nullable=True, comment='考试场景: training/standalone'))
    op.add_column('exams', sa.Column('participant_mode', sa.String(length=30), nullable=True, comment='参试方式: training_enrollment/excel_import'))
    op.add_column('exams', sa.Column('department_ids', sa.JSON(), nullable=True, comment='目标部门ID列表'))
    op.add_column('exams', sa.Column('police_type_ids', sa.JSON(), nullable=True, comment='目标警种ID列表'))
    op.add_column('exams', sa.Column('participant_summary', sa.Text(), nullable=True, comment='参试对象摘要'))
    op.add_column('exams', sa.Column('legacy_admission_exam_id', sa.Integer(), nullable=True, comment='兼容旧准入考试ID'))
    op.execute("UPDATE exams SET scene = COALESCE(scene, CASE WHEN training_id IS NULL THEN 'standalone' ELSE 'training' END)")
    op.execute("UPDATE exams SET participant_mode = COALESCE(participant_mode, CASE WHEN training_id IS NULL THEN 'excel_import' ELSE 'training_enrollment' END)")
    op.execute("UPDATE exams SET purpose = 'completion' WHERE purpose IS NULL OR purpose IN ('class_assessment', 'final_assessment')")
    op.execute("UPDATE exams SET purpose = 'quiz' WHERE purpose = 'quiz'")
    op.execute("UPDATE exams SET purpose = 'makeup' WHERE purpose = 'makeup'")
    op.alter_column('exams', 'scene', existing_type=sa.String(length=30), nullable=False)
    op.alter_column('exams', 'participant_mode', existing_type=sa.String(length=30), nullable=False)
    op.create_foreign_key(
        'fk_exams_legacy_admission_exam',
        'exams',
        'admission_exams',
        ['legacy_admission_exam_id'],
        ['id'],
    )
    op.create_unique_constraint('uq_exams_legacy_admission_exam_id', 'exams', ['legacy_admission_exam_id'])

    op.add_column('trainings', sa.Column('entry_exam_id', sa.Integer(), nullable=True, comment='统一入口考试ID'))
    op.create_foreign_key(
        'fk_trainings_entry_exam',
        'trainings',
        'exams',
        ['entry_exam_id'],
        ['id'],
    )

    op.create_table(
        'exam_participant_import_batches',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('exam_id', sa.Integer(), nullable=False, comment='考试ID'),
        sa.Column('file_name', sa.String(length=255), nullable=True, comment='导入文件名'),
        sa.Column('status', sa.String(length=30), nullable=True, server_default='preview', comment='状态: preview/confirmed'),
        sa.Column('summary', sa.JSON(), nullable=True, comment='导入汇总'),
        sa.Column('failure_rows', sa.JSON(), nullable=True, comment='失败行清单'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建人ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_exam_participant_import_batches_id', 'exam_participant_import_batches', ['id'])

    op.create_table(
        'exam_participants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('exam_id', sa.Integer(), nullable=False, comment='考试ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('import_batch_id', sa.Integer(), nullable=True, comment='导入批次ID'),
        sa.Column('source_row_no', sa.Integer(), nullable=True, comment='Excel 行号'),
        sa.Column('source_snapshot', sa.JSON(), nullable=True, comment='导入原始快照'),
        sa.Column('match_status', sa.String(length=30), nullable=True, server_default='matched', comment='匹配状态: matched/created'),
        sa.Column('participation_status', sa.String(length=30), nullable=True, server_default='assigned', comment='参试状态: assigned/submitted/absent'),
        sa.Column('generated_password', sa.String(length=100), nullable=True, comment='自动创建账号时生成的初始密码'),
        sa.Column('password_exported_at', sa.DateTime(timezone=True), nullable=True, comment='初始密码导出时间'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='分配时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['import_batch_id'], ['exam_participant_import_batches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('exam_id', 'user_id', name='uq_exam_participants_exam_user'),
    )
    op.create_index('ix_exam_participants_id', 'exam_participants', ['id'])


def downgrade() -> None:
    op.drop_index('ix_exam_participants_id', table_name='exam_participants')
    op.drop_table('exam_participants')
    op.drop_index('ix_exam_participant_import_batches_id', table_name='exam_participant_import_batches')
    op.drop_table('exam_participant_import_batches')
    op.drop_constraint('fk_trainings_entry_exam', 'trainings', type_='foreignkey')
    op.drop_column('trainings', 'entry_exam_id')
    op.drop_constraint('uq_exams_legacy_admission_exam_id', 'exams', type_='unique')
    op.drop_constraint('fk_exams_legacy_admission_exam', 'exams', type_='foreignkey')
    op.drop_column('exams', 'legacy_admission_exam_id')
    op.drop_column('exams', 'participant_summary')
    op.drop_column('exams', 'police_type_ids')
    op.drop_column('exams', 'department_ids')
    op.drop_column('exams', 'participant_mode')
    op.drop_column('exams', 'scene')
