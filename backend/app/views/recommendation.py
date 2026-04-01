"""
资源推荐与埋点路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    StandardResponse,
    TokenData,
    ResourceLikeStatusResponse,
    ResourceShareStatusResponse,
    ResourceRecommendationFeedResponse,
)
from app.schemas.recommendation import ResourceBehaviorEventCreate
from app.controllers.recommendation import RecommendationController


router = APIRouter(tags=['resource_recommendation'])


@router.post('/resources/{resource_id}/events', response_model=StandardResponse, summary='记录资源行为事件')
def record_event(
    resource_id: int,
    data: ResourceBehaviorEventCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = RecommendationController(db)
    result = controller.record_event(resource_id, current_user.user_id, current_user.permissions, data)
    return StandardResponse(data={'id': result.id})


@router.post('/resources/{resource_id}/likes', response_model=StandardResponse[ResourceLikeStatusResponse], summary='点赞资源')
def like_resource(
    resource_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = RecommendationController(db)
    data = controller.like_resource(resource_id, current_user.user_id, current_user.permissions)
    return StandardResponse(data=data)


@router.delete('/resources/{resource_id}/likes', response_model=StandardResponse[ResourceLikeStatusResponse], summary='取消点赞资源')
def unlike_resource(
    resource_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = RecommendationController(db)
    data = controller.unlike_resource(resource_id, current_user.user_id, current_user.permissions)
    return StandardResponse(data=data)


@router.post('/resources/{resource_id}/share', response_model=StandardResponse[ResourceShareStatusResponse], summary='转发资源')
def share_resource(
    resource_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = RecommendationController(db)
    data = controller.share_resource(resource_id, current_user.user_id, current_user.permissions)
    return StandardResponse(data=data)


@router.get(
    '/resources/recommendations/feed',
    response_model=StandardResponse[ResourceRecommendationFeedResponse],
    summary='推荐资源流',
)
def get_feed(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = RecommendationController(db)
    data = controller.get_feed(current_user.user_id, page, size)
    return StandardResponse(data=data)
