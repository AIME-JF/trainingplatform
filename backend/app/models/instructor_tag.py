"""
教官标签组模型
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class InstructorTag(Base):
    """教官标签组"""

    __tablename__ = "instructor_tags"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="教官用户ID")
    admin_level = Column(String(20), nullable=False, comment="行政级别: 厅级/市级/县级")
    professional_level = Column(String(20), nullable=False, comment="专业等级: 初级/中级/高级")
    specialty_id = Column(Integer, ForeignKey("dict_instructor_specialties.id"), nullable=False, comment="专长方向ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    __table_args__ = (
        UniqueConstraint("user_id", "admin_level", "professional_level", "specialty_id", name="uq_instructor_tag"),
    )

    user = relationship("User", foreign_keys=[user_id])
    specialty = relationship("DictInstructorSpecialty", foreign_keys=[specialty_id])
