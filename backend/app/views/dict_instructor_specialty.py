"""
教官专长方向字典管理接口
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.dict_instructor_specialty import DictInstructorSpecialty
from app.schemas import (
    DictInstructorSpecialtyCreate,
    DictInstructorSpecialtyUpdate,
    DictInstructorSpecialtyResponse,
    StandardResponse,
    TokenData,
)

router = APIRouter(prefix="/dict/instructor-specialties", tags=["dict_management"])


@router.get("", response_model=StandardResponse[List[DictInstructorSpecialtyResponse]], summary="获取教官专长方向列表")
def list_specialties(
    enabled: Optional[bool] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(DictInstructorSpecialty)
    if enabled is not None:
        query = query.filter(DictInstructorSpecialty.enabled == enabled)
    items = query.order_by(DictInstructorSpecialty.sort_order.asc(), DictInstructorSpecialty.id.asc()).all()
    return StandardResponse(data=[DictInstructorSpecialtyResponse.model_validate(item) for item in items])


@router.post("", response_model=StandardResponse[DictInstructorSpecialtyResponse], summary="创建教官专长方向")
def create_specialty(
    data: DictInstructorSpecialtyCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.query(DictInstructorSpecialty).filter(DictInstructorSpecialty.name == data.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="专长方向名称已存在")
    item = DictInstructorSpecialty(name=data.name, sort_order=data.sort_order, enabled=data.enabled)
    db.add(item)
    db.commit()
    db.refresh(item)
    return StandardResponse(data=DictInstructorSpecialtyResponse.model_validate(item))


@router.put("/{item_id}", response_model=StandardResponse[DictInstructorSpecialtyResponse], summary="更新教官专长方向")
def update_specialty(
    item_id: int,
    data: DictInstructorSpecialtyUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(DictInstructorSpecialty).filter(DictInstructorSpecialty.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="专长方向不存在")
    if data.name is not None:
        dup = db.query(DictInstructorSpecialty).filter(
            DictInstructorSpecialty.name == data.name, DictInstructorSpecialty.id != item_id
        ).first()
        if dup:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="专长方向名称已存在")
        item.name = data.name
    if data.sort_order is not None:
        item.sort_order = data.sort_order
    if data.enabled is not None:
        item.enabled = data.enabled
    db.commit()
    db.refresh(item)
    return StandardResponse(data=DictInstructorSpecialtyResponse.model_validate(item))


@router.delete("/{item_id}", response_model=StandardResponse, summary="删除教官专长方向")
def delete_specialty(
    item_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(DictInstructorSpecialty).filter(DictInstructorSpecialty.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="专长方向不存在")
    db.delete(item)
    db.commit()
    return StandardResponse(data={"deleted": True})
