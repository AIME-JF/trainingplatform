"""
课程管理相关的数据验证模型
"""

from typing import Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

from .exam import (
    ADMISSION_SCOPE_ALL,
    _normalize_admission_scope_target_ids,
    _normalize_admission_scope_type,
)
from .resource import ResourceListItemResponse


# ========== Chapter ==========

class ChapterCreate(BaseModel):
    """创建章节"""
    id: Optional[int] = Field(None, description="章节ID，更新时传递")
    title: str = Field(..., max_length=200, description="章节标题")
    sort_order: int = Field(0, description="排序")
    duration: int = Field(0, description="时长(分钟)")
    video_url: Optional[str] = Field(None, description="视频URL(兼容)")
    doc_url: Optional[str] = Field(None, description="文档URL(兼容)")
    file_id: Optional[int] = Field(None, description="关联文件ID")
    resource_id: Optional[int] = Field(None, description="关联资源ID")


class ChapterUpdate(BaseModel):
    """更新章节"""
    title: Optional[str] = Field(None, max_length=200)
    sort_order: Optional[int] = None
    duration: Optional[int] = None
    video_url: Optional[str] = None
    doc_url: Optional[str] = None
    file_id: Optional[int] = None
    resource_id: Optional[int] = None


class ChapterResponse(BaseModel):
    """章节响应"""
    id: int
    course_id: int
    title: str
    sort_order: int = 0
    duration: int = 0
    video_url: Optional[str] = None
    doc_url: Optional[str] = None
    file_id: Optional[int] = None
    resource_id: Optional[int] = None
    resource_title: Optional[str] = None
    resource_file_name: Optional[str] = None
    resource_file_label: Optional[str] = None
    file_url: Optional[str] = None
    content_type: Optional[str] = None
    progress: int = 0  # 当前用户学习进度(0-100)
    playback_seconds: int = 0
    last_studied_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========== Course ==========

class CourseCreate(BaseModel):
    """创建课程"""
    title: str = Field(..., max_length=200, description="课程标题")
    category: str = Field(..., max_length=50, description="课程分类")
    file_type: str = Field("video", description="文件类型: video/document/image/mixed")
    description: Optional[str] = Field(None, description="课程描述")
    instructor_id: Optional[int] = Field(None, description="教官ID")
    duration: int = Field(0, description="总时长(分钟)")
    difficulty: int = Field(1, ge=1, le=5, description="难度1-5")
    is_required: bool = Field(False, description="是否必修")
    cover_color: Optional[str] = Field(None, description="封面色")
    scope: Optional[str] = None
    scope_type: str = Field(ADMISSION_SCOPE_ALL, description="可见范围类型: all/user/department/role")
    scope_target_ids: List[int] = Field(default_factory=list, description="可见范围目标ID列表")
    tags: Optional[List[str]] = Field(None, description="标签数组")
    chapters: Optional[List[ChapterCreate]] = Field(None, description="章节列表")

    @field_validator("scope_type", mode="before")
    @classmethod
    def validate_scope_type(cls, value: Optional[str]) -> str:
        return _normalize_admission_scope_type(value) or ADMISSION_SCOPE_ALL

    @field_validator("scope_target_ids", mode="before")
    @classmethod
    def validate_scope_target_ids(cls, value: Any) -> List[int]:
        return _normalize_admission_scope_target_ids(value) or []


