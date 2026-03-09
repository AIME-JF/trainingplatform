"""add_resource_library_core

Revision ID: a1b2c3d4e5f6
Revises: f8edba8d885b
Create Date: 2026-03-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f8edba8d885b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table('resources'):
        op.create_table(
            'resources',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False, comment='资源标题'),
            sa.Column('summary', sa.Text(), nullable=True, comment='资源摘要'),
            sa.Column('content_type', sa.String(length=30), nullable=False, server_default='video', comment='内容类型: video/image_text/document/mixed'),
            sa.Column('uploader_id', sa.Integer(), nullable=False, comment='上传者ID'),
            sa.Column('source_type', sa.String(length=30), nullable=False, server_default='ugc', comment='来源类型: ugc/official/imported'),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='draft', comment='状态: draft/pending_review/reviewing/published/rejected/offline'),
            sa.Column('visibility_type', sa.String(length=30), nullable=False, server_default='public', comment='可见域类型: public/department/police_type/custom'),
            sa.Column('owner_department_id', sa.Integer(), nullable=True, comment='归属部门ID'),
            sa.Column('review_policy_id', sa.Integer(), nullable=True, comment='命中审核策略ID'),
            sa.Column('cover_media_file_id', sa.Integer(), nullable=True, comment='封面文件ID'),
            sa.Column('publish_at', sa.DateTime(timezone=True), nullable=True, comment='发布时间'),
            sa.Column('offline_at', sa.DateTime(timezone=True), nullable=True, comment='下线时间'),
            sa.Column('view_count', sa.Integer(), nullable=True, server_default='0', comment='浏览次数'),
            sa.Column('like_count', sa.Integer(), nullable=True, server_default='0', comment='点赞次数'),
            sa.Column('favorite_count', sa.Integer(), nullable=True, server_default='0', comment='收藏次数'),
            sa.Column('metadata_json', sa.JSON(), nullable=True, comment='扩展字段'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()'), comment='创建时间'),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
            sa.ForeignKeyConstraint(['uploader_id'], ['users.id']),
            sa.ForeignKeyConstraint(['owner_department_id'], ['departments.id']),
            sa.ForeignKeyConstraint(['cover_media_file_id'], ['media_files.id']),
            sa.PrimaryKeyConstraint('id')
        )

    if not inspector.has_table('resource_media_links'):
        op.create_table(
            'resource_media_links',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('resource_id', sa.Integer(), nullable=False),
            sa.Column('media_file_id', sa.Integer(), nullable=False),
            sa.Column('media_role', sa.String(length=30), nullable=False, server_default='main', comment='文件角色: main/attachment/subtitle'),
            sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0', comment='排序'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()'), comment='创建时间'),
            sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['media_file_id'], ['media_files.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('resource_id', 'media_file_id', 'media_role', name='uq_resource_media_role')
        )

    if not inspector.has_table('resource_tags'):
        op.create_table(
            'resource_tags',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=50), nullable=False, comment='标签名'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()'), comment='创建时间'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )

    if not inspector.has_table('resource_tag_relations'):
        op.create_table(
            'resource_tag_relations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('resource_id', sa.Integer(), nullable=False),
            sa.Column('tag_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['tag_id'], ['resource_tags.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('resource_id', 'tag_id', name='uq_resource_tag')
        )

    if not inspector.has_table('resource_visibility_scopes'):
        op.create_table(
            'resource_visibility_scopes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('resource_id', sa.Integer(), nullable=False),
            sa.Column('scope_type', sa.String(length=30), nullable=False, comment='范围类型: department/police_type/role/user'),
            sa.Column('scope_id', sa.Integer(), nullable=False, comment='范围ID'),
            sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('resource_id', 'scope_type', 'scope_id', name='uq_resource_scope')
        )

    if not inspector.has_table('course_resource_refs'):
        op.create_table(
            'course_resource_refs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('course_id', sa.Integer(), nullable=False),
            sa.Column('resource_id', sa.Integer(), nullable=False),
            sa.Column('usage_type', sa.String(length=30), nullable=False, server_default='required', comment='用途: required/optional/extension'),
            sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0', comment='排序'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()'), comment='创建时间'),
            sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('course_id', 'resource_id', name='uq_course_resource_ref')
        )

    if not inspector.has_table('training_resource_refs'):
        op.create_table(
            'training_resource_refs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('training_id', sa.Integer(), nullable=False),
            sa.Column('resource_id', sa.Integer(), nullable=False),
            sa.Column('usage_type', sa.String(length=30), nullable=False, server_default='required', comment='用途: required/optional/extension'),
            sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0', comment='排序'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()'), comment='创建时间'),
            sa.ForeignKeyConstraint(['training_id'], ['trainings.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('training_id', 'resource_id', name='uq_training_resource_ref')
        )

    # indexes
    if inspector.has_table('resources'):
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('resources')}
        if 'ix_resources_id' not in existing_indexes:
            op.create_index('ix_resources_id', 'resources', ['id'], unique=False)
        if 'ix_resources_uploader_id' not in existing_indexes:
            op.create_index('ix_resources_uploader_id', 'resources', ['uploader_id'], unique=False)
        if 'ix_resources_owner_department_id' not in existing_indexes:
            op.create_index('ix_resources_owner_department_id', 'resources', ['owner_department_id'], unique=False)
        if 'ix_resources_status' not in existing_indexes:
            op.create_index('ix_resources_status', 'resources', ['status'], unique=False)

    if inspector.has_table('resource_media_links'):
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('resource_media_links')}
        if 'ix_resource_media_links_id' not in existing_indexes:
            op.create_index('ix_resource_media_links_id', 'resource_media_links', ['id'], unique=False)
        if 'ix_resource_media_links_resource_id' not in existing_indexes:
            op.create_index('ix_resource_media_links_resource_id', 'resource_media_links', ['resource_id'], unique=False)
        if 'ix_resource_media_links_media_file_id' not in existing_indexes:
            op.create_index('ix_resource_media_links_media_file_id', 'resource_media_links', ['media_file_id'], unique=False)

    if inspector.has_table('resource_tags'):
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('resource_tags')}
        if 'ix_resource_tags_id' not in existing_indexes:
            op.create_index('ix_resource_tags_id', 'resource_tags', ['id'], unique=False)
        if 'ix_resource_tags_name' not in existing_indexes:
            op.create_index('ix_resource_tags_name', 'resource_tags', ['name'], unique=False)

    if inspector.has_table('resource_tag_relations'):
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('resource_tag_relations')}
        if 'ix_resource_tag_relations_id' not in existing_indexes:
            op.create_index('ix_resource_tag_relations_id', 'resource_tag_relations', ['id'], unique=False)
        if 'ix_resource_tag_relations_resource_id' not in existing_indexes:
            op.create_index('ix_resource_tag_relations_resource_id', 'resource_tag_relations', ['resource_id'], unique=False)
        if 'ix_resource_tag_relations_tag_id' not in existing_indexes:
            op.create_index('ix_resource_tag_relations_tag_id', 'resource_tag_relations', ['tag_id'], unique=False)

    if inspector.has_table('resource_visibility_scopes'):
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('resource_visibility_scopes')}
        if 'ix_resource_visibility_scopes_id' not in existing_indexes:
            op.create_index('ix_resource_visibility_scopes_id', 'resource_visibility_scopes', ['id'], unique=False)
        if 'ix_resource_visibility_scopes_resource_id' not in existing_indexes:
            op.create_index('ix_resource_visibility_scopes_resource_id', 'resource_visibility_scopes', ['resource_id'], unique=False)
        if 'ix_resource_scope_type_id' not in existing_indexes:
            op.create_index('ix_resource_scope_type_id', 'resource_visibility_scopes', ['scope_type', 'scope_id'], unique=False)

    if inspector.has_table('course_resource_refs'):
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('course_resource_refs')}
        if 'ix_course_resource_refs_id' not in existing_indexes:
            op.create_index('ix_course_resource_refs_id', 'course_resource_refs', ['id'], unique=False)
        if 'ix_course_resource_refs_course_id' not in existing_indexes:
            op.create_index('ix_course_resource_refs_course_id', 'course_resource_refs', ['course_id'], unique=False)
        if 'ix_course_resource_refs_resource_id' not in existing_indexes:
            op.create_index('ix_course_resource_refs_resource_id', 'course_resource_refs', ['resource_id'], unique=False)

    if inspector.has_table('training_resource_refs'):
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('training_resource_refs')}
        if 'ix_training_resource_refs_id' not in existing_indexes:
            op.create_index('ix_training_resource_refs_id', 'training_resource_refs', ['id'], unique=False)
        if 'ix_training_resource_refs_training_id' not in existing_indexes:
            op.create_index('ix_training_resource_refs_training_id', 'training_resource_refs', ['training_id'], unique=False)
        if 'ix_training_resource_refs_resource_id' not in existing_indexes:
            op.create_index('ix_training_resource_refs_resource_id', 'training_resource_refs', ['resource_id'], unique=False)

    # chapters.resource_id compatibility column
    if inspector.has_table('chapters'):
        chapter_columns = {col['name'] for col in inspector.get_columns('chapters')}
        if 'resource_id' not in chapter_columns:
            op.add_column('chapters', sa.Column('resource_id', sa.Integer(), nullable=True, comment='关联资源ID'))

        fk_names = {fk.get('name') for fk in inspector.get_foreign_keys('chapters')}
        if 'chapters_resource_id_fkey' not in fk_names:
            op.create_foreign_key('chapters_resource_id_fkey', 'chapters', 'resources', ['resource_id'], ['id'])

        chapter_indexes = {idx['name'] for idx in inspector.get_indexes('chapters')}
        if 'ix_chapters_resource_id' not in chapter_indexes:
            op.create_index('ix_chapters_resource_id', 'chapters', ['resource_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table('chapters'):
        chapter_indexes = {idx['name'] for idx in inspector.get_indexes('chapters')}
        if 'ix_chapters_resource_id' in chapter_indexes:
            op.drop_index('ix_chapters_resource_id', table_name='chapters')

        fk_names = {fk.get('name') for fk in inspector.get_foreign_keys('chapters')}
        if 'chapters_resource_id_fkey' in fk_names:
            op.drop_constraint('chapters_resource_id_fkey', 'chapters', type_='foreignkey')

        chapter_columns = {col['name'] for col in inspector.get_columns('chapters')}
        if 'resource_id' in chapter_columns:
            op.drop_column('chapters', 'resource_id')

    for table_name, index_names in [
        ('training_resource_refs', ['ix_training_resource_refs_resource_id', 'ix_training_resource_refs_training_id', 'ix_training_resource_refs_id']),
        ('course_resource_refs', ['ix_course_resource_refs_resource_id', 'ix_course_resource_refs_course_id', 'ix_course_resource_refs_id']),
        ('resource_visibility_scopes', ['ix_resource_scope_type_id', 'ix_resource_visibility_scopes_resource_id', 'ix_resource_visibility_scopes_id']),
        ('resource_tag_relations', ['ix_resource_tag_relations_tag_id', 'ix_resource_tag_relations_resource_id', 'ix_resource_tag_relations_id']),
        ('resource_tags', ['ix_resource_tags_name', 'ix_resource_tags_id']),
        ('resource_media_links', ['ix_resource_media_links_media_file_id', 'ix_resource_media_links_resource_id', 'ix_resource_media_links_id']),
        ('resources', ['ix_resources_status', 'ix_resources_owner_department_id', 'ix_resources_uploader_id', 'ix_resources_id']),
    ]:
        if inspector.has_table(table_name):
            existing_indexes = {idx['name'] for idx in inspector.get_indexes(table_name)}
            for idx in index_names:
                if idx in existing_indexes:
                    op.drop_index(idx, table_name=table_name)

    if inspector.has_table('training_resource_refs'):
        op.drop_table('training_resource_refs')
    if inspector.has_table('course_resource_refs'):
        op.drop_table('course_resource_refs')
    if inspector.has_table('resource_visibility_scopes'):
        op.drop_table('resource_visibility_scopes')
    if inspector.has_table('resource_tag_relations'):
        op.drop_table('resource_tag_relations')
    if inspector.has_table('resource_tags'):
        op.drop_table('resource_tags')
    if inspector.has_table('resource_media_links'):
        op.drop_table('resource_media_links')
    if inspector.has_table('resources'):
        op.drop_table('resources')
