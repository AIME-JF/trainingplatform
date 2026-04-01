"""
课程管理相关的数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Course(Base):
    """课程表"""
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment='课程标题')
    category = Column(String(50), nullable=False, comment='课程分类: law/fraud/traffic/community/cybersec/physical')
    file_type = Column(String(20), nullable=False, default='video', comment='文件类型: video/document/image/mixed')
    description = Column(Text, comment='课程描述')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, index=True, comment='创建人ID')
    instructor_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='教官ID')
    duration = Column(Integer, default=0, comment='总时长(分钟)')
    student_count = Column(Integer, default=0, comment='学习人数')
    rating = Column(Float, default=0, comment='评分')
    difficulty = Column(Integer, default=1, comment='难度1-5')
    is_required = Column(Boolean, default=False, comment='是否必修')
    cover_color = Column(String(20), nullable=True, comment='封面色')
    scope = Column(String(200), nullable=True, comment='可见范围摘要')
    scope_type = Column(String(30), nullable=False, default='all', comment='可见范围类型: all/user/department/role')
    scope_target_ids = Column(JSON, nullable=True, comment='可见范围目标ID列表')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')

    # 关联关系
    creator = relationship("User", foreign_keys=[created_by])
    instructor = relationship("User", foreign_keys=[instructor_id])
    chapters = relationship("Chapter", back_populates="course", cascade="all, delete-orphan")
    notes = relationship("CourseNote", back_populates="course", cascade="all, delete-orphan")
    qa_list = relationship("CourseQA", back_populates="course", cascade="all, delete-orphan")
    tag_relations = relationship("CourseTagRelation", back_populates="course", cascade="all, delete-orphan")
    knowledge_points = relationship("KnowledgePoint", back_populates="course")


class Chapter(Base):
    """课程章节表"""
    __tablename__ = 'chapters'

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, comment='课程ID')
    title = Column(String(200), nullable=False, comment='章节标题')
    sort_order = Column(Integer, default=0, comment='排序')
    duration = Column(Integer, default=0, comment='时长(分钟)')
    video_url = Column(String(500), nullable=True, comment='视频URL(兼容旧数据)')
    doc_url = Column(String(500), nullable=True, comment='文档URL(兼容旧数据)')
    file_id = Column(Integer, ForeignKey('media_files.id'), nullable=True, comment='关联文件ID')
    resource_id = Column(Integer, ForeignKey('resources.id'), nullable=True, index=True, comment='关联资源ID')

    # 关联关系
    course = relationship("Course", back_populates="chapters")
    file = relationship("MediaFile", foreign_keys=[file_id])
    resource = relationship("Resource", foreign_keys=[resource_id])


class CourseNote(Base):
    """课程笔记表"""
    __tablename__ = 'course_notes'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, comment='课程ID')
    content = Column(Text, nullable=False, default='', comment='笔记内容')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), comment='更新时间')

    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', name='uq_course_notes_user_course'),
        {'comment': '课程笔记表'},
    )

    user = relationship("User", foreign_keys=[user_id])
    course = relationship("Course", back_populates="notes", foreign_keys=[course_id])


class CourseProgress(Base):
    """学习进度表"""
    __tablename__ = 'course_progress'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False, comment='课程ID')
    chapter_id = Column(Integer, ForeignKey('chapters.id'), nullable=True, comment='章节ID')
    progress = Column(Integer, default=0, comment='进度0-100')
    playback_seconds = Column(Integer, default=0, comment='最近播放位置(秒)')
    last_studied_at = Column(DateTime(timezone=True), server_default=func.now(), comment='最后学习时间')

    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', 'chapter_id', name='uq_course_progress_user_course_chapter'),
        {'comment': '学习进度表'},
    )

    # 关联关系
    user = relationship("User", foreign_keys=[user_id])
    course = relationship("Course", foreign_keys=[course_id])
    chapter = relationship("Chapter", foreign_keys=[chapter_id])


class CourseTag(Base):
    """课程标签"""
    __tablename__ = 'course_tags'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True, comment='标签名')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')


class CourseTagRelation(Base):
    """课程标签关联"""
    __tablename__ = 'course_tag_relations'

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey('course_tags.id', ondelete='CASCADE'), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('course_id', 'tag_id', name='uq_course_tag'),
    )

    course = relationship("Course", back_populates="tag_relations")
    tag = relationship("CourseTag", foreign_keys=[tag_id])




class CourseQA(Base):
    """课程答疑表"""
    __tablename__ = 'course_qa'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, comment='课程ID')
    question = Column(Text, nullable=False, comment='问题内容')
    answer = Column(Text, nullable=True, comment='回答内容')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='提问时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')

    __table_args__ = (
        {'comment': '课程答疑表'},
    )

    user = relationship("User", foreign_keys=[user_id])
    course = relationship("Course", back_populates="qa_list", foreign_keys=[course_id])
