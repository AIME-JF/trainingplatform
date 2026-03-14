"""
AI 任务路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers import AIController
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    AIPaperAssemblyTaskCreateRequest,
    AIPaperAssemblyTaskDetailResponse,
    AIPaperGenerationTaskCreateRequest,
    AIPaperGenerationTaskDetailResponse,
    AIPaperTaskUpdateRequest,
    AIQuestionTaskCreateRequest,
    AIQuestionTaskDetailResponse,
    AIQuestionTaskUpdateRequest,
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
