"""
题库管理控制器
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import QuestionService
from app.schemas import QuestionCreate, QuestionUpdate, QuestionBatchCreate, PaginatedResponse
from logger import logger


class QuestionController:
    """题库控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = QuestionService(db)

    def get_questions(self, page: int = 1, size: int = 10, search: Optional[str] = None,
                      type: Optional[str] = None, difficulty: Optional[int] = None,
                      knowledge_point: Optional[str] = None, current_user_id: Optional[int] = None):
        try:
            return self.service.get_questions(page, size, search, type, difficulty, knowledge_point, current_user_id)
        except Exception as e:
            logger.error(f"获取题目列表异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取题目列表失败")

    def create_question(self, data: QuestionCreate, user_id: int):
        try:
            return self.service.create_question(data, user_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"创建题目异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建题目失败")

    def update_question(self, question_id: int, data: QuestionUpdate, user_id: Optional[int] = None):
        try:
            result = self.service.update_question(question_id, data, user_id)
            if not result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")
            return result
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新题目异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新题目失败")

    def delete_question(self, question_id: int):
        if not self.service.delete_question(question_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")
        return True

    def batch_create(self, data: QuestionBatchCreate, user_id: int):
        try:
            return self.service.batch_create(data, user_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"批量导入题目异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="批量导入题目失败")
