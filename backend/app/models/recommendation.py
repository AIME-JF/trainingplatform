"""
资源推荐与行为埋点相关数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON, UniqueConstraint, Index
from sqlalchemy.sql import func

from app.database import Base


class ResourceBehaviorEvent(Base):
    """资源行为事件"""
    __tablename__ = 'resource_behavior_events'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True, comment='用户ID')
    resource_id = Column(Integer, ForeignKey('resources.id', ondelete='CASCADE'), nullable=False, index=True, comment='资源ID')
    event_type = Column(String(30), nullable=False, index=True, comment='事件类型: impression/click/play/complete/like/unlike/share/favorite')
    watch_seconds = Column(Integer, default=0, comment='观看时长(秒)')
    context_json = Column(JSON, nullable=True, comment='上下文信息')
    event_time = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment='事件时间')

    __table_args__ = (
        Index('ix_behavior_user_time', 'user_id', 'event_time'),
    )


class ResourceRecommendScore(Base):
    """资源推荐预计算分数"""
    __tablename__ = 'resource_recommend_scores'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True, comment='用户ID')
    resource_id = Column(Integer, ForeignKey('resources.id', ondelete='CASCADE'), nullable=False, index=True, comment='资源ID')
    score = Column(Float, nullable=False, default=0, comment='综合分')
    police_type_score = Column(Float, nullable=False, default=0, comment='警种匹配分')
    department_score = Column(Float, nullable=False, default=0, comment='部门匹配分')
    interest_score = Column(Float, nullable=False, default=0, comment='兴趣分')
    freshness_score = Column(Float, nullable=False, default=0, comment='新鲜度分')
    popularity_score = Column(Float, nullable=False, default=0, comment='热度分')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment='更新时间')

    __table_args__ = (
        UniqueConstraint('user_id', 'resource_id', name='uq_user_resource_score'),
        Index('ix_recommend_user_score', 'user_id', 'score'),
    )
