"""
用户管理路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Body, UploadFile, File, Form, HTTPException, status
from fastapi.responses import StreamingResponse
from io import BytesIO
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, PaginatedResponse, TokenData, UserSimpleResponse, UserCreate, UserUpdate
from app.models import User, Role
from app.models.department import Department
from app.models.police_type import PoliceType
from app.services.auth import auth_service
from app.services.batch_import import BatchImportService
from app.services.system_exchange import SystemExchangeService
from app.utils.authz import can_access_user_record, can_access_user_record_with_context, is_admin_user
from app.utils.data_scope import (
    build_data_scope_context,
    can_assign_departments,
    can_assign_police_types,
)
from logger import logger

router = APIRouter(prefix="/users", tags=["用户管理"])


def _excel_response(data: bytes, filename: str) -> StreamingResponse:
    return StreamingResponse(
        BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _require_admin(db: Session, user_id: int):
    if not is_admin_user(db, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可执行该操作")


def _require_permission(current_user: TokenData, permission: str):
    if permission not in current_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"权限不足，需要权限: {permission}",
        )


def _is_protected_admin_user(user: User) -> bool:
    return str(user.username).lower() == "admin"


def _build_user_query(db: Session):
    return db.query(User).options(
        joinedload(User.roles),
        joinedload(User.departments),
        joinedload(User.police_types),
    )


def _get_scoped_user_or_403(db: Session, target_user_id: int, actor_user_id: int) -> User:
    user = _build_user_query(db).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if not can_access_user_record(db, user, actor_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该用户")
    return user


@router.get("", response_model=StandardResponse[PaginatedResponse[UserSimpleResponse]], summary="用户列表")
def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    role: Optional[str] = Query(None, description="按角色code筛选: admin/instructor/student"),
    search: Optional[str] = Query(None, description="搜索姓名/用户名/警号"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户列表，支持按角色和关键词筛选"""
    _require_permission(current_user, "GET_USERS")
    query = _build_user_query(db).filter(User.is_active == True)

    if role:
        query = query.filter(User.roles.any(Role.code == role))

    if search:
        query = query.filter(
            (User.nickname.ilike(f"%{search}%")) |
            (User.username.ilike(f"%{search}%")) |
            (User.police_id.ilike(f"%{search}%"))
        )

    records = query.order_by(User.id).all()
    scope_context = build_data_scope_context(db, current_user.user_id)
    records = [
        user
        for user in records
        if can_access_user_record_with_context(scope_context, user)
    ]
    total = len(records)
    if size != -1:
        skip = (page - 1) * size
        records = records[skip: skip + size]

    items = [UserSimpleResponse.model_validate(u) for u in records]

    return StandardResponse(data=PaginatedResponse(
        page=page,
        size=size if size != -1 else total,
        total=total,
        items=items
    ))


@router.get("/import/template", summary="下载用户导入模板")
def download_user_import_template(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "DOWNLOAD_USER_IMPORT_TEMPLATE")
    data = SystemExchangeService(db).build_user_template()
    return _excel_response(data, "user_import_template.xlsx")


