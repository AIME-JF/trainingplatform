"""
资源评论服务
"""
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models import Resource, ResourceComment
from app.schemas.resource import ResourceCommentCreate, ResourceCommentResponse
from .resource import ResourceService


class ResourceCommentService:
    """资源评论服务"""

    def __init__(self, db: Session):
        self.db = db
        self.resource_service = ResourceService(db)

    def list_comments(
        self,
        resource_id: int,
        current_user_id: int,
        user_permissions: List[str],
    ) -> List[ResourceCommentResponse]:
        resource = self.resource_service.get_viewable_resource_entity(resource_id, current_user_id, user_permissions)
        if not resource:
            raise ValueError('资源不存在或无访问权限')

        comments = self.db.query(ResourceComment).options(
            joinedload(ResourceComment.user),
        ).filter(
            ResourceComment.resource_id == resource.id,
        ).order_by(
            ResourceComment.created_at.desc(),
            ResourceComment.id.desc(),
        ).all()

        return [
            self._to_comment_response(comment, resource, current_user_id, user_permissions)
            for comment in comments
        ]

    def create_comment(
        self,
        resource_id: int,
        current_user_id: int,
        user_permissions: List[str],
        data: ResourceCommentCreate,
    ) -> ResourceCommentResponse:
        resource = self.resource_service.get_viewable_resource_entity(resource_id, current_user_id, user_permissions)
        if not resource:
            raise ValueError('资源不存在或无访问权限')

        comment = ResourceComment(
            resource_id=resource.id,
            user_id=current_user_id,
            content=data.content,
        )
        self.db.add(comment)
        resource.comment_count = int(resource.comment_count or 0) + 1
        self.db.commit()
        self.db.refresh(comment)

        comment = self._get_comment_entity(comment.id)
        return self._to_comment_response(comment, resource, current_user_id, user_permissions)

    def delete_comment(
        self,
        resource_id: int,
        comment_id: int,
        current_user_id: int,
        user_permissions: List[str],
    ) -> bool:
        resource = self.db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            return False

        comment = self._get_comment_entity(comment_id)
        if not comment or comment.resource_id != resource_id:
            return False

        if not self._can_delete_comment(comment, resource, current_user_id, user_permissions):
            raise PermissionError('无权限删除该评论')

        self.db.delete(comment)
        resource.comment_count = max(int(resource.comment_count or 0) - 1, 0)
        self.db.commit()
        return True

    def _get_comment_entity(self, comment_id: int) -> Optional[ResourceComment]:
        return self.db.query(ResourceComment).options(
            joinedload(ResourceComment.user),
        ).filter(ResourceComment.id == comment_id).first()

    def _can_delete_comment(
        self,
        comment: ResourceComment,
        resource: Resource,
        current_user_id: int,
        user_permissions: List[str],
    ) -> bool:
        return (
            comment.user_id == current_user_id
            or self.resource_service.can_edit_resource(resource, current_user_id, user_permissions)
        )

    def _to_comment_response(
        self,
        comment: ResourceComment,
        resource: Resource,
        current_user_id: int,
        user_permissions: List[str],
    ) -> ResourceCommentResponse:
        return ResourceCommentResponse(
            id=comment.id,
            resource_id=comment.resource_id,
            user_id=comment.user_id,
            user_name=(comment.user.nickname or comment.user.username) if comment.user else None,
            content=comment.content,
            can_delete=self._can_delete_comment(comment, resource, current_user_id, user_permissions),
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )
