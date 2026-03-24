"""
资源库服务
"""
import os
from typing import Optional, List, Dict, Any, Set
from datetime import datetime

from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import (
    Resource, ResourceMediaLink, ResourceTag, ResourceTagRelation,
    ResourceVisibilityScope, CourseResourceRef, TrainingResourceRef,
    MediaFile, User
)
from app.models.course import Course
from app.models.training import Training
from app.models.review import ResourceReviewTask
from app.schemas import PaginatedResponse
from app.schemas.resource import (
    ResourceCreate, ResourceUpdate, ResourceListItemResponse, ResourceDetailResponse,
    ResourceMediaLinkResponse, ResourceTagResponse,
    CourseResourceBindRequest, TrainingResourceBindRequest
)
from config import settings


RESOURCE_ALLOWED_TRANSITIONS = {
    'draft': {'pending_review', 'offline'},
    'pending_review': {'reviewing', 'offline'},
    'reviewing': {'published', 'rejected', 'offline'},
    'published': {'offline'},
    'rejected': {'draft', 'pending_review', 'offline'},
    'offline': {'published', 'draft'},
}

RESOURCE_CONTENT_FILE_EXTENSIONS = {
    'video': {'.mp4'},
    'document': {'.pdf', '.doc', '.docx', '.ppt', '.pptx'},
    'image': {'.jpg', '.jpeg', '.png', '.webp'},
    'image_text': {'.jpg', '.jpeg', '.png', '.webp'},
}


