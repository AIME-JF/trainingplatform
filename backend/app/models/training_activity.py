"""
培训班动态记录模型
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.sql import func

from app.database import Base


class TrainingActivity(Base):
    """培训班动态记录"""

    __tablename__ = "training_activities"

    id = Column(Integer, primary_key=True, index=True)
    training_id = Column(Integer, ForeignKey("trainings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_name = Column(String(100), nullable=True, comment="冗余存储用户名")
    action_type = Column(
        String(50),
        nullable=False,
        comment="动态类型: checkin/checkout/notice/enroll/session_checkin_start/session_checkin_end/session_checkout_start/session_checkout_end",
    )
    content = Column(String(500), nullable=False, comment="动态内容描述")
    extra_json = Column(JSON, nullable=True, comment="额外数据")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
