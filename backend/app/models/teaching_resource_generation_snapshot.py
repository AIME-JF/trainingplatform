"""
教学资源生成确认快照模型
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class TeachingResourceGenerationSnapshot(Base):
    """已确认的教学资源生成结果快照"""

    __tablename__ = "ai_resource_generation_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    ai_task_id = Column(Integer, ForeignKey("ai_tasks.id"), nullable=False, index=True, comment="来源 AI 任务 ID")
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False, index=True, comment="确认后的资源 ID")
    media_file_id = Column(Integer, ForeignKey("media_files.id"), nullable=False, index=True, comment="生成文件 ID")
    template_code = Column(String(100), nullable=False, comment="内容模板编码")
    task_name = Column(String(200), nullable=False, comment="任务名称快照")
    resource_title = Column(String(200), nullable=False, comment="资源标题快照")
    request_payload = Column(JSON, nullable=False, comment="任务请求快照")
    parsed_request = Column(JSON, nullable=True, comment="解析结果快照")
    template_payload = Column(JSON, nullable=True, comment="模板快照")
    page_plan = Column(JSON, nullable=True, comment="页面方案快照")
    html_content = Column(Text, nullable=False, comment="生成的 HTML 内容")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="任务创建人")
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="确认人")
    confirmed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment="确认时间")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment="创建时间")

    __table_args__ = (
        UniqueConstraint("ai_task_id", name="uq_ai_resource_generation_snapshot_task"),
    )

    ai_task = relationship("AITask", foreign_keys=[ai_task_id])
    resource = relationship("Resource", foreign_keys=[resource_id])
    media_file = relationship("MediaFile", foreign_keys=[media_file_id])
    creator = relationship("User", foreign_keys=[created_by])
    confirmer = relationship("User", foreign_keys=[confirmed_by])
