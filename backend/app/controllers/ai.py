"""
AI 任务控制器
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import (
    TeachingResourceGenerationMetaUpdateRequest,
    TeachingResourceGenerationTaskCreateRequest,
    AIPersonalTrainingTaskCreateRequest,
    AIPersonalTrainingTaskUpdateRequest,
    AIPaperAssemblyTaskCreateRequest,
    AIPaperGenerationTaskCreateRequest,
    AIPaperDocumentGenerationTaskCreateRequest,
    AIPaperTaskUpdateRequest,
    AIQuestionTaskCreateRequest,
    AIQuestionTaskUpdateRequest,
    AIScheduleTaskCreateRequest,
    AIScheduleParsePreviewResponse,
    AIScheduleTaskUpdateRequest,
)
from app.services import TeachingResourceGenerationService, AIService, TrainingAIService
from logger import logger


class AIController:
    """AI 任务控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = AIService(db)
        self.teaching_resource_generation_service = TeachingResourceGenerationService(db)
        self.training_ai_service = TrainingAIService(db)

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

    def list_paper_document_generation_tasks(self, page: int, size: int, status_value: str | None, current_user_id: int):
        try:
            return self.service.list_paper_document_generation_tasks(page, size, status_value, current_user_id)
        except Exception as exc:
            logger.error("获取 AI 文档生成试卷任务列表异常: %s", exc)
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

    def get_paper_document_generation_task_detail(self, task_id: int, current_user_id: int):
        try:
            return self.service.get_paper_document_generation_task_detail(task_id, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except Exception as exc:
            logger.error("获取 AI 文档生成试卷任务详情异常: %s", exc)
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

    def create_paper_document_generation_task(self, data: AIPaperDocumentGenerationTaskCreateRequest, current_user_id: int):
        try:
            return self.service.create_paper_document_generation_task(data, current_user_id)
        except Exception as exc:
            logger.error("创建 AI 文档生成试卷任务异常: %s", exc)
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

    def update_paper_document_generation_task(self, task_id: int, data: AIPaperTaskUpdateRequest, current_user_id: int):
        try:
            return self.service.update_paper_document_generation_task(task_id, data, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("更新 AI 文档生成试卷任务异常: %s", exc)
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

    def confirm_paper_document_generation_task(self, task_id: int, current_user_id: int):
        try:
            return self.service.confirm_paper_document_generation_task(task_id, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("确认 AI 文档生成试卷任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="确认任务失败")

    def list_teaching_resource_generation_tasks(self, page: int, size: int, status_value: str | None, current_user_id: int):
        try:
            return self.teaching_resource_generation_service.list_tasks(page, size, status_value, current_user_id)
        except Exception as exc:
            logger.error("获取教学资源生成任务列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务列表失败")

    def get_teaching_resource_generation_task_detail(self, task_id: int, current_user_id: int):
        try:
            return self.teaching_resource_generation_service.get_task_detail(task_id, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except Exception as exc:
            logger.error("获取教学资源生成任务详情异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务详情失败")

    def create_teaching_resource_generation_task(self, data: TeachingResourceGenerationTaskCreateRequest, current_user_id: int):
        try:
            return self.teaching_resource_generation_service.create_task(data, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("创建教学资源生成任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建任务失败")

    def confirm_teaching_resource_generation_task(self, task_id: int, current_user_id: int):
        try:
            return self.teaching_resource_generation_service.confirm_task(task_id, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("确认教学资源生成任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="确认任务失败")

    def update_teaching_resource_generation_task_meta(
        self,
        task_id: int,
        data: TeachingResourceGenerationMetaUpdateRequest,
        current_user_id: int,
    ):
        try:
            return self.teaching_resource_generation_service.update_task_meta(task_id, data, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("更新教学资源生成任务基础信息异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新基础信息失败")

    def list_schedule_tasks(self, page: int, size: int, status_value: str | None, current_user_id: int):
        try:
            return self.training_ai_service.list_schedule_tasks(page, size, status_value, current_user_id)
        except Exception as exc:
            logger.error("获取 AI 排课任务列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务列表失败")

    def get_schedule_task_detail(self, task_id: int, current_user_id: int):
        try:
            return self.training_ai_service.get_schedule_task_detail(task_id, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except Exception as exc:
            logger.error("获取 AI 排课任务详情异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务详情失败")

    def create_schedule_task(self, data: AIScheduleTaskCreateRequest, current_user_id: int):
        try:
            return self.training_ai_service.create_schedule_task(data, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("创建 AI 排课任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建任务失败")

    def preview_schedule_task(self, data: AIScheduleTaskCreateRequest, current_user_id: int) -> AIScheduleParsePreviewResponse:
        try:
            return self.training_ai_service.preview_schedule_task(data, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("预览 AI 排课任务解析结果异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="预览排课规则失败")

    def update_schedule_task(self, task_id: int, data: AIScheduleTaskUpdateRequest, current_user_id: int):
        try:
            return self.training_ai_service.update_schedule_task(task_id, data, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("更新 AI 排课任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新任务失败")

    def delete_schedule_task(self, task_id: int, current_user_id: int):
        try:
            return self.training_ai_service.delete_schedule_task(task_id, current_user_id)
        except ValueError as exc:
            detail = str(exc)
            status_code = status.HTTP_404_NOT_FOUND if detail == "任务不存在" else status.HTTP_400_BAD_REQUEST
            raise HTTPException(status_code=status_code, detail=detail)
        except Exception as exc:
            logger.error("删除 AI 排课任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除任务失败")

    def confirm_schedule_task(self, task_id: int, current_user_id: int):
        try:
            return self.training_ai_service.confirm_schedule_task(task_id, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("确认 AI 排课任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="确认任务失败")

    def confirm_schedule_task_rules(self, task_id: int, data: AIScheduleTaskCreateRequest, current_user_id: int):
        try:
            return self.training_ai_service.confirm_schedule_task_rules(task_id, data, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("确认 AI 排课任务规则异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="确认排课规则失败")

    def list_personal_training_tasks(self, page: int, size: int, status_value: str | None, current_user_id: int):
        try:
            return self.training_ai_service.list_personal_training_tasks(page, size, status_value, current_user_id)
        except Exception as exc:
            logger.error("获取 AI 个训任务列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务列表失败")

    def get_personal_training_task_detail(self, task_id: int, current_user_id: int):
        try:
            return self.training_ai_service.get_personal_training_task_detail(task_id, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except Exception as exc:
            logger.error("获取 AI 个训任务详情异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取任务详情失败")

    def create_personal_training_task(self, data: AIPersonalTrainingTaskCreateRequest, current_user_id: int):
        try:
            return self.training_ai_service.create_personal_training_task(data, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("创建 AI 个训任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建任务失败")

    def update_personal_training_task(self, task_id: int, data: AIPersonalTrainingTaskUpdateRequest, current_user_id: int):
        try:
            return self.training_ai_service.update_personal_training_task(task_id, data, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("更新 AI 个训任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新任务失败")

    def confirm_personal_training_task(self, task_id: int, current_user_id: int):
        try:
            return self.training_ai_service.confirm_personal_training_task(task_id, current_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("确认 AI 个训任务异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="确认任务失败")
