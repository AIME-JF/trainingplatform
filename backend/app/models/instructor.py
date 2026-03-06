"""
教官档案相关的数据库模型
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class InstructorProfile(Base):
    """教官档案表（扩展User）"""
    __tablename__ = 'instructor_profiles'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False, comment='用户ID')
    title = Column(String(50), nullable=True, comment='职称: 高级教官/中级教官/初级教官')
    level = Column(String(20), nullable=True, comment='等级: expert/senior/standard')
    specialties = Column(JSON, nullable=True, comment='专长数组')
    qualification = Column(JSON, nullable=True, comment='资质数组')
    certificates = Column(JSON, nullable=True, comment='证书列表 [{name,issuer,year}]')
    intro = Column(Text, nullable=True, comment='简介')
    rating = Column(Float, default=0, comment='评分')
    course_count = Column(Integer, default=0, comment='课程数')
    student_count = Column(Integer, default=0, comment='学员数')
    review_count = Column(Integer, default=0, comment='评价数')

    # 关联关系
    user = relationship("User", back_populates="instructor_profile")
