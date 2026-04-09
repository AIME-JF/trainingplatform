"""
教学方向字典管理接口
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.dict_teaching_direction import DictTeachingDirection
from app.schemas import (
    DictTeachingDirectionCreate,
    DictTeachingDirectionUpdate,
    DictTeachingDirectionResponse,
    StandardResponse,
    TokenData,
)

router = APIRouter(prefix="/dict/teaching-directions", tags=["dict_management"])


@router.get("", response_model=StandardResponse[List[DictTeachingDirectionResponse]], summary="获取教学方向列表")
def list_directions(
    enabled: Optional[bool] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(DictTeachingDirection)
    if enabled is not None:
        query = query.filter(DictTeachingDirection.enabled == enabled)
    items = query.order_by(DictTeachingDirection.sort_order.asc(), DictTeachingDirection.id.asc()).all()
    return StandardResponse(data=[DictTeachingDirectionResponse.model_validate(item) for item in items])


@router.post("", response_model=StandardResponse[DictTeachingDirectionResponse], summary="创建教学方向")
def create_direction(
    data: DictTeachingDirectionCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.query(DictTeachingDirection).filter(DictTeachingDirection.name == data.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="教学方向名称已存在")
    item = DictTeachingDirection(name=data.name, sort_order=data.sort_order, enabled=data.enabled)
    db.add(item)
    db.commit()
    db.refresh(item)
    return StandardResponse(data=DictTeachingDirectionResponse.model_validate(item))


@router.put("/{item_id}", response_model=StandardResponse[DictTeachingDirectionResponse], summary="更新教学方向")
def update_direction(
    item_id: int,
    data: DictTeachingDirectionUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(DictTeachingDirection).filter(DictTeachingDirection.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教学方向不存在")
    if data.name is not None:
        dup = db.query(DictTeachingDirection).filter(
            DictTeachingDirection.name == data.name, DictTeachingDirection.id != item_id
        ).first()
        if dup:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="教学方向名称已存在")
        item.name = data.name
    if data.sort_order is not None:
        item.sort_order = data.sort_order
    if data.enabled is not None:
        item.enabled = data.enabled
    db.commit()
    db.refresh(item)
    return StandardResponse(data=DictTeachingDirectionResponse.model_validate(item))


@router.delete("/{item_id}", response_model=StandardResponse, summary="删除教学方向")
def delete_direction(
    item_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(DictTeachingDirection).filter(DictTeachingDirection.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教学方向不存在")
    db.delete(item)
    db.commit()
    return StandardResponse(data={"deleted": True})
