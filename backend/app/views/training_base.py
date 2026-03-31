"""
培训基地路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers.training_base import TrainingBaseController
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import PaginatedResponse, StandardResponse, TokenData
from app.schemas.training import TrainingBaseCreate, TrainingBaseResponse, TrainingBaseUpdate
from app.models import TrainingBase
from app.utils.authz import can_manage_training_base, can_view_training_base, is_admin_user, is_instructor_user

router = APIRouter(prefix="/training-bases", tags=["培训基地"])


def _require_admin_or_instructor(db: Session, user_id: int):
    if not (is_admin_user(db, user_id) or is_instructor_user(db, user_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员或教官可执行该操作")


def _require_admin(db: Session, user_id: int):
    if not is_admin_user(db, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可执行该操作")


@router.get("", response_model=StandardResponse[PaginatedResponse[TrainingBaseResponse]], summary="培训基地列表")
def get_training_bases(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = TrainingBaseController(db)
    data = controller.get_training_bases(page, size, search, department_id, current_user.user_id)
    return StandardResponse(data=data)


@router.get("/{training_base_id}", response_model=StandardResponse[TrainingBaseResponse], summary="培训基地详情")
def get_training_base(
    training_base_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    training_base = db.query(TrainingBase).filter(TrainingBase.id == training_base_id).first()
    if training_base and not can_view_training_base(db, training_base, current_user.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该培训基地")
    controller = TrainingBaseController(db)
    data = controller.get_training_base_by_id(training_base_id, current_user.user_id)
    return StandardResponse(data=data)


@router.post("", response_model=StandardResponse[TrainingBaseResponse], summary="创建培训基地")
def create_training_base(
    data: TrainingBaseCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = TrainingBaseController(db)
    result = controller.create_training_base(data, current_user.user_id)
    return StandardResponse(data=result)


@router.put("/{training_base_id}", response_model=StandardResponse[TrainingBaseResponse], summary="更新培训基地")
def update_training_base(
    training_base_id: int,
    data: TrainingBaseUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    training_base = db.query(TrainingBase).filter(TrainingBase.id == training_base_id).first()
    if training_base and not can_manage_training_base(db, training_base, current_user.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该培训基地")
    controller = TrainingBaseController(db)
    result = controller.update_training_base(training_base_id, data, current_user.user_id)
    return StandardResponse(data=result)


@router.delete("/{training_base_id}", response_model=StandardResponse, summary="删除培训基地")
def delete_training_base(
    training_base_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    training_base = db.query(TrainingBase).filter(TrainingBase.id == training_base_id).first()
    if training_base and not can_manage_training_base(db, training_base, current_user.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该培训基地")
    controller = TrainingBaseController(db)
    controller.delete_training_base(training_base_id)
    return StandardResponse(message="删除成功")
