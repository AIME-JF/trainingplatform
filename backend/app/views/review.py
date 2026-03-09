"""
资源审核路由
"""
from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, TokenData
from app.schemas.review import (
    ReviewTaskActionRequest,
    ReviewTaskResponse,
    ReviewWorkflowResponse,
    ReviewPolicyCreate,
    ReviewPolicyUpdate,
    ReviewPolicyResponse,
)
from app.controllers.review import ReviewController


router = APIRouter(tags=['资源审核'])


def _require_any_permission(current_user: TokenData, permissions: List[str], detail: str):
    if not any(p in current_user.permissions for p in permissions):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


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


@router.get('/reviews/tasks', response_model=StandardResponse[List[ReviewTaskResponse]], summary='我的审核任务')
def get_review_tasks(
    status: str = Query('pending'),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ReviewController(db)
    result = controller.get_tasks(current_user.user_id, status)
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


@router.get('/reviews/workflows/{resource_id}', response_model=StandardResponse[ReviewWorkflowResponse], summary='资源审核轨迹')
def get_workflow(
    resource_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ReviewController(db)
    result = controller.get_workflow(resource_id)
    return StandardResponse(data=result)


@router.get('/review-policies', response_model=StandardResponse[List[ReviewPolicyResponse]], summary='审核策略列表')
def get_policies(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_any_permission(current_user, ['MANAGE_REVIEW_POLICY', 'VIEW_RESOURCE_ALL'], '无权限查看审核策略')
    controller = ReviewController(db)
    result = controller.get_policies()
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
