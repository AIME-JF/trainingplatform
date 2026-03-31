"""
考试管理相关的数据验证模型
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .knowledge_point import KnowledgePointSimpleResponse


ADMISSION_SCOPE_ALL = "all"
ADMISSION_SCOPE_USER = "user"
ADMISSION_SCOPE_DEPARTMENT = "department"
ADMISSION_SCOPE_ROLE = "role"
ADMISSION_SCOPE_CHOICES = {
    ADMISSION_SCOPE_ALL,
    ADMISSION_SCOPE_USER,
    ADMISSION_SCOPE_DEPARTMENT,
    ADMISSION_SCOPE_ROLE,
}


def _normalize_admission_scope_type(value: Optional[str], allow_none: bool = False) -> Optional[str]:
    if value is None:
        return None if allow_none else ADMISSION_SCOPE_ALL
    normalized = str(value).strip() or ADMISSION_SCOPE_ALL
    if normalized not in ADMISSION_SCOPE_CHOICES:
        raise ValueError(f"不支持的适用范围类型: {normalized}")
    return normalized


def _normalize_admission_scope_target_ids(value: Any, allow_none: bool = False) -> Optional[List[int]]:
    if value is None:
        return None if allow_none else []

    normalized: List[int] = []
    seen = set()
    for raw_item in value or []:
        try:
            item = int(raw_item)
        except (TypeError, ValueError) as exc:
            raise ValueError("适用范围目标ID必须为整数") from exc
        if item <= 0 or item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


def _normalize_knowledge_point_names(value: Any, allow_none: bool = False) -> Optional[List[str]]:
    if value is None:
        return None if allow_none else []

    if isinstance(value, str):
        raw_items = [value]
    else:
        raw_items = list(value or [])

    normalized: List[str] = []
    seen = set()
    for raw_item in raw_items:
        item = str(raw_item or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        normalized.append(item[:100])
    return normalized


class QuestionCreate(BaseModel):
    """创建题目"""

    type: str = Field(..., description="题目类型: single/multi/judge")
    content: str = Field(..., description="题干")
    options: Optional[List[dict]] = Field(None, description="选项 [{key, text}]")
    answer: Any = Field(..., description="答案")
    explanation: Optional[str] = Field(None, description="解析")
    difficulty: int = Field(1, ge=1, le=5, description="难度1-5")
    knowledge_point_names: List[str] = Field(default_factory=list, description="知识点名称列表")
    police_type_id: Optional[int] = Field(None, description="警种ID")
    folder_id: Optional[int] = Field(None, description="所属文件夹ID")
    score: int = Field(1, description="分值")

    @field_validator("knowledge_point_names", mode="before")
    @classmethod
    def validate_knowledge_point_names(cls, value: Any) -> List[str]:
        return _normalize_knowledge_point_names(value) or []


class QuestionUpdate(BaseModel):
    """更新题目"""

    type: Optional[str] = None
    content: Optional[str] = None
    options: Optional[List[dict]] = None
    answer: Optional[Any] = None
    explanation: Optional[str] = None
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    knowledge_point_names: Optional[List[str]] = Field(None, description="知识点名称列表")
    police_type_id: Optional[int] = None
    folder_id: Optional[int] = None
    score: Optional[int] = None

    @field_validator("knowledge_point_names", mode="before")
    @classmethod
    def validate_knowledge_point_names(cls, value: Any) -> Optional[List[str]]:
        return _normalize_knowledge_point_names(value, allow_none=True)


class QuestionResponse(BaseModel):
    """题目响应"""

    id: int
    type: str
    content: str
    options: Optional[List[dict]] = None
    answer: Any = None
    explanation: Optional[str] = None
    difficulty: int = 1
    knowledge_points: List[KnowledgePointSimpleResponse] = Field(default_factory=list)
    knowledge_point_names: List[str] = Field(default_factory=list)
    police_type_id: Optional[int] = None
    police_type_name: Optional[str] = None
    folder_id: Optional[int] = None
    folder_name: Optional[str] = None
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
    answer: Any = None
    explanation: Optional[str] = None
    score: int = 1
    knowledge_points: List[str] = Field(default_factory=list)


class ExamWrongQuestionResponse(BaseModel):
    """错题详情"""

    question_id: int
    type: str
    content: str
    my_answer: Any = None
    answer: Any = None
    explanation: Optional[str] = None
    score: int = 0


class PaperFolderCreate(BaseModel):
    """创建试卷文件夹"""

    name: str = Field(..., max_length=100, description="文件夹名称")
    parent_id: Optional[int] = Field(None, description="父文件夹ID")
    sort_order: int = Field(0, description="排序")


class PaperFolderUpdate(BaseModel):
    """更新试卷文件夹"""

    name: Optional[str] = Field(None, max_length=100)
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None


class PaperFolderResponse(BaseModel):
    """试卷文件夹响应"""

    id: int
    name: str
    parent_id: Optional[int] = None
    sort_order: int = 0
    paper_count: int = 0
    children: List["PaperFolderResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PaperMoveRequest(BaseModel):
    """移动试卷到文件夹"""

    folder_id: Optional[int] = Field(None, description="目标文件夹ID，null表示移出文件夹")


class QuestionFolderCreate(BaseModel):
    """创建试题文件夹"""

    name: str = Field(..., max_length=100, description="文件夹名称")
    parent_id: Optional[int] = Field(None, description="父文件夹ID")
    sort_order: int = Field(0, description="排序")


class QuestionFolderUpdate(BaseModel):
    """更新试题文件夹"""

    name: Optional[str] = Field(None, max_length=100)
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None


class QuestionFolderResponse(BaseModel):
    """试题文件夹响应"""

    id: int
    name: str
    parent_id: Optional[int] = None
    sort_order: int = 0
    question_count: int = 0
    children: List["QuestionFolderResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class QuestionMoveRequest(BaseModel):
    """移动试题到文件夹"""

    folder_id: Optional[int] = Field(None, description="目标文件夹ID，null表示移出文件夹")


class ExamPaperCreate(BaseModel):
    """创建试卷"""

    title: str = Field(..., max_length=200, description="试卷标题")
    description: Optional[str] = None
    duration: Optional[int] = Field(None, ge=10, le=300, description="考试时长(分钟)")
    total_score: Optional[int] = Field(None, ge=1, description="总分，默认按题目自动汇总")
    passing_score: Optional[int] = Field(None, ge=1, description="及格分")
    type: str = Field("formal", description="试卷类型: formal/quiz")
    folder_id: Optional[int] = Field(None, description="所属文件夹ID")
    question_ids: List[int] = Field(default_factory=list, description="题目ID列表")


class ExamPaperUpdate(BaseModel):
    """更新试卷"""

    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    duration: Optional[int] = Field(None, ge=10, le=300)
    total_score: Optional[int] = Field(None, ge=1)
    passing_score: Optional[int] = Field(None, ge=1)
    type: Optional[str] = None
    folder_id: Optional[int] = None
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
    folder_id: Optional[int] = None
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
    scope_type: str = Field(ADMISSION_SCOPE_ALL, description="适用范围类型: all/user/department/role")
    scope_target_ids: List[int] = Field(default_factory=list, description="适用范围目标ID列表")
    max_attempts: int = Field(1, ge=1, le=10, description="最大作答次数")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @field_validator("scope_type", mode="before")
    @classmethod
    def validate_scope_type(cls, value: Optional[str]) -> str:
        return _normalize_admission_scope_type(value) or ADMISSION_SCOPE_ALL

    @field_validator("scope_target_ids", mode="before")
    @classmethod
    def validate_scope_target_ids(cls, value: Any) -> List[int]:
        return _normalize_admission_scope_target_ids(value) or []


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
    scope_type: Optional[str] = Field(None, description="适用范围类型: all/user/department/role")
    scope_target_ids: Optional[List[int]] = Field(None, description="适用范围目标ID列表")
    max_attempts: Optional[int] = Field(None, ge=1, le=10)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @field_validator("scope_type", mode="before")
    @classmethod
    def validate_scope_type(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_admission_scope_type(value, allow_none=True)

    @field_validator("scope_target_ids", mode="before")
    @classmethod
    def validate_scope_target_ids(cls, value: Any) -> Optional[List[int]]:
        return _normalize_admission_scope_target_ids(value, allow_none=True)


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
    scope_type: str = ADMISSION_SCOPE_ALL
    scope_target_ids: List[int] = Field(default_factory=list)
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
