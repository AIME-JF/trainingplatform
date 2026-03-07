"""
文件管理数据验证模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class MediaFileResponse(BaseModel):
    """文件响应"""
    id: int
    filename: str
    mime_type: Optional[str] = None
    size: int = 0
    url: str = ""
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
