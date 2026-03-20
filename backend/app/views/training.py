"""
培训管理路由
"""
from datetime import date
from io import BytesIO
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.controllers import TrainingController
from app.database import get_db
from app.middleware.auth import get_current_user, get_current_user_optional
from app.models import Permission, Role, Training, User
from app.schemas import (
    CheckinCreate,
    CheckinResponse,
    CheckoutCreate,
    EnrollmentCreate,
    EnrollmentResponse,
    PaginatedResponse,
    ResourceListItemResponse,
    ScheduleItemResponse,
    StandardResponse,
    TokenData,
    TrainingAttendanceSummaryResponse,
    TrainingCheckinQrResponse,
    TrainingCreate,
    TrainingCourseChangeLogResponse,
    TrainingEvaluationCreate,
    TrainingHistoryResponse,
    TrainingListResponse,
    TrainingStatsResponse,
    TrainingResourceBindRequest,
    TrainingResponse,
    TrainingRosterAssignment,
    TrainingSkipCourseRequest,
    TrainingUpdate,
    TrainingWorkflowActionRequest,
)
from app.services.training import TrainingService
from app.utils.authz import can_manage_training, can_update_training, can_view_training, is_admin_user, is_instructor_user

router = APIRouter(prefix="/trainings", tags=["培训管理"])


