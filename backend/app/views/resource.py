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
    ResourceCreate, ResourceUpdate,
    ResourceListItemResponse, ResourceDetailResponse
)
from app.controllers.resource import ResourceController


router = APIRouter(prefix='/resources', tags=['资源库'])


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


