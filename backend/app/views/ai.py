"""
AI功能路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    StandardResponse, TokenData,
    AIGenerateQuestionsRequest, AIGenerateQuestionsResponse,
    AIGenerateLessonPlanRequest, AIGenerateLessonPlanResponse
)
from app.controllers import AIController

router = APIRouter(prefix="/ai", tags=["AI功能"])


@router.post("/generate-questions",
             response_model=StandardResponse[AIGenerateQuestionsResponse], summary="AI智能组卷")
def generate_questions(
    data: AIGenerateQuestionsRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI智能组卷"""
    controller = AIController(db)
    result = controller.generate_questions(data)
    return StandardResponse(data=result)


@router.post("/generate-lesson-plan",
             response_model=StandardResponse[AIGenerateLessonPlanResponse], summary="AI教案生成")
def generate_lesson_plan(
    data: AIGenerateLessonPlanRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI教案生成"""
    controller = AIController(db)
    result = controller.generate_lesson_plan(data)
    return StandardResponse(data=result)
