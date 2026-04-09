"""
教官档案相关模型（标签组、教学方向、授课经历）
"""
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
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


class InstructorTeachingDirection(Base):
    """教官教学方向关联"""

    __tablename__ = "instructor_teaching_directions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="教官用户ID")
    direction_id = Column(Integer, ForeignKey("dict_teaching_directions.id", ondelete="CASCADE"), nullable=False, index=True, comment="教学方向ID")

    __table_args__ = (
        UniqueConstraint("user_id", "direction_id", name="uq_instructor_teaching_direction"),
    )

    user = relationship("User", foreign_keys=[user_id])
    direction = relationship("DictTeachingDirection", foreign_keys=[direction_id])


class InstructorTeachingExperience(Base):
    """教官授课经历"""

    __tablename__ = "instructor_teaching_experiences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="教官用户ID")
    start_date = Column(Date, nullable=True, comment="开始日期")
    end_date = Column(Date, nullable=True, comment="结束日期")
    target_audience = Column(String(200), nullable=True, comment="授课对象")
    content = Column(Text, nullable=True, comment="授课内容")
    evaluation = Column(Text, nullable=True, comment="评课情况")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    user = relationship("User", foreign_keys=[user_id])
