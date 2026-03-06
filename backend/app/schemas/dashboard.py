"""
工作台相关的数据验证模型
"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict


class DashboardResponse(BaseModel):
    """工作台响应"""
    stats: Dict[str, Any] = {}
    recent_courses: List[Any] = []
    recent_exams: List[Any] = []
    recent_trainings: List[Any] = []
    announcements: List[Any] = []
