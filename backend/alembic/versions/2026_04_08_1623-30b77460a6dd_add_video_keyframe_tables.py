"""add video keyframe tables

Revision ID: 30b77460a6dd
Revises: d2e3f4a5b6c7
Create Date: 2026-04-08 16:23:07.881830

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '30b77460a6dd'
down_revision: Union[str, None] = 'd2e3f4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('video_keyframe_tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('media_file_id', sa.Integer(), nullable=False, comment='原始视频文件ID'),
    sa.Column('resource_id', sa.Integer(), nullable=True, comment='关联资源ID'),
    sa.Column('status', sa.String(length=30), nullable=False, comment='pending/running/success/partial_success/failed'),
    sa.Column('video_duration', sa.Float(), nullable=True, comment='视频时长(秒)'),
    sa.Column('thumbnail_storage_path', sa.String(length=1000), nullable=True, comment='缩略图视频存储路径'),
    sa.Column('base_candidate_count', sa.Integer(), nullable=True, comment='基础采样候选数'),
    sa.Column('scene_candidate_count', sa.Integer(), nullable=True, comment='场景补充候选数'),
    sa.Column('dedup_count', sa.Integer(), nullable=True, comment='去重后数量'),
    sa.Column('final_count', sa.Integer(), nullable=True, comment='最终输出数'),
    sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
    sa.Column('strategy_version', sa.String(length=20), nullable=True, comment='抽帧策略版本'),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['media_file_id'], ['media_files.id'], ),
    sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_video_keyframe_tasks_id'), 'video_keyframe_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_video_keyframe_tasks_media_file_id'), 'video_keyframe_tasks', ['media_file_id'], unique=False)
    op.create_index(op.f('ix_video_keyframe_tasks_resource_id'), 'video_keyframe_tasks', ['resource_id'], unique=False)
    op.create_table('video_keyframes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('media_file_id', sa.Integer(), nullable=False, comment='原始视频文件ID'),
    sa.Column('timestamp', sa.Float(), nullable=False, comment='帧时间点(秒)'),
    sa.Column('minute_bucket', sa.Integer(), nullable=False, comment='所属分钟桶'),
    sa.Column('source_type', sa.String(length=20), nullable=False, comment='base/scene'),
    sa.Column('scene_score', sa.Float(), nullable=True, comment='场景变化分数'),
    sa.Column('storage_path', sa.String(length=1000), nullable=False, comment='关键帧图片MinIO路径'),
    sa.Column('width', sa.Integer(), nullable=True),
    sa.Column('height', sa.Integer(), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=True, comment='排序序号'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['media_file_id'], ['media_files.id'], ),
    sa.ForeignKeyConstraint(['task_id'], ['video_keyframe_tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_video_keyframes_id'), 'video_keyframes', ['id'], unique=False)
    op.create_index(op.f('ix_video_keyframes_media_file_id'), 'video_keyframes', ['media_file_id'], unique=False)
    op.create_index(op.f('ix_video_keyframes_task_id'), 'video_keyframes', ['task_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_video_keyframes_task_id'), table_name='video_keyframes')
    op.drop_index(op.f('ix_video_keyframes_media_file_id'), table_name='video_keyframes')
    op.drop_index(op.f('ix_video_keyframes_id'), table_name='video_keyframes')
    op.drop_table('video_keyframes')
    op.drop_index(op.f('ix_video_keyframe_tasks_resource_id'), table_name='video_keyframe_tasks')
    op.drop_index(op.f('ix_video_keyframe_tasks_media_file_id'), table_name='video_keyframe_tasks')
    op.drop_index(op.f('ix_video_keyframe_tasks_id'), table_name='video_keyframe_tasks')
    op.drop_table('video_keyframe_tasks')
