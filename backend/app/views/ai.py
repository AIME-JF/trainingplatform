"""
AI 任务路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers import AIController
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import Permission, Role, User
from app.schemas import (
    AIPersonalTrainingTaskCreateRequest,
    AIPersonalTrainingTaskDetailResponse,
    AIPersonalTrainingTaskUpdateRequest,
    AIPaperAssemblyTaskCreateRequest,
    AIPaperAssemblyTaskDetailResponse,
    AIPaperGenerationTaskCreateRequest,
    AIPaperGenerationTaskDetailResponse,
    AIPaperTaskUpdateRequest,
    AIQuestionTaskCreateRequest,
    AIQuestionTaskDetailResponse,
    AIQuestionTaskUpdateRequest,
    AIScheduleTaskCreateRequest,
    AIScheduleParsePreviewResponse,
    AIScheduleTaskDetailResponse,
    AIScheduleTaskUpdateRequest,
    AITaskSummaryResponse,
    PaginatedResponse,
    StandardResponse,
    TokenData,
)
from app.utils.authz import is_admin_user, is_instructor_user

router = APIRouter(prefix="/ai", tags=["AI任务"])


def _require_admin_or_instructor(db: Session, user_id: int):
    if not (is_admin_user(db, user_id) or is_instructor_user(db, user_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员或教官可执行该操作")


def _has_permission(db: Session, current_user: TokenData, permission: str) -> bool:
    if permission in current_user.permissions:
        return True
    has_permission = db.query(User.id).join(User.roles).join(Role.permissions).filter(
        User.id == current_user.user_id,
        User.is_active == True,
        Permission.code == permission,
    ).first()
    return bool(has_permission)


def _require_schedule_task_permission(db: Session, current_user: TokenData):
    if _has_permission(db, current_user, "UPDATE_TRAINING") or _has_permission(db, current_user, "MANAGE_TRAINING"):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="权限不足，需要 UPDATE_TRAINING 或 MANAGE_TRAINING",
    )


@router.get(
    "/question-tasks",
    response_model=StandardResponse[PaginatedResponse[AITaskSummaryResponse]],
    summary="AI 智能出题任务列表",
)
def list_question_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    status_value: Optional[str] = Query(None, alias="status"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = AIController(db)
    data = controller.list_question_tasks(page, size, status_value, current_user.user_id)
    return StandardResponse(data=data)


@router.post(
    "/question-tasks",
    response_model=StandardResponse[AIQuestionTaskDetailResponse],
    summary="创建 AI 智能出题任务",
)
def create_question_task(
    data: AIQuestionTaskCreateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = AIController(db)
    result = controller.create_question_task(data, current_user.user_id)
    return StandardResponse(data=result)


@router.get(
    "/question-tasks/{task_id}",
    response_model=StandardResponse[AIQuestionTaskDetailResponse],
    summary="AI 智能出题任务详情",
)
def get_question_task_detail(
    task_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = AIController(db)
    data = controller.get_question_task_detail(task_id, current_user.user_id)
    return StandardResponse(data=data)


@router.put(
    "/question-tasks/{task_id}/result",
    response_model=StandardResponse[AIQuestionTaskDetailResponse],
    summary="更新 AI 智能出题任务结果",
)
def update_question_task(
    task_id: int,
    data: AIQuestionTaskUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = AIController(db)
    result = controller.update_question_task(task_id, data, current_user.user_id)
    return StandardResponse(data=result)


@router.post(
    "/question-tasks/{task_id}/confirm",
    response_model=StandardResponse[AIQuestionTaskDetailResponse],
    summary="确认 AI 智能出题任务",
)
def confirm_question_task(
    task_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = AIController(db)
    result = controller.confirm_question_task(task_id, current_user.user_id)
    return StandardResponse(data=result)


@router.get(
    "/paper-assembly-tasks",
    response_model=StandardResponse[PaginatedResponse[AITaskSummaryResponse]],
    summary="AI 自动组卷任务列表",
)
def list_paper_assembly_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    status_value: Optional[str] = Query(None, alias="status"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = AIController(db)
    data = controller.list_paper_assembly_tasks(page, size, status_value, current_user.user_id)
    return StandardResponse(data=data)


@router.post(
    "/paper-assembly-tasks",
    response_model=StandardResponse[AIPaperAssemblyTaskDetailResponse],
    summary="创建 AI 自动组卷任务",
)
def create_paper_assembly_task(
    data: AIPaperAssemblyTaskCreateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = AIController(db)
    result = controller.create_paper_assembly_task(data, current_user.user_id)
    return StandardResponse(data=result)


@router.get(
    "/paper-assembly-tasks/{task_id}",
    response_model=StandardResponse[AIPaperAssemblyTaskDetailResponse],
    summary="AI 自动组卷任务详情",
)
def get_paper_assembly_task_detail(
    task_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = AIController(db)
    data = controller.get_paper_assembly_task_detail(task_id, current_user.user_id)
    return StandardResponse(data=data)


@router.put(
    "/paper-assembly-tasks/{task_id}/result",
    response_model=StandardResponse[AIPaperAssemblyTaskDetailResponse],
    summary="更新 AI 自动组卷任务结果",
)
def update_paper_assembly_task(
    task_id: int,
    data: AIPaperTaskUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = AIController(db)
    result = controller.update_paper_assembly_task(task_id, data, current_user.user_id)
    return StandardResponse(data=result)


@router.post(
    "/paper-assembly-tasks/{task_id}/confirm",
    response_model=StandardResponse[AIPaperAssemblyTaskDetailResponse],
    summary="确认 AI 自动组卷任务",
)
def confirm_paper_assembly_task(
    task_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = AIController(db)
    result = controller.confirm_paper_assembly_task(task_id, current_user.user_id)
    return StandardResponse(data=result)


@router.get(
    "/paper-generation-tasks",
    response_model=StandardResponse[PaginatedResponse[AITaskSummaryResponse]],
    summary="AI 自动生成试卷任务列表",
)
def list_paper_generation_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    status_value: Optional[str] = Query(None, alias="status"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = AIController(db)
    data = controller.list_paper_generation_tasks(page, size, status_value, current_user.user_id)
    return StandardResponse(data=data)


@router.post(
    "/paper-generation-tasks",
    response_model=StandardResponse[AIPaperGenerationTaskDetailResponse],
    summary="创建 AI 自动生成试卷任务",
)
def create_paper_generation_task(
    data: AIPaperGenerationTaskCreateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = AIController(db)
    result = controller.create_paper_generation_task(data, current_user.user_id)
    return StandardResponse(data=result)


@router.get(
    "/paper-generation-tasks/{task_id}",
    response_model=StandardResponse[AIPaperGenerationTaskDetailResponse],
    summary="AI 自动生成试卷任务详情",
)
def get_paper_generation_task_detail(
    task_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = AIController(db)
    data = controller.get_paper_generation_task_detail(task_id, current_user.user_id)
    return StandardResponse(data=data)


@router.put(
    "/paper-generation-tasks/{task_id}/result",
    response_model=StandardResponse[AIPaperGenerationTaskDetailResponse],
    summary="更新 AI 自动生成试卷任务结果",
)
def update_paper_generation_task(
    task_id: int,
    data: AIPaperTaskUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = AIController(db)
    result = controller.update_paper_generation_task(task_id, data, current_user.user_id)
    return StandardResponse(data=result)


@router.post(
    "/paper-generation-tasks/{task_id}/confirm",
    response_model=StandardResponse[AIPaperGenerationTaskDetailResponse],
    summary="确认 AI 自动生成试卷任务",
)
def confirm_paper_generation_task(
    task_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = AIController(db)
    result = controller.confirm_paper_generation_task(task_id, current_user.user_id)
    return StandardResponse(data=result)


@router.get(
    "/schedule-tasks",
    response_model=StandardResponse[PaginatedResponse[AITaskSummaryResponse]],
    summary="AI 排课任务列表",
)
def list_schedule_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    status_value: Optional[str] = Query(None, alias="status"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_schedule_task_permission(db, current_user)
    controller = AIController(db)
    data = controller.list_schedule_tasks(page, size, status_value, current_user.user_id)
    return StandardResponse(data=data)


@router.post(
    "/schedule-tasks/preview",
    response_model=StandardResponse[AIScheduleParsePreviewResponse],
    summary="预览 AI 排课解析结果",
)
def preview_schedule_task(
    data: AIScheduleTaskCreateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_schedule_task_permission(db, current_user)
    controller = AIController(db)
    result = controller.preview_schedule_task(data, current_user.user_id)
    return StandardResponse(data=result)


@router.post(
    "/schedule-tasks",
    response_model=StandardResponse[AIScheduleTaskDetailResponse],
    summary="创建 AI 排课任务",
)
def create_schedule_task(
    data: AIScheduleTaskCreateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_schedule_task_permission(db, current_user)
    controller = AIController(db)
    result = controller.create_schedule_task(data, current_user.user_id)
    return StandardResponse(data=result)


@router.get(
    "/schedule-tasks/{task_id}",
    response_model=StandardResponse[AIScheduleTaskDetailResponse],
    summary="AI 排课任务详情",
)
def get_schedule_task_detail(
    task_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_schedule_task_permission(db, current_user)
    controller = AIController(db)
    data = controller.get_schedule_task_detail(task_id, current_user.user_id)
    return StandardResponse(data=data)


@router.put(
    "/schedule-tasks/{task_id}/result",
    response_model=StandardResponse[AIScheduleTaskDetailResponse],
    summary="更新 AI 排课任务结果",
)
def update_schedule_task(
    task_id: int,
    data: AIScheduleTaskUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_schedule_task_permission(db, current_user)
    controller = AIController(db)
    result = controller.update_schedule_task(task_id, data, current_user.user_id)
    return StandardResponse(data=result)


@router.delete(
    "/schedule-tasks/{task_id}",
    response_model=StandardResponse[dict],
    summary="删除 AI 排课任务",
)
def delete_schedule_task(
    task_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_schedule_task_permission(db, current_user)
    controller = AIController(db)
    controller.delete_schedule_task(task_id, current_user.user_id)
    return StandardResponse(data={"deleted": True})


@router.post(
    "/schedule-tasks/{task_id}/confirm-rules",
    response_model=StandardResponse[AIScheduleTaskDetailResponse],
    summary="确认 AI 排课规则并继续生成课表",
)
def confirm_schedule_task_rules(
    task_id: int,
    data: AIScheduleTaskCreateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_schedule_task_permission(db, current_user)
    controller = AIController(db)
    result = controller.confirm_schedule_task_rules(task_id, data, current_user.user_id)
    return StandardResponse(data=result)


@router.post(
    "/schedule-tasks/{task_id}/confirm",
    response_model=StandardResponse[AIScheduleTaskDetailResponse],
    summary="确认 AI 排课任务",
)
def confirm_schedule_task(
    task_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_schedule_task_permission(db, current_user)
    controller = AIController(db)
    result = controller.confirm_schedule_task(task_id, current_user.user_id)
    return StandardResponse(data=result)


@router.get(
    "/personal-training-tasks",
    response_model=StandardResponse[PaginatedResponse[AITaskSummaryResponse]],
    summary="AI 个训任务列表",
)
def list_personal_training_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    status_value: Optional[str] = Query(None, alias="status"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = AIController(db)
    data = controller.list_personal_training_tasks(page, size, status_value, current_user.user_id)
    return StandardResponse(data=data)


@router.post(
    "/personal-training-tasks",
    response_model=StandardResponse[AIPersonalTrainingTaskDetailResponse],
    summary="创建 AI 个训任务",
)
def create_personal_training_task(
    data: AIPersonalTrainingTaskCreateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = AIController(db)
    result = controller.create_personal_training_task(data, current_user.user_id)
    return StandardResponse(data=result)


@router.get(
    "/personal-training-tasks/{task_id}",
    response_model=StandardResponse[AIPersonalTrainingTaskDetailResponse],
    summary="AI 个训任务详情",
)
def get_personal_training_task_detail(
    task_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = AIController(db)
    data = controller.get_personal_training_task_detail(task_id, current_user.user_id)
    return StandardResponse(data=data)


@router.put(
    "/personal-training-tasks/{task_id}/result",
    response_model=StandardResponse[AIPersonalTrainingTaskDetailResponse],
    summary="更新 AI 个训任务结果",
)
def update_personal_training_task(
    task_id: int,
    data: AIPersonalTrainingTaskUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = AIController(db)
    result = controller.update_personal_training_task(task_id, data, current_user.user_id)
    return StandardResponse(data=result)


@router.post(
    "/personal-training-tasks/{task_id}/confirm",
    response_model=StandardResponse[AIPersonalTrainingTaskDetailResponse],
    summary="确认 AI 个训任务",
)
def confirm_personal_training_task(
    task_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = AIController(db)
    result = controller.confirm_personal_training_task(task_id, current_user.user_id)
    return StandardResponse(data=result)
