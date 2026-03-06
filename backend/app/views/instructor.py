"""
教官管理路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    StandardResponse, TokenData, PaginatedResponse,
    InstructorProfileCreate, InstructorResponse
)
from app.controllers import InstructorController

router = APIRouter(prefix="/instructors", tags=["教官管理"])


@router.get("", response_model=StandardResponse[PaginatedResponse[InstructorResponse]], summary="教官列表")
def get_instructors(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    search: Optional[str] = None,
    specialty: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取教官列表"""
    controller = InstructorController(db)
    data = controller.get_instructors(page, size, search, specialty)
    return StandardResponse(data=data)


@router.get("/{instructor_id}", response_model=StandardResponse[InstructorResponse], summary="教官详情")
def get_instructor(
    instructor_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取教官详情"""
    controller = InstructorController(db)
    data = controller.get_instructor_by_id(instructor_id)
    return StandardResponse(data=data)


@router.post("", response_model=StandardResponse[InstructorResponse], summary="新增教官")
def create_instructor(
    data: InstructorProfileCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """新增教官"""
    controller = InstructorController(db)
    result = controller.create_instructor(data)
    return StandardResponse(data=result)
