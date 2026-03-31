"""
个人中心相关的数据验证模型
"""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


class ProfileUpdate(BaseModel):
    """更新个人信息"""
    nickname: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None


class ProfileResponse(BaseModel):
    """个人信息响应"""
    id: int
    username: str
    nickname: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    police_id: Optional[str] = None
    avatar: Optional[str] = None
    join_date: Optional[date] = None
    level: Optional[str] = None
    study_hours: float = 0
    exam_count: int = 0
    avg_score: float = 0
    roles: List[str] = []
    departments: List[str] = []
    police_types: List[str] = []
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StudyStatsResponse(BaseModel):
    """学习统计响应"""
    total_courses: int = 0
    completed_courses: int = 0
    in_progress_courses: int = 0
    total_study_hours: float = 0
    total_exams: int = 0
    avg_score: float = 0
    certificates_count: int = 0


class ExamHistoryResponse(BaseModel):
    """考试历史响应"""
    id: int
    exam_id: int
    exam_title: Optional[str] = None
    score: int = 0
    result: Optional[str] = None
    grade: Optional[str] = None
    duration: int = 0
    end_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
