"""
AI 任务模型
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AITask(Base):
    """统一 AI 任务表"""

    __tablename__ = "ai_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(200), nullable=False, comment="任务名称")
    task_type = Column(String(50), nullable=False, index=True, comment="任务类型")
    status = Column(String(20), nullable=False, default="pending", index=True, comment="任务状态")
    request_payload = Column(JSON, nullable=False, comment="任务请求参数快照")
    result_payload = Column(JSON, nullable=True, comment="任务结果快照")
    error_message = Column(Text, nullable=True, comment="任务错误信息")
    confirmed_question_ids = Column(JSON, nullable=True, comment="确认后的题目 ID 列表")
    confirmed_paper_id = Column(Integer, ForeignKey("exam_papers.id"), nullable=True, comment="确认后的试卷 ID")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="创建人 ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始处理时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="处理完成时间")
    confirmed_at = Column(DateTime(timezone=True), nullable=True, comment="确认完成时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    creator = relationship("User", foreign_keys=[created_by])
    confirmed_paper = relationship("ExamPaper", foreign_keys=[confirmed_paper_id])
