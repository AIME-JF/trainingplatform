"""
培训管理路由
"""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    StandardResponse, TokenData, PaginatedResponse,
    TrainingCreate, TrainingUpdate, TrainingResponse, TrainingListResponse,
    EnrollmentCreate, EnrollmentResponse,
    CheckinCreate, CheckinResponse, ScheduleItemResponse
)
from app.controllers import TrainingController

router = APIRouter(prefix="/trainings", tags=["培训管理"])


@router.get("", response_model=StandardResponse[PaginatedResponse[TrainingListResponse]], summary="培训列表")
def get_trainings(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    status: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取培训列表"""
    controller = TrainingController(db)
    data = controller.get_trainings(page, size, status, type, search)
    return StandardResponse(data=data)


@router.post("", response_model=StandardResponse[TrainingResponse], summary="创建培训班")
def create_training(
    data: TrainingCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建培训班"""
    controller = TrainingController(db)
    result = controller.create_training(data, current_user.user_id)
    return StandardResponse(data=result)


@router.get("/{training_id}", response_model=StandardResponse[TrainingResponse], summary="培训详情")
def get_training(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取培训详情"""
    controller = TrainingController(db)
    data = controller.get_training_by_id(training_id)
    return StandardResponse(data=data)


@router.put("/{training_id}", response_model=StandardResponse[TrainingResponse], summary="更新培训班")
def update_training(
    training_id: int,
    data: TrainingUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新培训班"""
    controller = TrainingController(db)
    result = controller.update_training(training_id, data)
    return StandardResponse(data=result)


@router.delete("/{training_id}", response_model=StandardResponse, summary="删除培训班")
def delete_training(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除培训班"""
    controller = TrainingController(db)
    controller.delete_training(training_id)
    return StandardResponse(message="删除成功")


@router.get("/{training_id}/students",
            response_model=StandardResponse[PaginatedResponse[EnrollmentResponse]], summary="学员列表")
def get_students(
    training_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取培训学员列表"""
    controller = TrainingController(db)
    data = controller.get_training_students(training_id, page, size)
    return StandardResponse(data=data)


@router.get("/{training_id}/schedule",
            response_model=StandardResponse[List[ScheduleItemResponse]], summary="周计划")
def get_schedule(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取周计划"""
    controller = TrainingController(db)
    data = controller.get_schedule(training_id)
    return StandardResponse(data=data)


@router.post("/{training_id}/enroll",
             response_model=StandardResponse[EnrollmentResponse], summary="学员报名")
def enroll(
    training_id: int,
    data: EnrollmentCreate = Body(default=EnrollmentCreate()),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """学员报名"""
    controller = TrainingController(db)
    result = controller.enroll(training_id, current_user.user_id, data)
    return StandardResponse(data=result)


@router.get("/{training_id}/enrollments",
            response_model=StandardResponse[PaginatedResponse[EnrollmentResponse]], summary="报名列表")
def get_enrollments(
    training_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取报名列表"""
    controller = TrainingController(db)
    data = controller.get_enrollments(training_id, page, size)
    return StandardResponse(data=data)


@router.put("/{training_id}/enrollments/{eid}/approve",
            response_model=StandardResponse[EnrollmentResponse], summary="审批通过")
def approve_enrollment(
    training_id: int,
    eid: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """审批通过"""
    controller = TrainingController(db)
    result = controller.approve_enrollment(training_id, eid)
    return StandardResponse(data=result)


@router.put("/{training_id}/enrollments/{eid}/reject",
            response_model=StandardResponse[EnrollmentResponse], summary="审批拒绝")
def reject_enrollment(
    training_id: int,
    eid: int,
    note: Optional[str] = Body(None, embed=True),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """审批拒绝"""
    controller = TrainingController(db)
    result = controller.reject_enrollment(training_id, eid, note)
    return StandardResponse(data=result)


@router.get("/{training_id}/checkin/records",
            response_model=StandardResponse[List[CheckinResponse]], summary="签到记录")
def get_checkin_records(
    training_id: int,
    date: Optional[date] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取签到记录"""
    controller = TrainingController(db)
    data = controller.get_checkin_records(training_id, date)
    return StandardResponse(data=data)


@router.post("/{training_id}/checkin",
             response_model=StandardResponse[CheckinResponse], summary="签到")
def checkin(
    training_id: int,
    data: CheckinCreate = Body(default=CheckinCreate()),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """签到"""
    controller = TrainingController(db)
    result = controller.checkin(training_id, current_user.user_id, data)
    return StandardResponse(data=result)


@router.get("/{training_id}/checkin/qr",
            response_model=StandardResponse, summary="生成签到二维码")
def get_checkin_qr(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成签到二维码"""
    controller = TrainingController(db)
    data = controller.generate_checkin_qr(training_id)
    return StandardResponse(data=data)
