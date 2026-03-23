"""
训练域 AI 任务服务
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import AITask, Training, User
from app.schemas import (
    AIPersonalTrainingPlan,
    AIPersonalTrainingPortrait,
    AIPersonalTrainingTaskCreateRequest,
    AIPersonalTrainingTaskDetailResponse,
    AIPersonalTrainingTaskUpdateRequest,
    AIScheduleConflictItem,
    AIScheduleParsePreviewResponse,
    AISchedulePlan,
    AIScheduleTaskCreateRequest,
    AIScheduleTaskDetailResponse,
    AIScheduleTaskUpdateRequest,
    AITaskSummaryResponse,
    PaginatedResponse,
)
from app.services.personal_training_plan_agent import PersonalTrainingPlanAgentService
from app.services.ai_schedule_config_parser import AIScheduleConfigParserService
from app.services.schedule_agent import ScheduleAgentService
from app.services.training_schedule_rule import TrainingScheduleRuleService
from app.utils.authz import can_manage_training
from logger import logger


class TrainingAIService:
    """排课与个训任务管理服务"""

    SCHEDULE_TASK_TYPE = "schedule_generation"
    PERSONAL_TRAINING_TASK_TYPE = "personal_training_plan_generation"

    def __init__(self, db: Session):
        self.db = db
        self.schedule_agent = ScheduleAgentService(db)
        self.schedule_config_parser = AIScheduleConfigParserService()
        self.personal_plan_agent = PersonalTrainingPlanAgentService(db)

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

    def _can_delete_task(self, task: AITask) -> bool:
        if task.task_type != self.SCHEDULE_TASK_TYPE:
            return False
        return task.status != "processing"

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

    def _to_task_summary(self, task: AITask) -> AITaskSummaryResponse:
        request_payload = task.request_payload or {}
        result_payload = task.result_payload or {}
        paper_payload = result_payload.get("paper_draft") or {}
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
