"""add_recommendation_tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-09 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table('resource_behavior_events'):
        op.create_table(
            'resource_behavior_events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
            sa.Column('resource_id', sa.Integer(), nullable=False, comment='资源ID'),
            sa.Column('event_type', sa.String(length=30), nullable=False, comment='事件类型: impression/click/play/complete/like/favorite'),
            sa.Column('watch_seconds', sa.Integer(), nullable=True, server_default='0', comment='观看时长(秒)'),
            sa.Column('context_json', sa.JSON(), nullable=True, comment='上下文信息'),
            sa.Column('event_time', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()'), comment='事件时间'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    if not inspector.has_table('resource_recommend_scores'):
        op.create_table(
            'resource_recommend_scores',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
            sa.Column('resource_id', sa.Integer(), nullable=False, comment='资源ID'),
            sa.Column('score', sa.Float(), nullable=False, server_default='0', comment='综合分'),
            sa.Column('police_type_score', sa.Float(), nullable=False, server_default='0', comment='警种匹配分'),
            sa.Column('department_score', sa.Float(), nullable=False, server_default='0', comment='部门匹配分'),
            sa.Column('interest_score', sa.Float(), nullable=False, server_default='0', comment='兴趣分'),
            sa.Column('freshness_score', sa.Float(), nullable=False, server_default='0', comment='新鲜度分'),
            sa.Column('popularity_score', sa.Float(), nullable=False, server_default='0', comment='热度分'),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()'), comment='更新时间'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'resource_id', name='uq_user_resource_score')
        )

    table_indexes = {
        'resource_behavior_events': [
            ('ix_resource_behavior_events_id', ['id']),
            ('ix_resource_behavior_events_user_id', ['user_id']),
            ('ix_resource_behavior_events_resource_id', ['resource_id']),
            ('ix_resource_behavior_events_event_type', ['event_type']),
            ('ix_resource_behavior_events_event_time', ['event_time']),
            ('ix_behavior_user_time', ['user_id', 'event_time']),
        ],
        'resource_recommend_scores': [
            ('ix_resource_recommend_scores_id', ['id']),
            ('ix_resource_recommend_scores_user_id', ['user_id']),
            ('ix_resource_recommend_scores_resource_id', ['resource_id']),
            ('ix_recommend_user_score', ['user_id', 'score']),
        ],
    }

    for table_name, indexes in table_indexes.items():
        if not inspector.has_table(table_name):
            continue
        existing = {idx['name'] for idx in inspector.get_indexes(table_name)}
        for idx_name, cols in indexes:
            if idx_name not in existing:
                op.create_index(idx_name, table_name, cols, unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    table_indexes = {
        'resource_recommend_scores': ['ix_recommend_user_score', 'ix_resource_recommend_scores_resource_id', 'ix_resource_recommend_scores_user_id', 'ix_resource_recommend_scores_id'],
        'resource_behavior_events': ['ix_behavior_user_time', 'ix_resource_behavior_events_event_time', 'ix_resource_behavior_events_event_type', 'ix_resource_behavior_events_resource_id', 'ix_resource_behavior_events_user_id', 'ix_resource_behavior_events_id'],
    }

    for table_name, idx_names in table_indexes.items():
        if not inspector.has_table(table_name):
            continue
        existing = {idx['name'] for idx in inspector.get_indexes(table_name)}
        for idx in idx_names:
            if idx in existing:
                op.drop_index(idx, table_name=table_name)

    if inspector.has_table('resource_recommend_scores'):
        op.drop_table('resource_recommend_scores')
    if inspector.has_table('resource_behavior_events'):
        op.drop_table('resource_behavior_events')
