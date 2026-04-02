"""
权限管理路由
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers import PermissionController
from app.database import get_db
from app.middleware.auth import extract_permissions_from_routes, get_current_user
from app.schemas import (
    PaginatedResponse,
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
    StandardResponse,
    TokenData,
)


router = APIRouter(prefix="/permissions", tags=["permission_management"])


def _require_permission(current_user: TokenData, permission: str):
    if permission not in current_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"权限不足，需要权限: {permission}",
        )


@router.post("", response_model=StandardResponse[PermissionResponse], summary="创建权限")
@router.post("/create", response_model=StandardResponse[PermissionResponse], summary="创建权限")
def create_permission(
    data: PermissionCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "CREATE_PERMISSION")
    controller = PermissionController(db)
    result = controller.create_permission(data)
    return StandardResponse(message="创建权限成功", data=result)


@router.get("/{permission_id}/detail", response_model=StandardResponse[PermissionResponse], summary="权限详情")
def get_permission_detail(
    permission_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "GET_PERMISSION")
    controller = PermissionController(db)
    result = controller.get_permission_by_id(permission_id)
    return StandardResponse(message="获取权限成功", data=result)


@router.get("/list", response_model=StandardResponse[PaginatedResponse[PermissionResponse]], summary="权限列表")
def get_permission_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=-1, description="每页大小，-1 表示全部"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "GET_PERMISSIONS")
    controller = PermissionController(db)
    result = controller.get_permissions(page, size)
    return StandardResponse(message="获取权限列表成功", data=result)


@router.post("/{permission_id}/update", response_model=StandardResponse[PermissionResponse], summary="更新权限")
@router.put("/{permission_id}", response_model=StandardResponse[PermissionResponse], summary="更新权限")
def update_permission(
    permission_id: int,
    data: PermissionUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "UPDATE_PERMISSION")
    controller = PermissionController(db)
    result = controller.update_permission(permission_id, data)
    return StandardResponse(message="更新权限成功", data=result)


@router.post("/{permission_id}/delete", response_model=StandardResponse, summary="删除权限")
@router.delete("/{permission_id}", response_model=StandardResponse, summary="删除权限")
def delete_permission(
    permission_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "DELETE_PERMISSION")
    controller = PermissionController(db)
    controller.delete_permission(permission_id)
    return StandardResponse(message="删除权限成功")


@router.post("/sync", response_model=StandardResponse[List[PermissionResponse]], summary="同步权限")
def sync_permissions(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "SYNC_PERMISSIONS")
    from app import app as fastapi_app

    permissions_data = extract_permissions_from_routes(fastapi_app)
    controller = PermissionController(db)
    result = controller.sync_permissions(permissions_data)
    return StandardResponse(message="同步权限成功", data=result)


@router.get("/groups", summary="获取权限组列表")
def get_permission_groups(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.permission import PermissionGroup
    groups = db.query(PermissionGroup).filter(
        PermissionGroup.is_active == True
    ).order_by(PermissionGroup.sort_order).all()
    return StandardResponse(data=[
        {
            "id": g.id,
            "groupKey": g.group_key,
            "groupName": g.group_name,
            "description": g.description,
            "sortOrder": g.sort_order,
        }
        for g in groups
    ])