class CourseUpdate(BaseModel):
    """更新课程"""
    title: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = None
    file_type: Optional[str] = None
    description: Optional[str] = None
    instructor_id: Optional[int] = None
    duration: Optional[int] = None
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    is_required: Optional[bool] = None
    cover_color: Optional[str] = None
    scope: Optional[str] = None
    scope_type: Optional[str] = Field(None, description="可见范围类型: all/user/department/role")
    scope_target_ids: Optional[List[int]] = Field(None, description="可见范围目标ID列表")
    tags: Optional[List[str]] = None
    chapters: Optional[List[ChapterCreate]] = None

    @field_validator("scope_type", mode="before")
    @classmethod
    def validate_scope_type(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_admission_scope_type(value, allow_none=True)

    @field_validator("scope_target_ids", mode="before")
    @classmethod
    def validate_scope_target_ids(cls, value: Any) -> Optional[List[int]]:
        return _normalize_admission_scope_target_ids(value, allow_none=True)


# ========== CourseNote / CourseQA (定义在 CourseResponse 之前以避免 forward reference) ==========

class CourseNoteResponse(BaseModel):
    """课程笔记响应"""
    id: int
    user_id: int
    course_id: int
    content: str = ''
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CourseQAResponse(BaseModel):
    """答疑响应"""
    id: int
    user_id: int
    user_name: Optional[str] = None
    course_id: int
    question: str
    answer: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CourseResponse(BaseModel):
    """课程响应"""
    id: int
    title: str
    category: str
    file_type: str = "video"
    description: Optional[str] = None
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    duration: int = 0
    student_count: int = 0
    rating: float = 0
    difficulty: int = 1
    is_required: bool = False
    cover_color: Optional[str] = None
    scope: Optional[str] = None
    scope_type: str = ADMISSION_SCOPE_ALL
    scope_target_ids: List[int] = Field(default_factory=list)
    tags: Optional[List[str]] = None
    progress_percent: int = 0
    chapter_count: int = 0
    completed_chapter_count: int = 0
    last_studied_at: Optional[datetime] = None
    last_studied_chapter_id: Optional[int] = None
    last_studied_chapter_title: Optional[str] = None
    last_playback_seconds: int = 0
    can_view_learning_status: bool = False
    chapters: List[ChapterResponse] = []
    note: Optional[CourseNoteResponse] = None
    qa_list: List[CourseQAResponse] = Field(default_factory=list)
    resources: List[ResourceListItemResponse] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CourseListResponse(BaseModel):
    """课程列表响应（不含章节）"""
    id: int
    title: str
    category: str
    file_type: str = "video"
    description: Optional[str] = None
    created_by: Optional[int] = None
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    duration: int = 0
    student_count: int = 0
    rating: float = 0
    difficulty: int = 1
    is_required: bool = False
    cover_color: Optional[str] = None
    scope: Optional[str] = None
    scope_type: str = ADMISSION_SCOPE_ALL
    scope_target_ids: List[int] = Field(default_factory=list)
    tags: Optional[List[str]] = None
    progress_percent: int = 0
    chapter_count: int = 0
    completed_chapter_count: int = 0
    last_studied_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CourseTagResponse(BaseModel):
    """课程标签响应"""
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CourseTagCreate(BaseModel):
    """课程标签创建"""
    name: str = Field(..., min_length=1, max_length=50, description="标签名称")


# ========== CourseProgress ==========

class CourseProgressUpdate(BaseModel):
    """更新学习进度"""
    progress: int = Field(..., ge=0, le=100, description="进度0-100")
    playback_seconds: Optional[int] = Field(None, ge=0, description="最近播放位置(秒)")


class CourseNoteUpdate(BaseModel):
    """更新课程笔记"""
    content: str = Field('', description="笔记内容")


class CourseProgressResponse(BaseModel):
    """学习进度响应"""
    id: int
    user_id: int
    course_id: int
    chapter_id: Optional[int] = None
    progress: int = 0
    playback_seconds: int = 0
    last_studied_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CourseLearningStatusResponse(BaseModel):
    """课程学习情况响应"""
    user_id: int
    username: str
    user_name: Optional[str] = None
    police_id: Optional[str] = None
    department_name: Optional[str] = None
    progress_percent: int = 0
    chapter_count: int = 0
    completed_chapter_count: int = 0
    last_studied_at: Optional[datetime] = None
    last_studied_chapter_id: Optional[int] = None
    last_studied_chapter_title: Optional[str] = None
    last_playback_seconds: int = 0


# ========== CourseQA ==========

class CourseQACreate(BaseModel):
    """提出问题"""
    question: str = Field(..., description="问题内容")


class CourseQAUpdate(BaseModel):
    """回答问题（仅教官/管理员）"""
    answer: str = Field(..., description="回答内容")
