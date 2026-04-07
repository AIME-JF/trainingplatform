"""
资源库模块数据验证模型
"""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


LIBRARY_SCOPE_PRIVATE = "private"
LIBRARY_SCOPE_PUBLIC = "public"
LIBRARY_SCOPE_CHOICES = {LIBRARY_SCOPE_PRIVATE, LIBRARY_SCOPE_PUBLIC}

LIBRARY_CONTENT_TYPE_VIDEO = "video"
LIBRARY_CONTENT_TYPE_DOCUMENT = "document"
LIBRARY_CONTENT_TYPE_IMAGE = "image"
LIBRARY_CONTENT_TYPE_AUDIO = "audio"
LIBRARY_CONTENT_TYPE_KNOWLEDGE = "knowledge"
LIBRARY_CONTENT_TYPE_CHOICES = {
    LIBRARY_CONTENT_TYPE_VIDEO,
    LIBRARY_CONTENT_TYPE_DOCUMENT,
    LIBRARY_CONTENT_TYPE_IMAGE,
    LIBRARY_CONTENT_TYPE_AUDIO,
    LIBRARY_CONTENT_TYPE_KNOWLEDGE,
}

LIBRARY_SOURCE_KIND_FILE = "file"
LIBRARY_SOURCE_KIND_KNOWLEDGE = "knowledge"
LIBRARY_SOURCE_KIND_AI_GENERATED = "ai_generated"


def _normalize_int_list(value: Any, allow_none: bool = False) -> Optional[List[int]]:
    if value is None:
        return None if allow_none else []

    normalized: List[int] = []
    seen = set()
    for raw_item in value or []:
        try:
            item = int(raw_item)
        except (TypeError, ValueError) as exc:
            raise ValueError("ID 列表必须全部为整数") from exc
        if item <= 0 or item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


def _normalize_library_scope(value: Optional[str]) -> str:
    normalized = str(value or LIBRARY_SCOPE_PRIVATE).strip().lower() or LIBRARY_SCOPE_PRIVATE
    if normalized not in LIBRARY_SCOPE_CHOICES:
        raise ValueError("资源库范围仅支持 private 或 public")
    return normalized


def _normalize_library_content_type(value: Optional[str]) -> str:
    normalized = str(value or "").strip().lower()
    if normalized not in LIBRARY_CONTENT_TYPE_CHOICES:
        raise ValueError("不支持的资源类型")
    return normalized


class LibraryFolderCreate(BaseModel):
    """创建资源库文件夹"""

    name: str = Field(..., min_length=1, max_length=100, description="文件夹名称")
    parent_id: Optional[int] = Field(None, description="父文件夹ID")
    sort_order: int = Field(0, description="排序")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("文件夹名称不能为空")
        return normalized[:100]


class LibraryFolderUpdate(BaseModel):
    """更新资源库文件夹"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("文件夹名称不能为空")
        return normalized[:100]


class LibraryFolderResponse(BaseModel):
    """资源库文件夹响应"""

    id: int
    name: str
    parent_id: Optional[int] = None
    sort_order: int = 0
    item_count: int = 0
    children: List["LibraryFolderResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class LibraryBatchFileCreateRequest(BaseModel):
    """批量创建文件资源项"""

    folder_id: Optional[int] = Field(None, description="目标文件夹ID")
    media_file_ids: List[int] = Field(default_factory=list, description="已上传文件ID列表")

    @field_validator("media_file_ids", mode="before")
    @classmethod
    def validate_media_file_ids(cls, value: Any) -> List[int]:
        normalized = _normalize_int_list(value) or []
        if not normalized:
            raise ValueError("请至少选择一个文件")
        return normalized


class LibraryKnowledgeCreateRequest(BaseModel):
    """创建知识点卡片"""

    title: str = Field(..., min_length=1, max_length=200, description="标题")
    folder_id: Optional[int] = Field(None, description="目标文件夹ID")
    knowledge_content_html: str = Field(..., min_length=1, description="知识点内容")

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("知识点标题不能为空")
        return normalized[:200]

    @field_validator("knowledge_content_html")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("知识点内容不能为空")
        return normalized


class LibraryItemUpdateRequest(BaseModel):
    """更新资源项"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    knowledge_content_html: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("资源标题不能为空")
        return normalized[:200]


class LibraryItemMoveRequest(BaseModel):
    """移动资源项"""

    folder_id: Optional[int] = Field(None, description="目标文件夹ID，为空表示移动到根目录")


class LibraryItemListResponse(BaseModel):
    """资源库资源项列表响应"""

    id: int
    owner_user_id: int
    owner_name: Optional[str] = None
    folder_id: Optional[int] = None
    folder_name: Optional[str] = None
    title: str
    content_type: str
    source_kind: str
    media_file_id: Optional[int] = None
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    mime_type: Optional[str] = None
    size: int = 0
    duration_seconds: int = 0
    is_public: bool = False
    is_owner: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LibraryItemDetailResponse(LibraryItemListResponse):
    """资源库资源项详情响应"""

    knowledge_content_html: Optional[str] = None


class LibraryItemListParams(BaseModel):
    """资源库资源项查询参数"""

    scope: str = Field(LIBRARY_SCOPE_PRIVATE, description="private/public")
    category: Optional[str] = Field(None, description="固定资源分类")
    folder_id: Optional[int] = Field(None, description="文件夹ID")
    search: Optional[str] = Field(None, description="搜索关键词")
    source_kind: Optional[str] = Field(None, description="来源类型过滤")

    @field_validator("scope", mode="before")
    @classmethod
    def validate_scope(cls, value: Optional[str]) -> str:
        return _normalize_library_scope(value)

    @field_validator("category", mode="before")
    @classmethod
    def validate_category(cls, value: Optional[str]) -> Optional[str]:
        if value in (None, "", "all"):
            return None
        return _normalize_library_content_type(value)


__all__ = [
    "LIBRARY_SCOPE_PRIVATE",
    "LIBRARY_SCOPE_PUBLIC",
    "LIBRARY_CONTENT_TYPE_VIDEO",
    "LIBRARY_CONTENT_TYPE_DOCUMENT",
    "LIBRARY_CONTENT_TYPE_IMAGE",
    "LIBRARY_CONTENT_TYPE_AUDIO",
    "LIBRARY_CONTENT_TYPE_KNOWLEDGE",
    "LIBRARY_SOURCE_KIND_FILE",
    "LIBRARY_SOURCE_KIND_KNOWLEDGE",
    "LIBRARY_SOURCE_KIND_AI_GENERATED",
    "LibraryFolderCreate",
    "LibraryFolderUpdate",
    "LibraryFolderResponse",
    "LibraryBatchFileCreateRequest",
    "LibraryKnowledgeCreateRequest",
    "LibraryItemUpdateRequest",
    "LibraryItemMoveRequest",
    "LibraryItemListResponse",
    "LibraryItemDetailResponse",
    "LibraryItemListParams",
]


LibraryFolderResponse.model_rebuild()
