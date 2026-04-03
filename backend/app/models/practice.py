"""
刷题练习记录模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship

from app.database import Base


class PracticeRecord(Base):
    """刷题练习记录表"""

    __tablename__ = "practice_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    source_type = Column(String(20), nullable=False, comment="来源类型: knowledge_point/question_folder")
    source_id = Column(Integer, nullable=False, comment="来源ID")
    source_name = Column(String(255), nullable=True, comment="来源名称")
    total_count = Column(Integer, default=0, comment="总题数")
    correct_count = Column(Integer, default=0, comment="正确数")
    wrong_count = Column(Integer, default=0, comment="错误数")
    accuracy = Column(Integer, default=0, comment="正确率(%)")
    duration = Column(Integer, default=0, comment="用时(秒)")
    question_limit = Column(String(20), nullable=True, comment="题量限制")
    question_type = Column(String(20), nullable=True, comment="题型筛选")
    difficulty = Column(Integer, nullable=True, comment="难度筛选")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="练习时间")

    user = relationship("User", foreign_keys=[user_id])
