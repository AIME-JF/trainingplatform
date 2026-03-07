"""
教官档案相关的数据验证模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class InstructorProfileCreate(BaseModel):
    """创建教官档案"""
    user_id: Optional[int] = Field(None, description="用户ID(可选，不传则自动创建用户)")
    name: Optional[str] = Field(None, max_length=100, description="教官姓名(自动创建用户时使用)")
    title: Optional[str] = Field(None, max_length=50)
    level: Optional[str] = Field(None, max_length=20)
    specialties: Optional[List[str]] = None
    qualification: Optional[List[str]] = None
    certificates: Optional[List[dict]] = None
    intro: Optional[str] = None
    unit: Optional[str] = Field(None, description="所属单位")


class InstructorProfileUpdate(BaseModel):
    """更新教官档案"""
    title: Optional[str] = Field(None, max_length=50)
    level: Optional[str] = Field(None, max_length=20)
    specialties: Optional[List[str]] = None
    qualification: Optional[List[str]] = None
    certificates: Optional[List[dict]] = None
    intro: Optional[str] = None


class InstructorResponse(BaseModel):
    """教官响应"""
    id: int
    user_id: int
    name: Optional[str] = None
    nickname: Optional[str] = None
    police_id: Optional[str] = None
    avatar: Optional[str] = None
    title: Optional[str] = None
    level: Optional[str] = None
    specialties: Optional[List[str]] = None
    qualification: Optional[List[str]] = None
    certificates: Optional[List[dict]] = None
    intro: Optional[str] = None
    rating: float = 0
    course_count: int = 0
    student_count: int = 0
    review_count: int = 0

    model_config = ConfigDict(from_attributes=True)
