"""
培训班总结报告快照模型
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class TrainingReportSnapshot(Base):
    """已确认发布的培训班总结报告快照"""

    __tablename__ = "training_report_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    ai_task_id = Column(Integer, ForeignKey("ai_tasks.id"), nullable=False, index=True, comment="来源 AI 任务 ID")
    training_id = Column(Integer, ForeignKey("trainings.id", ondelete="CASCADE"), nullable=False, index=True, comment="培训班 ID")
    version_no = Column(Integer, nullable=False, default=1, comment="同一培训班的报告版本号")
    task_name = Column(String(200), nullable=False, comment="任务名称快照")
    title = Column(String(200), nullable=False, comment="报告标题")
    request_payload = Column(JSON, nullable=False, comment="任务请求快照")
    kpi_overview = Column(JSON, nullable=False, comment="KPI 概览")
    attendance_summary = Column(JSON, nullable=True, comment="出勤分析摘要")
    exam_summary = Column(JSON, nullable=True, comment="考试分析摘要")
    risk_items = Column(JSON, nullable=True, comment="风险提示")
    suggestions = Column(JSON, nullable=True, comment="建议项")
    report_markdown = Column(Text, nullable=False, comment="报告正文 Markdown")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="任务创建人")
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="确认人")
    confirmed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment="确认时间")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment="创建时间")

    __table_args__ = (
        UniqueConstraint("training_id", "version_no", name="uq_training_report_snapshot_version"),
    )

    ai_task = relationship("AITask", foreign_keys=[ai_task_id])
    training = relationship("Training", foreign_keys=[training_id])
    creator = relationship("User", foreign_keys=[created_by])
    confirmer = relationship("User", foreign_keys=[confirmed_by])
