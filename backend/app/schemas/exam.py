"""
考试管理相关的数据验证模型
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class QuestionCreate(BaseModel):
    """创建题目"""

    type: str = Field(..., description="题目类型: single/multi/judge")
    content: str = Field(..., description="题干")
    options: Optional[List[dict]] = Field(None, description="选项 [{key, text}]")
    answer: Any = Field(..., description="答案")
    explanation: Optional[str] = Field(None, description="解析")
    difficulty: int = Field(1, ge=1, le=5, description="难度1-5")
    knowledge_point: Optional[str] = Field(None, max_length=200)
    police_type_id: Optional[int] = Field(None, description="警种ID")
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
    police_type_id: Optional[int] = None
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
    police_type_id: Optional[int] = None
    police_type_name: Optional[str] = None
    score: int = 1
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class QuestionBatchCreate(BaseModel):
    """批量导入题目"""

    questions: List[QuestionCreate] = Field(..., description="题目列表")


class ExamQuestionSnapshotResponse(BaseModel):
    """试卷题目快照响应"""

    id: int = Field(..., description="来源题目ID")
    type: str
    content: str
    options: Optional[List[dict]] = None
    explanation: Optional[str] = None
    score: int = 1
    knowledge_point: Optional[str] = None


class ExamWrongQuestionResponse(BaseModel):
    """错题详情"""

    question_id: int
    type: str
    content: str
    my_answer: Any = None
    answer: Any = None
    explanation: Optional[str] = None
    score: int = 0


class ExamPaperCreate(BaseModel):
    """创建试卷"""

    title: str = Field(..., max_length=200, description="试卷标题")
    description: Optional[str] = None
    duration: Optional[int] = Field(None, ge=10, le=300, description="考试时长(分钟)")
    total_score: Optional[int] = Field(None, ge=1, description="总分，默认按题目自动汇总")
    passing_score: Optional[int] = Field(None, ge=1, description="及格分")
    type: str = Field("formal", description="试卷类型: formal/quiz")
    question_ids: List[int] = Field(default_factory=list, description="题目ID列表")


class ExamPaperUpdate(BaseModel):
    """更新试卷"""

    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    duration: Optional[int] = Field(None, ge=10, le=300)
    total_score: Optional[int] = Field(None, ge=1)
    passing_score: Optional[int] = Field(None, ge=1)
    type: Optional[str] = None
    question_ids: Optional[List[int]] = None


class ExamPaperResponse(BaseModel):
    """试卷响应"""

    id: int
    title: str
    description: Optional[str] = None
    duration: int = 60
    total_score: int = 100
    passing_score: int = 60
    type: str = "formal"
    status: str = "draft"
    published_at: Optional[datetime] = None
    created_by: Optional[int] = None
    question_count: int = 0
    usage_count: int = 0
    linked_exam_count: int = 0
    linked_admission_exam_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ExamPaperDetailResponse(ExamPaperResponse):
    """试卷详情响应"""

    questions: List[ExamQuestionSnapshotResponse] = Field(default_factory=list)


class AdmissionExamCreate(BaseModel):
    """创建独立准入考试"""

    title: str = Field(..., max_length=200, description="考试标题")
    paper_id: int = Field(..., description="关联试卷ID")
    description: Optional[str] = None
    duration: Optional[int] = Field(None, ge=10, le=300, description="考试时长(分钟)")
    passing_score: Optional[int] = Field(None, ge=1, description="及格分")
    status: str = Field("upcoming", description="状态")
    type: Optional[str] = Field(None, description="展示类型: formal/quiz")
    scope: Optional[str] = None
    max_attempts: int = Field(1, ge=1, le=10, description="最大作答次数")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class AdmissionExamUpdate(BaseModel):
    """更新独立准入考试"""

    title: Optional[str] = Field(None, max_length=200)
    paper_id: Optional[int] = Field(None, description="关联试卷ID")
    description: Optional[str] = None
    duration: Optional[int] = Field(None, ge=10, le=300)
    passing_score: Optional[int] = Field(None, ge=1)
    status: Optional[str] = None
    type: Optional[str] = None
    scope: Optional[str] = None
    max_attempts: Optional[int] = Field(None, ge=1, le=10)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class AdmissionExamResponse(BaseModel):
    """独立准入考试响应"""

    id: int
    kind: str = "admission"
    paper_id: Optional[int] = None
    paper_title: Optional[str] = None
    paper_status: Optional[str] = None
    title: str
    description: Optional[str] = None
    duration: int = 60
    total_score: int = 100
    passing_score: int = 60
    status: str = "upcoming"
    type: str = "formal"
    scope: Optional[str] = None
    max_attempts: int = 1
    linked_training_count: int = 0
    attempt_count: int = 0
    latest_result: Optional[str] = None
    can_join: Optional[bool] = None
    created_by: Optional[int] = None
    question_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AdmissionExamDetailResponse(AdmissionExamResponse):
    """独立准入考试详情响应"""

    questions: List[ExamQuestionSnapshotResponse] = Field(default_factory=list)


class ExamCreate(BaseModel):
    """创建培训班内考试"""

    title: str = Field(..., max_length=200, description="场次标题")
    paper_id: int = Field(..., description="关联试卷ID")
    description: Optional[str] = None
    duration: Optional[int] = Field(None, ge=10, le=300, description="考试时长(分钟)")
    passing_score: Optional[int] = Field(None, ge=1, description="及格分")
    status: str = Field("upcoming", description="状态")
    type: Optional[str] = Field(None, description="展示类型: formal/quiz")
    purpose: str = Field("class_assessment", description="用途")
    training_id: int = Field(..., description="关联培训班ID")
    max_attempts: int = Field(1, ge=1, le=10, description="最大作答次数")
    allow_makeup: bool = Field(False, description="是否允许补考")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ExamUpdate(BaseModel):
    """更新培训班内考试"""

    title: Optional[str] = Field(None, max_length=200)
    paper_id: Optional[int] = Field(None, description="关联试卷ID")
    description: Optional[str] = None
    duration: Optional[int] = Field(None, ge=10, le=300)
    passing_score: Optional[int] = Field(None, ge=1)
    status: Optional[str] = None
    type: Optional[str] = None
    purpose: Optional[str] = None
    training_id: Optional[int] = None
    max_attempts: Optional[int] = Field(None, ge=1, le=10)
    allow_makeup: Optional[bool] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ExamResponse(BaseModel):
    """培训班内考试响应"""

    id: int
    kind: str = "training"
    paper_id: Optional[int] = None
    paper_title: Optional[str] = None
    paper_status: Optional[str] = None
    title: str
    description: Optional[str] = None
    duration: int = 60
    total_score: int = 100
    passing_score: int = 60
    status: str = "upcoming"
    type: str = "formal"
    purpose: str = "class_assessment"
    training_id: Optional[int] = None
    training_name: Optional[str] = None
    max_attempts: int = 1
    allow_makeup: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_by: Optional[int] = None
    question_count: int = 0
    attempt_count: int = 0
    latest_result: Optional[str] = None
    can_join: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ExamDetailResponse(ExamResponse):
    """培训班内考试详情响应"""

    questions: List[ExamQuestionSnapshotResponse] = Field(default_factory=list)


class ExamSubmit(BaseModel):
    """提交考试"""

    answers: Dict[str, Any] = Field(default_factory=dict, description="答案 {questionId: answer}")
    start_time: Optional[datetime] = None


class AdmissionExamRecordResponse(BaseModel):
    """准入考试记录响应"""

    id: int
    exam_id: int
    kind: str = "admission"
    paper_id: Optional[int] = None
    exam_title: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    user_nickname: Optional[str] = None
    attempt_no: int = 1
    status: str = "submitted"
    score: int = 0
    result: Optional[str] = None
    grade: Optional[str] = None
    passing_score: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: int = 0
    correct_count: int = 0
    wrong_count: int = 0
    wrong_questions: List[int] = Field(default_factory=list)
    wrong_question_details: List[ExamWrongQuestionResponse] = Field(default_factory=list)
    dimension_scores: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class ExamRecordResponse(BaseModel):
    """培训班考试记录响应"""

    id: int
    exam_id: int
    kind: str = "training"
    paper_id: Optional[int] = None
    exam_title: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    user_nickname: Optional[str] = None
    attempt_no: int = 1
    status: str = "submitted"
    score: int = 0
    result: Optional[str] = None
    grade: Optional[str] = None
    passing_score: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: int = 0
    correct_count: int = 0
    wrong_count: int = 0
    wrong_questions: List[int] = Field(default_factory=list)
    wrong_question_details: List[ExamWrongQuestionResponse] = Field(default_factory=list)
    dimension_scores: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)
