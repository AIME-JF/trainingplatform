"""
知识点管理路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers import KnowledgePointController
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    KnowledgePointCreate,
    KnowledgePointResponse,
    KnowledgePointUpdate,
    PaginatedResponse,
    StandardResponse,
    TokenData,
)

router = APIRouter(prefix="/knowledge-points", tags=["知识点管理"])


def _require_permission(current_user: TokenData, permission: str):
    if permission not in current_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"权限不足，需要权限: {permission}",
        )


@router.get("", response_model=StandardResponse[PaginatedResponse[KnowledgePointResponse]], summary="知识点列表")
def get_knowledge_points(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "GET_KNOWLEDGE_POINTS")
    controller = KnowledgePointController(db)
    data = controller.get_knowledge_points(page, size, search, is_active)
    return StandardResponse(data=data)


@router.post("", response_model=StandardResponse[KnowledgePointResponse], summary="创建知识点")
def create_knowledge_point(
    data: KnowledgePointCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "CREATE_KNOWLEDGE_POINT")
    controller = KnowledgePointController(db)
    result = controller.create_knowledge_point(data, current_user.user_id)
    return StandardResponse(data=result)


@router.put("/{knowledge_point_id}", response_model=StandardResponse[KnowledgePointResponse], summary="更新知识点")
def update_knowledge_point(
    knowledge_point_id: int,
    data: KnowledgePointUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "UPDATE_KNOWLEDGE_POINT")
    controller = KnowledgePointController(db)
    result = controller.update_knowledge_point(knowledge_point_id, data)
    return StandardResponse(data=result)


@router.delete("/{knowledge_point_id}", response_model=StandardResponse, summary="删除知识点")
def delete_knowledge_point(
    knowledge_point_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_permission(current_user, "DELETE_KNOWLEDGE_POINT")
    controller = KnowledgePointController(db)
    controller.delete_knowledge_point(knowledge_point_id)
    return StandardResponse(message="删除成功")
