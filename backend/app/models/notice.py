"""
公告模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Notice(Base):
    """公告表"""
    __tablename__ = 'notices'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment='公告标题')
    content = Column(Text, nullable=False, comment='公告内容')
    type = Column(String(50), default='system', comment='类型: system/training')
    training_id = Column(Integer, ForeignKey('trainings.id', ondelete='CASCADE'), nullable=True, comment='培训班ID(培训班公告)')
    author_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='发布人ID')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')

    # 关联关系
    training = relationship("Training", foreign_keys=[training_id])
    author = relationship("User", foreign_keys=[author_id])
