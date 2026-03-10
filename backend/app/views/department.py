"""
部门管理路由
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers import DepartmentController
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    DepartmentCreate,
    DepartmentPermissionUpdate,
    DepartmentResponse,
    DepartmentSimpleResponse,
    DepartmentUpdate,
    PaginatedResponse,
    StandardResponse,
    TokenData,
)


router = APIRouter(prefix="/departments", tags=["部门管理"])


def _require_permission(current_user: TokenData, permission: str):
    if permission not in current_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"权限不足，需要权限: {permission}",
        )


@router.post("", response_model=StandardResponse[DepartmentSimpleResponse], summary="创建部门")
@router.post("/create", response_model=StandardResponse[DepartmentSimpleResponse], summary="创建部门")
def create_department(
    data: DepartmentCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "CREATE_DEPARTMENT")
    controller = DepartmentController(db)
    result = controller.create_department(data)
    return StandardResponse(message="创建部门成功", data=result)


@router.get("/{department_id}/detail", response_model=StandardResponse[DepartmentResponse], summary="部门详情")
def get_department_detail(
    department_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "GET_DEPARTMENT")
    controller = DepartmentController(db)
    result = controller.get_department_by_id(department_id)
    return StandardResponse(message="获取部门成功", data=result)


@router.get("/list", response_model=StandardResponse[PaginatedResponse[DepartmentSimpleResponse]], summary="部门列表")
def get_department_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=-1, description="每页大小，-1 表示全部"),
    parent_id: Optional[int] = Query(None, description="父部门 ID，-1 表示根部门"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "GET_DEPARTMENTS")
    controller = DepartmentController(db)
    result = controller.get_departments(page, size, parent_id)
    return StandardResponse(message="获取部门列表成功", data=result)


@router.get("/tree", response_model=StandardResponse[List[DepartmentResponse]], summary="部门树")
def get_department_tree(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "GET_DEPARTMENT_TREE")
    controller = DepartmentController(db)
    result = controller.get_department_tree()
    return StandardResponse(message="获取部门树成功", data=result)


@router.post("/{department_id}/update", response_model=StandardResponse[DepartmentSimpleResponse], summary="更新部门")
@router.put("/{department_id}", response_model=StandardResponse[DepartmentSimpleResponse], summary="更新部门")
def update_department(
    department_id: int,
    data: DepartmentUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "UPDATE_DEPARTMENT")
    controller = DepartmentController(db)
    result = controller.update_department(department_id, data)
    return StandardResponse(message="更新部门成功", data=result)


@router.post("/{department_id}/delete", response_model=StandardResponse, summary="删除部门")
@router.delete("/{department_id}", response_model=StandardResponse, summary="删除部门")
def delete_department(
    department_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "DELETE_DEPARTMENT")
    controller = DepartmentController(db)
    controller.delete_department(department_id)
    return StandardResponse(message="删除部门成功")


@router.post("/{department_id}/permissions", response_model=StandardResponse[DepartmentResponse], summary="更新部门权限")
def update_department_permissions(
    department_id: int,
    data: DepartmentPermissionUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "UPDATE_DEPARTMENT_PERMISSIONS")
    controller = DepartmentController(db)
    result = controller.update_department_permissions(department_id, data)
    return StandardResponse(message="更新部门权限成功", data=result)
