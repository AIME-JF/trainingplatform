"""
教官授课档案接口
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    InstructorTeachingRecordResponse,
    InstructorTeachingSummaryResponse,
    StandardResponse,
    TokenData,
)
from app.services.instructor import InstructorService
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/instructors", tags=["instructor_management"])


@router.get("/{user_id}/teaching-summary", response_model=StandardResponse[InstructorTeachingSummaryResponse], summary="教官训历聚合统计")
def get_teaching_summary(
    user_id: int,
    year: Optional[int] = Query(None, description="按年度过滤"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = InstructorService(db)
    result = service.get_teaching_summary(user_id, year)
    return StandardResponse(data=result)


@router.get("/{user_id}/teaching-records", response_model=StandardResponse[List[InstructorTeachingRecordResponse]], summary="教官授课记录列表")
def get_teaching_records(
    user_id: int,
    year: Optional[int] = Query(None, description="按年度过滤"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = InstructorService(db)
    result = service.get_teaching_records(user_id, year)
    return StandardResponse(data=result)
