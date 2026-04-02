"""
题库管理控制器
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import QuestionService
from app.schemas import QuestionCreate, QuestionUpdate, QuestionBatchCreate, PaginatedResponse, QuestionFolderCreate, QuestionFolderUpdate, QuestionMoveRequest
from logger import logger


class QuestionController:
    """题库控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = QuestionService(db)

    def get_questions(self, page: int = 1, size: int = 10, search: Optional[str] = None,
                      type: Optional[str] = None, difficulty: Optional[int] = None,
                      police_type_id: Optional[int] = None,
                      knowledge_point: Optional[str] = None, knowledge_point_id: Optional[int] = None,
                      folder_id: Optional[int] = None,
                      recursive: bool = False, current_user_id: Optional[int] = None):
        try:
            return self.service.get_questions(
                page,
                size,
                search,
                type,
                difficulty,
                police_type_id,
                knowledge_point,
                knowledge_point_id,
                folder_id,
                recursive,
                current_user_id,
            )
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

    # ============== 文件夹管理 ==============

    def get_question_folders(self):
        try:
            return self.service.get_question_folders()
        except Exception as e:
            logger.error(f"获取文件夹列表异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取文件夹列表失败")

    def create_question_folder(self, data: QuestionFolderCreate, user_id: int):
        try:
            return self.service.create_question_folder(data, user_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"创建文件夹异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建文件夹失败")

    def update_question_folder(self, folder_id: int, data: QuestionFolderUpdate):
        try:
            return self.service.update_question_folder(folder_id, data)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"更新文件夹异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新文件夹失败")

    def delete_question_folder(self, folder_id: int):
        try:
            self.service.delete_question_folder(folder_id)
            return {"deleted": True}
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"删除文件夹异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除文件夹失败")

    def move_question_to_folder(self, question_id: int, data: QuestionMoveRequest):
        try:
            return self.service.move_question_to_folder(question_id, data.folder_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"移动试题异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="移动试题失败")
