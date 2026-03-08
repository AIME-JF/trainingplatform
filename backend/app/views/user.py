"""
用户管理路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, PaginatedResponse, TokenData, UserSimpleResponse, UserCreate, UserUpdate
from app.schemas.role import RoleSimpleResponse
from app.schemas.department import DepartmentSimpleResponse
from app.models import User, Role
from app.models.department import Department
from app.models.police_type import PoliceType
from app.services.auth import auth_service
from logger import logger

router = APIRouter(prefix="/users", tags=["用户管理"])


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
    query = db.query(User).filter(User.is_active == True)

    if role:
        query = query.filter(User.roles.any(Role.code == role))

    if search:
        query = query.filter(
            (User.nickname.ilike(f"%{search}%")) |
            (User.username.ilike(f"%{search}%")) |
            (User.police_id.ilike(f"%{search}%"))
        )

    total = query.count()
    query = query.order_by(User.id)

    if size == -1:
        records = query.all()
    else:
        skip = (page - 1) * size
        records = query.offset(skip).limit(size).all()

    items = [UserSimpleResponse.model_validate(u) for u in records]

    return StandardResponse(data=PaginatedResponse(
        page=page,
        size=size if size != -1 else total,
        total=total,
        items=items
    ))


@router.get("/{user_id}", response_model=StandardResponse[UserSimpleResponse], summary="用户详情")
def get_user(
    user_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户详情"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return StandardResponse(code=404, message="用户不存在")
    return StandardResponse(data=UserSimpleResponse.model_validate(user))


@router.post("", response_model=StandardResponse[UserSimpleResponse], summary="创建用户")
def create_user(
    data: UserCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建用户"""
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
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return StandardResponse(code=404, message="用户不存在")

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
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return StandardResponse(code=404, message="用户不存在")

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
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return StandardResponse(code=404, message="用户不存在")

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
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return StandardResponse(code=404, message="用户不存在")

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
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return StandardResponse(code=404, message="用户不存在")

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
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return StandardResponse(code=404, message="用户不存在")

    user.is_active = False
    db.commit()
    logger.info(f"删除用户: {user.username}")
    return StandardResponse(message="删除成功")


roles_router = APIRouter(prefix="/roles", tags=["角色管理"])


@roles_router.get("", response_model=StandardResponse[list[RoleSimpleResponse]], summary="角色列表")
def get_roles(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有角色"""
    roles = db.query(Role).filter(Role.is_active == True).all()
    items = [RoleSimpleResponse.model_validate(r) for r in roles]
    return StandardResponse(data=items)


# 部门列表路由
departments_router = APIRouter(prefix="/departments", tags=["部门管理"])


@departments_router.get("", response_model=StandardResponse[List[DepartmentSimpleResponse]], summary="部门列表")
def get_departments(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有激活的部门列表"""
    depts = db.query(Department).filter(Department.is_active == True).order_by(Department.id).all()
    items = [DepartmentSimpleResponse.model_validate(d) for d in depts]
    return StandardResponse(data=items)


@departments_router.post("", response_model=StandardResponse[DepartmentSimpleResponse], summary="新建部门")
def create_department(
    name: str = Body(..., embed=True),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """快速创建新部门（名称不能重复）"""
    name = name.strip()
    if not name:
        return StandardResponse(code=400, message="部门名称不能为空")
    existing = db.query(Department).filter(Department.name == name).first()
    if existing:
        return StandardResponse(data=DepartmentSimpleResponse.model_validate(existing))
    # 生成唯一 code：用名称拼音首字母 + id，这里简单用时间戳
    import time
    code = f"dept_{int(time.time() * 1000) % 10**9}"
    dept = Department(name=name, code=code, is_active=True)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    logger.info(f"新建部门: {name}")
    return StandardResponse(data=DepartmentSimpleResponse.model_validate(dept))