@router.get("/export", summary="导出用户")
def export_users_excel(
    role: Optional[str] = Query(None, description="按角色 code 筛选"),
    search: Optional[str] = Query(None, description="搜索姓名/用户名/警号"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "EXPORT_USERS")
    data = SystemExchangeService(db).export_users(search=search, role_code=role)
    return _excel_response(data, "users_export.xlsx")


@router.post("/import", response_model=StandardResponse, summary="导入用户")
async def import_users_excel(
    file: UploadFile = File(...),
    default_role: str = Form("student"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "IMPORT_USERS")
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="导入文件为空")

    service = SystemExchangeService(db)
    try:
        data = service.import_users(file_bytes=file_bytes, default_role_code=default_role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return StandardResponse(data=data)


@router.post("/import/police-base", response_model=StandardResponse, summary="全员底库导入")
async def import_police_base(
    file: UploadFile = File(...),
    default_role: str = Form("student"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="导入文件为空")

    importer = BatchImportService(db)
    try:
        data = importer.import_police_base(file_bytes=file_bytes, default_role_code=default_role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return StandardResponse(data=data)


@router.get("/{user_id}", response_model=StandardResponse[UserSimpleResponse], summary="用户详情")
def get_user(
    user_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户详情"""
    _require_permission(current_user, "GET_USER")
    user = _get_scoped_user_or_403(db, user_id, current_user.user_id)
    return StandardResponse(data=UserSimpleResponse.model_validate(user))


@router.post("", response_model=StandardResponse[UserSimpleResponse], summary="创建用户")
def create_user(
    data: UserCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建用户"""
    _require_permission(current_user, "CREATE_USER")
    scope_context = build_data_scope_context(db, current_user.user_id)
    if not can_assign_departments(scope_context, data.department_ids or []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="超出当前角色可操作的部门范围")
    if not can_assign_police_types(scope_context, data.police_type_ids or []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="超出当前角色可操作的警种范围")
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        return StandardResponse(code=400, message="用户名已存在")

    user = User(
        username=data.username,
        password_hash=auth_service.get_password_hash(data.password),
        nickname=data.nickname,
        gender=data.gender,
        email=data.email,
        phone=data.phone,
        police_id=data.police_id,
        avatar=data.avatar,
        join_date=data.join_date,
        level=data.level,
        instructor_title=data.instructor_title,
        instructor_level=data.instructor_level,
        instructor_specialties=data.instructor_specialties,
        instructor_qualification=data.instructor_qualification,
        instructor_certificates=data.instructor_certificates,
        instructor_intro=data.instructor_intro,
        instructor_rating=data.instructor_rating if data.instructor_rating is not None else 0,
        instructor_course_count=data.instructor_course_count if data.instructor_course_count is not None else 0,
        instructor_student_count=data.instructor_student_count if data.instructor_student_count is not None else 0,
        instructor_review_count=data.instructor_review_count if data.instructor_review_count is not None else 0,
        is_active=True,
    )

    if data.role_ids:
        roles = db.query(Role).filter(Role.id.in_(data.role_ids)).all()
        user.roles = roles

    if data.department_ids:
        departments = db.query(Department).filter(Department.id.in_(data.department_ids)).all()
        user.departments = departments

    if data.police_type_ids:
        police_types = db.query(PoliceType).filter(PoliceType.id.in_(data.police_type_ids)).all()
        user.police_types = police_types

    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"创建用户: {data.username}")
    return StandardResponse(data=UserSimpleResponse.model_validate(user))


@router.put("/{user_id}", response_model=StandardResponse[UserSimpleResponse], summary="更新用户")
def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户"""
    _require_permission(current_user, "UPDATE_USER")
    user = _get_scoped_user_or_403(db, user_id, current_user.user_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    logger.info(f"更新用户: {user.username}")
    return StandardResponse(data=UserSimpleResponse.model_validate(user))


@router.put("/{user_id}/roles", response_model=StandardResponse[UserSimpleResponse], summary="更新用户角色")
def update_user_roles(
    user_id: int,
    role_ids: list[int] = Body(..., embed=True),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户角色"""
    _require_permission(current_user, "UPDATE_USER_ROLES")
    user = _get_scoped_user_or_403(db, user_id, current_user.user_id)
    if _is_protected_admin_user(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="管理员用户权限不可修改")

    roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
    user.roles = roles
    db.commit()
    db.refresh(user)
    logger.info(f"更新用户角色: {user.username}")
    return StandardResponse(data=UserSimpleResponse.model_validate(user))


@router.put("/{user_id}/departments", response_model=StandardResponse[UserSimpleResponse], summary="更新用户所属单位")
def update_user_departments(
    user_id: int,
    department_ids: list[int] = Body(..., embed=True),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户所属单位"""
    _require_permission(current_user, "UPDATE_USER_DEPARTMENTS")
    user = _get_scoped_user_or_403(db, user_id, current_user.user_id)
    scope_context = build_data_scope_context(db, current_user.user_id)
    if not can_assign_departments(scope_context, department_ids):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="超出当前角色可操作的部门范围")

    departments = db.query(Department).filter(Department.id.in_(department_ids)).all()
    user.departments = departments
    db.commit()
    db.refresh(user)
    logger.info(f"更新用户所属单位: {user.username}")
    return StandardResponse(data=UserSimpleResponse.model_validate(user))


@router.put("/{user_id}/police-types", response_model=StandardResponse[UserSimpleResponse], summary="更新用户警种")
def update_user_police_types(
    user_id: int,
    police_type_ids: list[int] = Body(..., embed=True),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户警种"""
    _require_permission(current_user, "UPDATE_USER_POLICE_TYPES")
    user = _get_scoped_user_or_403(db, user_id, current_user.user_id)
    scope_context = build_data_scope_context(db, current_user.user_id)
    if not can_assign_police_types(scope_context, police_type_ids):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="超出当前角色可操作的警种范围")

    police_types = db.query(PoliceType).filter(PoliceType.id.in_(police_type_ids)).all()
    user.police_types = police_types
    db.commit()
    db.refresh(user)
    logger.info(f"更新用户警种: {user.username}")
    return StandardResponse(data=UserSimpleResponse.model_validate(user))


@router.put("/{user_id}/password", response_model=StandardResponse, summary="重置密码")
def reset_password(
    user_id: int,
    password: str = Body(..., embed=True),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重置用户密码"""
    _require_permission(current_user, "UPDATE_USER")
    user = _get_scoped_user_or_403(db, user_id, current_user.user_id)

    user.password_hash = auth_service.get_password_hash(password)
    db.commit()
    logger.info(f"重置用户密码: {user.username}")
    return StandardResponse(message="密码重置成功")


@router.delete("/{user_id}", response_model=StandardResponse, summary="删除用户")
def delete_user(
    user_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除用户（软删除）"""
    _require_permission(current_user, "DELETE_USER")
    user = _get_scoped_user_or_403(db, user_id, current_user.user_id)

    user.is_active = False
    db.commit()
    logger.info(f"删除用户: {user.username}")
    return StandardResponse(message="删除成功")
