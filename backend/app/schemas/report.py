"""
数据看板相关的数据验证模型
"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel


class KpiResponse(BaseModel):
    """KPI数据响应"""
    total_students: int = 0
    total_courses: int = 0
    total_exams: int = 0
    total_trainings: int = 0
    avg_score: float = 0
    pass_rate: float = 0
    completion_rate: float = 0
    active_trainings: int = 0


class TrendItem(BaseModel):
    """月度趋势项"""
    month: str
    students: int = 0
    exams: int = 0
    avg_score: float = 0


class PoliceTypeDistribution(BaseModel):
    """警种分布"""
    name: str
    value: int = 0


class CityRanking(BaseModel):
    """城市排名"""
    city: str
    score: float = 0
    students: int = 0
