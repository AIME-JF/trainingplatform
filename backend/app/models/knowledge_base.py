"""
知识库模型
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class KnowledgeBase(Base):
    """知识库"""

    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="知识库名称")
    description = Column(Text, nullable=True, comment="知识库描述")
    visibility = Column(String(20), nullable=False, default="all", comment="可见范围: all/instructor/admin")
    document_count = Column(Integer, nullable=False, default=0, comment="文档数量")
    usage_count = Column(Integer, nullable=False, default=0, comment="引用次数")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="创建人 ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    creator = relationship("User", foreign_keys=[created_by])
    documents = relationship("KnowledgeDocument", back_populates="knowledge_base", cascade="all, delete-orphan")


class KnowledgeDocument(Base):
    """知识库文档条目"""

    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属知识库 ID")
    title = Column(String(500), nullable=False, comment="文档标题")
    content = Column(Text, nullable=False, comment="文档全文内容")
    source_type = Column(String(20), nullable=False, default="manual", comment="来源类型: manual/import/ai_generated")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="创建人 ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    creator = relationship("User", foreign_keys=[created_by])
