"""
题库管理路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import Question
from app.schemas import (
    StandardResponse, TokenData, PaginatedResponse,
    QuestionCreate, QuestionUpdate, QuestionResponse, QuestionBatchCreate,
    QuestionFolderCreate, QuestionFolderUpdate, QuestionFolderResponse, QuestionMoveRequest
)
from app.controllers import QuestionController
from app.utils.authz import can_view_question

router = APIRouter(prefix="/questions", tags=["question_management"])


def _require_permission(current_user: TokenData, permission: str):
    if permission not in current_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"权限不足，需要权限: {permission}",
        )


@router.get("", response_model=StandardResponse[PaginatedResponse[QuestionResponse]], summary="题目列表")
def get_questions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    search: Optional[str] = None,
    type: Optional[str] = None,
    difficulty: Optional[int] = None,
    knowledge_point: Optional[str] = None,
    knowledge_point_id: Optional[int] = Query(None, description="按知识点ID筛选"),
    folder_id: Optional[int] = Query(None, description="按文件夹ID筛选"),
    recursive: bool = Query(False, description="是否递归查询子文件夹的题目"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取题目列表"""
    _require_permission(current_user, "GET_QUESTIONS")
    controller = QuestionController(db)
    data = controller.get_questions(
        page,
        size,
        search,
        type,
        difficulty,
        knowledge_point,
        knowledge_point_id,
        folder_id,
        recursive,
        current_user.user_id,
    )
    return StandardResponse(data=data)


@router.post("", response_model=StandardResponse[QuestionResponse], summary="创建题目")
def create_question(
    data: QuestionCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建题目"""
    _require_permission(current_user, "CREATE_QUESTION")
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
    _require_permission(current_user, "UPDATE_QUESTION")
    question = db.query(Question).filter(Question.id == question_id).first()
    if question and not can_view_question(db, question, current_user.user_id):
        raise HTTPException(status_code=403, detail="无权操作该题目")
    controller = QuestionController(db)
    result = controller.update_question(question_id, data, current_user.user_id)
    return StandardResponse(data=result)


@router.delete("/{question_id}", response_model=StandardResponse, summary="删除题目")
def delete_question(
    question_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除题目"""
    _require_permission(current_user, "DELETE_QUESTION")
    question = db.query(Question).filter(Question.id == question_id).first()
    if question and not can_view_question(db, question, current_user.user_id):
        raise HTTPException(status_code=403, detail="无权操作该题目")
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
    _require_permission(current_user, "BATCH_CREATE_QUESTIONS")
    controller = QuestionController(db)
    result = controller.batch_create(data, current_user.user_id)
    return StandardResponse(data=result)


# ============== 文件夹管理 ==============

@router.get("/folders", response_model=StandardResponse[list], summary="获取试题文件夹树")
def get_question_folders(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取试题文件夹树"""
    _require_permission(current_user, "GET_QUESTIONS")
    controller = QuestionController(db)
    data = controller.get_question_folders()
    return StandardResponse(data=data)


@router.post("/folders", response_model=StandardResponse, summary="创建试题文件夹")
def create_question_folder(
    data: QuestionFolderCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建试题文件夹"""
    _require_permission(current_user, "CREATE_QUESTION")
    controller = QuestionController(db)
    result = controller.create_question_folder(data, current_user.user_id)
    return StandardResponse(data=result)


@router.put("/folders/{folder_id}", response_model=StandardResponse, summary="更新试题文件夹")
def update_question_folder(
    folder_id: int,
    data: QuestionFolderUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新试题文件夹"""
    _require_permission(current_user, "UPDATE_QUESTION")
    controller = QuestionController(db)
    result = controller.update_question_folder(folder_id, data)
    return StandardResponse(data=result)


@router.delete("/folders/{folder_id}", response_model=StandardResponse, summary="删除试题文件夹")
def delete_question_folder(
    folder_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除试题文件夹"""
    _require_permission(current_user, "DELETE_QUESTION")
    controller = QuestionController(db)
    result = controller.delete_question_folder(folder_id)
    return StandardResponse(data=result)


@router.patch("/{question_id}/folder", response_model=StandardResponse[QuestionResponse], summary="移动试题到文件夹")
def move_question_to_folder(
    question_id: int,
    data: QuestionMoveRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """移动试题到文件夹"""
    _require_permission(current_user, "UPDATE_QUESTION")
    controller = QuestionController(db)
    result = controller.move_question_to_folder(question_id, data)
    return StandardResponse(data=result)
