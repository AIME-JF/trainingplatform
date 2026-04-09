"""
场景模板模型
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ScenarioTemplate(Base):
    """场景模拟模板"""

    __tablename__ = "scenario_templates"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False, comment="场景名称")
    description = Column(Text, nullable=True, comment="场景描述")
    category = Column(String(30), nullable=False, index=True, comment="场景分类: law_enforcement/record_taking/law_application")
    difficulty = Column(Integer, nullable=False, default=3, comment="难度等级 1-5")
    estimated_minutes = Column(Integer, nullable=False, default=15, comment="预计时长(分钟)")
    background = Column(Text, nullable=False, comment="场景背景描述")
    npc_role = Column(Text, nullable=False, comment="AI 扮演角色描述")
    npc_name = Column(String(50), nullable=True, comment="AI 角色名称")
    npc_opening = Column(Text, nullable=True, comment="AI 开场白")
    knowledge_base_id = Column(
        Integer,
        ForeignKey("knowledge_bases.id", ondelete="SET NULL"),
        nullable=True,
        comment="历史关联知识库 ID",
    )
    knowledge_item_ids = Column(JSON, nullable=False, default=list, comment="关联知识点 ID 列表")
    checkpoints = Column(JSON, nullable=False, default=list, comment="考察要点 [{label, score}]")
    status = Column(String(20), nullable=False, default="draft", index=True, comment="状态: draft/published/archived")
    usage_count = Column(Integer, nullable=False, default=0, comment="使用次数")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="创建人 ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    creator = relationship("User", foreign_keys=[created_by])
    knowledge_base = relationship("KnowledgeBase", foreign_keys=[knowledge_base_id])
    sessions = relationship("ScenarioSession", back_populates="scenario_template", cascade="all, delete-orphan")
