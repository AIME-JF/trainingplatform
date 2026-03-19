"""
AI 任务控制器
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import (
    AIPaperAssemblyTaskCreateRequest,
    AIPaperGenerationTaskCreateRequest,
    AIPaperTaskUpdateRequest,
    AIQuestionTaskCreateRequest,
    AIQuestionTaskUpdateRequest,
)
from app.services import AIService
from logger import logger


class AIController:
    """AI 任务控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = AIService(db)

    def list_question_tasks(self, page: int, size: int, status_value: str | None, current_user_id: int):
        try:
            return self.service.list_question_tasks(page, size, status_value, current_user_id)
        except Exception as exc:
            logger.error("获取 AI 智能出题任务列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务列表失败")

    def list_paper_assembly_tasks(self, page: int, size: int, status_value: str | None, current_user_id: int):
        try:
            return self.service.list_paper_assembly_tasks(page, size, status_value, current_user_id)
        except Exception as exc:
            logger.error("获取 AI 自动组卷任务列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务列表失败")

    def list_paper_generation_tasks(self, page: int, size: int, status_value: str | None, current_user_id: int):
        try:
            return self.service.list_paper_generation_tasks(page, size, status_value, current_user_id)
        except Exception as exc:
            logger.error("获取 AI 自动生成试卷任务列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务列表失败")

    def get_question_task_detail(self, task_id: int, current_user_id: int):
        try:
            return self.service.get_question_task_detail(task_id, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except Exception as exc:
            logger.error("获取 AI 智能出题任务详情异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务详情失败")

    def get_paper_assembly_task_detail(self, task_id: int, current_user_id: int):
        try:
            return self.service.get_paper_assembly_task_detail(task_id, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except Exception as exc:
            logger.error("获取 AI 自动组卷任务详情异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务详情失败")

    def get_paper_generation_task_detail(self, task_id: int, current_user_id: int):
        try:
            return self.service.get_paper_generation_task_detail(task_id, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except Exception as exc:
            logger.error("获取 AI 自动生成试卷任务详情异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务详情失败")

    def create_question_task(self, data: AIQuestionTaskCreateRequest, current_user_id: int):
        try:
            return self.service.create_question_task(data, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("创建 AI 智能出题任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建任务失败")

    def create_paper_assembly_task(self, data: AIPaperAssemblyTaskCreateRequest, current_user_id: int):
        try:
            return self.service.create_paper_assembly_task(data, current_user_id)
        except Exception as exc:
            logger.error("创建 AI 自动组卷任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建任务失败")

    def create_paper_generation_task(self, data: AIPaperGenerationTaskCreateRequest, current_user_id: int):
        try:
            return self.service.create_paper_generation_task(data, current_user_id)
        except Exception as exc:
            logger.error("创建 AI 自动生成试卷任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建任务失败")

    def update_question_task(self, task_id: int, data: AIQuestionTaskUpdateRequest, current_user_id: int):
        try:
            return self.service.update_question_task(task_id, data, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("更新 AI 智能出题任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新任务失败")

    def update_paper_assembly_task(self, task_id: int, data: AIPaperTaskUpdateRequest, current_user_id: int):
        try:
            return self.service.update_paper_assembly_task(task_id, data, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("更新 AI 自动组卷任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新任务失败")

    def update_paper_generation_task(self, task_id: int, data: AIPaperTaskUpdateRequest, current_user_id: int):
        try:
            return self.service.update_paper_generation_task(task_id, data, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("更新 AI 自动生成试卷任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新任务失败")

    def confirm_question_task(self, task_id: int, current_user_id: int):
        try:
            return self.service.confirm_question_task(task_id, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("确认 AI 智能出题任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="确认任务失败")

    def confirm_paper_assembly_task(self, task_id: int, current_user_id: int):
        try:
            return self.service.confirm_paper_assembly_task(task_id, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("确认 AI 自动组卷任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="确认任务失败")

    def confirm_paper_generation_task(self, task_id: int, current_user_id: int):
        try:
            return self.service.confirm_paper_generation_task(task_id, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("确认 AI 自动生成试卷任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="确认任务失败")
