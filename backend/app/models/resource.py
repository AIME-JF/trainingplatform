"""
资源库相关数据库模型
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, JSON,
    UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Resource(Base):
    """资源主体"""
    __tablename__ = 'resources'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment='资源标题')
    summary = Column(Text, nullable=True, comment='资源摘要')
    content_type = Column(String(30), nullable=False, default='video', comment='内容类型: video/image/document（兼容历史值 image_text）/mixed')
    uploader_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True, comment='上传者ID')
    source_type = Column(String(30), nullable=False, default='ugc', comment='来源类型: ugc/official/imported')
    status = Column(String(30), nullable=False, default='draft', index=True, comment='状态: draft/pending_review/reviewing/published/rejected/offline')
    visibility_type = Column(String(30), nullable=False, default='public', comment='可见域类型: public/department/police_type/custom')
    owner_department_id = Column(Integer, ForeignKey('departments.id'), nullable=True, index=True, comment='归属部门ID')
    review_policy_id = Column(Integer, nullable=True, comment='命中审核策略ID')
    cover_media_file_id = Column(Integer, ForeignKey('media_files.id'), nullable=True, comment='封面文件ID')

    publish_at = Column(DateTime(timezone=True), nullable=True, comment='发布时间')
    offline_at = Column(DateTime(timezone=True), nullable=True, comment='下线时间')

    view_count = Column(Integer, default=0, comment='浏览次数')
    like_count = Column(Integer, default=0, comment='点赞次数')
    favorite_count = Column(Integer, default=0, comment='收藏次数')

    metadata_json = Column(JSON, nullable=True, comment='扩展字段')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')

    uploader = relationship('User', foreign_keys=[uploader_id])
    owner_department = relationship('Department', foreign_keys=[owner_department_id])
    cover_media = relationship('MediaFile', foreign_keys=[cover_media_file_id])
    media_links = relationship('ResourceMediaLink', back_populates='resource', cascade='all, delete-orphan')
    tag_relations = relationship('ResourceTagRelation', back_populates='resource', cascade='all, delete-orphan')
    visibility_scopes = relationship('ResourceVisibilityScope', back_populates='resource', cascade='all, delete-orphan')


class ResourceMediaLink(Base):
    """资源与文件关联"""
    __tablename__ = 'resource_media_links'

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey('resources.id', ondelete='CASCADE'), nullable=False, index=True)
    media_file_id = Column(Integer, ForeignKey('media_files.id'), nullable=False, index=True)
    media_role = Column(String(30), nullable=False, default='main', comment='文件角色: main/attachment/subtitle')
    sort_order = Column(Integer, default=0, comment='排序')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')

    __table_args__ = (
        UniqueConstraint('resource_id', 'media_file_id', 'media_role', name='uq_resource_media_role'),
    )

    resource = relationship('Resource', back_populates='media_links')
    media_file = relationship('MediaFile', foreign_keys=[media_file_id])


class ResourceTag(Base):
    """资源标签"""
    __tablename__ = 'resource_tags'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True, comment='标签名')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')


class ResourceTagRelation(Base):
    """资源标签关联"""
    __tablename__ = 'resource_tag_relations'

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey('resources.id', ondelete='CASCADE'), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey('resource_tags.id', ondelete='CASCADE'), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('resource_id', 'tag_id', name='uq_resource_tag'),
    )

    resource = relationship('Resource', back_populates='tag_relations')
    tag = relationship('ResourceTag', foreign_keys=[tag_id])


class ResourceVisibilityScope(Base):
    """资源可见域明细"""
    __tablename__ = 'resource_visibility_scopes'

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey('resources.id', ondelete='CASCADE'), nullable=False, index=True)
    scope_type = Column(String(30), nullable=False, comment='范围类型: department/police_type/role/user')
    scope_id = Column(Integer, nullable=False, comment='范围ID')

    __table_args__ = (
        UniqueConstraint('resource_id', 'scope_type', 'scope_id', name='uq_resource_scope'),
        Index('ix_resource_scope_type_id', 'scope_type', 'scope_id'),
    )

    resource = relationship('Resource', back_populates='visibility_scopes')


class CourseResourceRef(Base):
    """课程引用资源"""
    __tablename__ = 'course_resource_refs'

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    resource_id = Column(Integer, ForeignKey('resources.id', ondelete='CASCADE'), nullable=False, index=True)
    usage_type = Column(String(30), nullable=False, default='required', comment='用途: required/optional/extension')
    sort_order = Column(Integer, default=0, comment='排序')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')

    __table_args__ = (
        UniqueConstraint('course_id', 'resource_id', name='uq_course_resource_ref'),
    )

    resource = relationship('Resource', foreign_keys=[resource_id])


class TrainingResourceRef(Base):
    """培训引用资源"""
    __tablename__ = 'training_resource_refs'

    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey('trainings.id', ondelete='CASCADE'), nullable=False, index=True)
    resource_id = Column(Integer, ForeignKey('resources.id', ondelete='CASCADE'), nullable=False, index=True)
    usage_type = Column(String(30), nullable=False, default='required', comment='用途: required/optional/extension')
    sort_order = Column(Integer, default=0, comment='排序')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')

    __table_args__ = (
        UniqueConstraint('training_id', 'resource_id', name='uq_training_resource_ref'),
    )

    resource = relationship('Resource', foreign_keys=[resource_id])
