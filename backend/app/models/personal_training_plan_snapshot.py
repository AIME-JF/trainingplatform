"""
个性化训练方案快照模型
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PersonalTrainingPlanSnapshot(Base):
    """已确认的个训方案快照"""

    __tablename__ = "personal_training_plan_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    ai_task_id = Column(Integer, ForeignKey("ai_tasks.id"), nullable=False, index=True, comment="来源 AI 任务 ID")
    training_id = Column(Integer, ForeignKey("trainings.id", ondelete="CASCADE"), nullable=False, index=True, comment="培训班 ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="学员 ID")
    version_no = Column(Integer, nullable=False, default=1, comment="同一培训同一学员的版本号")
    task_name = Column(String(200), nullable=False, comment="任务名称快照")
    request_payload = Column(JSON, nullable=False, comment="任务请求快照")
    portrait_payload = Column(JSON, nullable=False, comment="画像快照")
    plan_payload = Column(JSON, nullable=False, comment="方案快照")
    summary = Column(Text, nullable=True, comment="方案摘要")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="任务创建人")
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="确认人")
    confirmed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment="确认时间")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment="创建时间")

    __table_args__ = (
        UniqueConstraint("training_id", "user_id", "version_no", name="uq_personal_training_snapshot_version"),
    )

    ai_task = relationship("AITask", foreign_keys=[ai_task_id])
    training = relationship("Training", foreign_keys=[training_id])
    user = relationship("User", foreign_keys=[user_id])
    creator = relationship("User", foreign_keys=[created_by])
    confirmer = relationship("User", foreign_keys=[confirmed_by])
