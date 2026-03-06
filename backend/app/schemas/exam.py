"""
考试管理相关的数据验证模型
"""
from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ========== Question ==========

class QuestionCreate(BaseModel):
    """创建题目"""
    type: str = Field(..., description="题目类型: single/multi/judge")
    content: str = Field(..., description="题干")
    options: Optional[List[dict]] = Field(None, description="选项 [{key, text}]")
    answer: Any = Field(..., description="答案")
    explanation: Optional[str] = Field(None, description="解析")
    difficulty: int = Field(1, ge=1, le=5, description="难度1-5")
    knowledge_point: Optional[str] = Field(None, max_length=200)
    score: int = Field(1, description="分值")


class QuestionUpdate(BaseModel):
    """更新题目"""
    type: Optional[str] = None
    content: Optional[str] = None
    options: Optional[List[dict]] = None
    answer: Optional[Any] = None
    explanation: Optional[str] = None
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    knowledge_point: Optional[str] = None
    score: Optional[int] = None


class QuestionResponse(BaseModel):
    """题目响应"""
    id: int
    type: str
    content: str
    options: Optional[List[dict]] = None
    answer: Any = None
    explanation: Optional[str] = None
    difficulty: int = 1
    knowledge_point: Optional[str] = None
    score: int = 1
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class QuestionBatchCreate(BaseModel):
    """批量导入题目"""
    questions: List[QuestionCreate] = Field(..., description="题目列表")


# ========== Exam ==========

class ExamCreate(BaseModel):
    """创建考试"""
    title: str = Field(..., max_length=200, description="考试标题")
    description: Optional[str] = None
    duration: int = Field(60, description="考试时长(分钟)")
    total_score: int = Field(100, description="总分")
    passing_score: int = Field(60, description="及格分")
    status: str = Field("upcoming", description="状态")
    type: str = Field("formal", description="类型: formal/quiz")
    scope: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    question_ids: Optional[List[int]] = Field(None, description="题目ID列表")


class ExamUpdate(BaseModel):
    """更新考试"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    duration: Optional[int] = None
    total_score: Optional[int] = None
    passing_score: Optional[int] = None
    status: Optional[str] = None
    type: Optional[str] = None
    scope: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    question_ids: Optional[List[int]] = None


class ExamQuestionResponse(BaseModel):
    """考试题目响应"""
    exam_id: int
    question_id: int
    sort_order: int = 0
    question: Optional[QuestionResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ExamResponse(BaseModel):
    """考试响应"""
    id: int
    title: str
    description: Optional[str] = None
    duration: int = 60
    total_score: int = 100
    passing_score: int = 60
    status: str = "upcoming"
    type: str = "formal"
    scope: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_by: Optional[int] = None
    question_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ExamDetailResponse(ExamResponse):
    """考试详情响应（含题目）"""
    questions: List[QuestionResponse] = []


# ========== ExamRecord ==========

class ExamSubmit(BaseModel):
    """提交考试"""
    answers: Dict[str, Any] = Field(..., description="答案 {questionId: answer}")
    start_time: Optional[datetime] = None


class ExamRecordResponse(BaseModel):
    """考试记录响应"""
    id: int
    exam_id: int
    exam_title: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    user_nickname: Optional[str] = None
    score: int = 0
    result: Optional[str] = None
    grade: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: int = 0
    correct_count: int = 0
    wrong_count: int = 0
    wrong_questions: Optional[List[int]] = None
    dimension_scores: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
