"""
刷题练习路由
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.controllers import KnowledgePointController, PoliceTypeController, QuestionController
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import PaginatedResponse, QuestionResponse, StandardResponse, TokenData

router = APIRouter(prefix="/practice", tags=["practice"])


@router.get("/sources", response_model=StandardResponse[dict[str, Any]], summary="获取练习来源")
def get_practice_sources(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    knowledge_point_controller = KnowledgePointController(db)
    question_controller = QuestionController(db)
    police_type_controller = PoliceTypeController(db)

    knowledge_points = knowledge_point_controller.get_knowledge_points(
        page=1,
        size=-1,
        is_active=True,
    ).items
    question_folders = question_controller.get_question_folders()
    police_types = police_type_controller.get_police_types(
        page=1,
        size=-1,
        is_active=True,
    ).items

    return StandardResponse(
        data={
            "knowledge_points": knowledge_points,
            "question_folders": question_folders,
            "police_types": police_types,
        }
    )


@router.get(
    "/questions",
    response_model=StandardResponse[PaginatedResponse[QuestionResponse]],
    summary="获取练习题目",
)
def get_practice_questions(
    page: int = Query(1, ge=1),
    size: int = Query(-1, ge=-1),
    search: Optional[str] = None,
    type: Optional[str] = None,
    difficulty: Optional[int] = None,
    police_type_id: Optional[int] = Query(None, description="按警种ID筛选"),
    knowledge_point_id: Optional[int] = Query(None, description="按知识点ID筛选"),
    folder_id: Optional[int] = Query(None, description="按文件夹ID筛选"),
    recursive: bool = Query(False, description="是否递归查询子文件夹的题目"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question_controller = QuestionController(db)
    data = question_controller.get_questions(
        page,
        size,
        search,
        type,
        difficulty,
        police_type_id,
        None,
        knowledge_point_id,
        folder_id,
        recursive,
        current_user.user_id,
    )
    return StandardResponse(data=data)