class ResourceService:
    """资源库服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_resources(
        self,
        current_user_id: int,
        user_permissions: List[str],
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        status: Optional[str] = None,
        content_type: Optional[str] = None,
        my_only: bool = False,
    ) -> PaginatedResponse[ResourceListItemResponse]:
        query = self.db.query(Resource).options(
            joinedload(Resource.uploader),
            joinedload(Resource.owner_department),
            joinedload(Resource.cover_media),
            selectinload(Resource.tag_relations).joinedload(ResourceTagRelation.tag),
            selectinload(Resource.visibility_scopes),
        )

        if search:
            query = query.filter(Resource.title.contains(search))
        if status:
            query = query.filter(Resource.status == status)
        if content_type:
            normalized_content_type = self._normalize_content_type(content_type)
            if normalized_content_type == 'image':
                query = query.filter(Resource.content_type.in_(['image', 'image_text']))
            else:
                query = query.filter(Resource.content_type == normalized_content_type)

        query = query.order_by(Resource.created_at.desc())

        records = query.all()
        user_ctx = self._get_user_context(current_user_id)

        filtered = []
        for r in records:
            if my_only and r.uploader_id != current_user_id:
                continue
            if self._can_view_resource(r, current_user_id, user_permissions, user_ctx):
                filtered.append(r)

        total = len(filtered)
        if size == -1:
            paged = filtered
        else:
            start = (page - 1) * size
            paged = filtered[start: start + size]

        items = [self._to_list_item_response(r) for r in paged]
        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=items,
        )

    def list_resource_tags(self, search: Optional[str] = None) -> List[ResourceTagResponse]:
        """获取全部资源标签。"""
        query = self.db.query(ResourceTag)
        keyword = str(search or '').strip()
        if keyword:
            query = query.filter(ResourceTag.name.contains(keyword))
        tags = query.order_by(ResourceTag.name.asc()).all()
        return [ResourceTagResponse.model_validate(tag) for tag in tags]

    def create_resource_tag(self, name: str) -> ResourceTagResponse:
        """创建资源标签。若标签已存在则直接返回。"""
        tag = self._get_or_create_resource_tag(name)
        self.db.commit()
        self.db.refresh(tag)
        return ResourceTagResponse.model_validate(tag)

    def create_resource(self, data: ResourceCreate, current_user_id: int) -> ResourceDetailResponse:
        user_ctx = self._get_user_context(current_user_id)
        owner_department_id = data.owner_department_id or (next(iter(user_ctx['department_ids'])) if user_ctx['department_ids'] else None)
        normalized_content_type = self._normalize_content_type(data.content_type)

        media_file_ids = self._extract_media_file_ids(data.media_links)
        if data.cover_media_file_id:
            media_file_ids.append(data.cover_media_file_id)
        self._validate_media_file_ids(normalized_content_type, media_file_ids)

        resource = Resource(
            title=data.title,
            summary=data.summary,
            content_type=normalized_content_type,
            source_type=data.source_type,
            status='draft',
            visibility_type=data.visibility_type,
            uploader_id=current_user_id,
            owner_department_id=owner_department_id,
            cover_media_file_id=data.cover_media_file_id,
        )
        self.db.add(resource)
        self.db.flush()

        self._sync_tags(resource, data.tags)
        self._sync_media_links(resource, data.media_links)
        self._sync_visibility_scopes(resource, data.visibility_type, data.visibility_scopes)

        self.db.commit()
        self.db.refresh(resource)
        resource = self._get_resource_entity(resource.id)
        return self._to_detail_response(resource)

    def get_resource_by_id(
        self,
        resource_id: int,
        current_user_id: int,
        user_permissions: List[str],
    ) -> Optional[ResourceDetailResponse]:
        resource = self._get_resource_entity(resource_id)
        if not resource:
            return None

        user_ctx = self._get_user_context(current_user_id)
        if not self._can_view_resource(resource, current_user_id, user_permissions, user_ctx):
            return None
        return self._to_detail_response(resource)

    def update_resource(
        self,
        resource_id: int,
        data: ResourceUpdate,
        current_user_id: int,
        user_permissions: List[str],
    ) -> Optional[ResourceDetailResponse]:
        resource = self._get_resource_entity(resource_id)
        if not resource:
            return None

        if not self._can_edit_resource(resource, current_user_id, user_permissions):
            raise PermissionError('无权限编辑该资源')

        update_data = data.model_dump(exclude_unset=True)
        tags = update_data.pop('tags', None)
        media_links = update_data.pop('media_links', None)
        visibility_scopes = update_data.pop('visibility_scopes', None)

        for field, value in update_data.items():
            if field == 'content_type' and value is not None:
                value = self._normalize_content_type(value)
            setattr(resource, field, value)

        if tags is not None:
            self._sync_tags(resource, tags)
        if media_links is not None:
            self._sync_media_links(resource, media_links)
        if visibility_scopes is not None:
            self._sync_visibility_scopes(resource, resource.visibility_type, visibility_scopes)

        file_ids = [link.media_file_id for link in (resource.media_links or []) if link.media_file_id]
        if resource.cover_media_file_id:
            file_ids.append(resource.cover_media_file_id)
        self._validate_media_file_ids(resource.content_type, file_ids)

        self.db.commit()
        self.db.refresh(resource)
        resource = self._get_resource_entity(resource_id)
        return self._to_detail_response(resource)

    def publish_resource(
        self,
        resource_id: int,
        current_user_id: int,
        user_permissions: List[str],
        force: bool = False,
    ) -> Optional[ResourceDetailResponse]:
        resource = self._get_resource_entity(resource_id)
        if not resource:
            return None
        if not self._can_edit_resource(resource, current_user_id, user_permissions):
            raise PermissionError('无权限发布该资源')
        self.transition_resource_status(resource, 'published', force=force)
        self.db.commit()
        self.db.refresh(resource)
        resource = self._get_resource_entity(resource_id)
        return self._to_detail_response(resource)

    def offline_resource(
        self,
        resource_id: int,
        current_user_id: int,
        user_permissions: List[str],
        force: bool = False,
    ) -> Optional[ResourceDetailResponse]:
        resource = self._get_resource_entity(resource_id)
        if not resource:
            return None
        if not self._can_edit_resource(resource, current_user_id, user_permissions):
            raise PermissionError('无权限下线该资源')
        self.transition_resource_status(resource, 'offline', force=force)
        self.db.commit()
        self.db.refresh(resource)
        resource = self._get_resource_entity(resource_id)
        return self._to_detail_response(resource)

    def delete_resource(
        self,
        resource_id: int,
        current_user_id: int,
        user_permissions: List[str],
    ) -> bool:
        resource = self.db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            return False
        if not self._can_edit_resource(resource, current_user_id, user_permissions):
            raise PermissionError('无权限删除该资源')

        self.db.delete(resource)
        self.db.commit()
        return True

    def transition_resource_status(self, resource: Resource, target_status: str, force: bool = False):
        current_status = resource.status
        if current_status == target_status:
            return

        if not force and target_status not in RESOURCE_ALLOWED_TRANSITIONS.get(current_status, set()):
            raise ValueError(f'不允许的状态流转: {current_status} -> {target_status}')

        resource.status = target_status
        now = datetime.now()
        if target_status == 'published' and not resource.publish_at:
            resource.publish_at = now
        if target_status == 'offline':
            resource.offline_at = now

    # ===== 课程/培训引用 =====
    def bind_course_resource(self, course_id: int, data: CourseResourceBindRequest) -> ResourceListItemResponse:
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError('课程不存在')

        resource = self.db.query(Resource).filter(Resource.id == data.resource_id).first()
        if not resource:
            raise ValueError('资源不存在')

        ref = self.db.query(CourseResourceRef).filter(
            CourseResourceRef.course_id == course_id,
            CourseResourceRef.resource_id == data.resource_id,
        ).first()

        if not ref:
            ref = CourseResourceRef(
                course_id=course_id,
                resource_id=data.resource_id,
                usage_type=data.usage_type,
                sort_order=data.sort_order,
            )
            self.db.add(ref)
        else:
            ref.usage_type = data.usage_type
            ref.sort_order = data.sort_order

        self.db.commit()
        resource = self._get_resource_entity(data.resource_id)
        return self._to_list_item_response(resource)

    def list_course_resources(
        self,
        course_id: int,
        current_user_id: int,
        user_permissions: List[str],
    ) -> List[ResourceListItemResponse]:
        refs = self.db.query(CourseResourceRef).options(
            joinedload(CourseResourceRef.resource).joinedload(Resource.uploader),
            joinedload(CourseResourceRef.resource).joinedload(Resource.owner_department),
            joinedload(CourseResourceRef.resource).joinedload(Resource.cover_media),
            joinedload(CourseResourceRef.resource).selectinload(Resource.tag_relations).joinedload(ResourceTagRelation.tag),
            joinedload(CourseResourceRef.resource).selectinload(Resource.visibility_scopes),
        ).filter(CourseResourceRef.course_id == course_id).order_by(CourseResourceRef.sort_order.asc(), CourseResourceRef.id.asc()).all()

        user_ctx = self._get_user_context(current_user_id)
        items = []
        for ref in refs:
            r = ref.resource
            if r and self._can_view_resource(r, current_user_id, user_permissions, user_ctx):
                items.append(self._to_list_item_response(r))
        return items

    def unbind_course_resource(self, course_id: int, resource_id: int) -> bool:
        ref = self.db.query(CourseResourceRef).filter(
            CourseResourceRef.course_id == course_id,
            CourseResourceRef.resource_id == resource_id,
        ).first()
        if not ref:
            return False
        self.db.delete(ref)
        self.db.commit()
        return True

    def bind_training_resource(self, training_id: int, data: TrainingResourceBindRequest) -> ResourceListItemResponse:
        training = self.db.query(Training).filter(Training.id == training_id).first()
        if not training:
            raise ValueError('培训不存在')

        resource = self.db.query(Resource).filter(Resource.id == data.resource_id).first()
        if not resource:
            raise ValueError('资源不存在')

        ref = self.db.query(TrainingResourceRef).filter(
            TrainingResourceRef.training_id == training_id,
            TrainingResourceRef.resource_id == data.resource_id,
        ).first()

        if not ref:
            ref = TrainingResourceRef(
                training_id=training_id,
                resource_id=data.resource_id,
                usage_type=data.usage_type,
                sort_order=data.sort_order,
            )
            self.db.add(ref)
        else:
            ref.usage_type = data.usage_type
            ref.sort_order = data.sort_order

        self.db.commit()
        resource = self._get_resource_entity(data.resource_id)
        return self._to_list_item_response(resource)

    def list_training_resources(
        self,
        training_id: int,
        current_user_id: int,
        user_permissions: List[str],
    ) -> List[ResourceListItemResponse]:
        refs = self.db.query(TrainingResourceRef).options(
            joinedload(TrainingResourceRef.resource).joinedload(Resource.uploader),
            joinedload(TrainingResourceRef.resource).joinedload(Resource.owner_department),
            joinedload(TrainingResourceRef.resource).joinedload(Resource.cover_media),
            joinedload(TrainingResourceRef.resource).selectinload(Resource.tag_relations).joinedload(ResourceTagRelation.tag),
            joinedload(TrainingResourceRef.resource).selectinload(Resource.visibility_scopes),
        ).filter(TrainingResourceRef.training_id == training_id).order_by(TrainingResourceRef.sort_order.asc(), TrainingResourceRef.id.asc()).all()

        user_ctx = self._get_user_context(current_user_id)
        items = []
        for ref in refs:
            r = ref.resource
            if r and self._can_view_resource(r, current_user_id, user_permissions, user_ctx):
                items.append(self._to_list_item_response(r))
        return items

    def unbind_training_resource(self, training_id: int, resource_id: int) -> bool:
        ref = self.db.query(TrainingResourceRef).filter(
            TrainingResourceRef.training_id == training_id,
            TrainingResourceRef.resource_id == resource_id,
        ).first()
        if not ref:
            return False
        self.db.delete(ref)
        self.db.commit()
        return True

    # ===== internal =====
    def _get_resource_entity(self, resource_id: int) -> Optional[Resource]:
        return self.db.query(Resource).options(
            joinedload(Resource.uploader),
            joinedload(Resource.owner_department),
            joinedload(Resource.cover_media),
            selectinload(Resource.media_links).joinedload(ResourceMediaLink.media_file),
            selectinload(Resource.tag_relations).joinedload(ResourceTagRelation.tag),
            selectinload(Resource.visibility_scopes),
        ).filter(Resource.id == resource_id).first()

    def _normalize_content_type(self, content_type: Optional[str]) -> Optional[str]:
        if content_type == 'image_text':
            return 'image'
        return content_type

    def _sync_tags(self, resource: Resource, tags: List[str]):
        self.db.query(ResourceTagRelation).filter(ResourceTagRelation.resource_id == resource.id).delete()
        cleaned = []
        for raw_name in (tags or []):
            name = self._normalize_tag_name(raw_name)
            if name and name not in cleaned:
                cleaned.append(name)

        for name in cleaned:
            tag = self._get_or_create_resource_tag(name)
            self.db.add(ResourceTagRelation(resource_id=resource.id, tag_id=tag.id))

    def _normalize_tag_name(self, raw_name: Optional[str]) -> str:
        return str(raw_name or '').strip()

    def _get_or_create_resource_tag(self, raw_name: Optional[str]) -> ResourceTag:
        name = self._normalize_tag_name(raw_name)
        if not name:
            raise ValueError('标签名称不能为空')
        if len(name) > 50:
            raise ValueError('标签名称长度不能超过50个字符')

        tag = self.db.query(ResourceTag).filter(ResourceTag.name == name).first()
        if tag:
            return tag

        tag = ResourceTag(name=name)
        self.db.add(tag)
        self.db.flush()
        return tag

    def _sync_media_links(self, resource: Resource, media_links: List[Dict[str, Any]]):
        self.db.query(ResourceMediaLink).filter(ResourceMediaLink.resource_id == resource.id).delete()
        for idx, item in enumerate(media_links or []):
            payload = item.model_dump() if hasattr(item, 'model_dump') else dict(item)
            media_file_id = payload.get('media_file_id')
            if not media_file_id:
                continue
            self.db.add(ResourceMediaLink(
                resource_id=resource.id,
                media_file_id=media_file_id,
                media_role=payload.get('media_role') or 'main',
                sort_order=payload.get('sort_order', idx),
            ))

    def _sync_visibility_scopes(self, resource: Resource, visibility_type: str, scope_ids: List[int]):
        self.db.query(ResourceVisibilityScope).filter(ResourceVisibilityScope.resource_id == resource.id).delete()
        if visibility_type == 'public':
            return

        scope_type = 'department'
        if visibility_type == 'police_type':
            scope_type = 'police_type'
        elif visibility_type == 'custom':
            scope_type = 'department'

        for sid in scope_ids or []:
            self.db.add(ResourceVisibilityScope(
                resource_id=resource.id,
                scope_type=scope_type,
                scope_id=int(sid),
            ))

    def _extract_media_file_ids(self, media_links: Optional[List[Any]]) -> List[int]:
        ids = []
        for item in media_links or []:
            payload = item.model_dump() if hasattr(item, 'model_dump') else dict(item)
            media_file_id = payload.get('media_file_id')
            if media_file_id:
                ids.append(media_file_id)
        return ids

    def _validate_media_file_ids(self, content_type: Optional[str], media_file_ids: List[int]):
        allowed_extensions = RESOURCE_CONTENT_FILE_EXTENSIONS.get(content_type or '')
        if not allowed_extensions:
            return

        unique_file_ids = set(media_file_ids or [])
        if not unique_file_ids:
            return

        file_map = {
            row.id: row.filename
            for row in self.db.query(MediaFile.id, MediaFile.filename).filter(MediaFile.id.in_(unique_file_ids)).all()
        }

        for file_id in unique_file_ids:
            filename = file_map.get(file_id)
            if not filename:
                raise ValueError(f'文件不存在: {file_id}')
            ext = os.path.splitext(filename)[1].lower()
            if ext not in allowed_extensions:
                allowed = ', '.join(sorted(allowed_extensions))
                raise ValueError(f'内容类型 {content_type} 仅允许文件类型: {allowed}')

    def _get_user_context(self, user_id: int) -> Dict[str, Set[int]]:
        user = self.db.query(User).options(
            selectinload(User.departments),
            selectinload(User.police_types),
            selectinload(User.roles),
        ).filter(User.id == user_id).first()

        if not user:
            return {
                'department_ids': set(),
                'police_type_ids': set(),
                'role_ids': set(),
            }

        return {
            'department_ids': {d.id for d in (user.departments or [])},
            'police_type_ids': {p.id for p in (user.police_types or [])},
            'role_ids': {r.id for r in (user.roles or [])},
        }

    def _can_edit_resource(self, resource: Resource, user_id: int, user_permissions: List[str]) -> bool:
        return (
            resource.uploader_id == user_id
            or 'UPDATE_RESOURCE' in (user_permissions or [])
            or 'VIEW_RESOURCE_ALL' in (user_permissions or [])
        )

    def _can_view_resource(
        self,
        resource: Resource,
        user_id: int,
        user_permissions: List[str],
        user_ctx: Optional[Dict[str, Set[int]]] = None,
    ) -> bool:
        perms = set(user_permissions or [])
        if 'VIEW_RESOURCE_ALL' in perms:
            return True

        if resource.uploader_id == user_id:
            return True

        task = self.db.query(ResourceReviewTask.id).filter(
            ResourceReviewTask.resource_id == resource.id,
            ResourceReviewTask.assignee_user_id == user_id,
            ResourceReviewTask.status == 'pending',
        ).first()
        if task:
            return True

        if resource.status != 'published':
            if 'VIEW_RESOURCE_DEPARTMENT' in perms:
                dept_ids = (user_ctx or {}).get('department_ids', set())
                return bool(resource.owner_department_id and resource.owner_department_id in dept_ids)
            return False

        return self._is_visible_by_scope(resource, user_id, user_ctx or self._get_user_context(user_id))

    def _is_visible_by_scope(self, resource: Resource, user_id: int, user_ctx: Dict[str, Set[int]]) -> bool:
        if resource.visibility_type == 'public':
            return True

        department_ids = user_ctx.get('department_ids', set())
        police_type_ids = user_ctx.get('police_type_ids', set())
        role_ids = user_ctx.get('role_ids', set())

        if resource.visibility_type == 'department':
            if resource.owner_department_id and resource.owner_department_id in department_ids:
                return True
            return any(s.scope_type == 'department' and s.scope_id in department_ids for s in (resource.visibility_scopes or []))

        if resource.visibility_type == 'police_type':
            return any(s.scope_type == 'police_type' and s.scope_id in police_type_ids for s in (resource.visibility_scopes or []))

        if resource.visibility_type == 'custom':
            for s in (resource.visibility_scopes or []):
                if s.scope_type == 'user' and s.scope_id == user_id:
                    return True
                if s.scope_type == 'department' and s.scope_id in department_ids:
                    return True
                if s.scope_type == 'police_type' and s.scope_id in police_type_ids:
                    return True
                if s.scope_type == 'role' and s.scope_id in role_ids:
                    return True
            return False

        return False

    def _build_media_url(self, media: Optional[MediaFile]) -> Optional[str]:
        if not media:
            return None
        base = (settings.MINIO_PUBLIC_URL or '').rstrip('/')
        bucket = (settings.MINIO_BUCKET or '').strip('/')
        path = (media.storage_path or '').lstrip('/')
        if base and bucket and path:
            return f'{base}/{bucket}/{path}'
        return f'{settings.API_V1_STR}/media/files/{media.id}'

    def _to_list_item_response(self, resource: Resource) -> ResourceListItemResponse:
        tags = [rel.tag.name for rel in (resource.tag_relations or []) if rel.tag]
        return ResourceListItemResponse(
            id=resource.id,
            title=resource.title,
            summary=resource.summary,
            content_type=self._normalize_content_type(resource.content_type),
            source_type=resource.source_type,
            status=resource.status,
            visibility_type=resource.visibility_type,
            uploader_id=resource.uploader_id,
            uploader_name=resource.uploader.nickname if resource.uploader else None,
            owner_department_id=resource.owner_department_id,
            owner_department_name=resource.owner_department.name if resource.owner_department else None,
            cover_media_file_id=resource.cover_media_file_id,
            cover_url=self._build_media_url(resource.cover_media),
            tags=tags,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
        )

    def _to_detail_response(self, resource: Resource) -> ResourceDetailResponse:
        base = self._to_list_item_response(resource)
        media_links = []
        for link in sorted((resource.media_links or []), key=lambda x: x.sort_order):
            media_links.append(ResourceMediaLinkResponse(
                id=link.id,
                media_file_id=link.media_file_id,
                media_role=link.media_role,
                sort_order=link.sort_order,
                file_url=self._build_media_url(link.media_file),
            ))

        return ResourceDetailResponse(
            **base.model_dump(),
            media_links=media_links,
            visibility_scopes=[s.scope_id for s in (resource.visibility_scopes or [])],
        )
