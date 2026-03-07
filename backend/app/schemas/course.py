"""
课程管理相关的数据验证模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ========== Chapter ==========

class ChapterCreate(BaseModel):
    """创建章节"""
    title: str = Field(..., max_length=200, description="章节标题")
    sort_order: int = Field(0, description="排序")
    duration: int = Field(0, description="时长(分钟)")
    video_url: Optional[str] = Field(None, description="视频URL(兼容)")
    doc_url: Optional[str] = Field(None, description="文档URL(兼容)")
    file_id: Optional[int] = Field(None, description="关联文件ID")


class ChapterUpdate(BaseModel):
    """更新章节"""
    title: Optional[str] = Field(None, max_length=200)
    sort_order: Optional[int] = None
    duration: Optional[int] = None
    video_url: Optional[str] = None
    doc_url: Optional[str] = None
    file_id: Optional[int] = None


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
    file_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ========== Course ==========

class CourseCreate(BaseModel):
    """创建课程"""
    title: str = Field(..., max_length=200, description="课程标题")
    category: str = Field(..., max_length=50, description="课程分类")
    file_type: str = Field("video", description="文件类型")
    description: Optional[str] = Field(None, description="课程描述")
    instructor_id: Optional[int] = Field(None, description="教官ID")
    duration: int = Field(0, description="总时长(分钟)")
    difficulty: int = Field(1, ge=1, le=5, description="难度1-5")
    is_required: bool = Field(False, description="是否必修")
    cover_color: Optional[str] = Field(None, description="封面色")
    tags: Optional[List[str]] = Field(None, description="标签数组")
    chapters: Optional[List[ChapterCreate]] = Field(None, description="章节列表")


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
    tags: Optional[List[str]] = None
    chapters: Optional[List[ChapterCreate]] = None


class CourseResponse(BaseModel):
    """课程响应"""
    id: int
    title: str
    category: str
    file_type: str = "video"
    description: Optional[str] = None
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    duration: int = 0
    student_count: int = 0
    rating: float = 0
    difficulty: int = 1
    is_required: bool = False
    cover_color: Optional[str] = None
    tags: Optional[List[str]] = None
    chapters: List[ChapterResponse] = []
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
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    duration: int = 0
    student_count: int = 0
    rating: float = 0
    difficulty: int = 1
    is_required: bool = False
    cover_color: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========== CourseProgress ==========

class CourseProgressUpdate(BaseModel):
    """更新学习进度"""
    progress: int = Field(..., ge=0, le=100, description="进度0-100")


class CourseNoteUpdate(BaseModel):
    """更新课程笔记"""
    content: str = Field('', description="笔记内容")


class CourseNoteResponse(BaseModel):
    """课程笔记响应"""
    id: int
    user_id: int
    course_id: int
    content: str = ''
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CourseProgressResponse(BaseModel):
    """学习进度响应"""
    id: int
    user_id: int
    course_id: int
    chapter_id: Optional[int] = None
    progress: int = 0
    last_studied_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
