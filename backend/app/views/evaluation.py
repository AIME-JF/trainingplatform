"""
评价模块接口
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    EvaluationDimensionCreate, EvaluationDimensionResponse, EvaluationDimensionUpdate,
    EvaluationRecordResponse, EvaluationSubmit, EvaluationSummaryResponse,
    EvaluationTaskCreate, EvaluationTaskDetailResponse, EvaluationTaskResponse,
    EvaluationTaskUpdate, EvaluationTemplateResponse, EvaluationTemplateUpdate,
    StandardResponse, TokenData,
)
from app.services.evaluation import EvaluationService

router = APIRouter(prefix="/evaluations", tags=["evaluation_management"])


# ========== 模板 ==========

@router.get("/templates", response_model=StandardResponse[List[EvaluationTemplateResponse]], summary="问卷模板列表")
def list_templates(
    target_type: Optional[str] = Query(None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StandardResponse(data=EvaluationService(db).list_templates(target_type))


@router.get("/templates/{template_id}", response_model=StandardResponse[EvaluationTemplateResponse], summary="问卷模板详情")
def get_template(
    template_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = EvaluationService(db).get_template(template_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")
    return StandardResponse(data=result)


@router.put("/templates/{template_id}", response_model=StandardResponse[EvaluationTemplateResponse], summary="更新问卷模板")
def update_template(
    template_id: int, data: EvaluationTemplateUpdate,
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db),
):
    try:
        return StandardResponse(data=EvaluationService(db).update_template(template_id, data))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ========== 维度 ==========

@router.post("/templates/{template_id}/dimensions", response_model=StandardResponse[EvaluationDimensionResponse], summary="添加评价维度")
def add_dimension(
    template_id: int, data: EvaluationDimensionCreate,
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db),
):
    try:
        return StandardResponse(data=EvaluationService(db).add_dimension(template_id, data))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put("/dimensions/{dimension_id}", response_model=StandardResponse[EvaluationDimensionResponse], summary="更新评价维度")
def update_dimension(
    dimension_id: int, data: EvaluationDimensionUpdate,
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db),
):
    try:
        return StandardResponse(data=EvaluationService(db).update_dimension(dimension_id, data))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/dimensions/{dimension_id}", response_model=StandardResponse, summary="删除评价维度")
def delete_dimension(
    dimension_id: int,
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db),
):
    try:
        EvaluationService(db).delete_dimension(dimension_id)
        return StandardResponse(data={"deleted": True})
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ========== 任务 ==========

@router.get("/tasks", response_model=StandardResponse[List[EvaluationTaskResponse]], summary="评价任务列表")
def list_tasks(
    target_type: Optional[str] = Query(None),
    task_status: Optional[str] = Query(None, alias="status"),
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db),
):
    return StandardResponse(data=EvaluationService(db).list_tasks(target_type, task_status, current_user.user_id))


@router.post("/tasks", response_model=StandardResponse[EvaluationTaskResponse], summary="创建评价任务")
def create_task(
    data: EvaluationTaskCreate,
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db),
):
    try:
        return StandardResponse(data=EvaluationService(db).create_task(data, current_user.user_id))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/tasks/{task_id}/detail", response_model=StandardResponse[EvaluationTaskDetailResponse], summary="评价任务详情")
def get_task_detail(
    task_id: int,
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db),
):
    result = EvaluationService(db).get_task_detail(task_id, current_user.user_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return StandardResponse(data=result)


@router.put("/tasks/{task_id}", response_model=StandardResponse[EvaluationTaskResponse], summary="更新评价任务")
def update_task(
    task_id: int, data: EvaluationTaskUpdate,
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db),
):
    try:
        return StandardResponse(data=EvaluationService(db).update_task(task_id, data))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/tasks/{task_id}", response_model=StandardResponse, summary="删除评价任务")
def delete_task(
    task_id: int,
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db),
):
    try:
        EvaluationService(db).delete_task(task_id)
        return StandardResponse(data={"deleted": True})
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ========== 评价提交与记录 ==========

@router.post("/submit", response_model=StandardResponse[List[EvaluationRecordResponse]], summary="批量提交评价")
def submit_evaluation(
    data: EvaluationSubmit,
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db),
):
    try:
        return StandardResponse(data=EvaluationService(db).submit_evaluation(current_user.user_id, data))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/records", response_model=StandardResponse[List[EvaluationRecordResponse]], summary="评价记录列表")
def list_records(
    target_type: Optional[str] = Query(None), target_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None), task_id: Optional[int] = Query(None),
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db),
):
    return StandardResponse(data=EvaluationService(db).list_records(target_type, target_id, user_id, task_id))


@router.get("/summary", response_model=StandardResponse[EvaluationSummaryResponse], summary="评价统计")
def get_summary(
    target_type: str = Query(...), target_id: int = Query(...),
    current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db),
):
    return StandardResponse(data=EvaluationService(db).get_summary(target_type, target_id))
