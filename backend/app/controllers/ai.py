"""
AI功能控制器
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import AIService
from app.schemas import AIGenerateQuestionsRequest, AIGenerateLessonPlanRequest
from logger import logger


class AIController:
    """AI功能控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = AIService(db)

    def generate_questions(self, data: AIGenerateQuestionsRequest):
        try:
            return self.service.generate_questions(data)
        except Exception as e:
            logger.error(f"AI组卷异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI组卷失败")

    def generate_lesson_plan(self, data: AIGenerateLessonPlanRequest):
        try:
            return self.service.generate_lesson_plan(data)
        except Exception as e:
            logger.error(f"AI教案生成异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI教案生成失败")
