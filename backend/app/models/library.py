"""
资源库模块数据模型
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class LibraryFolder(Base):
    """教官个人资源库文件夹"""

    __tablename__ = "library_folders"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="所属用户ID")
    name = Column(String(100), nullable=False, comment="文件夹名称")
    parent_id = Column(Integer, ForeignKey("library_folders.id", ondelete="CASCADE"), nullable=True, index=True, comment="父文件夹ID")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    __table_args__ = (
        UniqueConstraint("owner_user_id", "parent_id", "name", name="uq_library_folder_owner_parent_name"),
    )

    owner = relationship("User", foreign_keys=[owner_user_id])
    parent = relationship("LibraryFolder", remote_side=[id], backref="children")
    items = relationship("LibraryItem", back_populates="folder")


class LibraryItem(Base):
    """资源库资源项"""

    __tablename__ = "library_items"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="所属用户ID")
    folder_id = Column(Integer, ForeignKey("library_folders.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属文件夹ID")
    title = Column(String(200), nullable=False, comment="资源标题")
    content_type = Column(String(20), nullable=False, comment="资源类型: video/document/image/audio/knowledge")
    source_kind = Column(String(20), nullable=False, default="file", comment="来源类型: file/knowledge")
    media_file_id = Column(Integer, ForeignKey("media_files.id"), nullable=True, comment="关联文件ID")
    knowledge_content_html = Column(Text, nullable=True, comment="知识点富文本内容")
    is_public = Column(Boolean, nullable=False, default=False, server_default=text("false"), comment="是否公开到公共资源")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    owner = relationship("User", foreign_keys=[owner_user_id])
    folder = relationship("LibraryFolder", back_populates="items")
    media_file = relationship("MediaFile", foreign_keys=[media_file_id])
