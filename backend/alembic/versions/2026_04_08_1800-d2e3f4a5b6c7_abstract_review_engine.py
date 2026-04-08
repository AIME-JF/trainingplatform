"""abstract_review_engine

新增通用审核表（review_workflows / review_tasks / review_logs），
ReviewPolicy 新增 business_type 字段，
将 resource_review_* 旧表数据迁移到通用表。
旧表保留不删除。

Revision ID: d2e3f4a5b6c7
Revises: b1c2d3e4f5a6
Create Date: 2026-04-08 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


# revision identifiers, used by Alembic.
revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # === 1. ReviewPolicy 新增 business_type 字段 ===
    if 'review_policies' in existing_tables:
        existing_columns = {col['name'] for col in inspector.get_columns('review_policies')}
        if 'business_type' not in existing_columns:
            op.add_column('review_policies', sa.Column(
                'business_type', sa.String(length=30), nullable=False,
                server_default='resource', comment='业务类型: resource/training/exam'
            ))

        # 尝试添加联合唯一约束（business_type + name），先移除旧的 name 唯一约束
        existing_constraints = {uc['name'] for uc in inspector.get_unique_constraints('review_policies')}
        if 'uq_review_policy_biz_name' not in existing_constraints:
            # 尝试移除旧的 name 唯一约束
            for uc in inspector.get_unique_constraints('review_policies'):
                if uc.get('column_names') == ['name']:
                    try:
                        op.drop_constraint(uc['name'], 'review_policies', type_='unique')
                    except Exception:
                        pass
                    break
            try:
                op.create_unique_constraint(
                    'uq_review_policy_biz_name', 'review_policies', ['business_type', 'name']
                )
            except Exception:
                pass

    # === 2. 创建通用审核表 ===
    if 'review_workflows' not in existing_tables:
        op.create_table(
            'review_workflows',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('business_type', sa.String(length=30), nullable=False, comment='业务类型: resource/training/exam'),
            sa.Column('business_id', sa.Integer(), nullable=False, comment='业务对象ID'),
            sa.Column('policy_id', sa.Integer(), nullable=False),
            sa.Column('current_stage', sa.Integer(), nullable=True, server_default='1', comment='当前阶段'),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='pending',
                      comment='状态: pending/reviewing/approved/rejected/cancelled'),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()'), comment='发起时间'),
            sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True, comment='结束时间'),
            sa.ForeignKeyConstraint(['policy_id'], ['review_policies.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_review_workflows_id', 'review_workflows', ['id'], unique=False)
        op.create_index('ix_review_workflows_policy_id', 'review_workflows', ['policy_id'], unique=False)
        op.create_index('ix_review_workflows_status', 'review_workflows', ['status'], unique=False)
        op.create_index('ix_review_workflow_biz', 'review_workflows', ['business_type', 'business_id'], unique=False)
        op.create_index('ix_review_workflow_biz_status', 'review_workflows', ['business_type', 'business_id', 'status'], unique=False)

    if 'review_tasks' not in existing_tables:
        op.create_table(
            'review_tasks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('workflow_id', sa.Integer(), nullable=False),
            sa.Column('business_type', sa.String(length=30), nullable=False, comment='业务类型'),
            sa.Column('business_id', sa.Integer(), nullable=False, comment='业务对象ID'),
            sa.Column('stage_order', sa.Integer(), nullable=False, comment='阶段顺序'),
            sa.Column('assignee_user_id', sa.Integer(), nullable=False, comment='审核人ID'),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='pending',
                      comment='状态: pending/approved/rejected/skipped'),
            sa.Column('comment', sa.Text(), nullable=True, comment='审核意见'),
            sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True, comment='审核时间'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()'), comment='创建时间'),
            sa.ForeignKeyConstraint(['workflow_id'], ['review_workflows.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['assignee_user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_review_tasks_id', 'review_tasks', ['id'], unique=False)
        op.create_index('ix_review_tasks_workflow_id', 'review_tasks', ['workflow_id'], unique=False)
        op.create_index('ix_review_tasks_assignee_user_id', 'review_tasks', ['assignee_user_id'], unique=False)
        op.create_index('ix_review_tasks_status', 'review_tasks', ['status'], unique=False)
        op.create_index('ix_review_task_biz', 'review_tasks', ['business_type', 'business_id'], unique=False)
        op.create_index('ix_review_task_assignee_status_v2', 'review_tasks', ['assignee_user_id', 'status'], unique=False)

    if 'review_logs' not in existing_tables:
        op.create_table(
            'review_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('business_type', sa.String(length=30), nullable=False, comment='业务类型'),
            sa.Column('business_id', sa.Integer(), nullable=False, comment='业务对象ID'),
            sa.Column('workflow_id', sa.Integer(), nullable=False),
            sa.Column('actor_id', sa.Integer(), nullable=False),
            sa.Column('action', sa.String(length=30), nullable=False, comment='动作: submit/approve/reject/revoke/reassign'),
            sa.Column('detail_json', sa.JSON(), nullable=True, comment='日志详情'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()'), comment='创建时间'),
            sa.ForeignKeyConstraint(['workflow_id'], ['review_workflows.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['actor_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_review_logs_id', 'review_logs', ['id'], unique=False)
        op.create_index('ix_review_logs_workflow_id', 'review_logs', ['workflow_id'], unique=False)
        op.create_index('ix_review_logs_actor_id', 'review_logs', ['actor_id'], unique=False)
        op.create_index('ix_review_log_biz', 'review_logs', ['business_type', 'business_id'], unique=False)

    # === 3. 数据迁移：从旧表搬到新表 ===
    # 检查新表刚建且旧表存在时才迁移
    if 'resource_review_workflows' in existing_tables and 'review_workflows' in existing_tables:
        # 只在新表为空时迁移，避免重复执行
        conn = op.get_bind()
        count = conn.execute(text('SELECT COUNT(*) FROM review_workflows')).scalar()
        if count == 0:
            conn.execute(text("""
                INSERT INTO review_workflows (id, business_type, business_id, policy_id, current_stage, status, started_at, finished_at)
                SELECT id, 'resource', resource_id, policy_id, current_stage, status, started_at, finished_at
                FROM resource_review_workflows
            """))

    if 'resource_review_tasks' in existing_tables and 'review_tasks' in existing_tables:
        conn = op.get_bind()
        count = conn.execute(text('SELECT COUNT(*) FROM review_tasks')).scalar()
        if count == 0:
            conn.execute(text("""
                INSERT INTO review_tasks (id, workflow_id, business_type, business_id, stage_order, assignee_user_id, status, comment, reviewed_at, created_at)
                SELECT id, workflow_id, 'resource', resource_id, stage_order, assignee_user_id, status, comment, reviewed_at, created_at
                FROM resource_review_tasks
            """))

    if 'resource_review_logs' in existing_tables and 'review_logs' in existing_tables:
        conn = op.get_bind()
        count = conn.execute(text('SELECT COUNT(*) FROM review_logs')).scalar()
        if count == 0:
            conn.execute(text("""
                INSERT INTO review_logs (id, business_type, business_id, workflow_id, actor_id, action, detail_json, created_at)
                SELECT id, 'resource', resource_id, workflow_id, actor_id, action, detail_json, created_at
                FROM resource_review_logs
            """))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # 删除通用表（按依赖顺序）
    if 'review_logs' in existing_tables:
        op.drop_table('review_logs')
    if 'review_tasks' in existing_tables:
        op.drop_table('review_tasks')
    if 'review_workflows' in existing_tables:
        op.drop_table('review_workflows')

    # 移除 business_type 字段
    if 'review_policies' in existing_tables:
        existing_columns = {col['name'] for col in inspector.get_columns('review_policies')}
        if 'business_type' in existing_columns:
            # 先移除联合唯一约束
            existing_constraints = {uc['name'] for uc in inspector.get_unique_constraints('review_policies')}
            if 'uq_review_policy_biz_name' in existing_constraints:
                op.drop_constraint('uq_review_policy_biz_name', 'review_policies', type_='unique')
            op.drop_column('review_policies', 'business_type')
            # 恢复旧的 name 唯一约束
            try:
                op.create_unique_constraint(None, 'review_policies', ['name'])
            except Exception:
                pass
