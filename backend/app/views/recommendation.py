"""
资源推荐与埋点路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, TokenData
from app.schemas.recommendation import ResourceBehaviorEventCreate
from app.controllers.recommendation import RecommendationController


router = APIRouter(tags=['资源推荐'])


@router.post('/resources/{resource_id}/events', response_model=StandardResponse, summary='记录资源行为事件')
def record_event(
    resource_id: int,
    data: ResourceBehaviorEventCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = RecommendationController(db)
    result = controller.record_event(resource_id, current_user.user_id, data)
    return StandardResponse(data={'id': result.id})


@router.get('/resources/recommendations/feed', response_model=StandardResponse, summary='推荐资源流')
def get_feed(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = RecommendationController(db)
    data = controller.get_feed(current_user.user_id, page, size)
    return StandardResponse(data=data)
