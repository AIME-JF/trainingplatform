"""
资源库相关数据验证模型
"""
from typing import Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from .exam import (
    ADMISSION_SCOPE_ALL,
    ADMISSION_SCOPE_DEPARTMENT,
    ADMISSION_SCOPE_ROLE,
    ADMISSION_SCOPE_USER,
    _normalize_admission_scope_target_ids,
    _normalize_admission_scope_type,
)


RESOURCE_SCOPE_TYPE_LEGACY_MAP = {
    'public': ADMISSION_SCOPE_ALL,
    'department': ADMISSION_SCOPE_DEPARTMENT,
    'custom': ADMISSION_SCOPE_DEPARTMENT,
}


def _normalize_resource_scope_type(value: Optional[str], allow_none: bool = False) -> Optional[str]:
    if value is None:
        return None if allow_none else ADMISSION_SCOPE_ALL

    normalized = str(value).strip() or ADMISSION_SCOPE_ALL
    normalized = RESOURCE_SCOPE_TYPE_LEGACY_MAP.get(normalized, normalized)
    if normalized == 'police_type':
        raise ValueError('资源可见范围不再支持按警种配置，请改用全部、指定部门、指定角色或指定用户')
    return _normalize_admission_scope_type(normalized, allow_none=allow_none)


class ResourceMediaLinkPayload(BaseModel):
    media_file_id: int = Field(..., description='文件ID')
    media_role: str = Field('main', description='文件角色')
    sort_order: int = Field(0, description='排序')


class ResourceTagResponse(BaseModel):
    """资源标签响应"""
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ResourceTagCreate(BaseModel):
    """资源标签创建"""
    name: str = Field(..., min_length=1, max_length=50, description='标签名称')


class ResourceCreate(BaseModel):
    title: str = Field(..., max_length=200, description='资源标题')
    summary: Optional[str] = Field(None, description='资源摘要')
    content_type: str = Field('video', description='内容类型')
    source_type: str = Field('ugc', description='来源类型')
    scope: Optional[str] = Field(None, description='可见范围摘要')
    scope_type: str = Field(ADMISSION_SCOPE_ALL, description='可见范围类型: all/user/department/role')
    scope_target_ids: List[int] = Field(default_factory=list, description='可见范围目标ID列表')
    visibility_type: Optional[str] = Field(None, description='兼容旧字段：可见域类型')
    owner_department_id: Optional[int] = Field(None, description='归属部门ID')
    cover_media_file_id: Optional[int] = Field(None, description='封面文件ID')
    tags: List[str] = Field(default_factory=list, description='标签')
    media_links: List[ResourceMediaLinkPayload] = Field(default_factory=list, description='资源文件关联')
    visibility_scopes: List[int] = Field(default_factory=list, description='兼容旧字段：可见域ID列表')

    @model_validator(mode='before')
    @classmethod
    def normalize_legacy_scope_fields(cls, value: Any):
        payload = dict(value or {})
        if payload.get('scope_type') in (None, '') and payload.get('visibility_type') not in (None, ''):
            payload['scope_type'] = payload.get('visibility_type')
        if payload.get('scope_target_ids') is None and payload.get('visibility_scopes') is not None:
            payload['scope_target_ids'] = payload.get('visibility_scopes')
        return payload

    @field_validator('scope_type', mode='before')
    @classmethod
    def validate_scope_type(cls, value: Optional[str]) -> str:
        return _normalize_resource_scope_type(value) or ADMISSION_SCOPE_ALL

    @field_validator('scope_target_ids', 'visibility_scopes', mode='before')
    @classmethod
    def validate_scope_target_ids(cls, value: Any) -> List[int]:
        return _normalize_admission_scope_target_ids(value) or []


class ResourceUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    summary: Optional[str] = None
    content_type: Optional[str] = None
    source_type: Optional[str] = None
    scope: Optional[str] = None
    scope_type: Optional[str] = Field(None, description='可见范围类型: all/user/department/role')
    scope_target_ids: Optional[List[int]] = Field(None, description='可见范围目标ID列表')
    visibility_type: Optional[str] = None
    owner_department_id: Optional[int] = None
    cover_media_file_id: Optional[int] = None
    tags: Optional[List[str]] = None
    media_links: Optional[List[ResourceMediaLinkPayload]] = None
    visibility_scopes: Optional[List[int]] = None

    @model_validator(mode='before')
    @classmethod
    def normalize_legacy_scope_fields(cls, value: Any):
        payload = dict(value or {})
        if payload.get('scope_type') in (None, '') and payload.get('visibility_type') not in (None, ''):
            payload['scope_type'] = payload.get('visibility_type')
        if payload.get('scope_target_ids') is None and payload.get('visibility_scopes') is not None:
            payload['scope_target_ids'] = payload.get('visibility_scopes')
        return payload

    @field_validator('scope_type', mode='before')
    @classmethod
    def validate_scope_type(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_resource_scope_type(value, allow_none=True)

    @field_validator('scope_target_ids', 'visibility_scopes', mode='before')
    @classmethod
    def validate_scope_target_ids(cls, value: Any) -> Optional[List[int]]:
        return _normalize_admission_scope_target_ids(value, allow_none=True)


class ResourcePublishRequest(BaseModel):
    publish_at: Optional[datetime] = Field(None, description='发布时间，为空时立即发布')


class ResourceOfflineRequest(BaseModel):
    offline_at: Optional[datetime] = Field(None, description='下线时间，为空时立即下线')


class ResourceMediaLinkResponse(BaseModel):
    id: int
    media_file_id: int
    media_role: str
    sort_order: int
    file_name: Optional[str] = None
    display_label: Optional[str] = None
    content_type: Optional[str] = None
    file_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ResourceListItemResponse(BaseModel):
    id: int
    title: str
    summary: Optional[str] = None
    content_type: str
    source_type: str
    status: str
    visibility_type: Optional[str] = None
    scope: Optional[str] = None
    scope_type: str = ADMISSION_SCOPE_ALL
    scope_target_ids: List[int] = Field(default_factory=list)
    uploader_id: int
    uploader_name: Optional[str] = None
    owner_department_id: Optional[int] = None
    owner_department_name: Optional[str] = None
    cover_media_file_id: Optional[int] = None
    cover_url: Optional[str] = None
    tags: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ResourceDetailResponse(ResourceListItemResponse):
    media_links: List[ResourceMediaLinkResponse] = []
    visibility_scopes: List[int] = []


class CourseResourceBindRequest(BaseModel):
    resource_id: int
    usage_type: str = Field('required', description='用途')
    sort_order: int = Field(0, description='排序')


class TrainingResourceBindRequest(BaseModel):
    resource_id: int
    usage_type: str = Field('required', description='用途')
    sort_order: int = Field(0, description='排序')
