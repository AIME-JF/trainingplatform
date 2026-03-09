"""
资源库相关数据验证模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ResourceMediaLinkPayload(BaseModel):
    media_file_id: int = Field(..., description='文件ID')
    media_role: str = Field('main', description='文件角色')
    sort_order: int = Field(0, description='排序')


class ResourceCreate(BaseModel):
    title: str = Field(..., max_length=200, description='资源标题')
    summary: Optional[str] = Field(None, description='资源摘要')
    content_type: str = Field('video', description='内容类型')
    source_type: str = Field('ugc', description='来源类型')
    visibility_type: str = Field('public', description='可见域类型')
    owner_department_id: Optional[int] = Field(None, description='归属部门ID')
    cover_media_file_id: Optional[int] = Field(None, description='封面文件ID')
    tags: List[str] = Field(default_factory=list, description='标签')
    media_links: List[ResourceMediaLinkPayload] = Field(default_factory=list, description='资源文件关联')
    visibility_scopes: List[int] = Field(default_factory=list, description='可见域ID列表(与visibilityType匹配)')


class ResourceUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    summary: Optional[str] = None
    content_type: Optional[str] = None
    source_type: Optional[str] = None
    visibility_type: Optional[str] = None
    owner_department_id: Optional[int] = None
    cover_media_file_id: Optional[int] = None
    tags: Optional[List[str]] = None
    media_links: Optional[List[ResourceMediaLinkPayload]] = None
    visibility_scopes: Optional[List[int]] = None


class ResourcePublishRequest(BaseModel):
    publish_at: Optional[datetime] = Field(None, description='发布时间，为空时立即发布')


class ResourceOfflineRequest(BaseModel):
    offline_at: Optional[datetime] = Field(None, description='下线时间，为空时立即下线')


class ResourceMediaLinkResponse(BaseModel):
    id: int
    media_file_id: int
    media_role: str
    sort_order: int
    file_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ResourceListItemResponse(BaseModel):
    id: int
    title: str
    summary: Optional[str] = None
    content_type: str
    source_type: str
    status: str
    visibility_type: str
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
