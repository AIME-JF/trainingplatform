"""
AI功能相关的数据验证模型
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class AIGenerateQuestionsRequest(BaseModel):
    """AI智能组卷请求"""
    topic: str = Field(..., description="考试主题")
    count: int = Field(10, description="题目数量")
    difficulty: int = Field(3, ge=1, le=5, description="难度")
    types: Optional[List[str]] = Field(None, description="题目类型列表")


class AIGenerateQuestionsResponse(BaseModel):
    """AI智能组卷响应"""
    questions: List[Any] = []
    total: int = 0


class AIGenerateLessonPlanRequest(BaseModel):
    """AI教案生成请求"""
    title: str = Field(..., description="教案标题")
    subject: str = Field(..., description="科目")
    duration: int = Field(90, description="课时(分钟)")
    objectives: Optional[List[str]] = Field(None, description="教学目标")
    level: Optional[str] = Field(None, description="学员等级")


class AIGenerateLessonPlanResponse(BaseModel):
    """AI教案生成响应"""
    title: str = ""
    content: str = ""
    outline: List[Any] = []
