"""
知识问答会话模型
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class KnowledgeChatSession(Base):
    """知识问答对话会话"""

    __tablename__ = "knowledge_chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户 ID")
    knowledge_base_id = Column(
        Integer,
        ForeignKey("knowledge_bases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="历史关联知识库 ID",
    )
    knowledge_item_ids = Column(JSON, nullable=False, default=list, comment="关联知识点 ID 列表")
    mode = Column(String(20), nullable=False, default="qa", comment="对话模式: qa/case")
    messages = Column(JSON, nullable=False, default=list, comment="对话消息列表")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    user = relationship("User", foreign_keys=[user_id])
    knowledge_base = relationship("KnowledgeBase", foreign_keys=[knowledge_base_id])
