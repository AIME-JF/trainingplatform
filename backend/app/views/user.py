"""
用户管理路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, PaginatedResponse, TokenData, UserSimpleResponse
from app.models import User, Role

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
