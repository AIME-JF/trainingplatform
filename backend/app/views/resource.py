"""
资源库路由
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, TokenData, PaginatedResponse
from app.schemas.resource import (
    ResourceCreate, ResourceUpdate, ResourceTagCreate, ResourceTagResponse,
    ResourceListItemResponse, ResourceDetailResponse,
    ResourceCommentCreate, ResourceCommentResponse,
)
from app.controllers.resource import ResourceController
from app.controllers.resource_comment import ResourceCommentController


router = APIRouter(prefix='/resources', tags=['resource_library'])


@router.get('', response_model=StandardResponse[PaginatedResponse[ResourceListItemResponse]], summary='资源列表')
def get_resources(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    search: Optional[str] = None,
    status: Optional[str] = None,
    content_type: Optional[str] = None,
    my_only: bool = False,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ResourceController(db)
    data = controller.get_resources(
        current_user_id=current_user.user_id,
        user_permissions=current_user.permissions,
        page=page,
        size=size,
        search=search,
        status_filter=status,
        content_type=content_type,
        my_only=my_only,
    )
    return StandardResponse(data=data)


@router.get('/tags', response_model=StandardResponse[List[ResourceTagResponse]], summary='资源标签列表')
def get_resource_tags(
    search: Optional[str] = Query(None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ResourceController(db)
    data = controller.list_resource_tags(search=search)
    return StandardResponse(data=data)


@router.post('/tags', response_model=StandardResponse[ResourceTagResponse], summary='创建资源标签')
def create_resource_tag(
    data: ResourceTagCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ResourceController(db)
    result = controller.create_resource_tag(data)
    return StandardResponse(data=result)


@router.post('', response_model=StandardResponse[ResourceDetailResponse], summary='创建资源')
def create_resource(
    data: ResourceCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if 'CREATE_RESOURCE' not in current_user.permissions and 'VIEW_RESOURCE_ALL' not in current_user.permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='无权限创建资源')
    controller = ResourceController(db)
    result = controller.create_resource(data, current_user.user_id)
    return StandardResponse(data=result)


@router.get('/{resource_id}/comments', response_model=StandardResponse[List[ResourceCommentResponse]], summary='资源评论列表')
def get_resource_comments(
    resource_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ResourceCommentController(db)
    result = controller.list_comments(resource_id, current_user.user_id, current_user.permissions)
    return StandardResponse(data=result)


@router.post('/{resource_id}/comments', response_model=StandardResponse[ResourceCommentResponse], summary='发表评论')
def create_resource_comment(
    resource_id: int,
    data: ResourceCommentCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ResourceCommentController(db)
    result = controller.create_comment(resource_id, current_user.user_id, current_user.permissions, data)
    return StandardResponse(data=result)


@router.delete('/{resource_id}/comments/{comment_id}', response_model=StandardResponse[dict], summary='删除资源评论')
def delete_resource_comment(
    resource_id: int,
    comment_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ResourceCommentController(db)
    result = controller.delete_comment(resource_id, comment_id, current_user.user_id, current_user.permissions)
    return StandardResponse(data=result)


@router.get('/{resource_id}', response_model=StandardResponse[ResourceDetailResponse], summary='资源详情')
def get_resource(
    resource_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ResourceController(db)
    result = controller.get_resource_by_id(resource_id, current_user.user_id, current_user.permissions)
    return StandardResponse(data=result)


@router.put('/{resource_id}', response_model=StandardResponse[ResourceDetailResponse], summary='更新资源')
def update_resource(
    resource_id: int,
    data: ResourceUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ResourceController(db)
    result = controller.update_resource(resource_id, data, current_user.user_id, current_user.permissions)
    return StandardResponse(data=result)


@router.post('/{resource_id}/publish', response_model=StandardResponse[ResourceDetailResponse], summary='发布资源')
def publish_resource(
    resource_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ResourceController(db)
    result = controller.publish_resource(resource_id, current_user.user_id, current_user.permissions)
    return StandardResponse(data=result)


@router.post('/{resource_id}/offline', response_model=StandardResponse[ResourceDetailResponse], summary='下线资源')
def offline_resource(
    resource_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ResourceController(db)
    result = controller.offline_resource(resource_id, current_user.user_id, current_user.permissions)
    return StandardResponse(data=result)


@router.delete('/{resource_id}', response_model=StandardResponse[dict], summary='Delete resource')
def delete_resource(
    resource_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ResourceController(db)
    result = controller.delete_resource(resource_id, current_user.user_id, current_user.permissions)
    return StandardResponse(data=result)


