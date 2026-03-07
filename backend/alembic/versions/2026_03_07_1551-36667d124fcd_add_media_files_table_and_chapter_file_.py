"""add media files table and chapter file_id

Revision ID: 36667d124fcd
Revises: fb59ba77bec3
Create Date: 2026-03-07 15:51:20.577348

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '36667d124fcd'
down_revision: Union[str, None] = 'fb59ba77bec3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # media_files 表（若不存在则创建）
    if not inspector.has_table('media_files'):
        op.create_table('media_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False, comment='原始文件名'),
        sa.Column('storage_path', sa.String(length=1000), nullable=False, comment='存储路径(相对)'),
        sa.Column('mime_type', sa.String(length=100), nullable=True, comment='MIME类型'),
        sa.Column('size', sa.BigInteger(), nullable=True, comment='文件大小(字节)'),
        sa.Column('hash', sa.String(length=64), nullable=True, comment='SHA256哈希(秒传)'),
        sa.Column('uploader_id', sa.Integer(), nullable=True, comment='上传者ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='上传时间'),
        sa.ForeignKeyConstraint(['uploader_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    # 索引（存在则跳过）
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('media_files')} if inspector.has_table('media_files') else set()
    if op.f('ix_media_files_hash') not in existing_indexes:
        op.create_index(op.f('ix_media_files_hash'), 'media_files', ['hash'], unique=False)
    if op.f('ix_media_files_id') not in existing_indexes:
        op.create_index(op.f('ix_media_files_id'), 'media_files', ['id'], unique=False)

    # chapters.file_id（存在则跳过）
    chapter_columns = {col['name'] for col in inspector.get_columns('chapters')}
    if 'file_id' not in chapter_columns:
        op.add_column('chapters', sa.Column('file_id', sa.Integer(), nullable=True, comment='关联文件ID'))

    # 字段注释同步（可重复执行）
    op.alter_column('chapters', 'video_url',
               existing_type=sa.VARCHAR(length=500),
               comment='视频URL(兼容旧数据)',
               existing_comment='视频URL',
               existing_nullable=True)
    op.alter_column('chapters', 'doc_url',
               existing_type=sa.VARCHAR(length=500),
               comment='文档URL(兼容旧数据)',
               existing_comment='文档URL',
               existing_nullable=True)

    # 外键（存在则跳过）
    fk_names = {fk.get('name') for fk in inspector.get_foreign_keys('chapters')}
    if 'chapters_file_id_fkey' not in fk_names:
        op.create_foreign_key('chapters_file_id_fkey', 'chapters', 'media_files', ['file_id'], ['id'])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # chapters 外键/列
    fk_names = {fk.get('name') for fk in inspector.get_foreign_keys('chapters')}
    if 'chapters_file_id_fkey' in fk_names:
        op.drop_constraint('chapters_file_id_fkey', 'chapters', type_='foreignkey')

    chapter_columns = {col['name'] for col in inspector.get_columns('chapters')}
    if 'file_id' in chapter_columns:
        op.drop_column('chapters', 'file_id')

    # 注释回滚
    op.alter_column('chapters', 'doc_url',
               existing_type=sa.VARCHAR(length=500),
               comment='文档URL',
               existing_comment='文档URL(兼容旧数据)',
               existing_nullable=True)
    op.alter_column('chapters', 'video_url',
               existing_type=sa.VARCHAR(length=500),
               comment='视频URL',
               existing_comment='视频URL(兼容旧数据)',
               existing_nullable=True)

    # media_files 表
    if inspector.has_table('media_files'):
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('media_files')}
        if op.f('ix_media_files_id') in existing_indexes:
            op.drop_index(op.f('ix_media_files_id'), table_name='media_files')
        if op.f('ix_media_files_hash') in existing_indexes:
            op.drop_index(op.f('ix_media_files_hash'), table_name='media_files')
        op.drop_table('media_files')
