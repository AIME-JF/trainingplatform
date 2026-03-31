"""
公告相关的数据验证模型
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class NoticeCreate(BaseModel):
    """创建公告"""
    title: str = Field(..., max_length=200, description="公告标题")
    content: str = Field(..., description="公告内容")
    type: str = Field("system", description="类型: system/training")
    training_id: Optional[int] = Field(None, description="培训班ID(培训班公告时必填)")


class NoticeUpdate(BaseModel):
    """更新公告"""
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None


class NoticeResponse(BaseModel):
    """公告响应"""
    id: int
    title: str
    content: str
    type: str = "system"
    training_id: Optional[int] = None
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
