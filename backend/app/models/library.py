"""
Library module database models.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class LibraryFolder(Base):
    """User-owned library folder."""

    __tablename__ = "library_folders"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="Owner user ID")
    name = Column(String(100), nullable=False, comment="Folder name")
    parent_id = Column(
        Integer,
        ForeignKey("library_folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Parent folder ID",
    )
    sort_order = Column(Integer, default=0, comment="Sort order")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Created at")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="Updated at")

    __table_args__ = (
        UniqueConstraint("owner_user_id", "parent_id", "name", name="uq_library_folder_owner_parent_name"),
    )

    owner = relationship("User", foreign_keys=[owner_user_id])
    parent = relationship("LibraryFolder", remote_side=[id], backref="children")
    items = relationship("LibraryItem", back_populates="folder")


class LibraryItem(Base):
    """Library item."""

    __tablename__ = "library_items"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="Owner user ID")
    folder_id = Column(
        Integer,
        ForeignKey("library_folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Folder ID",
    )
    title = Column(String(200), nullable=False, comment="Item title")
    content_type = Column(String(20), nullable=False, comment="video/document/image/audio/knowledge")
    source_kind = Column(String(20), nullable=False, default="file", comment="file/knowledge/ai_generated")
    media_file_id = Column(Integer, ForeignKey("media_files.id"), nullable=True, comment="Linked media file ID")
    knowledge_content_html = Column(Text, nullable=True, comment="Knowledge card HTML content")
    plain_text_content = Column(Text, nullable=True, comment="Plain text used by AI context")
    is_public = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        comment="Whether item is public",
    )
    status = Column(String(30), nullable=False, default='draft', index=True, comment='状态: draft/pending_review/reviewing/published/rejected')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Created at")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="Updated at")

    owner = relationship("User", foreign_keys=[owner_user_id])
    folder = relationship("LibraryFolder", back_populates="items")
    media_file = relationship("MediaFile", foreign_keys=[media_file_id])
