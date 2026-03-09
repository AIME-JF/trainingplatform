"""add_review_workflow_tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-09 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table('review_policies'):
        op.create_table(
            'review_policies',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False, comment='策略名称'),
            sa.Column('enabled', sa.Boolean(), nullable=True, server_default=sa.text('true'), comment='是否启用'),
            sa.Column('scope_type', sa.String(length=30), nullable=False, server_default='global', comment='作用域: global/department/department_tree'),
            sa.Column('scope_department_id', sa.Integer(), nullable=True, comment='作用部门ID'),
            sa.Column('uploader_constraint', sa.String(length=30), nullable=False, server_default='all', comment='上传者约束: all/specific_role/specific_department'),
            sa.Column('constraint_ref_id', sa.Integer(), nullable=True, comment='约束对象ID'),
            sa.Column('priority', sa.Integer(), nullable=True, server_default='100', comment='优先级(小优先)'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()'), comment='创建时间'),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
            sa.ForeignKeyConstraint(['scope_department_id'], ['departments.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )

    if not inspector.has_table('review_policy_stages'):
        op.create_table(
            'review_policy_stages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('policy_id', sa.Integer(), nullable=False),
            sa.Column('stage_order', sa.Integer(), nullable=False, comment='阶段顺序'),
            sa.Column('reviewer_type', sa.String(length=30), nullable=False, comment='审核人类型: role/department/user'),
            sa.Column('reviewer_ref_id', sa.Integer(), nullable=False, comment='审核对象ID'),
            sa.Column('min_approvals', sa.Integer(), nullable=True, server_default='1', comment='最小通过数'),
            sa.Column('allow_self_review', sa.Boolean(), nullable=True, server_default=sa.text('false'), comment='允许自审'),
            sa.ForeignKeyConstraint(['policy_id'], ['review_policies.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('policy_id', 'stage_order', name='uq_review_policy_stage_order')
        )

    if not inspector.has_table('resource_review_workflows'):
        op.create_table(
            'resource_review_workflows',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('resource_id', sa.Integer(), nullable=False),
            sa.Column('policy_id', sa.Integer(), nullable=False),
            sa.Column('current_stage', sa.Integer(), nullable=True, server_default='1', comment='当前阶段'),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='pending', comment='状态: pending/reviewing/approved/rejected/cancelled'),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()'), comment='发起时间'),
            sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True, comment='结束时间'),
            sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['policy_id'], ['review_policies.id']),
            sa.PrimaryKeyConstraint('id')
        )

    if not inspector.has_table('resource_review_tasks'):
        op.create_table(
            'resource_review_tasks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('workflow_id', sa.Integer(), nullable=False),
            sa.Column('resource_id', sa.Integer(), nullable=False),
            sa.Column('stage_order', sa.Integer(), nullable=False, comment='阶段顺序'),
            sa.Column('assignee_user_id', sa.Integer(), nullable=False, comment='审核人ID'),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='pending', comment='状态: pending/approved/rejected/skipped'),
            sa.Column('comment', sa.Text(), nullable=True, comment='审核意见'),
            sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True, comment='审核时间'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()'), comment='创建时间'),
            sa.ForeignKeyConstraint(['workflow_id'], ['resource_review_workflows.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['assignee_user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )

    if not inspector.has_table('resource_review_logs'):
        op.create_table(
            'resource_review_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('resource_id', sa.Integer(), nullable=False),
            sa.Column('workflow_id', sa.Integer(), nullable=False),
            sa.Column('actor_id', sa.Integer(), nullable=False),
            sa.Column('action', sa.String(length=30), nullable=False, comment='动作: submit/approve/reject/revoke/reassign'),
            sa.Column('detail_json', sa.JSON(), nullable=True, comment='日志详情'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()'), comment='创建时间'),
            sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['workflow_id'], ['resource_review_workflows.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['actor_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )

    table_indexes = {
        'review_policies': ['ix_review_policies_id', 'ix_review_policies_priority'],
        'review_policy_stages': ['ix_review_policy_stages_id', 'ix_review_policy_stages_policy_id'],
        'resource_review_workflows': ['ix_resource_review_workflows_id', 'ix_resource_review_workflows_resource_id', 'ix_resource_review_workflows_policy_id', 'ix_workflow_resource_status'],
        'resource_review_tasks': ['ix_resource_review_tasks_id', 'ix_resource_review_tasks_workflow_id', 'ix_resource_review_tasks_resource_id', 'ix_resource_review_tasks_assignee_user_id', 'ix_resource_review_tasks_status', 'ix_review_task_assignee_status'],
        'resource_review_logs': ['ix_resource_review_logs_id', 'ix_resource_review_logs_resource_id', 'ix_resource_review_logs_workflow_id', 'ix_resource_review_logs_actor_id'],
    }

    for table_name, index_names in table_indexes.items():
        if not inspector.has_table(table_name):
            continue
        existing = {idx['name'] for idx in inspector.get_indexes(table_name)}
        for idx_name in index_names:
            if idx_name in existing:
                continue
            if idx_name == 'ix_review_policies_priority':
                op.create_index(idx_name, table_name, ['priority'], unique=False)
            elif idx_name == 'ix_review_policy_stages_policy_id':
                op.create_index(idx_name, table_name, ['policy_id'], unique=False)
            elif idx_name == 'ix_workflow_resource_status':
                op.create_index(idx_name, table_name, ['resource_id', 'status'], unique=False)
            elif idx_name == 'ix_review_task_assignee_status':
                op.create_index(idx_name, table_name, ['assignee_user_id', 'status'], unique=False)
            elif idx_name == 'ix_resource_review_tasks_workflow_id':
                op.create_index(idx_name, table_name, ['workflow_id'], unique=False)
            elif idx_name == 'ix_resource_review_tasks_resource_id':
                op.create_index(idx_name, table_name, ['resource_id'], unique=False)
            elif idx_name == 'ix_resource_review_tasks_assignee_user_id':
                op.create_index(idx_name, table_name, ['assignee_user_id'], unique=False)
            elif idx_name == 'ix_resource_review_tasks_status':
                op.create_index(idx_name, table_name, ['status'], unique=False)
            elif idx_name == 'ix_resource_review_workflows_resource_id':
                op.create_index(idx_name, table_name, ['resource_id'], unique=False)
            elif idx_name == 'ix_resource_review_workflows_policy_id':
                op.create_index(idx_name, table_name, ['policy_id'], unique=False)
            elif idx_name == 'ix_resource_review_logs_resource_id':
                op.create_index(idx_name, table_name, ['resource_id'], unique=False)
            elif idx_name == 'ix_resource_review_logs_workflow_id':
                op.create_index(idx_name, table_name, ['workflow_id'], unique=False)
            elif idx_name == 'ix_resource_review_logs_actor_id':
                op.create_index(idx_name, table_name, ['actor_id'], unique=False)
            else:
                # 默认按 id 建索引
                op.create_index(idx_name, table_name, ['id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    table_indexes = {
        'resource_review_logs': ['ix_resource_review_logs_actor_id', 'ix_resource_review_logs_workflow_id', 'ix_resource_review_logs_resource_id', 'ix_resource_review_logs_id'],
        'resource_review_tasks': ['ix_review_task_assignee_status', 'ix_resource_review_tasks_status', 'ix_resource_review_tasks_assignee_user_id', 'ix_resource_review_tasks_resource_id', 'ix_resource_review_tasks_workflow_id', 'ix_resource_review_tasks_id'],
        'resource_review_workflows': ['ix_workflow_resource_status', 'ix_resource_review_workflows_policy_id', 'ix_resource_review_workflows_resource_id', 'ix_resource_review_workflows_id'],
        'review_policy_stages': ['ix_review_policy_stages_policy_id', 'ix_review_policy_stages_id'],
        'review_policies': ['ix_review_policies_priority', 'ix_review_policies_id'],
    }

    for table_name, idx_names in table_indexes.items():
        if not inspector.has_table(table_name):
            continue
        existing = {idx['name'] for idx in inspector.get_indexes(table_name)}
        for idx in idx_names:
            if idx in existing:
                op.drop_index(idx, table_name=table_name)

    if inspector.has_table('resource_review_logs'):
        op.drop_table('resource_review_logs')
    if inspector.has_table('resource_review_tasks'):
        op.drop_table('resource_review_tasks')
    if inspector.has_table('resource_review_workflows'):
        op.drop_table('resource_review_workflows')
    if inspector.has_table('review_policy_stages'):
        op.drop_table('review_policy_stages')
    if inspector.has_table('review_policies'):
        op.drop_table('review_policies')
