"""
培训班类型管理路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, TokenData, PaginatedResponse
from app.schemas.training_type import (
    TrainingTypeCreate, TrainingTypeUpdate, TrainingTypeResponse
)
from app.controllers.training_type import TrainingTypeController

router = APIRouter(prefix="/training-types", tags=["training_type_management"])


@router.get("", response_model=StandardResponse[PaginatedResponse[TrainingTypeResponse]], summary="培训班类型列表")
def get_training_types(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取培训班类型列表"""
    controller = TrainingTypeController(db)
    data = controller.get_training_types(page, size, name, is_active)
    return StandardResponse(data=data)


@router.post("", response_model=StandardResponse[TrainingTypeResponse], summary="创建培训班类型")
def create_training_type(
    data: TrainingTypeCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建培训班类型"""
    controller = TrainingTypeController(db)
    result = controller.create_training_type(data)
    return StandardResponse(data=result)


@router.get("/{training_type_id}", response_model=StandardResponse[TrainingTypeResponse], summary="培训班类型详情")
def get_training_type(
    training_type_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取培训班类型详情"""
    controller = TrainingTypeController(db)
    data = controller.get_training_type_by_id(training_type_id)
    return StandardResponse(data=data)


@router.put("/{training_type_id}", response_model=StandardResponse[TrainingTypeResponse], summary="更新培训班类型")
def update_training_type(
    training_type_id: int,
    data: TrainingTypeUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新培训班类型"""
    controller = TrainingTypeController(db)
    result = controller.update_training_type(training_type_id, data)
    return StandardResponse(data=result)


@router.delete("/{training_type_id}", response_model=StandardResponse, summary="删除培训班类型")
def delete_training_type(
    training_type_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除培训班类型"""
    controller = TrainingTypeController(db)
    controller.delete_training_type(training_type_id)
    return StandardResponse(message="删除成功")
