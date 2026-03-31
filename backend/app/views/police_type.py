"""
警种管理路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    StandardResponse, TokenData, PaginatedResponse,
    PoliceTypeCreate, PoliceTypeUpdate, PoliceTypeSimpleResponse
)
from app.controllers import PoliceTypeController

router = APIRouter(prefix="/police-types", tags=["police_type_management"])


@router.get("", response_model=StandardResponse[PaginatedResponse[PoliceTypeSimpleResponse]], summary="警种列表")
def get_police_types(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取警种列表"""
    controller = PoliceTypeController(db)
    data = controller.get_police_types(page, size, name, is_active)
    return StandardResponse(data=data)


@router.post("", response_model=StandardResponse[PoliceTypeSimpleResponse], summary="创建警种")
def create_police_type(
    data: PoliceTypeCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建警种"""
    controller = PoliceTypeController(db)
    result = controller.create_police_type(data)
    return StandardResponse(data=result)


@router.get("/{police_type_id}", response_model=StandardResponse[PoliceTypeSimpleResponse], summary="警种详情")
def get_police_type(
    police_type_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取警种详情"""
    controller = PoliceTypeController(db)
    data = controller.get_police_type_by_id(police_type_id)
    return StandardResponse(data=data)


@router.put("/{police_type_id}", response_model=StandardResponse[PoliceTypeSimpleResponse], summary="更新警种")
def update_police_type(
    police_type_id: int,
    data: PoliceTypeUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新警种"""
    controller = PoliceTypeController(db)
    result = controller.update_police_type(police_type_id, data)
    return StandardResponse(data=result)


@router.delete("/{police_type_id}", response_model=StandardResponse, summary="删除警种")
def delete_police_type(
    police_type_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除警种"""
    controller = PoliceTypeController(db)
    controller.delete_police_type(police_type_id)
    return StandardResponse(message="删除成功")
