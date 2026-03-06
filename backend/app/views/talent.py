"""
人才库路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    StandardResponse, TokenData, PaginatedResponse,
    TalentResponse, TalentStatsResponse
)
from app.controllers import TalentController

router = APIRouter(prefix="/talent", tags=["人才库"])


@router.get("", response_model=StandardResponse[PaginatedResponse[TalentResponse]], summary="人才列表")
def get_talents(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    search: Optional[str] = None,
    tier: Optional[str] = None,
    department_id: Optional[int] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取人才列表"""
    controller = TalentController(db)
    data = controller.get_talents(page, size, search, tier, department_id)
    return StandardResponse(data=data)


@router.get("/stats", response_model=StandardResponse[TalentStatsResponse], summary="统计概览")
def get_stats(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取统计概览"""
    controller = TalentController(db)
    data = controller.get_stats()
    return StandardResponse(data=data)
