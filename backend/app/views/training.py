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
    BatchManualCheckinRequest,
    CheckinCreate,
    CheckinResponse,
    CheckoutCreate,
    TrainingLeaveCreate,
    TrainingLeaveResponse,
    EnrollmentCreate,
    EnrollmentResponse,
    PaginatedResponse,
    ResourceListItemResponse,
    ScheduleItemResponse,
    StandardResponse,
    TokenData,
    TrainingActivityResponse,
    TrainingAttendanceSummaryResponse,
    TrainingCheckinQrResponse,
    TrainingCourseResponse,
    TrainingCreate,
    TrainingCourseChangeLogResponse,
    TrainingExamSummary,
    TrainingEvaluationCreate,
    TrainingHistoryResponse,
    TrainingQuizPublishRequest,
    TrainingQuizUpdateRequest,
    TrainingReportSnapshotResponse,
    TrainingListResponse,
    TrainingStatsResponse,
    CalendarEventResponse,
    TrainingBoundResourceResponse,
    TrainingResourceBindRequest,
    TrainingResponse,
    TrainingRosterAssignment,
    TrainingSkipCourseRequest,
    TrainingUpdate,
    TrainingWorkflowActionRequest,
)
from app.services.training import TrainingService
from app.utils.authz import (
    can_manage_training,
    can_manage_training_quiz,
    can_update_training,
    can_view_training,
    is_admin_user,
    is_instructor_user,
    is_training_director,
)
from logger import logger

router = APIRouter(prefix="/trainings", tags=["training_management"])


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


def _require_training_quiz_manager(db: Session, training_id: int, user_id: int):
    training = _get_training_or_404(db, training_id)
    if not can_manage_training_quiz(db, training, user_id):
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


