"""
培训管理路由
"""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Query, Body, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    StandardResponse, TokenData, PaginatedResponse,
    TrainingCreate, TrainingUpdate, TrainingResponse, TrainingListResponse,
    EnrollmentCreate, EnrollmentResponse,
    CheckinCreate, CheckinResponse, ScheduleItemResponse,
    TrainingResourceBindRequest, ResourceListItemResponse
)
from app.controllers import TrainingController
from app.services.training import TrainingService
from app.utils.authz import is_admin_user, is_instructor_user

router = APIRouter(prefix="/trainings", tags=["培训管理"])


def _require_admin(db: Session, user_id: int):
    if not is_admin_user(db, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可执行该操作")


def _require_admin_or_instructor(db: Session, user_id: int):
    if not (is_admin_user(db, user_id) or is_instructor_user(db, user_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员或教官可执行该操作")


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
    if data.courses is not None and not is_admin_user(db, current_user.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="调课权限仅限系统管理员")
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


@router.post("/{training_id}/start", response_model=StandardResponse[TrainingResponse], summary="手动开班")
def start_training(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = TrainingController(db)
    result = controller.start_training(training_id)
    return StandardResponse(data=result)


@router.post("/{training_id}/end", response_model=StandardResponse[TrainingResponse], summary="手动结班")
def end_training(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = TrainingController(db)
    result = controller.end_training(training_id)
    return StandardResponse(data=result)


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


@router.post("/{training_id}/import/students", response_model=StandardResponse, summary="批量导入学员并自动开户")
async def import_students(
    training_id: int,
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="导入文件为空")
    service = TrainingService(db)
    try:
        data = service.import_training_students(training_id, file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return StandardResponse(data=data)


@router.post("/{training_id}/import/instructors", response_model=StandardResponse, summary="批量导入教官")
async def import_instructors(
    training_id: int,
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="导入文件为空")
    service = TrainingService(db)
    try:
        data = service.import_training_instructors(training_id, file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return StandardResponse(data=data)


@router.post("/{training_id}/import/schedule", response_model=StandardResponse, summary="批量导入课表")
async def import_schedule(
    training_id: int,
    file: UploadFile = File(...),
    replace_existing: bool = Form(True),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="导入文件为空")
    service = TrainingService(db)
    try:
        data = service.import_training_schedule(training_id, file_bytes, replace_existing=replace_existing)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
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


@router.post("/{training_id}/resources", response_model=StandardResponse[ResourceListItemResponse], summary="培训绑定资源")
def add_training_resource(
    training_id: int,
    data: TrainingResourceBindRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = TrainingService(db)
    result = service.add_training_resource(training_id, data)
    return StandardResponse(data=result)


@router.get("/{training_id}/resources", response_model=StandardResponse[List[ResourceListItemResponse]], summary="培训资源列表")
def list_training_resources(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = TrainingService(db)
    result = service.list_training_resources(training_id)
    return StandardResponse(data=result)


@router.delete("/{training_id}/resources/{resource_id}", response_model=StandardResponse, summary="培训解绑资源")
def remove_training_resource(
    training_id: int,
    resource_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = TrainingService(db)
    ok = service.remove_training_resource(training_id, resource_id)
    if not ok:
        return StandardResponse(code=404, message="绑定关系不存在")
    return StandardResponse(message="解绑成功")
