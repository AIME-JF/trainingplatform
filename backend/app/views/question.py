"""
题库管理路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    StandardResponse, TokenData, PaginatedResponse,
    QuestionCreate, QuestionUpdate, QuestionResponse, QuestionBatchCreate
)
from app.controllers import QuestionController

router = APIRouter(prefix="/questions", tags=["题库管理"])


@router.get("", response_model=StandardResponse[PaginatedResponse[QuestionResponse]], summary="题目列表")
def get_questions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    search: Optional[str] = None,
    type: Optional[str] = None,
    difficulty: Optional[int] = None,
    knowledge_point: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取题目列表"""
    controller = QuestionController(db)
    data = controller.get_questions(page, size, search, type, difficulty, knowledge_point)
    return StandardResponse(data=data)


@router.post("", response_model=StandardResponse[QuestionResponse], summary="创建题目")
def create_question(
    data: QuestionCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建题目"""
    controller = QuestionController(db)
    result = controller.create_question(data, current_user.user_id)
    return StandardResponse(data=result)


@router.put("/{question_id}", response_model=StandardResponse[QuestionResponse], summary="更新题目")
def update_question(
    question_id: int,
    data: QuestionUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新题目"""
    controller = QuestionController(db)
    result = controller.update_question(question_id, data)
    return StandardResponse(data=result)


@router.delete("/{question_id}", response_model=StandardResponse, summary="删除题目")
def delete_question(
    question_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除题目"""
    controller = QuestionController(db)
    controller.delete_question(question_id)
    return StandardResponse(message="删除成功")


@router.post("/batch", response_model=StandardResponse[List[QuestionResponse]], summary="批量导入")
def batch_create(
    data: QuestionBatchCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量导入题目"""
    controller = QuestionController(db)
    result = controller.batch_create(data, current_user.user_id)
    return StandardResponse(data=result)