@router.get("/calendar", response_model=StandardResponse[List[CalendarEventResponse]], summary="聚合日历")
def get_calendar_events(
    training_id: Optional[int] = Query(None, description="指定班级ID，不传则返回所有相关班级"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TrainingService(db)
    data = service.get_calendar_events(current_user.user_id, training_id)
    return StandardResponse(data=data)


@router.get("/{training_id}/activities", response_model=StandardResponse[List[TrainingActivityResponse]], summary="培训班动态")
def get_training_activities(
    training_id: int,
    limit: int = Query(5, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_viewer(db, training_id, current_user.user_id)
    service = TrainingService(db)
    data = service.get_training_activities(training_id, limit)
    return StandardResponse(data=data)


@router.get("/attendance/qr/{token}", response_model=StandardResponse[TrainingCheckinQrResponse], summary="获取出勤二维码信息")
def get_attendance_qr_payload(
    token: str,
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    data = controller.get_attendance_qr_payload(token)
    return StandardResponse(data=data)


@router.post("/attendance/qr/{token}", response_model=StandardResponse[CheckinResponse], summary="扫码出勤（签到或签退）")
def attendance_by_qr(
    token: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    result = controller.attendance_by_qr(token, current_user.user_id)
    return StandardResponse(data=result)


@router.get("/course-resources", response_model=StandardResponse[PaginatedResponse], summary="获取课程资源列表（培训用）")
def get_course_resources_for_training(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="搜索课程名称"),
    category: Optional[str] = Query(None, description="课程分类"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取课程资源列表，供培训班添加课程时选择。需要培训班管理权限（教官或管理员）。"""
    _require_admin_or_instructor(db, current_user.user_id)
    service = TrainingService(db)
    data = service.get_course_resources_for_training(current_user.user_id, page, size, search, category)
    return StandardResponse(data=data)


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


@router.get(
    "/{training_id}/report-snapshots",
    response_model=StandardResponse[List[TrainingReportSnapshotResponse]],
    summary="培训班报告版本列表",
)
def get_training_report_snapshots(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    data = controller.list_training_report_snapshots(training_id)
    return StandardResponse(data=data)


@router.get(
    "/{training_id}/report-snapshots/latest",
    response_model=StandardResponse[Optional[TrainingReportSnapshotResponse]],
    summary="培训班最新报告版本",
)
def get_latest_training_report_snapshot(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    data = controller.get_latest_training_report_snapshot(training_id)
    return StandardResponse(data=data)


@router.post(
    "/{training_id}/quizzes",
    response_model=StandardResponse[TrainingExamSummary],
    summary="发布培训班随堂测试",
)
def create_training_quiz(
    training_id: int,
    data: TrainingQuizPublishRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_quiz_manager(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    result = controller.create_training_quiz(training_id, data, current_user.user_id)
    return StandardResponse(data=result)


@router.put(
    "/{training_id}/quizzes/{exam_id}",
    response_model=StandardResponse[TrainingExamSummary],
    summary="更新培训班随堂测试",
)
def update_training_quiz(
    training_id: int,
    exam_id: int,
    data: TrainingQuizUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_quiz_manager(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    result = controller.update_training_quiz(training_id, exam_id, data, current_user.user_id)
    return StandardResponse(data=result)


@router.delete(
    "/{training_id}/quizzes/{exam_id}",
    response_model=StandardResponse[dict],
    summary="删除培训班随堂测试",
)
def delete_training_quiz(
    training_id: int,
    exam_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_quiz_manager(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    result = controller.delete_training_quiz(training_id, exam_id, current_user.user_id)
    return StandardResponse(data=result)


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
    training = _get_training_or_404(db, training_id)
    user_id = current_user.user_id
    # Allow admin, training director (班主任), or any course instructor in this training
    allowed = is_admin_user(db, user_id) or is_training_director(training, user_id)
    if not allowed:
        for course in (training.courses or []):
            if course.primary_instructor_id == user_id:
                allowed = True
                break
            if user_id in (course.assistant_instructor_ids or []):
                allowed = True
                break
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看学员列表")
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


@router.get("/{training_id}/courses", response_model=StandardResponse[List[TrainingCourseResponse]], summary="课程与课次列表")
def get_training_courses(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取培训班课程与课次列表"""
    controller = TrainingController(db)
    data = controller.get_training_courses(training_id, current_user.user_id)
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


@router.get("/{training_id}/import/schedule/template", summary="下载培训班课表导入模板")
def download_training_schedule_import_template(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    data = TrainingService(db).build_training_schedule_import_template()
    return _excel_response(data, "training_schedule_import_template.xlsx")


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


@router.post("/{training_id}/import/schedule/preview", response_model=StandardResponse, summary="预览课表导入")
async def preview_schedule_import(
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
        data = service.preview_schedule_import(training_id, file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return StandardResponse(data=data)


@router.post("/{training_id}/import/schedule/confirm", response_model=StandardResponse, summary="确认课表导入")
async def confirm_schedule_import(
    training_id: int,
    file: UploadFile = File(...),
    skip_rows: str = Form("[]"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="导入文件为空")

    import json as _json_mod
    try:
        skip_rows_list = _json_mod.loads(skip_rows)
        if not isinstance(skip_rows_list, list):
            skip_rows_list = []
    except (ValueError, TypeError):
        skip_rows_list = []

    service = TrainingService(db)
    try:
        data = service.confirm_schedule_import(
            training_id,
            file_bytes,
            skip_rows=skip_rows_list,
            actor_id=current_user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return StandardResponse(data=data)


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
    training = _get_training_or_404(db, training_id)
    user_id = current_user.user_id
    controller = TrainingController(db)
    manager_mode = can_manage_training(db, training, user_id)
    # Course instructors (primary or assistant) can see all records
    instructor_mode = False
    if not manager_mode:
        for course in (training.courses or []):
            if course.primary_instructor_id == user_id or user_id in (course.assistant_instructor_ids or []):
                instructor_mode = True
                break
    session_operator_mode = bool(session_key) and TrainingService(db).can_user_operate_session(training_id, session_key, user_id)
    full_access = manager_mode or instructor_mode or session_operator_mode
    data = controller.get_checkin_records(
        training_id,
        date,
        session_key,
        None if full_access else user_id,
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
    checkin_mode: str = Query("direct", description="签到模式: direct/qr"),
    checkin_duration_minutes: int = Query(15, ge=1, le=120, description="签到限时（分钟）"),
    checkin_gesture_pattern: Optional[str] = Query(None, description="手势签到图案，JSON数组如[0,1,2,5,8]"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    result = controller.start_session_checkin(training_id, session_key, current_user.user_id, checkin_mode, checkin_duration_minutes, checkin_gesture_pattern=checkin_gesture_pattern)
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
    checkout_mode: str = Query("direct", description="签退模式: direct/qr"),
    checkout_duration_minutes: int = Query(15, ge=1, le=120, description="签退限时（分钟）"),
    checkout_gesture_pattern: Optional[str] = Query(None, description="手势签退图案，JSON数组如[0,1,2,5,8]"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    result = controller.start_session_checkout(training_id, session_key, current_user.user_id, checkout_mode, checkout_duration_minutes, checkout_gesture_pattern=checkout_gesture_pattern)
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


@router.post("/{training_id}/checkin/batch-manual", response_model=StandardResponse[List[CheckinResponse]], summary="批量手动点名")
def batch_manual_checkin(
    training_id: int,
    data: BatchManualCheckinRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    controller = TrainingController(db)
    result = controller.batch_manual_checkin(training_id, data)
    return StandardResponse(data=result)


@router.post("/{training_id}/leaves", response_model=StandardResponse[TrainingLeaveResponse], summary="请假")
def create_leave(
    training_id: int,
    data: TrainingLeaveCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_self_or_manager(db, training_id, current_user.user_id, None)
    controller = TrainingController(db)
    result = controller.create_leave(training_id, current_user.user_id, data)
    return StandardResponse(data=result)


@router.delete("/{training_id}/leaves/{leave_id}", response_model=StandardResponse[TrainingLeaveResponse], summary="销假")
def cancel_leave(
    training_id: int,
    leave_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    result = controller.cancel_leave(training_id, leave_id, current_user.user_id)
    return StandardResponse(data=result)


@router.get("/{training_id}/leaves", response_model=StandardResponse[List[TrainingLeaveResponse]], summary="请假记录")
def get_leaves(
    training_id: int,
    session_key: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    training = _get_training_or_404(db, training_id)
    is_manager = can_manage_training(db, training, current_user.user_id)
    controller = TrainingController(db)
    result = controller.get_leaves(training_id, current_user.user_id, session_key, is_manager)
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


@router.get("/{training_id}/attendance/qr", response_model=StandardResponse[TrainingCheckinQrResponse], summary="生成出勤二维码")
def get_attendance_qr(
    training_id: int,
    session_key: str = Query("start"),
    date: Optional[date] = None,
    action: str = Query("checkin", description="出勤动作: checkin/checkout"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = TrainingController(db)
    data = controller.generate_attendance_qr(training_id, session_key, date, current_user.user_id, action=action)
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


@router.post("/{training_id}/resources", response_model=StandardResponse[TrainingBoundResourceResponse], summary="培训绑定资源")
def add_training_resource(
    training_id: int,
    data: TrainingResourceBindRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    service = TrainingService(db)
    try:
        result = service.add_training_resource(training_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return StandardResponse(data=result)


@router.get("/{training_id}/resources", response_model=StandardResponse[List[TrainingBoundResourceResponse]], summary="培训资源列表")
def list_training_resources(
    training_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TrainingService(db)
    result = service.list_training_resources(training_id)
    return StandardResponse(data=result)


@router.delete("/{training_id}/resources/{ref_id}", response_model=StandardResponse, summary="培训解绑资源")
def remove_training_resource(
    training_id: int,
    ref_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_training_manager(db, training_id, current_user.user_id)
    service = TrainingService(db)
    ok = service.remove_training_resource(training_id, ref_id)
    if not ok:
        return StandardResponse(code=404, message="绑定关系不存在")
    return StandardResponse(message="解绑成功")


# ===== 智能创建培训班（SSE 流式） =====

import asyncio
import json as _json
import uuid as _uuid

from fastapi import Request
from fastapi.responses import StreamingResponse as _StreamingResponse
from pydantic import BaseModel as _BaseModel

from app.agents.training_create_parser import TrainingCreateParser
from app.database import get_redis


class _AiCreateRequest(_BaseModel):
    session_id: Optional[str] = None
    message: str


@router.post("/ai-create", summary="智能创建培训班（SSE）")
async def ai_create_training(
    data: _AiCreateRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(db, current_user, "CREATE_TRAINING")
    _require_admin_or_instructor(db, current_user.user_id)

    redis = get_redis()
    session_id = data.session_id or str(_uuid.uuid4())
    cache_key = f"training_ai_create:{session_id}"

    # 加载或初始化会话上下文
    raw = redis.get(cache_key)
    session_data = _json.loads(raw) if raw else {"fields": {}, "conversation": []}
    context = session_data["fields"]
    conversation = session_data["conversation"]

    # 追加用户消息到对话历史
    conversation.append({"role": "user", "content": data.message})

    parser = TrainingCreateParser(db)
    event_queue = asyncio.Queue()

    def _worker():
        """在子线程中执行同步 LLM 调用，通过 queue 推送 SSE 事件"""
        try:
            event_queue.put_nowait(_sse_event("thinking", {"text": "正在分析您的需求..."}))

            result = parser.parse_round(data.message, context, conversation)

            if result.get("cancelled"):
                event_queue.put_nowait(_sse_event("cancelled", {"text": "已取消"}))
                return

            fields = result["fields"]

            conversation.append({
                "role": "assistant",
                "content": _json.dumps(fields, ensure_ascii=False, default=str),
            })
            redis.setex(cache_key, 600, _json.dumps(
                {"fields": fields, "conversation": conversation},
                ensure_ascii=False, default=str,
            ))

            if result["complete"]:
                event_queue.put_nowait(_sse_event("thinking", {"text": "信息已齐全，正在创建培训班..."}))

                try:
                    payload = parser.build_training_create_payload(fields)
                    training_data = TrainingCreate(**payload)
                    controller = TrainingController(db)
                    training = controller.create_training(training_data, current_user.user_id)
                    redis.delete(cache_key)
                    event_queue.put_nowait(_sse_event("created", {
                        "training_id": training.id,
                        "training_name": training.name,
                        "text": f"培训班「{training.name}」创建成功",
                    }))
                except Exception as e:
                    logger.error(f"智能创建培训班失败: {e}")
                    event_queue.put_nowait(_sse_event("error", {"text": f"创建失败：{str(e)}"}))
            else:
                questions = result.get("questions", ["请补充缺失信息"])
                event_queue.put_nowait(_sse_event("question", {
                    "session_id": session_id,
                    "fields": _serialize_fields(fields),
                    "missing": result["missing"],
                    "questions": questions,
                    "text": questions[0] if questions else "请补充缺失信息",
                }))

            event_queue.put_nowait(_sse_event("done", {}))
        except Exception as e:
            logger.error(f"智能创建培训班 SSE 异常: {e}")
            event_queue.put_nowait(_sse_event("error", {"text": f"系统异常：{str(e)}"}))
        finally:
            event_queue.put_nowait(None)  # 结束信号

    async def async_generate():
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, _worker)

        while True:
            if await request.is_disconnected():
                parser.cancel()
                redis.delete(cache_key)
                break

            try:
                chunk = await asyncio.wait_for(event_queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

            if chunk is None:
                break
            yield chunk

    return _StreamingResponse(
        async_generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {_json.dumps(data, ensure_ascii=False, default=str)}\n\n"


def _serialize_fields(fields: dict) -> dict:
    """确保字段可 JSON 序列化"""
    result = {}
    for k, v in fields.items():
        if isinstance(v, (date,)):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result
