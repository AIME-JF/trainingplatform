"""
证书管理相关的数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Certificate(Base):
    """结业证书表"""
    __tablename__ = 'certificates'

    id = Column(Integer, primary_key=True, index=True)
    cert_no = Column(String(100), unique=True, nullable=False, comment='证书编号')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    training_id = Column(Integer, ForeignKey('trainings.id'), nullable=True, comment='培训班ID')
    training_name = Column(String(200), nullable=True, comment='培训名称')
    score = Column(Float, default=0, comment='成绩')
    issue_date = Column(Date, nullable=True, comment='签发日期')
    expire_date = Column(Date, nullable=True, comment='过期日期')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')

    # 关联关系
    user = relationship("User", foreign_keys=[user_id])
    training = relationship("Training", foreign_keys=[training_id])
