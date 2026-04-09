"""
场景模拟会话模型
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ScenarioSession(Base):
    """场景模拟对话会话"""

    __tablename__ = "scenario_sessions"

    id = Column(Integer, primary_key=True, index=True)
    scenario_template_id = Column(Integer, ForeignKey("scenario_templates.id", ondelete="CASCADE"), nullable=False, index=True, comment="场景模板 ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户 ID")
    messages = Column(JSON, nullable=False, default=list, comment="对话消息列表 [{role, content, npc_name?}]")
    status = Column(String(20), nullable=False, default="in_progress", comment="状态: in_progress/completed")
    score = Column(Integer, nullable=True, comment="综合评分 0-100")
    checkpoint_results = Column(JSON, nullable=True, comment="考察要点结果 [{label, passed}]")
    feedback = Column(Text, nullable=True, comment="AI 评价反馈")
    duration_minutes = Column(Integer, nullable=True, comment="用时(分钟)")
    started_at = Column(DateTime(timezone=True), server_default=func.now(), comment="开始时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    scenario_template = relationship("ScenarioTemplate", back_populates="sessions")
    user = relationship("User", foreign_keys=[user_id])
