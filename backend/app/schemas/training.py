"""
培训管理相关的数据验证模型
"""
from typing import Optional, List, Any
from datetime import datetime, date as DateType
from pydantic import BaseModel, Field, ConfigDict


# ========== TrainingCourse ==========

class TrainingCourseCreate(BaseModel):
    """创建培训课程安排"""
    name: str = Field(..., max_length=200, description="课程名称")
    instructor: Optional[str] = Field(None, description="授课教官")
    hours: float = Field(0, description="课时")
    type: str = Field("theory", description="类型: theory/practice")


class TrainingCourseResponse(BaseModel):
    """培训课程安排响应"""
    id: int
    training_id: int
    name: str
    instructor: Optional[str] = None
    hours: float = 0
    type: str = "theory"

    model_config = ConfigDict(from_attributes=True)


# ========== Training ==========

class TrainingCreate(BaseModel):
    """创建培训班"""
    name: str = Field(..., max_length=200, description="培训名称")
    type: str = Field(..., description="培训类型: basic/special/promotion/online")
    status: str = Field("upcoming", description="状态")
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    location: Optional[str] = Field(None, max_length=200)
    instructor_id: Optional[int] = None
    capacity: int = Field(0, description="容量")
    description: Optional[str] = None
    subjects: Optional[List[str]] = None
    courses: Optional[List[TrainingCourseCreate]] = None


class TrainingUpdate(BaseModel):
    """更新培训班"""
    name: Optional[str] = Field(None, max_length=200)
    type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    location: Optional[str] = None
    instructor_id: Optional[int] = None
    capacity: Optional[int] = None
    description: Optional[str] = None
    subjects: Optional[List[str]] = None


class TrainingResponse(BaseModel):
    """培训班响应"""
    id: int
    name: str
    type: str
    status: str = "upcoming"
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    location: Optional[str] = None
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    capacity: int = 0
    enrolled_count: Optional[int] = 0
    description: Optional[str] = None
    subjects: Optional[List[str]] = None
    courses: List[TrainingCourseResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TrainingListResponse(BaseModel):
    """培训班列表响应"""
    id: int
    name: str
    type: str
    status: str = "upcoming"
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    location: Optional[str] = None
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    capacity: int = 0
    enrolled_count: Optional[int] = 0
    description: Optional[str] = None
    subjects: Optional[List[str]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========== Enrollment ==========

class EnrollmentCreate(BaseModel):
    """报名"""
    note: Optional[str] = Field(None, description="报名备注")


class EnrollmentResponse(BaseModel):
    """报名响应"""
    id: int
    training_id: int
    user_id: int
    user_name: Optional[str] = None
    user_nickname: Optional[str] = None
    police_id: Optional[str] = None
    unit: Optional[str] = None
    status: str = "pending"
    note: Optional[str] = None
    enroll_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========== CheckinRecord ==========

class CheckinCreate(BaseModel):
    """签到"""
    date: Optional[DateType] = None
    time: Optional[str] = Field(None, description="签到时间 HH:MM")


class CheckinResponse(BaseModel):
    """签到响应"""
    id: int
    training_id: int
    user_id: int
    user_name: Optional[str] = None
    user_nickname: Optional[str] = None
    date: Optional[DateType] = None
    time: Optional[str] = None
    status: str = "on_time"

    model_config = ConfigDict(from_attributes=True)


# ========== ScheduleItem ==========

class ScheduleItemCreate(BaseModel):
    """创建计划条目"""
    week_start: Optional[DateType] = None
    day: Optional[int] = Field(None, ge=1, le=5)
    date: Optional[DateType] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None
    title: str = Field(..., max_length=200)
    type: str = Field("theory", description="类型")
    location: Optional[str] = None
    instructor: Optional[str] = None
    participants: Optional[str] = None
    content: Optional[str] = None
    status: str = Field("pending", description="状态")


class ScheduleItemResponse(BaseModel):
    """计划条目响应"""
    id: int
    training_id: int
    week_start: Optional[DateType] = None
    day: Optional[int] = None
    date: Optional[DateType] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None
    title: str
    type: str = "theory"
    location: Optional[str] = None
    instructor: Optional[str] = None
    participants: Optional[str] = None
    content: Optional[str] = None
    status: str = "pending"

    model_config = ConfigDict(from_attributes=True)
