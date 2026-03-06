"""
证书管理相关的数据验证模型
"""
from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


class CertificateCreate(BaseModel):
    """签发证书"""
    user_id: int = Field(..., description="用户ID")
    training_id: Optional[int] = Field(None, description="培训班ID")
    training_name: Optional[str] = Field(None, max_length=200)
    score: float = Field(0, description="成绩")
    issue_date: Optional[date] = None
    expire_date: Optional[date] = None


class CertificateResponse(BaseModel):
    """证书响应"""
    id: int
    cert_no: str
    user_id: int
    user_name: Optional[str] = None
    user_nickname: Optional[str] = None
    training_id: Optional[int] = None
    training_name: Optional[str] = None
    score: float = 0
    issue_date: Optional[date] = None
    expire_date: Optional[date] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
