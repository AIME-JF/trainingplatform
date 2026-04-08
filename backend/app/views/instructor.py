"""
教官授课档案与标签管理接口
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.instructor_tag import InstructorTag
from app.models.dict_instructor_specialty import DictInstructorSpecialty
from app.schemas import (
    InstructorTagCreate,
    InstructorTagResponse,
    InstructorTeachingRecordResponse,
    InstructorTeachingSummaryResponse,
    StandardResponse,
    TokenData,
)
from app.services.instructor import InstructorService
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/instructors", tags=["instructor_management"])


# ====== 授课档案 ======

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


# ====== 教官标签组 ======

@router.get("/{user_id}/tags", response_model=StandardResponse[List[InstructorTagResponse]], summary="获取教官标签组")
def get_instructor_tags(
    user_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tags = db.query(InstructorTag).filter(InstructorTag.user_id == user_id).all()
    result = []
    for tag in tags:
        result.append(InstructorTagResponse(
            id=tag.id,
            user_id=tag.user_id,
            admin_level=tag.admin_level,
            professional_level=tag.professional_level,
            specialty_id=tag.specialty_id,
            specialty_name=tag.specialty.name if tag.specialty else None,
            created_at=tag.created_at,
        ))
    return StandardResponse(data=result)


@router.post("/{user_id}/tags", response_model=StandardResponse[InstructorTagResponse], summary="添加教官标签组")
def add_instructor_tag(
    user_id: int,
    data: InstructorTagCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.admin_level not in ("厅级", "市级", "县级"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="行政级别无效")
    if data.professional_level not in ("初级", "中级", "高级"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="专业等级无效")
    if not db.query(DictInstructorSpecialty).filter(DictInstructorSpecialty.id == data.specialty_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="专长方向不存在")

    existing = db.query(InstructorTag).filter(
        InstructorTag.user_id == user_id,
        InstructorTag.admin_level == data.admin_level,
        InstructorTag.professional_level == data.professional_level,
        InstructorTag.specialty_id == data.specialty_id,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该标签组已存在")

    tag = InstructorTag(
        user_id=user_id,
        admin_level=data.admin_level,
        professional_level=data.professional_level,
        specialty_id=data.specialty_id,
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    specialty = db.query(DictInstructorSpecialty).filter(DictInstructorSpecialty.id == tag.specialty_id).first()
    return StandardResponse(data=InstructorTagResponse(
        id=tag.id,
        user_id=tag.user_id,
        admin_level=tag.admin_level,
        professional_level=tag.professional_level,
        specialty_id=tag.specialty_id,
        specialty_name=specialty.name if specialty else None,
        created_at=tag.created_at,
    ))


@router.delete("/{user_id}/tags/{tag_id}", response_model=StandardResponse, summary="删除教官标签组")
def delete_instructor_tag(
    user_id: int,
    tag_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tag = db.query(InstructorTag).filter(InstructorTag.id == tag_id, InstructorTag.user_id == user_id).first()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签组不存在")
    db.delete(tag)
    db.commit()
    return StandardResponse(data={"deleted": True})
