"""
培训计划管理路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, TokenData, PaginatedResponse
from app.schemas.training_plan import TrainingPlanCreate, TrainingPlanUpdate, TrainingPlanResponse
from app.controllers.training_plan import TrainingPlanController

router = APIRouter(prefix="/training-plans", tags=["training_plan_management"])


@router.get("", response_model=StandardResponse[PaginatedResponse[TrainingPlanResponse]], summary="培训计划列表")
def get_training_plans(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    year: Optional[str] = None,
    search: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingPlanController(db)
    data = controller.get_list(page, size, year, search)
    return StandardResponse(data=data)


@router.get("/{plan_id}", response_model=StandardResponse[TrainingPlanResponse], summary="培训计划详情")
def get_training_plan(
    plan_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingPlanController(db)
    data = controller.get_by_id(plan_id)
    return StandardResponse(data=data)


@router.post("", response_model=StandardResponse[TrainingPlanResponse], summary="创建培训计划")
def create_training_plan(
    data: TrainingPlanCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingPlanController(db)
    result = controller.create(data, current_user.user_id)
    return StandardResponse(data=result)


@router.put("/{plan_id}", response_model=StandardResponse[TrainingPlanResponse], summary="更新培训计划")
def update_training_plan(
    plan_id: int,
    data: TrainingPlanUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingPlanController(db)
    result = controller.update(plan_id, data)
    return StandardResponse(data=result)


@router.delete("/{plan_id}", response_model=StandardResponse, summary="删除培训计划")
def delete_training_plan(
    plan_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingPlanController(db)
    controller.delete(plan_id)
    return StandardResponse(message="删除成功")
