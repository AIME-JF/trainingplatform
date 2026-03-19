"""
系统配置路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers import SystemConfigController
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    ConfigCreate,
    ConfigGroupCreate,
    ConfigGroupDetailResponse,
    ConfigGroupResponse,
    ConfigGroupUpdate,
    ConfigResponse,
    ConfigUpdate,
    PaginatedResponse,
    StandardResponse,
    TokenData,
)
from app.utils.authz import is_admin_user

router = APIRouter(prefix="/system", tags=["系统配置"])


def _require_admin(db: Session, user_id: int):
    if not is_admin_user(db, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可执行该操作")


@router.get(
    "/config-groups",
    response_model=StandardResponse[PaginatedResponse[ConfigGroupResponse]],
    summary="配置组列表",
)
def get_config_groups(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=-1, description="每页大小，-1 表示全部"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    data = controller.get_config_groups(page, size)
    return StandardResponse(data=data)


@router.post(
    "/config-groups",
    response_model=StandardResponse[ConfigGroupResponse],
    summary="创建配置组",
)
def create_config_group(
    data: ConfigGroupCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    result = controller.create_config_group(data)
    return StandardResponse(message="创建配置组成功", data=result)


@router.get(
    "/config-groups/{group_id}",
    response_model=StandardResponse[ConfigGroupDetailResponse],
    summary="配置组详情",
)
def get_config_group(
    group_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    result = controller.get_config_group_by_id(group_id)
    return StandardResponse(data=result)


@router.put(
    "/config-groups/{group_id}",
    response_model=StandardResponse[ConfigGroupResponse],
    summary="更新配置组",
)
def update_config_group(
    group_id: int,
    data: ConfigGroupUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    result = controller.update_config_group(group_id, data)
    return StandardResponse(message="更新配置组成功", data=result)


@router.delete(
    "/config-groups/{group_id}",
    response_model=StandardResponse,
    summary="删除配置组",
)
def delete_config_group(
    group_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    controller.delete_config_group(group_id)
    return StandardResponse(message="删除配置组成功")


@router.post(
    "/config-groups/{group_id}/reset",
    response_model=StandardResponse[ConfigGroupDetailResponse],
    summary="重置配置组",
)
def reset_config_group(
    group_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    result = controller.reset_config_group(group_id)
    return StandardResponse(message="重置配置组成功", data=result)


@router.get(
    "/configs",
    response_model=StandardResponse[PaginatedResponse[ConfigResponse]],
    summary="配置项列表",
)
def get_configs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=-1, description="每页大小，-1 表示全部"),
    group_id: Optional[int] = Query(None, description="配置组ID"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    data = controller.get_configs(page, size, group_id)
    return StandardResponse(data=data)


@router.post(
    "/configs",
    response_model=StandardResponse[ConfigResponse],
    summary="创建配置项",
)
def create_config(
    data: ConfigCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    result = controller.create_config(data)
    return StandardResponse(message="创建配置项成功", data=result)


@router.get(
    "/configs/{config_id}",
    response_model=StandardResponse[ConfigResponse],
    summary="配置项详情",
)
def get_config(
    config_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    result = controller.get_config_by_id(config_id)
    return StandardResponse(data=result)


@router.put(
    "/configs/{config_id}",
    response_model=StandardResponse[ConfigResponse],
    summary="更新配置项",
)
def update_config(
    config_id: int,
    data: ConfigUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    result = controller.update_config(config_id, data)
    return StandardResponse(message="更新配置项成功", data=result)


@router.delete(
    "/configs/{config_id}",
    response_model=StandardResponse,
    summary="删除配置项",
)
def delete_config(
    config_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    controller.delete_config(config_id)
    return StandardResponse(message="删除配置项成功")
