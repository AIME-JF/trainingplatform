"""
刷题练习路由
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.controllers import PoliceTypeController, QuestionController
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import PracticeRecord
from app.schemas import PaginatedResponse, QuestionResponse, StandardResponse, TokenData

router = APIRouter(prefix="/practice", tags=["practice"])


class SavePracticeRecordRequest(BaseModel):
    """保存练习记录请求"""
    source_type: str
    source_id: int
    source_name: Optional[str] = None
    total_count: int
    correct_count: int
    wrong_count: int
    accuracy: int
    duration: int
    question_limit: Optional[str] = None
    question_type: Optional[str] = None
    difficulty: Optional[int] = None


@router.get("/sources", response_model=StandardResponse[dict[str, Any]], summary="获取练习来源")
def get_practice_sources(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question_controller = QuestionController(db)
    police_type_controller = PoliceTypeController(db)

    knowledge_points = question_controller.get_practice_knowledge_points(current_user.user_id)
    question_folders = question_controller.get_practice_question_folders(current_user.user_id)
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
    course_id: Optional[int] = Query(None, description="按课程ID筛选"),
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
        course_id,
        visibility_mode="practice",
    )
    return StandardResponse(data=data)


@router.post("/records", response_model=StandardResponse[dict], summary="保存练习记录")
def save_practice_record(
    record: SavePracticeRecordRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存练习记录"""
    practice_record = PracticeRecord(
        user_id=current_user.user_id,
        source_type=record.source_type,
        source_id=record.source_id,
        source_name=record.source_name,
        total_count=record.total_count,
        correct_count=record.correct_count,
        wrong_count=record.wrong_count,
        accuracy=record.accuracy,
        duration=record.duration,
        question_limit=record.question_limit,
        question_type=record.question_type,
        difficulty=record.difficulty,
    )
    db.add(practice_record)
    db.commit()
    db.refresh(practice_record)
    return StandardResponse(data={"id": practice_record.id})
