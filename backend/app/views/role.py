"""
角色管理路由
"""
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.controllers import RoleController
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    PaginatedResponse,
    RoleCreate,
    RolePermissionUpdate,
    RoleResponse,
    RoleSimpleResponse,
    RoleUpdate,
    StandardResponse,
    TokenData,
)
from app.services.system_exchange import SystemExchangeService


router = APIRouter(prefix="/roles", tags=["角色管理"])


def _excel_response(data: bytes, filename: str) -> StreamingResponse:
    return StreamingResponse(
        BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _require_permission(current_user: TokenData, permission: str):
    if permission not in current_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"权限不足，需要权限: {permission}",
        )


@router.post("", response_model=StandardResponse[RoleResponse], summary="创建角色")
@router.post("/create", response_model=StandardResponse[RoleResponse], summary="创建角色")
def create_role(
    data: RoleCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "CREATE_ROLE")
    controller = RoleController(db)
    result = controller.create_role(data)
    return StandardResponse(message="创建角色成功", data=result)


@router.get("/import/template", summary="下载角色导入模板")
def download_role_import_template(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "DOWNLOAD_ROLE_IMPORT_TEMPLATE")
    data = SystemExchangeService(db).build_role_template()
    return _excel_response(data, "role_import_template.xlsx")


@router.get("/export", summary="导出角色")
def export_roles_excel(
    name: Optional[str] = Query(None, description="角色名称"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "EXPORT_ROLES")
    data = SystemExchangeService(db).export_roles(name=name, is_active=is_active)
    return _excel_response(data, "roles_export.xlsx")


@router.post("/import", response_model=StandardResponse, summary="导入角色")
async def import_roles_excel(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "IMPORT_ROLES")
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="导入文件为空")

    service = SystemExchangeService(db)
    try:
        data = service.import_roles(file_bytes=file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return StandardResponse(data=data)


@router.get("/{role_id}/detail", response_model=StandardResponse[RoleResponse], summary="角色详情")
def get_role_detail(
    role_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "GET_ROLE")
    controller = RoleController(db)
    result = controller.get_role_by_id(role_id)
    return StandardResponse(message="获取角色成功", data=result)


@router.get("/list", response_model=StandardResponse[PaginatedResponse[RoleSimpleResponse]], summary="角色列表")
def get_role_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=-1, description="每页大小，-1 表示全部"),
    name: Optional[str] = Query(None, description="角色名称"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    order: int = Query(0, ge=0, le=1, description="排序：0 正序，1 倒序"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "GET_ROLES")
    controller = RoleController(db)
    result = controller.get_roles(page, size, name, is_active, order)
    return StandardResponse(message="获取角色列表成功", data=result)


@router.post("/{role_id}/update", response_model=StandardResponse[RoleResponse], summary="更新角色")
@router.put("/{role_id}", response_model=StandardResponse[RoleResponse], summary="更新角色")
def update_role(
    role_id: int,
    data: RoleUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "UPDATE_ROLE")
    controller = RoleController(db)
    result = controller.update_role(role_id, data)
    return StandardResponse(message="更新角色成功", data=result)


@router.post("/{role_id}/delete", response_model=StandardResponse, summary="删除角色")
@router.delete("/{role_id}", response_model=StandardResponse, summary="删除角色")
def delete_role(
    role_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "DELETE_ROLE")
    controller = RoleController(db)
    controller.delete_role(role_id)
    return StandardResponse(message="删除角色成功")


@router.post("/{role_id}/permissions", response_model=StandardResponse[RoleResponse], summary="更新角色权限")
def update_role_permissions(
    role_id: int,
    data: RolePermissionUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "UPDATE_ROLE_PERMISSIONS")
    controller = RoleController(db)
    result = controller.update_role_permissions(role_id, data)
    return StandardResponse(message="更新角色权限成功", data=result)
