"""
审核路由（通用审核引擎）
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, TokenData
from app.schemas.review import (
    ReviewTaskActionRequest,
    ReviewTaskResponse,
    ReviewWorkflowResponse,
    ReviewLogDetailResponse,
    ReviewPolicyCreate,
    ReviewPolicyUpdate,
    ReviewPolicyResponse,
    SubmitReviewRequest,
)
from app.controllers.review import ReviewController


router = APIRouter(tags=['review'])


def _require_any_permission(current_user: TokenData, permissions: List[str], detail: str):
    if not any(p in current_user.permissions for p in permissions):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


# ===== 资源审核兼容入口（保留旧路由） =====

@router.post('/resources/{resource_id}/submit', response_model=StandardResponse[ReviewWorkflowResponse], summary='资源提交审核')
def submit_resource(
    resource_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_any_permission(current_user, ['SUBMIT_RESOURCE_REVIEW', 'VIEW_RESOURCE_ALL'], '无权限提交审核')
    controller = ReviewController(db)
    result = controller.submit_resource(resource_id, current_user.user_id)
    return StandardResponse(data=result)


# ===== 通用审核提交 =====

@router.post('/reviews/submit', response_model=StandardResponse[ReviewWorkflowResponse], summary='通用提交审核')
def submit_review(
    data: SubmitReviewRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_any_permission(current_user, ['SUBMIT_RESOURCE_REVIEW', 'VIEW_RESOURCE_ALL'], '无权限提交审核')
    controller = ReviewController(db)
    result = controller.submit_for_review(data, current_user.user_id)
    return StandardResponse(data=result)


# ===== 审核任务 =====

@router.get('/reviews/tasks', response_model=StandardResponse[List[ReviewTaskResponse]], summary='我的审核任务')
def get_review_tasks(
    status: str = Query('pending'),
    business_type: Optional[str] = Query(None, description='业务类型过滤: resource/training/exam'),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ReviewController(db)
    result = controller.get_tasks(current_user.user_id, status, business_type=business_type)
    return StandardResponse(data=result)


@router.post('/reviews/tasks/{task_id}/approve', response_model=StandardResponse[ReviewWorkflowResponse], summary='审核通过')
def approve_task(
    task_id: int,
    data: ReviewTaskActionRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ReviewController(db)
    result = controller.approve_task(task_id, current_user.user_id, data)
    return StandardResponse(data=result)


@router.post('/reviews/tasks/{task_id}/reject', response_model=StandardResponse[ReviewWorkflowResponse], summary='审核驳回')
def reject_task(
    task_id: int,
    data: ReviewTaskActionRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ReviewController(db)
    result = controller.reject_task(task_id, current_user.user_id, data)
    return StandardResponse(data=result)


# ===== 审核工作流列表与日志 =====

@router.get("/reviews/workflows", response_model=StandardResponse, summary="审核工作流列表")
def list_review_workflows(
    business_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ReviewController(db)
    result = controller.list_workflows(business_type, status, search, page, size)
    return StandardResponse(data=result)


@router.get("/reviews/workflows/{workflow_id}/logs", response_model=StandardResponse[List[ReviewLogDetailResponse]], summary="审核工作流日志")
def get_review_workflow_logs(
    workflow_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ReviewController(db)
    result = controller.get_workflow_logs(workflow_id)
    return StandardResponse(data=result)


# ===== 审核轨迹 =====

@router.get('/reviews/workflows/{resource_id}', response_model=StandardResponse[ReviewWorkflowResponse], summary='资源审核轨迹（兼容旧路由）')
def get_workflow_legacy(
    resource_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """兼容旧路由：通过 resource_id 查询资源审核轨迹"""
    controller = ReviewController(db)
    result = controller.get_workflow('resource', resource_id)
    return StandardResponse(data=result)


@router.get('/reviews/workflows/{business_type}/{business_id}', response_model=StandardResponse[ReviewWorkflowResponse], summary='审核轨迹')
def get_workflow(
    business_type: str,
    business_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ReviewController(db)
    result = controller.get_workflow(business_type, business_id)
    return StandardResponse(data=result)


# ===== 策略管理 =====

@router.get('/review-policies', response_model=StandardResponse[List[ReviewPolicyResponse]], summary='审核策略列表')
def get_policies(
    business_type: Optional[str] = Query(None, description='业务类型过滤'),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_any_permission(current_user, ['MANAGE_REVIEW_POLICY', 'VIEW_RESOURCE_ALL'], '无权限查看审核策略')
    controller = ReviewController(db)
    result = controller.get_policies(business_type=business_type)
    return StandardResponse(data=result)


@router.post('/review-policies', response_model=StandardResponse[ReviewPolicyResponse], summary='创建审核策略')
def create_policy(
    data: ReviewPolicyCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_any_permission(current_user, ['MANAGE_REVIEW_POLICY', 'VIEW_RESOURCE_ALL'], '无权限创建审核策略')
    controller = ReviewController(db)
    result = controller.create_policy(data)
    return StandardResponse(data=result)


@router.put('/review-policies/{policy_id}', response_model=StandardResponse[ReviewPolicyResponse], summary='更新审核策略')
def update_policy(
    policy_id: int,
    data: ReviewPolicyUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_any_permission(current_user, ['MANAGE_REVIEW_POLICY', 'VIEW_RESOURCE_ALL'], '无权限更新审核策略')
    controller = ReviewController(db)
    result = controller.update_policy(policy_id, data)
    return StandardResponse(data=result)
