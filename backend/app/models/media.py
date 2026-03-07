"""
文件管理数据模型
"""
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class MediaFile(Base):
    """文件表"""
    __tablename__ = 'media_files'

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(500), nullable=False, comment='原始文件名')
    storage_path = Column(String(1000), nullable=False, comment='存储路径(相对)')
    mime_type = Column(String(100), nullable=True, comment='MIME类型')
    size = Column(BigInteger, default=0, comment='文件大小(字节)')
    hash = Column(String(64), nullable=True, index=True, comment='SHA256哈希(秒传)')
    uploader_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='上传者ID')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='上传时间')