def _excel_response(data: bytes, filename: str) -> StreamingResponse:
    return StreamingResponse(
        BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _require_admin(db: Session, user_id: int):
    if not is_admin_user(db, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可执行该操作")


def _require_admin_or_instructor(db: Session, user_id: int):
    if not (is_admin_user(db, user_id) or is_instructor_user(db, user_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员或教官可执行该操作")


def _require_permission(db: Session, current_user: TokenData, permission: str):
    if _has_permission(db, current_user, permission):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"权限不足，需要权限: {permission}",
    )


def _has_permission(db: Session, current_user: TokenData, permission: str) -> bool:
    if permission in current_user.permissions:
        return True
    has_permission = db.query(User.id).join(User.roles).join(Role.permissions).filter(
        User.id == current_user.user_id,
        User.is_active == True,
        Permission.code == permission,
    ).first()
    return bool(has_permission)


def _get_training_or_404(db: Session, training_id: int) -> Training:
    training = db.query(Training).filter(Training.id == training_id).first()
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="培训班不存在")
    return training


def _require_training_manager(db: Session, training_id: int, user_id: int):
    training = _get_training_or_404(db, training_id)
    if not can_manage_training(db, training, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该培训班")
    return training


def _require_training_updater(db: Session, training_id: int, user_id: int):
    training = _get_training_or_404(db, training_id)
    if not can_update_training(db, training, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅当前培训班班主任可更新")
    return training


def _require_training_viewer(db: Session, training_id: int, user_id: int):
    training = _get_training_or_404(db, training_id)
    if not can_view_training(db, training, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该培训班")
    return training


def _require_self_or_manager(db: Session, training_id: int, actor_id: int, target_user_id: Optional[int]):
    if target_user_id is None or target_user_id == actor_id:
        return
    _require_training_manager(db, training_id, actor_id)


def _require_training_course_change_log_viewer(db: Session, training_id: int, current_user: TokenData):
    training = _get_training_or_404(db, training_id)
    if can_update_training(db, training, current_user.user_id):
        return training
    if _has_permission(db, current_user, "MANAGE_TRAINING") and can_manage_training(db, training, current_user.user_id):
        return training
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看课程变更记录")


@router.get("/histories/me", response_model=StandardResponse[List[TrainingHistoryResponse]], summary="我的训历")
def get_my_training_histories(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    data = controller.get_user_training_histories(current_user.user_id)
    return StandardResponse(data=data)


@router.get("", response_model=StandardResponse[PaginatedResponse[TrainingListResponse]], summary="培训列表")
def get_trainings(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    status: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    data = controller.get_trainings(page, size, status, type, search, current_user.user_id)
    return StandardResponse(data=data)


@router.get("/stats", response_model=StandardResponse[TrainingStatsResponse], summary="培训统计")
def get_training_stats(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    data = controller.get_training_stats(current_user.user_id)
    return StandardResponse(data=data)


@router.get("/checkin/qr/{token}", response_model=StandardResponse[TrainingCheckinQrResponse], summary="扫码签到信息")
def get_checkin_qr_payload(
    token: str,
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    data = controller.get_checkin_qr_payload(token)
    return StandardResponse(data=data)


@router.post("/checkin/qr/{token}", response_model=StandardResponse[CheckinResponse], summary="扫码签到")
def checkin_by_qr(
    token: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    result = controller.checkin_by_qr(token, current_user.user_id)
    return StandardResponse(data=result)


@router.post("", response_model=StandardResponse[TrainingResponse], summary="创建培训班")
def create_training(
    data: TrainingCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = TrainingController(db)
    result = controller.create_training(data, current_user.user_id)
    return StandardResponse(data=result)


@router.get("/{training_id}", response_model=StandardResponse[TrainingResponse], summary="培训详情")
def get_training(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_viewer(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    data = controller.get_training_by_id(training_id, current_user.user_id)
    return StandardResponse(data=data)


@router.put("/{training_id}", response_model=StandardResponse[TrainingResponse], summary="更新培训班")
def update_training(
    training_id: int,
    data: TrainingUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user, "UPDATE_TRAINING")
    _require_training_updater(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    result = controller.update_training(training_id, data, current_user.user_id)
    return StandardResponse(data=result)


@router.put("/{training_id}/manage", response_model=StandardResponse[TrainingResponse], summary="管理端更新培训班")
def manage_training(
    training_id: int,
    data: TrainingUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user, "MANAGE_TRAINING")
    _require_training_manager(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    result = controller.manage_training(training_id, data, current_user.user_id)
    return StandardResponse(data=result)


@router.delete("/{training_id}", response_model=StandardResponse, summary="删除培训班")
def delete_training(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = TrainingController(db)
    controller.delete_training(training_id)
    return StandardResponse(message="删除成功")


@router.post("/{training_id}/publish", response_model=StandardResponse[TrainingResponse], summary="发布培训班")
def publish_training(
    training_id: int,
    data: Optional[TrainingWorkflowActionRequest] = Body(default=None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    result = controller.publish_training(training_id, current_user.user_id, data)
    return StandardResponse(data=result)


@router.post("/{training_id}/lock", response_model=StandardResponse[TrainingResponse], summary="锁定名单")
def lock_training(
    training_id: int,
    data: Optional[TrainingWorkflowActionRequest] = Body(default=None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    result = controller.lock_training(training_id, current_user.user_id, data)
    return StandardResponse(data=result)


@router.post("/{training_id}/start", response_model=StandardResponse[TrainingResponse], summary="手动开班")
def start_training(
    training_id: int,
    data: Optional[TrainingWorkflowActionRequest] = Body(default=None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    result = controller.start_training(training_id, current_user.user_id, data)
    return StandardResponse(data=result)


@router.post("/{training_id}/end", response_model=StandardResponse[TrainingResponse], summary="手动结班")
def end_training(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    result = controller.end_training(training_id, current_user.user_id)
    return StandardResponse(data=result)


@router.get("/{training_id}/students", response_model=StandardResponse[PaginatedResponse[EnrollmentResponse]], summary="学员列表")
def get_students(
    training_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    data = controller.get_training_students(training_id, page, size)
    return StandardResponse(data=data)


@router.get("/{training_id}/schedule", response_model=StandardResponse[List[ScheduleItemResponse]], summary="周计划")
def get_schedule(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_viewer(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    data = controller.get_schedule(training_id)
    return StandardResponse(data=data)


@router.get("/import/students/template", summary="下载培训班学员导入模板")
def download_training_student_import_template(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user, "CREATE_TRAINING")
    _require_admin_or_instructor(db, current_user.user_id)
    data = TrainingService(db).build_training_student_import_template()
    return _excel_response(data, "training_students_import_template.xlsx")


@router.get("/{training_id}/import/students/template", summary="下载培训班学员导入模板")
def download_training_student_import_template_for_training(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    data = TrainingService(db).build_training_student_import_template()
    return _excel_response(data, "training_students_import_template.xlsx")


@router.get("/{training_id}/import/instructors/template", summary="下载培训班教官导入模板")
def download_training_instructor_import_template(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    data = TrainingService(db).build_training_instructor_import_template()
    return _excel_response(data, "training_instructors_import_template.xlsx")


@router.get("/{training_id}/import/courses/template", summary="下载培训班课程导入模板")
def download_training_course_import_template(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    data = TrainingService(db).build_training_course_import_template()
    return _excel_response(data, "training_courses_import_template.xlsx")


@router.get("/{training_id}/import/sessions/template", summary="下载培训班课次导入模板")
def download_training_session_import_template(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    data = TrainingService(db).build_training_session_import_template()
    return _excel_response(data, "training_sessions_import_template.xlsx")


@router.get("/{training_id}/import/schedule/template", summary="下载培训班课次导入模板")
def download_training_schedule_import_template(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return download_training_session_import_template(training_id, current_user, db)


@router.post("/{training_id}/import/students", response_model=StandardResponse, summary="批量导入学员并自动开户")
async def import_students(
    training_id: int,
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
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
    _require_training_manager(db, training_id, current_user.user_id)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="导入文件为空")
    service = TrainingService(db)
    try:
        data = service.import_training_instructors(training_id, file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return StandardResponse(data=data)


@router.post("/{training_id}/import/courses", response_model=StandardResponse, summary="批量导入课程")
async def import_courses(
    training_id: int,
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="导入文件为空")
    service = TrainingService(db)
    try:
        data = service.import_training_courses(
            training_id,
            file_bytes,
            actor_id=current_user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return StandardResponse(data=data)


@router.post("/{training_id}/import/sessions", response_model=StandardResponse, summary="批量导入课次")
async def import_sessions(
    training_id: int,
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="导入文件为空")
    service = TrainingService(db)
    try:
        data = service.import_training_sessions(
            training_id,
            file_bytes,
            actor_id=current_user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return StandardResponse(data=data)


@router.post("/{training_id}/import/schedule", response_model=StandardResponse, summary="批量导入课次")
async def import_schedule(
    training_id: int,
    file: UploadFile = File(...),
    replace_existing: bool = Form(True),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await import_sessions(training_id, file, current_user, db)


@router.post("/{training_id}/enroll", response_model=StandardResponse[EnrollmentResponse], summary="学员报名")
def enroll(
    training_id: int,
    data: Optional[EnrollmentCreate] = Body(default=None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_viewer(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    result = controller.enroll(training_id, current_user.user_id, data or EnrollmentCreate())
    return StandardResponse(data=result)


@router.get("/{training_id}/enrollments", response_model=StandardResponse[PaginatedResponse[EnrollmentResponse]], summary="报名列表")
def get_enrollments(
    training_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    manager_mode = can_manage_training(db, _get_training_or_404(db, training_id), current_user.user_id)
    data = controller.get_enrollments(
        training_id,
        page,
        size,
        None if manager_mode else current_user.user_id,
    )
    return StandardResponse(data=data)


@router.put("/{training_id}/enrollments/{eid}/approve", response_model=StandardResponse[EnrollmentResponse], summary="审批通过")
def approve_enrollment(
    training_id: int,
    eid: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    result = controller.approve_enrollment(training_id, eid, current_user.user_id)
    return StandardResponse(data=result)


@router.put("/{training_id}/enrollments/{eid}/reject", response_model=StandardResponse[EnrollmentResponse], summary="审批拒绝")
def reject_enrollment(
    training_id: int,
    eid: int,
    note: Optional[str] = Body(None, embed=True),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    result = controller.reject_enrollment(training_id, eid, note, current_user.user_id)
    return StandardResponse(data=result)


@router.put("/{training_id}/roster", response_model=StandardResponse[List[EnrollmentResponse]], summary="更新编组与班干部")
def update_roster_assignments(
    training_id: int,
    assignments: List[TrainingRosterAssignment],
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    result = controller.update_roster_assignments(training_id, assignments)
    return StandardResponse(data=result)


@router.get("/{training_id}/checkin/records", response_model=StandardResponse[List[CheckinResponse]], summary="签到记录")
def get_checkin_records(
    training_id: int,
    date: Optional[date] = None,
    session_key: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    manager_mode = can_manage_training(db, _get_training_or_404(db, training_id), current_user.user_id)
    session_operator_mode = bool(session_key) and TrainingService(db).can_user_operate_session(training_id, session_key, current_user.user_id)
    data = controller.get_checkin_records(
        training_id,
        date,
        session_key,
        None if (manager_mode or session_operator_mode) else current_user.user_id,
    )
    return StandardResponse(data=data)


@router.get("/{training_id}/attendance/summary", response_model=StandardResponse[TrainingAttendanceSummaryResponse], summary="签到统计")
def get_attendance_summary(
    training_id: int,
    session_key: str = Query(...),
    date: Optional[date] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TrainingService(db)
    if not (
        can_manage_training(db, _get_training_or_404(db, training_id), current_user.user_id)
        or service.can_user_operate_session(training_id, session_key, current_user.user_id)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员、班主任或当前课次授课教官可查看")
    controller = TrainingController(db)
    data = controller.get_attendance_summary(training_id, session_key, date)
    return StandardResponse(data=data)


@router.post("/{training_id}/sessions/{session_key}/checkin/start", response_model=StandardResponse[TrainingResponse], summary="开始课次签到")
def start_session_checkin(
    training_id: int,
    session_key: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    result = controller.start_session_checkin(training_id, session_key, current_user.user_id)
    return StandardResponse(data=result)


@router.post("/{training_id}/sessions/{session_key}/checkin/end", response_model=StandardResponse[TrainingResponse], summary="结束课次签到")
def end_session_checkin(
    training_id: int,
    session_key: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    result = controller.end_session_checkin(training_id, session_key, current_user.user_id)
    return StandardResponse(data=result)


@router.post("/{training_id}/sessions/{session_key}/checkout/start", response_model=StandardResponse[TrainingResponse], summary="开始课次签退")
def start_session_checkout(
    training_id: int,
    session_key: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    result = controller.start_session_checkout(training_id, session_key, current_user.user_id)
    return StandardResponse(data=result)


@router.post("/{training_id}/sessions/{session_key}/checkout/end", response_model=StandardResponse[TrainingResponse], summary="结束课次签退")
def end_session_checkout(
    training_id: int,
    session_key: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    result = controller.end_session_checkout(training_id, session_key, current_user.user_id)
    return StandardResponse(data=result)


@router.post("/{training_id}/sessions/{session_key}/skip", response_model=StandardResponse[TrainingResponse], summary="跳过课次")
def skip_session(
    training_id: int,
    session_key: str,
    data: Optional[TrainingSkipCourseRequest] = Body(default=None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    result = controller.skip_session(training_id, session_key, current_user.user_id, data)
    return StandardResponse(data=result)


@router.post("/{training_id}/checkin", response_model=StandardResponse[CheckinResponse], summary="签到")
def checkin(
    training_id: int,
    data: Optional[CheckinCreate] = Body(default=None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payload = data or CheckinCreate()
    _require_self_or_manager(db, training_id, current_user.user_id, payload.user_id)
    controller = TrainingController(db)
    result = controller.checkin(training_id, current_user.user_id, payload)
    return StandardResponse(data=result)


@router.post("/{training_id}/checkout", response_model=StandardResponse[CheckinResponse], summary="签退")
def checkout(
    training_id: int,
    data: Optional[CheckoutCreate] = Body(default=None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payload = data or CheckoutCreate()
    _require_self_or_manager(db, training_id, current_user.user_id, payload.user_id)
    controller = TrainingController(db)
    result = controller.checkout(training_id, current_user.user_id, payload)
    return StandardResponse(data=result)


@router.post("/{training_id}/evaluation", response_model=StandardResponse[CheckinResponse], summary="评课")
def submit_training_evaluation(
    training_id: int,
    data: TrainingEvaluationCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_self_or_manager(db, training_id, current_user.user_id, data.user_id)
    controller = TrainingController(db)
    result = controller.submit_training_evaluation(training_id, current_user.user_id, data)
    return StandardResponse(data=result)


@router.get("/{training_id}/checkin/qr", response_model=StandardResponse[TrainingCheckinQrResponse], summary="生成签到二维码")
def get_checkin_qr(
    training_id: int,
    session_key: str = Query("start"),
    date: Optional[date] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    data = controller.generate_checkin_qr(training_id, session_key, date, current_user.user_id)
    return StandardResponse(data=data)


@router.get("/{training_id}/histories", response_model=StandardResponse[List[TrainingHistoryResponse]], summary="培训训历")
def get_training_histories(
    training_id: int,
    user_id: Optional[int] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    manager_mode = can_manage_training(db, _get_training_or_404(db, training_id), current_user.user_id)
    target_user_id = user_id
    if not manager_mode:
        if target_user_id is not None and target_user_id != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅可查看自己的训历")
        target_user_id = current_user.user_id
    controller = TrainingController(db)
    data = controller.get_training_histories(training_id, target_user_id)
    return StandardResponse(data=data)


@router.get(
    "/{training_id}/course-change-logs",
    response_model=StandardResponse[List[TrainingCourseChangeLogResponse]],
    summary="培训班课程变更记录",
)
def get_training_course_change_logs(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_course_change_log_viewer(db, training_id, current_user)
    controller = TrainingController(db)
    data = controller.get_training_course_change_logs(training_id)
    return StandardResponse(data=data)


@router.post("/{training_id}/resources", response_model=StandardResponse[ResourceListItemResponse], summary="培训绑定资源")
def add_training_resource(
    training_id: int,
    data: TrainingResourceBindRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    service = TrainingService(db)
    result = service.add_training_resource(training_id, data)
    return StandardResponse(data=result)


@router.get("/{training_id}/resources", response_model=StandardResponse[List[ResourceListItemResponse]], summary="培训资源列表")
def list_training_resources(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TrainingService(db)
    result = service.list_training_resources(training_id)
    return StandardResponse(data=result)


@router.delete("/{training_id}/resources/{resource_id}", response_model=StandardResponse, summary="培训解绑资源")
def remove_training_resource(
    training_id: int,
    resource_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    service = TrainingService(db)
    ok = service.remove_training_resource(training_id, resource_id)
    if not ok:
        return StandardResponse(code=404, message="绑定关系不存在")
    return StandardResponse(message="解绑成功")
