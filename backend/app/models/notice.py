"""
公告模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Notice(Base):
    """公告表"""
    __tablename__ = 'notices'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment='公告标题')
    content = Column(Text, nullable=False, comment='公告内容')
    type = Column(String(50), default='system', comment='类型: system/training/reminder')
    training_id = Column(Integer, ForeignKey('trainings.id', ondelete='CASCADE'), nullable=True, comment='培训班ID(培训班公告)')
    author_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='发布人ID')
    target_user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True, comment='目标用户ID(提醒类通知)')
    reminder_type = Column(String(50), nullable=True, comment='提醒子类型: exam_reminder/review_approved/review_rejected/enrollment_approved 等')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')

    # 关联关系
    training = relationship("Training", foreign_keys=[training_id])
    author = relationship("User", foreign_keys=[author_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    reads = relationship("NoticeRead", back_populates="notice", cascade="all, delete-orphan")


class NoticeRead(Base):
    """通知已读记录"""
    __tablename__ = 'notice_reads'
    __table_args__ = (
        UniqueConstraint('notice_id', 'user_id', name='uq_notice_read_user'),
    )

    id = Column(Integer, primary_key=True, index=True)
    notice_id = Column(Integer, ForeignKey('notices.id', ondelete='CASCADE'), nullable=False, index=True, comment='通知ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True, comment='用户ID')
    read_at = Column(DateTime(timezone=True), server_default=func.now(), comment='已读时间')

    notice = relationship("Notice", back_populates="reads")
