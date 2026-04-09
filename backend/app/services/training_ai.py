"""
训练域 AI 任务服务
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.models import AITask, CheckinRecord, Enrollment, Exam, ExamRecord, Training, TrainingReportSnapshot, User
from app.schemas import (
    AIPersonalTrainingPlan,
    AIPersonalTrainingPortrait,
    AIPersonalTrainingTaskCreateRequest,
    AIPersonalTrainingTaskDetailResponse,
    AIPersonalTrainingTaskUpdateRequest,
    AITrainingReportTaskCreateRequest,
    AITrainingReportTaskDetailResponse,
    AITrainingReportTaskUpdateRequest,
    AIScheduleConflictItem,
    AIScheduleParsePreviewResponse,
    AISchedulePlan,
    AIScheduleTaskCreateRequest,
    AIScheduleTaskDetailResponse,
    AIScheduleTaskUpdateRequest,
    AITaskSummaryResponse,
    PaginatedResponse,
    TrainingReportDraft,
    TrainingReportKpiItem,
)
from app.agents.personal_training_plan_agent import PersonalTrainingPlanAgentService
from app.agents.schedule_config_parser import AIScheduleConfigParserService
from app.agents.schedule_agent import ScheduleAgentService
from app.agents.training_report_agent import TrainingReportAgentService
from app.services.training_schedule_rule import TrainingScheduleRuleService
from app.utils.authz import can_manage_training
from logger import logger


class TrainingAIService:
    """排课与个训任务管理服务"""

    SCHEDULE_TASK_TYPE = "schedule_generation"
    PERSONAL_TRAINING_TASK_TYPE = "personal_training_plan_generation"
    TRAINING_REPORT_TASK_TYPE = "training_report_generation"

    def __init__(self, db: Session):
        self.db = db
        self.schedule_agent = ScheduleAgentService(db)
        self.schedule_config_parser = AIScheduleConfigParserService()
        self.personal_plan_agent = PersonalTrainingPlanAgentService(db)
        self.training_report_agent = TrainingReportAgentService()

    def list_schedule_tasks(
        self,
        page: int,
        size: int,
        status: Optional[str],
        current_user_id: int,
    ) -> PaginatedResponse[AITaskSummaryResponse]:
        return self._list_tasks(self.SCHEDULE_TASK_TYPE, page, size, status, current_user_id)

    def list_personal_training_tasks(
        self,
        page: int,
        size: int,
        status: Optional[str],
        current_user_id: int,
    ) -> PaginatedResponse[AITaskSummaryResponse]:
        return self._list_tasks(self.PERSONAL_TRAINING_TASK_TYPE, page, size, status, current_user_id, allow_target_user=True)

    def list_training_report_tasks(
        self,
        page: int,
        size: int,
        status: Optional[str],
        current_user_id: int,
        training_id: Optional[int] = None,
    ) -> PaginatedResponse[AITaskSummaryResponse]:
        query = self.db.query(AITask).filter(
            AITask.task_type == self.TRAINING_REPORT_TASK_TYPE,
        ).order_by(AITask.created_at.desc(), AITask.id.desc())
        tasks = query.all()
        filtered = []
        for item in tasks:
            if not self._can_access_task(item, current_user_id):
                continue
            if status and item.status != status:
                continue
            payload_training_id = int((item.request_payload or {}).get("training_id") or 0)
            if training_id and payload_training_id != int(training_id):
                continue
            filtered.append(item)
        total = len(filtered)
        if size != -1:
            start = (page - 1) * size
            filtered = filtered[start:start + size]
        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=[self._to_task_summary(item) for item in filtered],
        )

    def get_schedule_task_detail(self, task_id: int, current_user_id: int) -> AIScheduleTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.SCHEDULE_TASK_TYPE, current_user_id)
        return self._to_schedule_task_detail(task)

    def preview_schedule_task(
        self,
        data: AIScheduleTaskCreateRequest,
        current_user_id: int,
    ) -> AIScheduleParsePreviewResponse:
        training = self.schedule_agent._load_training_or_raise(data.training_id)  # noqa: SLF001
        self.schedule_agent._ensure_manage_permission(training, current_user_id)  # noqa: SLF001
        preview = self.schedule_config_parser.preview_task_request(training, data)
        return AIScheduleParsePreviewResponse(
            request_payload=preview["request"],
            parse_summary=preview.get("summary"),
            parse_warnings=list(preview.get("warnings") or []),
            understood_items=list(preview.get("understood_items") or []),
            training_rule_config=preview.get("training_rule_config"),
            effective_rule_config=preview.get("effective_rule_config"),
        )

    def get_personal_training_task_detail(self, task_id: int, current_user_id: int) -> AIPersonalTrainingTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.PERSONAL_TRAINING_TASK_TYPE, current_user_id, allow_target_user=True)
        return self._to_personal_training_task_detail(task)

    def get_training_report_task_detail(self, task_id: int, current_user_id: int) -> AITrainingReportTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.TRAINING_REPORT_TASK_TYPE, current_user_id)
        return self._to_training_report_task_detail(task)

    def create_schedule_task(
        self,
        data: AIScheduleTaskCreateRequest,
        current_user_id: int,
    ) -> AIScheduleTaskDetailResponse:
        training = self.schedule_agent._load_training_or_raise(data.training_id)  # noqa: SLF001
        self.schedule_agent._ensure_manage_permission(training, current_user_id)  # noqa: SLF001
        initial_stage = self._resolve_initial_schedule_task_stage(data)
        task = self._create_task_entity(
            data.task_name,
            self.SCHEDULE_TASK_TYPE,
            self._build_schedule_request_payload(data),
            current_user_id,
            status="pending",
        )
        task.result_payload = {
            "task_stage": initial_stage,
            "parse_summary": None,
            "parse_warnings": [],
            "understood_items": [],
            "main_plan": None,
            "alternative_plans": [],
            "conflicts": [],
            "explanation": None,
        }
        self.db.commit()
        self.db.refresh(task)

        try:
            from app.tasks.ai_schedule import schedule_ai_schedule_task

            schedule_ai_schedule_task(preferred_task_id=task.id, db=self.db)
            self.db.refresh(task)
        except Exception as exc:
            logger.error("调度 AI 排课任务失败: %s", exc)
        return self.get_schedule_task_detail(task.id, current_user_id)

    def execute_schedule_task(self, task_id: int) -> None:
        task = self.db.query(AITask).filter(
            AITask.id == task_id,
            AITask.task_type == self.SCHEDULE_TASK_TYPE,
        ).first()
        if not task:
            raise ValueError("任务不存在")
        if task.status in {"confirmed", "failed"}:
            return

        request_payload = AIScheduleTaskCreateRequest.model_validate(task.request_payload or {})
        training = self.schedule_agent._load_training_or_raise(request_payload.training_id)  # noqa: SLF001
        self.schedule_agent._ensure_manage_permission(training, task.created_by)  # noqa: SLF001
        task_stage = self._get_schedule_task_stage(task)
        if task_stage not in {"rule_parsing", "schedule_generation"}:
            return

        if task.status != "processing":
            task.status = "processing"
            task.started_at = task.started_at or datetime.now()
            task.completed_at = None
            task.error_message = None
            self.db.commit()

        parser_result = self.schedule_config_parser.preview_task_request(training, request_payload, parse_prompt=(task_stage == "rule_parsing"))
        effective_request = parser_result["request"]
        task.task_name = effective_request.task_name
        task.request_payload = self._build_schedule_request_payload(effective_request)

        if task_stage == "rule_parsing":
            task.result_payload = {
                **(task.result_payload or {}),
                "task_stage": "rule_confirmation",
                "parse_summary": parser_result.get("summary"),
                "parse_warnings": parser_result.get("warnings") or [],
                "understood_items": parser_result.get("understood_items") or [],
                "main_plan": None,
                "alternative_plans": [],
                "conflicts": [],
                "explanation": None,
            }
            self._mark_task_completed(task)
            self.db.commit()
            return

        task.result_payload = {
            **self.schedule_agent.build_task_result(effective_request, task.created_by),
            "task_stage": "schedule_confirmation",
            "parse_summary": parser_result.get("summary"),
            "parse_warnings": parser_result.get("warnings") or [],
            "understood_items": parser_result.get("understood_items") or [],
        }
        self._mark_task_completed(task)
        self.db.commit()

    def confirm_schedule_task_rules(
        self,
        task_id: int,
        data: AIScheduleTaskCreateRequest,
        current_user_id: int,
    ) -> AIScheduleTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.SCHEDULE_TASK_TYPE, current_user_id)
        if self._get_schedule_task_stage(task) != "rule_confirmation" or task.status != "completed":
            raise ValueError("当前任务尚未进入规则确认阶段")

        original_payload = AIScheduleTaskCreateRequest.model_validate(task.request_payload or {})
        if int(data.training_id) != int(original_payload.training_id):
            raise ValueError("规则确认时不能切换培训班")

        normalized_request = data.model_copy(update={
            "natural_language_prompt": original_payload.natural_language_prompt,
            "parsed_request_confirmed": True,
        })
        training = self.schedule_agent._load_training_or_raise(normalized_request.training_id)  # noqa: SLF001
        self.schedule_agent._ensure_manage_permission(training, current_user_id)  # noqa: SLF001
        preview = self.schedule_config_parser.preview_task_request(training, normalized_request, parse_prompt=False)
        effective_request = preview["request"]

        task.task_name = effective_request.task_name
        task.request_payload = self._build_schedule_request_payload(effective_request)
        task.status = "pending"
        task.started_at = None
        task.completed_at = None
        task.error_message = None
        task.result_payload = {
            **(task.result_payload or {}),
            "task_stage": "schedule_generation",
            "parse_summary": preview.get("summary"),
            "parse_warnings": list(preview.get("warnings") or []),
            "understood_items": list(preview.get("understood_items") or []),
            "main_plan": None,
            "alternative_plans": [],
            "conflicts": [],
            "explanation": None,
        }
        self.db.commit()
        self.db.refresh(task)

        try:
            from app.tasks.ai_schedule import schedule_ai_schedule_task

            schedule_ai_schedule_task(preferred_task_id=task.id, db=self.db)
            self.db.refresh(task)
        except Exception as exc:
            logger.error("调度 AI 排课课表生成阶段失败: %s", exc)
        return self.get_schedule_task_detail(task.id, current_user_id)

    def create_personal_training_task(
        self,
        data: AIPersonalTrainingTaskCreateRequest,
        current_user_id: int,
    ) -> AIPersonalTrainingTaskDetailResponse:
        training = self.personal_plan_agent.portrait_aggregator._load_training_or_raise(data.training_id)  # noqa: SLF001
        self.personal_plan_agent.portrait_aggregator._load_user_or_raise(data.target_user_id)  # noqa: SLF001
        self.personal_plan_agent.portrait_aggregator._ensure_access(training, data.target_user_id, current_user_id)  # noqa: SLF001
        task = self._create_task_entity(
            data.task_name,
            self.PERSONAL_TRAINING_TASK_TYPE,
            self._build_personal_request_payload(data),
            current_user_id,
        )
        try:
            task.result_payload = self.personal_plan_agent.build_task_result(data, current_user_id)
            self._mark_task_completed(task)
        except Exception as exc:
            self._mark_task_failed(task, str(exc))
            raise
        finally:
            self.db.commit()
        return self.get_personal_training_task_detail(task.id, current_user_id)

    def create_training_report_task(
        self,
        data: AITrainingReportTaskCreateRequest,
        current_user_id: int,
    ) -> AITrainingReportTaskDetailResponse:
        training = self._load_report_training_or_raise(data.training_id, current_user_id)
        task_name = data.task_name or f"{training.name}总结报告"
        task = self._create_task_entity(
            task_name,
            self.TRAINING_REPORT_TASK_TYPE,
            self._build_training_report_request_payload(data, training.name),
            current_user_id,
            status="pending",
        )
        task.result_payload = {
            "draft": None,
            "confirmed_snapshot_id": None,
        }
        self.db.commit()
        self.db.refresh(task)

        try:
            from app.tasks.ai_training_report import schedule_training_report_task

            schedule_training_report_task(preferred_task_id=task.id, db=self.db)
            self.db.refresh(task)
        except Exception as exc:
            logger.error("调度培训班总结报告 AI 任务失败: %s", exc)
        return self.get_training_report_task_detail(task.id, current_user_id)

    def execute_training_report_task(self, task_id: int) -> None:
        task = self.db.query(AITask).filter(
            AITask.id == task_id,
            AITask.task_type == self.TRAINING_REPORT_TASK_TYPE,
        ).first()
        if not task:
            raise ValueError("任务不存在")
        if task.status in {"completed", "confirmed", "failed"}:
            return

        if task.status != "processing":
            task.status = "processing"
            task.started_at = task.started_at or datetime.now()
            task.completed_at = None
            task.error_message = None
            self.db.commit()

        request_payload = AITrainingReportTaskCreateRequest.model_validate(task.request_payload or {})
        training = self._load_report_training_or_raise(request_payload.training_id, task.created_by)
        task.task_name = request_payload.task_name or f"{training.name}总结报告"
        task.request_payload = self._build_training_report_request_payload(request_payload, training.name)
        task.result_payload = {
            **(task.result_payload or {}),
            "draft": self._build_training_report_draft(training, request_payload).model_dump(mode="json"),
            "confirmed_snapshot_id": (task.result_payload or {}).get("confirmed_snapshot_id"),
        }
        self._mark_task_completed(task)
        self.db.commit()

    def update_schedule_task(
        self,
        task_id: int,
        data: AIScheduleTaskUpdateRequest,
        current_user_id: int,
    ) -> AIScheduleTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.SCHEDULE_TASK_TYPE, current_user_id)
        self._ensure_schedule_task_plan_editable(task)
        data = self.schedule_agent.validate_task_update(task, data, current_user_id)
        request_payload = AIScheduleTaskCreateRequest.model_validate(task.request_payload or {})
        main_plan_payload = data.main_plan.model_dump(mode="json")
        training = self.db.query(Training).filter(Training.id == request_payload.training_id).first()
        recalculated_conflicts = []
        if training:
            rule_config = self.schedule_agent._resolve_rule_config(training, request_payload)  # noqa: SLF001
            self.schedule_agent._normalize_plan_courses(main_plan_payload.get("courses") or [], rule_config)  # noqa: SLF001
            recalculated_conflicts = self.schedule_agent._validate_plan_courses(  # noqa: SLF001
                training,
                main_plan_payload.get("courses") or [],
                request_payload.constraint_payload,
                request_payload.overwrite_existing_schedule,
                request_payload.planning_mode,
                rule_config,
            )
            main_plan_payload["metrics"] = self.schedule_agent._build_plan_metrics(  # noqa: SLF001
                main_plan_payload.get("courses") or [],
                rule_config,
            ).model_dump(mode="json")
            main_plan_payload["summary"] = self.schedule_agent._build_plan_summary(  # noqa: SLF001
                training,
                request_payload,
                AISchedulePlan.model_validate(main_plan_payload).metrics,
                recalculated_conflicts,
                rule_config,
            )
        if data.task_name:
            task.task_name = data.task_name
        task.result_payload = {
            "task_stage": "schedule_confirmation",
            "main_plan": main_plan_payload,
            "alternative_plans": [item.model_dump(mode="json") for item in data.alternative_plans],
            "conflicts": [item.model_dump(mode="json") for item in (recalculated_conflicts or data.conflicts)],
            "explanation": data.explanation,
            "parse_summary": (task.result_payload or {}).get("parse_summary"),
            "parse_warnings": list((task.result_payload or {}).get("parse_warnings") or []),
            "understood_items": list((task.result_payload or {}).get("understood_items") or []),
        }
        self.db.commit()
        return self.get_schedule_task_detail(task_id, current_user_id)

    def delete_schedule_task(self, task_id: int, current_user_id: int) -> bool:
        task = self._get_task_or_raise(task_id, self.SCHEDULE_TASK_TYPE, current_user_id)
        self._ensure_schedule_task_deletable(task)
        self.db.delete(task)
        self.db.commit()
        return True

    def update_personal_training_task(
        self,
        task_id: int,
        data: AIPersonalTrainingTaskUpdateRequest,
        current_user_id: int,
    ) -> AIPersonalTrainingTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.PERSONAL_TRAINING_TASK_TYPE, current_user_id)
        self._ensure_task_editable(task)
        data = self.personal_plan_agent.validate_task_update(task, data, current_user_id)
        if data.task_name:
            task.task_name = data.task_name
        task.result_payload = {
            "portrait": data.portrait.model_dump(mode="json"),
            "plan": data.plan.model_dump(mode="json"),
            "confirmed_snapshot_id": (task.result_payload or {}).get("confirmed_snapshot_id"),
        }
        self.db.commit()
        return self.get_personal_training_task_detail(task_id, current_user_id)

    def update_training_report_task(
        self,
        task_id: int,
        data: AITrainingReportTaskUpdateRequest,
        current_user_id: int,
    ) -> AITrainingReportTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.TRAINING_REPORT_TASK_TYPE, current_user_id)
        self._ensure_task_editable(task)
        draft = TrainingReportDraft.model_validate((task.result_payload or {}).get("draft") or {})
        updated_title = data.title.strip() if isinstance(data.title, str) and data.title.strip() else draft.title
        updated_markdown = data.report_markdown if data.report_markdown is not None else draft.report_markdown
        if data.task_name:
            task.task_name = data.task_name
        task.result_payload = {
            **(task.result_payload or {}),
            "draft": draft.model_copy(update={
                "title": updated_title,
                "report_markdown": updated_markdown,
            }).model_dump(mode="json"),
        }
        self.db.commit()
        return self.get_training_report_task_detail(task_id, current_user_id)

    def confirm_schedule_task(self, task_id: int, current_user_id: int) -> AIScheduleTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.SCHEDULE_TASK_TYPE, current_user_id)
        self._ensure_schedule_task_confirmable(task)
        self.schedule_agent.confirm_task(task, current_user_id)
        task.status = "confirmed"
        task.confirmed_at = datetime.now()
        task.result_payload = {
            **(task.result_payload or {}),
            "task_stage": "schedule_confirmation",
        }
        self.db.commit()
        return self.get_schedule_task_detail(task_id, current_user_id)

    def confirm_personal_training_task(self, task_id: int, current_user_id: int) -> AIPersonalTrainingTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.PERSONAL_TRAINING_TASK_TYPE, current_user_id)
        self._ensure_task_confirmable(task)
        snapshot = self.personal_plan_agent.confirm_task(task, current_user_id)
        task.status = "confirmed"
        task.confirmed_at = datetime.now()
        task.result_payload = {
            **(task.result_payload or {}),
            "confirmed_snapshot_id": snapshot.id,
        }
        self.db.commit()
        return self.get_personal_training_task_detail(task_id, current_user_id)

    def confirm_training_report_task(self, task_id: int, current_user_id: int) -> AITrainingReportTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.TRAINING_REPORT_TASK_TYPE, current_user_id)
        self._ensure_task_confirmable(task)
        snapshot = self._confirm_training_report_snapshot(task, current_user_id)
        task.status = "confirmed"
        task.confirmed_at = datetime.now()
        task.result_payload = {
            **(task.result_payload or {}),
            "confirmed_snapshot_id": snapshot.id,
        }
        self.db.commit()
        return self.get_training_report_task_detail(task_id, current_user_id)

    def delete_training_report_task(self, task_id: int, current_user_id: int) -> bool:
        task = self._get_task_or_raise(task_id, self.TRAINING_REPORT_TASK_TYPE, current_user_id)
        self._ensure_training_report_task_deletable(task)
        self.db.delete(task)
        self.db.commit()
        return True

    def _list_tasks(
        self,
        task_type: str,
        page: int,
        size: int,
        status: Optional[str],
        current_user_id: int,
        allow_target_user: bool = False,
    ) -> PaginatedResponse[AITaskSummaryResponse]:
        query = self.db.query(AITask).filter(AITask.task_type == task_type).order_by(AITask.created_at.desc(), AITask.id.desc())
        tasks = query.all()
        filtered = [
            item for item in tasks
            if self._can_access_task(item, current_user_id, allow_target_user=allow_target_user)
            and (not status or item.status == status)
        ]
        total = len(filtered)
        if size != -1:
            start = (page - 1) * size
            filtered = filtered[start:start + size]
        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=[self._to_task_summary(item) for item in filtered],
        )

    def _create_task_entity(
        self,
        task_name: str,
        task_type: str,
        request_payload: dict,
        current_user_id: int,
        status: str = "processing",
    ) -> AITask:
        task = AITask(
            task_name=task_name,
            task_type=task_type,
            status=status,
            request_payload=request_payload,
            created_by=current_user_id,
            started_at=datetime.now() if status == "processing" else None,
        )
        self.db.add(task)
        self.db.flush()
        return task

    def _mark_task_completed(self, task: AITask) -> None:
        task.status = "completed"
        task.completed_at = datetime.now()
        task.error_message = None

    def _mark_task_failed(self, task: AITask, error_message: str) -> None:
        task.status = "failed"
        task.completed_at = datetime.now()
        task.error_message = error_message

    def _get_task_or_raise(
        self,
        task_id: int,
        task_type: str,
        current_user_id: int,
        allow_target_user: bool = False,
    ) -> AITask:
        task = self.db.query(AITask).filter(
            AITask.id == task_id,
            AITask.task_type == task_type,
        ).first()
        if not task or not self._can_access_task(task, current_user_id, allow_target_user=allow_target_user):
            raise ValueError("任务不存在")
        return task

    def _can_access_task(self, task: AITask, current_user_id: int, allow_target_user: bool = False) -> bool:
        request_payload = task.request_payload or {}
        training_id = int(request_payload.get("training_id") or 0)
        if task.task_type == self.SCHEDULE_TASK_TYPE:
            if not training_id:
                return False
            training = self.db.query(Training).filter(Training.id == training_id).first()
            return bool(training and can_manage_training(self.db, training, current_user_id))

        if task.created_by == current_user_id:
            return True

        if training_id:
            training = self.db.query(Training).filter(Training.id == training_id).first()
            if training and can_manage_training(self.db, training, current_user_id):
                return True

        if not allow_target_user or task.status != "confirmed":
            return False
        return int(request_payload.get("target_user_id") or 0) == current_user_id

    def _ensure_task_editable(self, task: AITask) -> None:
        if task.status == "confirmed":
            raise ValueError("任务已确认完成，不能继续编辑")
        if task.status != "completed":
            raise ValueError("任务未完成，暂不能编辑结果")

    def _ensure_task_confirmable(self, task: AITask) -> None:
        if task.status == "confirmed":
            raise ValueError("任务已确认完成")
        if task.status != "completed":
            raise ValueError("任务未完成，不能确认")

    def _ensure_schedule_task_plan_editable(self, task: AITask) -> None:
        self._ensure_task_editable(task)
        if self._get_schedule_task_stage(task) != "schedule_confirmation":
            raise ValueError("当前任务尚未进入课表确认阶段，暂不能编辑课表结果")

    def _ensure_schedule_task_confirmable(self, task: AITask) -> None:
        self._ensure_task_confirmable(task)
        if self._get_schedule_task_stage(task) != "schedule_confirmation":
            raise ValueError("当前任务尚未生成可确认的课表方案")

    def _ensure_schedule_task_deletable(self, task: AITask) -> None:
        if task.status == "processing":
            raise ValueError("任务处理中，暂不能删除")

    def _ensure_training_report_task_deletable(self, task: AITask) -> None:
        if task.status == "processing":
            raise ValueError("任务处理中，暂不能删除")
        if task.status == "confirmed":
            raise ValueError("已确认发布的报告任务不能删除")

    def _can_delete_task(self, task: AITask) -> bool:
        if task.task_type == self.SCHEDULE_TASK_TYPE:
            return task.status != "processing"
        if task.task_type == self.TRAINING_REPORT_TASK_TYPE:
            return task.status not in {"processing", "confirmed"}
        return False

    def _build_schedule_request_payload(self, data: AIScheduleTaskCreateRequest) -> dict:
        training = self.db.query(Training).filter(Training.id == data.training_id).first()
        payload = data.model_dump(mode="json")
        payload["training_name"] = training.name if training else None
        return payload

    def _build_personal_request_payload(self, data: AIPersonalTrainingTaskCreateRequest) -> dict:
        training = self.db.query(Training).filter(Training.id == data.training_id).first()
        user = self.db.query(User).filter(User.id == data.target_user_id).first()
        payload = data.model_dump(mode="json")
        payload["training_name"] = training.name if training else None
        payload["target_user_name"] = (user.nickname or user.username) if user else None
        return payload

    def _build_training_report_request_payload(self, data: AITrainingReportTaskCreateRequest, training_name: str) -> dict:
        payload = data.model_dump(mode="json")
        payload["task_name"] = data.task_name or f"{training_name}总结报告"
        payload["training_name"] = training_name
        return payload

    def _to_task_summary(self, task: AITask) -> AITaskSummaryResponse:
        request_payload = task.request_payload or {}
        result_payload = task.result_payload or {}
        paper_payload = result_payload.get("paper_draft") or {}
        draft_payload = result_payload.get("draft") or {}
        summary_text = None
        item_count = 0
        confirmed_snapshot_id = result_payload.get("confirmed_snapshot_id")
        task_stage = result_payload.get("task_stage")

        if task.task_type == self.SCHEDULE_TASK_TYPE:
            main_plan = result_payload.get("main_plan") or {}
            metrics = main_plan.get("metrics") or {}
            if task_stage == "rule_confirmation":
                item_count = 0
                summary_text = result_payload.get("parse_summary")
            else:
                item_count = int(metrics.get("total_sessions") or 0)
                summary_text = main_plan.get("summary") or result_payload.get("explanation") or result_payload.get("parse_summary")
        elif task.task_type == self.PERSONAL_TRAINING_TASK_TYPE:
            plan = result_payload.get("plan") or {}
            item_count = len(plan.get("actions") or [])
            summary_text = plan.get("summary")
        elif task.task_type == self.TRAINING_REPORT_TASK_TYPE:
            item_count = len(draft_payload.get("kpi_overview") or [])
            summary_text = draft_payload.get("title") or task.error_message or task.task_name

        return AITaskSummaryResponse(
            id=task.id,
            task_name=task.task_name,
            task_type=task.task_type,
            status=task.status,
            task_stage=task_stage,
            item_count=item_count,
            paper_title=paper_payload.get("title"),
            training_id=request_payload.get("training_id"),
            training_name=request_payload.get("training_name"),
            target_user_id=request_payload.get("target_user_id"),
            target_user_name=request_payload.get("target_user_name"),
            summary_text=summary_text,
            created_by=task.created_by,
            confirmed_question_ids=list(task.confirmed_question_ids or []),
            confirmed_paper_id=task.confirmed_paper_id,
            confirmed_snapshot_id=confirmed_snapshot_id,
            can_delete=self._can_delete_task(task),
            created_at=task.created_at,
            completed_at=task.completed_at,
            confirmed_at=task.confirmed_at,
            updated_at=task.updated_at,
        )

    def _to_schedule_task_detail(self, task: AITask) -> AIScheduleTaskDetailResponse:
        result_payload = task.result_payload or {}
        main_plan_payload = result_payload.get("main_plan")
        request_payload = AIScheduleTaskCreateRequest.model_validate(task.request_payload or {})
        training = self.schedule_agent._load_training_or_raise(request_payload.training_id)  # noqa: SLF001
        training_rule_config = TrainingScheduleRuleService.resolve_effective_rule_config(training.schedule_rule_config)
        effective_rule_config = TrainingScheduleRuleService.resolve_effective_rule_config(
            training.schedule_rule_config,
            request_payload.schedule_rule_override.model_dump(mode="json") if request_payload.schedule_rule_override else None,
        )
        return AIScheduleTaskDetailResponse(
            **self._to_task_summary(task).model_dump(),
            request_payload=request_payload,
            main_plan=AISchedulePlan.model_validate(main_plan_payload) if main_plan_payload else None,
            alternative_plans=[AISchedulePlan.model_validate(item) for item in (result_payload.get("alternative_plans") or [])],
            conflicts=[AIScheduleConflictItem.model_validate(item) for item in (result_payload.get("conflicts") or [])],
            explanation=result_payload.get("explanation"),
            parse_summary=result_payload.get("parse_summary"),
            parse_warnings=list(result_payload.get("parse_warnings") or []),
            understood_items=list(result_payload.get("understood_items") or []),
            training_rule_config=training_rule_config,
            effective_rule_config=effective_rule_config,
            error_message=task.error_message,
        )

    def _resolve_initial_schedule_task_stage(self, data: AIScheduleTaskCreateRequest) -> str:
        if str(data.natural_language_prompt or "").strip() and not data.parsed_request_confirmed:
            return "rule_parsing"
        return "schedule_generation"

    def _get_schedule_task_stage(self, task: AITask) -> str:
        if task.task_type != self.SCHEDULE_TASK_TYPE:
            return ""
        stage = str((task.result_payload or {}).get("task_stage") or "").strip()
        if stage in {"rule_parsing", "rule_confirmation", "schedule_generation", "schedule_confirmation"}:
            return stage
        return "schedule_confirmation" if task.status == "completed" else "rule_parsing"

    def _to_personal_training_task_detail(self, task: AITask) -> AIPersonalTrainingTaskDetailResponse:
        result_payload = task.result_payload or {}
        portrait_payload = result_payload.get("portrait")
        plan_payload = result_payload.get("plan")
        return AIPersonalTrainingTaskDetailResponse(
            **self._to_task_summary(task).model_dump(),
            request_payload=AIPersonalTrainingTaskCreateRequest.model_validate(task.request_payload or {}),
            portrait=AIPersonalTrainingPortrait.model_validate(portrait_payload) if portrait_payload else None,
            plan=AIPersonalTrainingPlan.model_validate(plan_payload) if plan_payload else None,
            error_message=task.error_message,
        )

    def _to_training_report_task_detail(self, task: AITask) -> AITrainingReportTaskDetailResponse:
        result_payload = task.result_payload or {}
        draft_payload = result_payload.get("draft")
        return AITrainingReportTaskDetailResponse(
            **self._to_task_summary(task).model_dump(),
            request_payload=AITrainingReportTaskCreateRequest.model_validate(task.request_payload or {}),
            draft=TrainingReportDraft.model_validate(draft_payload) if draft_payload else None,
            error_message=task.error_message,
        )

    def _load_report_training_or_raise(self, training_id: int, current_user_id: int) -> Training:
        training = self.db.query(Training).filter(Training.id == training_id).first()
        if not training:
            raise ValueError("培训班不存在")
        if not can_manage_training(self.db, training, current_user_id):
            raise ValueError("无权管理该培训班")
        return training

    def _build_training_report_draft(
        self,
        training: Training,
        data: AITrainingReportTaskCreateRequest,
    ) -> TrainingReportDraft:
        metrics = self._collect_training_report_metrics(training.id)
        ai_result = self.training_report_agent.generate_report(
            training_name=training.name,
            metrics=metrics,
            focus_points=list(data.focus_points or []),
            extra_requirements=data.extra_requirements,
        )
        risk_items = list(ai_result.get("risk_items") or metrics["risk_items"])
        suggestions = list(ai_result.get("suggestions") or metrics["suggestions"])

        return TrainingReportDraft(
            title=str(ai_result.get("title") or f"{training.name}培训总结报告"),
            report_markdown=str(ai_result.get("report_markdown") or "").strip(),
            kpi_overview=self._build_training_report_kpis(metrics),
            attendance_summary=metrics["attendance_summary"],
            exam_summary=metrics["exam_summary"],
            risk_items=risk_items,
            suggestions=suggestions,
        )

    @staticmethod
    def _build_training_report_kpis(metrics: dict) -> List[TrainingReportKpiItem]:
        return [
            TrainingReportKpiItem(key="enrolled_count", label="报名人数", value=str(metrics["enrolled_count"]), unit="人"),
            TrainingReportKpiItem(key="attendance_rate", label="整体出勤率", value=metrics["attendance_rate_text"]),
            TrainingReportKpiItem(key="course_completion", label="课次完成率", value=metrics["course_completion_text"]),
            TrainingReportKpiItem(key="formal_pass_rate", label="正式考试通过率", value=metrics["formal_pass_rate_text"]),
            TrainingReportKpiItem(key="quiz_count", label="随堂测试场次", value=str(metrics["quiz_exam_count"]), unit="场"),
        ]

    def _collect_training_report_metrics(self, training_id: int) -> dict:
        training = self.db.query(Training).filter(Training.id == training_id).first()
        if not training:
            raise ValueError("培训班不存在")

        approved_enrollments = self.db.query(Enrollment).filter(
            Enrollment.training_id == training_id,
            Enrollment.status == "approved",
        ).all()
        enrolled_count = len(approved_enrollments)
        grouped_count = sum(1 for item in approved_enrollments if item.group_name)

        courses = list(training.courses or [])
        schedules = []
        for course in courses:
            schedules.extend(list(course.schedules or []))
        total_session_count = len(schedules)
        completed_statuses = {"completed", "checkout_open", "checkin_closed"}
        completed_session_count = sum(1 for item in schedules if str(item.get("status") or "").lower() in completed_statuses)
        course_completion_rate = (completed_session_count / total_session_count) if total_session_count else None

        attendance_records = self.db.query(CheckinRecord).filter(CheckinRecord.training_id == training_id).all()
        attendance_record_count = len(attendance_records)
        on_time_count = sum(1 for item in attendance_records if item.status == "on_time")
        late_count = sum(1 for item in attendance_records if item.status == "late")
        absent_count = sum(1 for item in attendance_records if item.status == "absent")
        attendance_present_count = attendance_record_count - absent_count
        attendance_rate = (attendance_present_count / attendance_record_count) if attendance_record_count else None

        training_exams = self.db.query(Exam).filter(Exam.training_id == training_id).all()
        formal_exams = [item for item in training_exams if (item.purpose or "").lower() != "quiz"]
        formal_exam_ids = [item.id for item in formal_exams]
        formal_records = self.db.query(ExamRecord).filter(ExamRecord.exam_id.in_(formal_exam_ids)).all() if formal_exam_ids else []
        formal_submitted_records = [item for item in formal_records if item.status != "absent"]
        formal_pass_count = sum(1 for item in formal_submitted_records if (item.result or "").lower() == "pass")
        formal_avg_score = (
            sum(float(item.score or 0) for item in formal_submitted_records) / len(formal_submitted_records)
            if formal_submitted_records else None
        )

        quiz_exams = [item for item in training_exams if (item.purpose or "").lower() == "quiz"]
        quiz_exam_ids = [item.id for item in quiz_exams]
        quiz_records = self.db.query(ExamRecord).filter(ExamRecord.exam_id.in_(quiz_exam_ids)).all() if quiz_exam_ids else []
        quiz_submitted_count = sum(1 for item in quiz_records if item.status != "absent")

        risk_items: List[str] = []
        suggestions: List[str] = []
        if enrolled_count == 0:
            risk_items.append("当前培训班还没有已通过报名的学员，报告统计数据会明显偏少。")
            suggestions.append("建议先完成招生审核或导入正式学员名单后，再发起总结报告复核。")
        if total_session_count == 0:
            risk_items.append("当前尚未形成有效课次安排，课程执行情况暂无法充分评估。")
            suggestions.append("建议先完善课程编排与课次落地，再使用报告跟踪执行质量。")
        if attendance_rate is None:
            risk_items.append("当前没有签到记录，出勤表现暂时无法准确分析。")
            suggestions.append("建议在培训执行中严格使用签到签退流程，保证后续分析口径一致。")
        elif attendance_rate < 0.85:
            risk_items.append(f"当前整体出勤率为 {self._format_percent(attendance_rate)}，低于常规管理预期。")
            suggestions.append("建议重点排查缺勤课次、迟到集中时段，并安排班主任开展针对性提醒。")
        if not formal_exams:
            risk_items.append("当前尚未组织正式考试，正式考核结果暂无法支撑结班评估。")
            suggestions.append("建议在培训关键节点配置结课考试或阶段性正式考试。")
        elif formal_submitted_records and formal_pass_count / len(formal_submitted_records) < 0.7:
            risk_items.append(f"正式考试通过率仅为 {self._format_percent(formal_pass_count / len(formal_submitted_records))}。")
            suggestions.append("建议结合错题与课程薄弱环节安排强化训练或补考。")

        attendance_data_hint = "基于签到记录统计" if attendance_record_count else "暂无签到记录"
        training_period_text = f"{training.start_date or '-'} ~ {training.end_date or '-'}"
        return {
            "training_period_text": training_period_text,
            "enrolled_count": enrolled_count,
            "grouped_count": grouped_count,
            "course_count": len(courses),
            "total_session_count": total_session_count,
            "completed_session_count": completed_session_count,
            "course_completion_text": self._format_percent(course_completion_rate),
            "attendance_record_count": attendance_record_count,
            "on_time_count": on_time_count,
            "late_count": late_count,
            "absent_count": absent_count,
            "attendance_rate_text": self._format_percent(attendance_rate),
            "attendance_data_hint": attendance_data_hint,
            "formal_exam_count": len(formal_exams),
            "formal_submitted_count": len(formal_submitted_records),
            "formal_absent_count": sum(1 for item in formal_records if item.status == "absent"),
            "formal_pass_count": formal_pass_count,
            "formal_pass_rate_text": self._format_percent(
                (formal_pass_count / len(formal_submitted_records)) if formal_submitted_records else None
            ),
            "formal_avg_score_text": "-" if formal_avg_score is None else f"{formal_avg_score:.1f}分",
            "quiz_exam_count": len(quiz_exams),
            "quiz_submitted_count": quiz_submitted_count,
            "risk_items": risk_items,
            "suggestions": suggestions,
            "attendance_summary": {
                "record_count": attendance_record_count,
                "on_time_count": on_time_count,
                "late_count": late_count,
                "absent_count": absent_count,
                "attendance_rate": attendance_rate,
                "attendance_rate_text": self._format_percent(attendance_rate),
                "total_sessions": total_session_count,
                "completed_sessions": completed_session_count,
                "course_completion_rate": course_completion_rate,
                "course_completion_rate_text": self._format_percent(course_completion_rate),
            },
            "exam_summary": {
                "formal_exam_count": len(formal_exams),
                "formal_submitted_count": len(formal_submitted_records),
                "formal_absent_count": sum(1 for item in formal_records if item.status == "absent"),
                "formal_pass_count": formal_pass_count,
                "formal_pass_rate_text": self._format_percent(
                    (formal_pass_count / len(formal_submitted_records)) if formal_submitted_records else None
                ),
                "formal_avg_score": formal_avg_score,
                "quiz_exam_count": len(quiz_exams),
                "quiz_submitted_count": quiz_submitted_count,
            },
        }

    def _confirm_training_report_snapshot(self, task: AITask, current_user_id: int) -> TrainingReportSnapshot:
        request_payload = task.request_payload or {}
        training_id = int(request_payload.get("training_id") or 0)
        if not training_id:
            raise ValueError("报告任务缺少培训班信息")
        self._load_report_training_or_raise(training_id, current_user_id)
        draft = TrainingReportDraft.model_validate((task.result_payload or {}).get("draft") or {})
        current_version = self.db.query(sa_func.max(TrainingReportSnapshot.version_no)).filter(
            TrainingReportSnapshot.training_id == training_id,
        ).scalar() or 0
        snapshot = TrainingReportSnapshot(
            ai_task_id=task.id,
            training_id=training_id,
            version_no=int(current_version) + 1,
            task_name=task.task_name,
            title=draft.title,
            request_payload=request_payload,
            kpi_overview=[item.model_dump(mode="json") for item in draft.kpi_overview],
            attendance_summary=draft.attendance_summary,
            exam_summary=draft.exam_summary,
            risk_items=draft.risk_items,
            suggestions=draft.suggestions,
            report_markdown=draft.report_markdown,
            created_by=task.created_by,
            confirmed_by=current_user_id,
            confirmed_at=datetime.now(),
        )
        self.db.add(snapshot)
        self.db.flush()
        return snapshot

    @staticmethod
    def _format_percent(value: Optional[float]) -> str:
        if value is None:
            return "-"
        return f"{round(float(value) * 100)}%"
