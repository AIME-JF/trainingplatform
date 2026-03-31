"""
AI 任务服务
"""
from datetime import datetime
from typing import Iterable, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models import AITask, ExamPaper, KnowledgePoint, Question
from app.schemas import (
    AIPaperAssemblyTaskCreateRequest,
    AIPaperAssemblyParsedRequest,
    AIPaperAssemblyParsedTypeConfig,
    AIPaperAssemblyTaskDetailResponse,
    AIPaperAssemblyTypeConfig,
    AIPaperGenerationTaskCreateRequest,
    AIPaperGenerationTaskDetailResponse,
    AIPaperTaskUpdateRequest,
    AIQuestionTaskCreateRequest,
    AIQuestionTaskDetailResponse,
    AIQuestionTaskUpdateRequest,
    AITaskPaperDraft,
    AITaskQuestionDraft,
    AITaskSummaryResponse,
    PaginatedResponse,
    QuestionCreate,
)
from app.agents.paper_assembly_parser import AIPaperAssemblyParser
from app.services.exam import ExamService
from app.services.question import QuestionService, deduplicate_questions
from app.utils.authz import can_view_question_with_context
from app.utils.data_scope import build_data_scope_context
from logger import logger


class AIService:
    """AI 任务服务"""

    QUESTION_TASK_TYPE = "question_generation"
    PAPER_ASSEMBLY_TASK_TYPE = "paper_assembly"
    PAPER_GENERATION_TASK_TYPE = "paper_generation"
    QUESTION_TASK_MAX_COUNT = 20
    SUPPORTED_QUESTION_TYPES = ("single", "multi", "judge")
    QUESTION_TYPE_ORDER = {
        "single": 0,
        "multi": 1,
        "judge": 2,
    }

    DEFAULT_TYPE_CONFIGS = [
        AIPaperAssemblyTypeConfig(type="single", count=5, difficulty=3, score=2),
        AIPaperAssemblyTypeConfig(type="multi", count=3, difficulty=3, score=3),
        AIPaperAssemblyTypeConfig(type="judge", count=2, difficulty=2, score=1),
    ]

    def __init__(self, db: Session):
        self.db = db
        self.paper_assembly_parser = AIPaperAssemblyParser()

    def list_question_tasks(
        self,
        page: int,
        size: int,
        status: Optional[str],
        current_user_id: int,
    ) -> PaginatedResponse[AITaskSummaryResponse]:
        return self._list_tasks(self.QUESTION_TASK_TYPE, page, size, status, current_user_id)

    def list_paper_assembly_tasks(
        self,
        page: int,
        size: int,
        status: Optional[str],
        current_user_id: int,
    ) -> PaginatedResponse[AITaskSummaryResponse]:
        return self._list_tasks(self.PAPER_ASSEMBLY_TASK_TYPE, page, size, status, current_user_id)

    def list_paper_generation_tasks(
        self,
        page: int,
        size: int,
        status: Optional[str],
        current_user_id: int,
    ) -> PaginatedResponse[AITaskSummaryResponse]:
        return self._list_tasks(self.PAPER_GENERATION_TASK_TYPE, page, size, status, current_user_id)

    def get_question_task_detail(self, task_id: int, current_user_id: int) -> AIQuestionTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.QUESTION_TASK_TYPE, current_user_id)
        return self._to_question_task_detail(task)

    def get_paper_assembly_task_detail(
        self,
        task_id: int,
        current_user_id: int,
    ) -> AIPaperAssemblyTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.PAPER_ASSEMBLY_TASK_TYPE, current_user_id)
        return self._to_paper_assembly_task_detail(task)

    def get_paper_generation_task_detail(
        self,
        task_id: int,
        current_user_id: int,
    ) -> AIPaperGenerationTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.PAPER_GENERATION_TASK_TYPE, current_user_id)
        return self._to_paper_generation_task_detail(task)

    def create_question_task(
        self,
        data: AIQuestionTaskCreateRequest,
        current_user_id: int,
    ) -> AIQuestionTaskDetailResponse:
        normalized_data = self._normalize_question_task_request(data)
        task = self._create_task_entity(
            normalized_data.task_name,
            self.QUESTION_TASK_TYPE,
            normalized_data.model_dump(mode="python"),
            current_user_id,
            status="pending",
        )
        self.db.commit()
        self.db.refresh(task)

        try:
            from app.tasks.ai_question import schedule_question_task

            schedule_question_task(preferred_task_id=task.id, db=self.db)
            self.db.refresh(task)
        except Exception as exc:
            logger.error("调度 AI 智能出题任务失败: %s", exc)

        return self.get_question_task_detail(task.id, current_user_id)

    def create_paper_assembly_task(
        self,
        data: AIPaperAssemblyTaskCreateRequest,
        current_user_id: int,
    ) -> AIPaperAssemblyTaskDetailResponse:
        normalized_data = self._normalize_paper_assembly_task_request(data)
        task = self._create_task_entity(
            normalized_data.task_name,
            self.PAPER_ASSEMBLY_TASK_TYPE,
            normalized_data.model_dump(mode="python"),
            current_user_id,
            status="pending",
        )
        task.result_payload = self._build_paper_assembly_result_payload()
        self.db.commit()
        self.db.refresh(task)

        try:
            from app.tasks.ai_paper_assembly import schedule_paper_assembly_task

            schedule_paper_assembly_task(preferred_task_id=task.id, db=self.db)
            self.db.refresh(task)
        except Exception as exc:
            logger.error("调度 AI 自动组卷任务失败: %s", exc)

        return self.get_paper_assembly_task_detail(task.id, current_user_id)

    def execute_paper_assembly_task(self, task_id: int) -> None:
        task = self.db.query(AITask).filter(
            AITask.id == task_id,
            AITask.task_type == self.PAPER_ASSEMBLY_TASK_TYPE,
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

        request_payload = AIPaperAssemblyTaskCreateRequest.model_validate(task.request_payload or {})
        normalized_request = self._normalize_paper_assembly_task_request(request_payload)
        task.task_name = normalized_request.task_name
        task.request_payload = normalized_request.model_dump(mode="python")

        parsed_request = self.paper_assembly_parser.parse_request(
            normalized_request,
            self.DEFAULT_TYPE_CONFIGS,
        )
        task.result_payload = self._build_paper_assembly_result_payload(parsed_request=parsed_request)
        self.db.commit()

        paper_draft, selection_notes = self._assemble_paper_from_question_bank(
            normalized_request,
            parsed_request,
            task.created_by,
        )
        task.result_payload = self._build_paper_assembly_result_payload(
            paper_draft=paper_draft,
            parsed_request=parsed_request,
            selection_notes=selection_notes,
        )
        self._mark_task_completed(task)
        self.db.commit()

    def create_paper_generation_task(
        self,
        data: AIPaperGenerationTaskCreateRequest,
        current_user_id: int,
    ) -> AIPaperGenerationTaskDetailResponse:
        normalized_data = self._normalize_paper_generation_task_request(data)
        task = self._create_task_entity(
            normalized_data.task_name,
            self.PAPER_GENERATION_TASK_TYPE,
            normalized_data.model_dump(mode="python"),
            current_user_id,
        )
        try:
            paper_draft = self._simulate_paper_generation_result(normalized_data)
            task.result_payload = {"paper_draft": paper_draft.model_dump(mode="python")}
            self._mark_task_completed(task)
        except Exception as exc:
            self._mark_task_failed(task, str(exc))
            logger.error("AI 自动生成试卷任务失败: %s", exc)
        self.db.commit()
        return self.get_paper_generation_task_detail(task.id, current_user_id)

    def update_question_task(
        self,
        task_id: int,
        data: AIQuestionTaskUpdateRequest,
        current_user_id: int,
    ) -> AIQuestionTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.QUESTION_TASK_TYPE, current_user_id)
        self._ensure_task_editable(task)
        if data.task_name:
            task.task_name = data.task_name
        sorted_questions = self._sort_question_drafts(data.questions)
        self._validate_question_task_result(task, sorted_questions)
        task.result_payload = {
            "questions": [self._sanitize_question_draft(item).model_dump(mode="python") for item in sorted_questions],
        }
        self.db.commit()
        return self.get_question_task_detail(task_id, current_user_id)

    def update_paper_assembly_task(
        self,
        task_id: int,
        data: AIPaperTaskUpdateRequest,
        current_user_id: int,
    ) -> AIPaperAssemblyTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.PAPER_ASSEMBLY_TASK_TYPE, current_user_id)
        self._ensure_task_editable(task)
        if data.task_name:
            task.task_name = data.task_name
        result_payload = dict(task.result_payload or {})
        result_payload["paper_draft"] = self._sanitize_paper_draft(data.paper_draft).model_dump(mode="python")
        task.result_payload = result_payload
        self.db.commit()
        return self.get_paper_assembly_task_detail(task_id, current_user_id)

    def update_paper_generation_task(
        self,
        task_id: int,
        data: AIPaperTaskUpdateRequest,
        current_user_id: int,
    ) -> AIPaperGenerationTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.PAPER_GENERATION_TASK_TYPE, current_user_id)
        self._ensure_task_editable(task)
        if data.task_name:
            task.task_name = data.task_name
        task.result_payload = {
            "paper_draft": self._sanitize_paper_draft(data.paper_draft).model_dump(mode="python"),
        }
        self.db.commit()
        return self.get_paper_generation_task_detail(task_id, current_user_id)

    def confirm_question_task(self, task_id: int, current_user_id: int) -> AIQuestionTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.QUESTION_TASK_TYPE, current_user_id)
        self._ensure_task_confirmable(task)
        questions = [
            self._sanitize_question_draft(AITaskQuestionDraft.model_validate(item))
            for item in (task.result_payload or {}).get("questions", [])
        ]
        if not questions:
            raise ValueError("任务结果中没有可确认的题目")
        self._validate_question_task_result(task, questions)

        created_ids = [self._persist_question_draft(item, current_user_id).id for item in questions]
        task.confirmed_question_ids = created_ids
        task.status = "confirmed"
        task.confirmed_at = datetime.now()
        self.db.commit()
        return self.get_question_task_detail(task_id, current_user_id)

    def confirm_paper_assembly_task(
        self,
        task_id: int,
        current_user_id: int,
    ) -> AIPaperAssemblyTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.PAPER_ASSEMBLY_TASK_TYPE, current_user_id)
        self._ensure_task_confirmable(task)
        paper_id, question_ids = self._confirm_paper_task(task, current_user_id)
        task.confirmed_paper_id = paper_id
        task.confirmed_question_ids = question_ids
        task.status = "confirmed"
        task.confirmed_at = datetime.now()
        self.db.commit()
        return self.get_paper_assembly_task_detail(task_id, current_user_id)

    def confirm_paper_generation_task(
        self,
        task_id: int,
        current_user_id: int,
    ) -> AIPaperGenerationTaskDetailResponse:
        task = self._get_task_or_raise(task_id, self.PAPER_GENERATION_TASK_TYPE, current_user_id)
        self._ensure_task_confirmable(task)
        paper_id, question_ids = self._confirm_paper_task(task, current_user_id)
        task.confirmed_paper_id = paper_id
        task.confirmed_question_ids = question_ids
        task.status = "confirmed"
        task.confirmed_at = datetime.now()
        self.db.commit()
        return self.get_paper_generation_task_detail(task_id, current_user_id)

    def _confirm_paper_task(self, task: AITask, current_user_id: int) -> tuple[int, List[int]]:
        paper_payload = (task.result_payload or {}).get("paper_draft")
        if not paper_payload:
            raise ValueError("任务结果中没有可确认的试卷草稿")

        paper_draft = self._sanitize_paper_draft(AITaskPaperDraft.model_validate(paper_payload))
        ordered_question_ids = self._materialize_paper_questions(paper_draft.questions, current_user_id)
        if not ordered_question_ids:
            raise ValueError("试卷至少需要保留一道题目")

        exam_service = ExamService(self.db)
        questions = exam_service._load_questions(ordered_question_ids)
        paper = ExamPaper(
            title=paper_draft.title,
            description=paper_draft.description,
            duration=paper_draft.duration,
            total_score=paper_draft.total_score or exam_service._sum_question_scores(questions),
            passing_score=paper_draft.passing_score,
            type=paper_draft.type,
            status="draft",
            created_by=current_user_id,
        )
        self.db.add(paper)
        self.db.flush()
        exam_service._replace_paper_questions(paper.id, ordered_question_ids, questions)
        return paper.id, ordered_question_ids

    def _list_tasks(
        self,
        task_type: str,
        page: int,
        size: int,
        status: Optional[str],
        current_user_id: int,
    ) -> PaginatedResponse[AITaskSummaryResponse]:
        query = self.db.query(AITask).filter(
            AITask.task_type == task_type,
            AITask.created_by == current_user_id,
        )
        if status:
            query = query.filter(AITask.status == status)
        query = query.order_by(AITask.created_at.desc(), AITask.id.desc())

        total = query.count()
        items_query = query
        if size != -1:
            items_query = items_query.offset((page - 1) * size).limit(size)
        items = [self._to_task_summary(item) for item in items_query.all()]

        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=items,
        )

    def _create_task_entity(
        self,
        task_name: str,
        task_type: str,
        request_payload: dict,
        current_user_id: int,
        status: str = "processing",
    ) -> AITask:
        started_at = datetime.now() if status == "processing" else None
        task = AITask(
            task_name=task_name,
            task_type=task_type,
            status=status,
            request_payload=request_payload,
            created_by=current_user_id,
            started_at=started_at,
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

    def _get_task_or_raise(self, task_id: int, task_type: str, current_user_id: int) -> AITask:
        task = self.db.query(AITask).filter(
            AITask.id == task_id,
            AITask.task_type == task_type,
            AITask.created_by == current_user_id,
        ).first()
        if not task:
            raise ValueError("任务不存在")
        return task

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

    def _to_task_summary(self, task: AITask) -> AITaskSummaryResponse:
        result_payload = task.result_payload or {}
        paper_payload = result_payload.get("paper_draft") or {}
        return AITaskSummaryResponse(
            id=task.id,
            task_name=task.task_name,
            task_type=task.task_type,
            status=task.status,
            item_count=self._resolve_task_item_count(task),
            paper_title=paper_payload.get("title"),
            created_by=task.created_by,
            confirmed_question_ids=list(task.confirmed_question_ids or []),
            confirmed_paper_id=task.confirmed_paper_id,
            created_at=task.created_at,
            completed_at=task.completed_at,
            confirmed_at=task.confirmed_at,
            updated_at=task.updated_at,
        )

    def _to_question_task_detail(self, task: AITask) -> AIQuestionTaskDetailResponse:
        questions = [
            self._sanitize_question_draft(AITaskQuestionDraft.model_validate(item))
            for item in (task.result_payload or {}).get("questions", [])
        ]
        return AIQuestionTaskDetailResponse(
            **self._to_task_summary(task).model_dump(),
            request_payload=AIQuestionTaskCreateRequest.model_validate(task.request_payload or {}),
            questions=self._sort_question_drafts(questions),
            error_message=task.error_message,
        )

    def _to_paper_assembly_task_detail(self, task: AITask) -> AIPaperAssemblyTaskDetailResponse:
        result_payload = task.result_payload or {}
        paper_draft = self._extract_paper_draft(task)
        parsed_payload = result_payload.get("parsed_request")
        parsed_request = None
        if parsed_payload:
            parsed_request = AIPaperAssemblyParsedRequest.model_validate(parsed_payload)
        return AIPaperAssemblyTaskDetailResponse(
            **self._to_task_summary(task).model_dump(),
            request_payload=AIPaperAssemblyTaskCreateRequest.model_validate(task.request_payload or {}),
            paper_draft=paper_draft,
            parse_summary=result_payload.get("parse_summary") or (parsed_request.summary if parsed_request else None),
            parsed_request=parsed_request,
            selection_notes=[str(item).strip() for item in (result_payload.get("selection_notes") or []) if str(item).strip()],
            error_message=task.error_message,
        )

    def _to_paper_generation_task_detail(self, task: AITask) -> AIPaperGenerationTaskDetailResponse:
        paper_draft = self._extract_paper_draft(task)
        return AIPaperGenerationTaskDetailResponse(
            **self._to_task_summary(task).model_dump(),
            request_payload=AIPaperGenerationTaskCreateRequest.model_validate(task.request_payload or {}),
            paper_draft=paper_draft,
            error_message=task.error_message,
        )

    def _extract_paper_draft(self, task: AITask) -> Optional[AITaskPaperDraft]:
        paper_payload = (task.result_payload or {}).get("paper_draft")
        if not paper_payload:
            return None
        return self._sanitize_paper_draft(AITaskPaperDraft.model_validate(paper_payload))

    def _resolve_task_item_count(self, task: AITask) -> int:
        result_payload = task.result_payload or {}
        if task.task_type == self.QUESTION_TASK_TYPE:
            return len(result_payload.get("questions", []) or [])
        paper_payload = result_payload.get("paper_draft") or {}
        return len(paper_payload.get("questions", []) or [])

    def _normalize_question_task_request(self, data: AIQuestionTaskCreateRequest) -> AIQuestionTaskCreateRequest:
        question_count = int(data.question_count or 0)
        if question_count < 1 or question_count > self.QUESTION_TASK_MAX_COUNT:
            raise ValueError(f"AI 智能出题任务最多生成 {self.QUESTION_TASK_MAX_COUNT} 道题目")

        question_types = []
        for item in data.question_types or []:
            normalized_item = str(item).strip()
            if normalized_item and normalized_item not in question_types:
                question_types.append(normalized_item)

        if not question_types:
            question_types = ["single"]
        if len(question_types) != 1:
            raise ValueError("AI 智能出题每次只能选择一种题型")

        invalid_types = [item for item in question_types if item not in self.SUPPORTED_QUESTION_TYPES]
        if invalid_types:
            raise ValueError("AI 智能出题仅支持 single、multi、judge 三种题型")

        knowledge_points = []
        for item in data.knowledge_points or []:
            normalized_item = str(item).strip()
            if normalized_item and normalized_item not in knowledge_points:
                knowledge_points.append(normalized_item)

        task_name = str(data.task_name or "").strip()
        topic = str(data.topic or "").strip()
        if not task_name or not topic:
            raise ValueError("请填写任务名称和出题主题")

        payload = data.model_dump(mode="python")
        payload["task_name"] = task_name
        payload["topic"] = topic
        payload["source_text"] = (data.source_text or "").strip() or None
        payload["requirements"] = (data.requirements or "").strip() or None
        payload["question_count"] = question_count
        payload["question_types"] = question_types
        payload["knowledge_points"] = knowledge_points
        return AIQuestionTaskCreateRequest.model_validate(payload)

    def _normalize_paper_assembly_task_request(
        self,
        data: AIPaperAssemblyTaskCreateRequest,
    ) -> AIPaperAssemblyTaskCreateRequest:
        task_name = str(data.task_name or "").strip()
        paper_title = str(data.paper_title or "").strip()
        if not task_name or not paper_title:
            raise ValueError("请填写任务名称和试卷名称")

        type_configs = self._normalize_task_type_configs(
            data.type_configs or list(self.DEFAULT_TYPE_CONFIGS),
            "AI 自动组卷仅支持 single、multi、judge 三种题型",
        )

        exclude_question_ids = []
        seen_question_ids = set()
        for raw_item in data.exclude_question_ids or []:
            question_id = int(raw_item or 0)
            if question_id <= 0 or question_id in seen_question_ids:
                continue
            seen_question_ids.add(question_id)
            exclude_question_ids.append(question_id)

        knowledge_point_ids = self._normalize_positive_ints(data.knowledge_point_ids)
        if knowledge_point_ids:
            knowledge_points = self._resolve_knowledge_point_names(knowledge_point_ids)
        else:
            knowledge_points = self._normalize_knowledge_points(data.knowledge_points)

        payload = data.model_dump(mode="python")
        payload["task_name"] = task_name
        payload["paper_title"] = paper_title
        payload["paper_type"] = str(data.paper_type or "formal").strip() or "formal"
        payload["description"] = (data.description or "").strip() or None
        payload["requirements"] = (data.requirements or "").strip() or None
        payload["knowledge_point_ids"] = knowledge_point_ids
        payload["knowledge_points"] = knowledge_points
        payload["allow_relaxation"] = bool(data.allow_relaxation)
        payload["exclude_question_ids"] = exclude_question_ids
        payload["type_configs"] = [item.model_dump(mode="python") for item in type_configs]
        return AIPaperAssemblyTaskCreateRequest.model_validate(payload)

    def _normalize_paper_generation_task_request(
        self,
        data: AIPaperGenerationTaskCreateRequest,
    ) -> AIPaperGenerationTaskCreateRequest:
        task_name = str(data.task_name or "").strip()
        paper_title = str(data.paper_title or "").strip()
        topic = str(data.topic or "").strip()
        if not task_name or not paper_title or not topic:
            raise ValueError("请填写任务名称、试卷名称和生成主题")

        type_configs = self._normalize_task_type_configs(
            data.type_configs or list(self.DEFAULT_TYPE_CONFIGS),
            "AI 自动生成试卷仅支持 single、multi、judge 三种题型",
        )
        knowledge_points = self._normalize_knowledge_points(data.knowledge_points)

        payload = data.model_dump(mode="python")
        payload["task_name"] = task_name
        payload["paper_title"] = paper_title
        payload["paper_type"] = str(data.paper_type or "formal").strip() or "formal"
        payload["description"] = (data.description or "").strip() or None
        payload["topic"] = topic
        payload["source_text"] = (data.source_text or "").strip() or None
        payload["knowledge_points"] = knowledge_points
        payload["requirements"] = (data.requirements or "").strip() or None
        payload["type_configs"] = [item.model_dump(mode="python") for item in type_configs]
        return AIPaperGenerationTaskCreateRequest.model_validate(payload)

    def _normalize_task_type_configs(
        self,
        raw_type_configs,
        unsupported_message: str,
    ) -> List[AIPaperAssemblyTypeConfig]:
        type_configs: List[AIPaperAssemblyTypeConfig] = []
        seen_types = set()
        for item in raw_type_configs or []:
            normalized_type = str(item.type or "").strip()
            if normalized_type in seen_types:
                continue
            if normalized_type not in self.SUPPORTED_QUESTION_TYPES:
                raise ValueError(unsupported_message)
            seen_types.add(normalized_type)
            type_configs.append(
                AIPaperAssemblyTypeConfig(
                    type=normalized_type,
                    count=int(item.count or 0),
                    difficulty=item.difficulty,
                    score=int(item.score or 0),
                )
            )

        if not type_configs:
            raise ValueError("请至少配置一种题型")
        if not any(item.count > 0 for item in type_configs):
            raise ValueError("请至少将一种题型的数量设置为大于 0")
        return type_configs

    def _build_paper_assembly_result_payload(
        self,
        *,
        paper_draft: Optional[AITaskPaperDraft] = None,
        parsed_request: Optional[AIPaperAssemblyParsedRequest] = None,
        selection_notes: Optional[Iterable[str]] = None,
    ) -> dict:
        normalized_notes = [str(item).strip() for item in (selection_notes or []) if str(item).strip()]
        return {
            "paper_draft": paper_draft.model_dump(mode="python") if paper_draft else None,
            "parse_summary": parsed_request.summary if parsed_request else None,
            "parsed_request": parsed_request.model_dump(mode="python") if parsed_request else None,
            "selection_notes": normalized_notes,
        }

    def _validate_question_task_result(self, task: AITask, questions: List[AITaskQuestionDraft]) -> None:
        request_payload = task.request_payload or {}
        allowed_types = [
            str(item).strip()
            for item in (request_payload.get("question_types") or [])
            if str(item).strip()
        ] or ["single", "multi", "judge"]

        if len(questions) > self.QUESTION_TASK_MAX_COUNT and int(request_payload.get("question_count") or 0) <= self.QUESTION_TASK_MAX_COUNT:
            raise ValueError(f"AI 智能出题任务最多保留 {self.QUESTION_TASK_MAX_COUNT} 道题目")

        invalid_questions = [item.type for item in questions if item.type not in allowed_types]
        if invalid_questions:
            allowed_type_names = "、".join(allowed_types)
            raise ValueError(f"当前任务仅允许题型：{allowed_type_names}")

    def _assemble_paper_from_question_bank(
        self,
        data: AIPaperAssemblyTaskCreateRequest,
        parsed_request: AIPaperAssemblyParsedRequest,
        current_user_id: int,
    ) -> tuple[AITaskPaperDraft, List[str]]:
        drafts: List[AITaskQuestionDraft] = []
        used_question_ids = {int(item) for item in (data.exclude_question_ids or []) if item}
        selection_notes: List[str] = []
        selected_knowledge_point_ids = self._normalize_positive_ints(data.knowledge_point_ids)

        parsed_type_configs = parsed_request.type_configs or [
            AIPaperAssemblyParsedTypeConfig(
                type=item.type,
                count=item.count,
                difficulty=item.difficulty,
                score=item.score,
                knowledge_points=parsed_request.knowledge_points,
                police_type_id=parsed_request.police_type_id,
            )
            for item in (data.type_configs or list(self.DEFAULT_TYPE_CONFIGS))
        ]

        for config in parsed_type_configs:
            selected_questions, notes = self._select_questions_for_assembly_type(
                config=config,
                global_police_type_id=parsed_request.police_type_id,
                global_knowledge_point_ids=selected_knowledge_point_ids,
                global_knowledge_points=parsed_request.knowledge_points,
                allow_relaxation=bool(data.allow_relaxation),
                used_question_ids=used_question_ids,
                current_user_id=current_user_id,
            )
            selection_notes.extend(notes)
            for question in selected_questions:
                used_question_ids.add(question.id)
                drafts.append(
                    self._question_to_draft(
                        question,
                        origin="existing",
                        difficulty=None,
                        score=config.score,
                    )
                )

        if not drafts:
            raise ValueError("未能根据当前条件从题库筛出任何题目")

        return self._build_paper_draft(
            title=data.paper_title,
            description=data.description,
            paper_type=data.paper_type,
            duration=data.duration,
            passing_score=data.passing_score,
            questions=drafts,
        ), selection_notes

    def _select_questions_for_assembly_type(
        self,
        config: AIPaperAssemblyParsedTypeConfig,
        global_police_type_id: Optional[int],
        global_knowledge_point_ids: Iterable[int],
        global_knowledge_points: Iterable[str],
        allow_relaxation: bool,
        used_question_ids: set[int],
        current_user_id: int,
    ) -> tuple[List[Question], List[str]]:
        selected_questions: List[Question] = []
        selection_notes: List[str] = []
        question_type_label = self._type_label(config.type)
        target_police_type_id = config.police_type_id if config.police_type_id is not None else global_police_type_id
        target_knowledge_point_ids = self._normalize_positive_ints(global_knowledge_point_ids)
        target_keywords = (
            []
            if target_knowledge_point_ids
            else self._normalize_knowledge_points(config.knowledge_points or global_knowledge_points)
        )

        for step_index, step in enumerate(
            self._build_assembly_relaxation_steps(
                difficulty=config.difficulty,
                knowledge_point_ids=target_knowledge_point_ids,
                knowledge_points=target_keywords,
                police_type_id=target_police_type_id,
                allow_relaxation=allow_relaxation,
            ),
            start=1,
        ):
            needed = config.count - len(selected_questions)
            if needed <= 0:
                break

            candidates = self._query_questions_for_assembly(
                question_type=config.type,
                police_type_id=target_police_type_id,
                difficulties=step["difficulties"],
                knowledge_point_ids=step["knowledge_point_ids"],
                knowledge_points=step["knowledge_points"],
                exclude_question_ids=used_question_ids | {item.id for item in selected_questions},
                current_user_id=current_user_id,
            )
            if not candidates:
                continue

            picked_questions = candidates[:needed]
            selected_questions.extend(picked_questions)
            if step_index == 1:
                selection_notes.append(f"{question_type_label}按“{step['label']}”选中 {len(picked_questions)} 道。")
            else:
                selection_notes.append(
                    f"{question_type_label}严格条件不足，已放宽到“{step['label']}”，补入 {len(picked_questions)} 道。"
                )

        missing_count = config.count - len(selected_questions)
        if missing_count > 0:
            if allow_relaxation:
                selection_notes.append(
                    f"{question_type_label}目标 {config.count} 道，当前仅选到 {len(selected_questions)} 道，仍缺 {missing_count} 道。"
                )
            else:
                selection_notes.append(
                    f"{question_type_label}未开启放宽条件，按严格条件仅选到 {len(selected_questions)} 道，仍缺 {missing_count} 道。"
                )

        return selected_questions, selection_notes

    def _build_assembly_relaxation_steps(
        self,
        *,
        difficulty: Optional[int],
        knowledge_point_ids: List[int],
        knowledge_points: List[str],
        police_type_id: Optional[int],
        allow_relaxation: bool,
    ) -> List[dict]:
        steps: List[dict] = []
        seen_keys = set()

        def add_step(difficulties: Optional[List[int]], use_knowledge_filter: bool) -> None:
            normalized_difficulties = None
            if difficulties:
                normalized_difficulties = sorted({int(item) for item in difficulties if 1 <= int(item) <= 5})
                if not normalized_difficulties:
                    normalized_difficulties = None

            point_ids = knowledge_point_ids if use_knowledge_filter else []
            keywords = knowledge_points if use_knowledge_filter and not point_ids else []
            key = (tuple(normalized_difficulties or []), tuple(point_ids), tuple(keywords))
            if key in seen_keys:
                return
            seen_keys.add(key)
            steps.append(
                {
                    "label": self._describe_assembly_step(
                        police_type_id,
                        normalized_difficulties,
                        bool(point_ids),
                        bool(keywords),
                    ),
                    "difficulties": normalized_difficulties,
                    "knowledge_point_ids": point_ids,
                    "knowledge_points": keywords,
                }
            )

        has_knowledge_filter = bool(knowledge_point_ids) or bool(knowledge_points)
        if not allow_relaxation:
            add_step([difficulty] if difficulty is not None else None, has_knowledge_filter)
            return steps

        if difficulty is not None:
            add_step([difficulty], has_knowledge_filter)
            if has_knowledge_filter:
                add_step([difficulty], False)

            nearby_difficulties = [item for item in [difficulty - 1, difficulty, difficulty + 1] if 1 <= item <= 5]
            if len(set(nearby_difficulties)) > 1:
                add_step(nearby_difficulties, has_knowledge_filter)
                if has_knowledge_filter:
                    add_step(nearby_difficulties, False)

            add_step(None, False)
            return steps

        add_step(None, has_knowledge_filter)
        if has_knowledge_filter:
            add_step(None, False)
        return steps

    def _describe_assembly_step(
        self,
        police_type_id: Optional[int],
        difficulties: Optional[List[int]],
        has_knowledge_point_ids: bool,
        has_keywords: bool,
    ) -> str:
        parts = ["题型"]
        if police_type_id is not None:
            parts.append("警种")
        if difficulties:
            if len(difficulties) == 1:
                parts.append(f"难度 {difficulties[0]}")
            else:
                parts.append("难度 " + "/".join(str(item) for item in difficulties))
        if has_knowledge_point_ids:
            parts.append("知识点")
        elif has_keywords:
            parts.append("知识点关键词")
        return " + ".join(parts) if len(parts) > 1 else "仅按题型"

    def _simulate_paper_generation_result(self, data: AIPaperGenerationTaskCreateRequest) -> AITaskPaperDraft:
        type_configs = data.type_configs or list(self.DEFAULT_TYPE_CONFIGS)
        knowledge_points = data.knowledge_points or [data.topic]
        drafts: List[AITaskQuestionDraft] = []

        for config in type_configs:
            for _ in range(config.count):
                knowledge_point = knowledge_points[len(drafts) % len(knowledge_points)]
                drafts.append(
                    self._build_generated_question_draft(
                        index=len(drafts),
                        question_type=config.type,
                        topic=data.topic,
                        knowledge_points=[knowledge_point],
                        difficulty=config.difficulty or data.difficulty,
                        police_type_id=data.police_type_id,
                        score=config.score,
                        source_text=data.source_text,
                        requirements=data.requirements,
                    )
                )

        return self._build_paper_draft(
            title=data.paper_title,
            description=data.description,
            paper_type=data.paper_type,
            duration=data.duration,
            passing_score=data.passing_score,
            questions=drafts,
        )

    def _build_paper_draft(
        self,
        title: str,
        description: Optional[str],
        paper_type: str,
        duration: int,
        passing_score: int,
        questions: List[AITaskQuestionDraft],
    ) -> AITaskPaperDraft:
        sanitized_questions = [self._sanitize_question_draft(item) for item in questions]
        total_score = sum(int(item.score or 0) for item in sanitized_questions)
        return AITaskPaperDraft(
            title=title,
            description=description,
            type=paper_type,
            duration=duration,
            passing_score=passing_score,
            total_score=total_score,
            questions=self._sort_question_drafts(sanitized_questions),
        )

    def _query_questions_for_assembly(
        self,
        *,
        question_type: str,
        police_type_id: Optional[int],
        difficulties: Optional[List[int]],
        knowledge_point_ids: Iterable[int],
        knowledge_points: Iterable[str],
        exclude_question_ids: Iterable[int],
        current_user_id: int,
    ) -> List[Question]:
        query = (
            self.db.query(Question)
            .options(selectinload(Question.knowledge_points))
            .filter(Question.type == question_type)
            .order_by(Question.created_at.desc(), Question.id.desc())
        )
        if police_type_id is not None:
            query = query.filter(Question.police_type_id == police_type_id)

        difficulty_values = [int(item) for item in (difficulties or []) if 1 <= int(item) <= 5]
        if difficulty_values:
            query = query.filter(Question.difficulty.in_(difficulty_values))

        excluded = [int(item) for item in exclude_question_ids if int(item or 0) > 0]
        if excluded:
            query = query.filter(~Question.id.in_(excluded))

        normalized_knowledge_point_ids = self._normalize_positive_ints(knowledge_point_ids)
        if normalized_knowledge_point_ids:
            query = query.join(Question.knowledge_points).filter(
                KnowledgePoint.id.in_(normalized_knowledge_point_ids)
            )
        else:
            normalized_points = self._normalize_knowledge_points(knowledge_points)
            if normalized_points:
                query = query.join(Question.knowledge_points).filter(
                    or_(
                        *[
                            KnowledgePoint.name.ilike(self._build_knowledge_point_like_pattern(item), escape="\\")
                            for item in normalized_points
                        ]
                    )
                )

        questions = deduplicate_questions(query.all())
        scope_context = build_data_scope_context(self.db, current_user_id) if current_user_id else None
        if scope_context:
            questions = [
                question
                for question in questions
                if can_view_question_with_context(scope_context, question)
            ]
        return questions

    def _resolve_knowledge_point_names(self, knowledge_point_ids: Iterable[int]) -> List[str]:
        normalized_ids = self._normalize_positive_ints(knowledge_point_ids)
        if not normalized_ids:
            return []

        knowledge_points = self.db.query(KnowledgePoint).filter(
            KnowledgePoint.id.in_(normalized_ids)
        ).all()
        knowledge_point_map = {item.id: item for item in knowledge_points}
        missing_ids = [item for item in normalized_ids if item not in knowledge_point_map]
        if missing_ids:
            missing_text = "、".join(str(item) for item in missing_ids)
            raise ValueError(f"所选知识点不存在：{missing_text}")

        ordered_names: List[str] = []
        seen = set()
        for knowledge_point_id in normalized_ids:
            knowledge_point = knowledge_point_map[knowledge_point_id]
            name = str(knowledge_point.name or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            ordered_names.append(name[:100])
        return ordered_names

    @staticmethod
    def _normalize_positive_ints(values: Iterable[int]) -> List[int]:
        normalized: List[int] = []
        seen = set()
        for raw_item in values or []:
            try:
                item = int(raw_item)
            except (TypeError, ValueError):
                continue
            if item <= 0 or item in seen:
                continue
            seen.add(item)
            normalized.append(item)
        return normalized

    def _question_to_draft(
        self,
        question: Question,
        origin: str,
        difficulty: Optional[int],
        score: Optional[int],
    ) -> AITaskQuestionDraft:
        knowledge_points = self._normalize_knowledge_points(
            item.name
            for item in sorted(
                question.knowledge_points or [],
                key=lambda knowledge_point: (knowledge_point.name or "", knowledge_point.id or 0),
            )
        )
        return self._sanitize_question_draft(
            AITaskQuestionDraft(
                temp_id=f"question-{question.id}",
                source_question_id=question.id,
                origin=origin,
                type=question.type,
                content=question.content,
                options=question.options,
                answer=question.answer,
                explanation=question.explanation,
                difficulty=difficulty or int(question.difficulty or 3),
                knowledge_points=knowledge_points,
                police_type_id=question.police_type_id,
                score=score or int(question.score or 1),
            )
        )

    def _build_generated_question_draft(
        self,
        index: int,
        question_type: str,
        topic: str,
        knowledge_points: List[str],
        difficulty: int,
        police_type_id: Optional[int],
        score: int,
        source_text: Optional[str],
        requirements: Optional[str],
    ) -> AITaskQuestionDraft:
        question_no = index + 1
        normalized_points = self._normalize_knowledge_points(knowledge_points) or [topic]
        primary_knowledge_point = normalized_points[0]
        prompt_tail = source_text[:18] if source_text else topic
        if question_type == "judge":
            options = [
                {"key": "A", "text": "正确"},
                {"key": "B", "text": "错误"},
            ]
            answer = "A"
        else:
            options = [
                {"key": "A", "text": f"{topic}要点一"},
                {"key": "B", "text": f"{primary_knowledge_point}常见误区"},
                {"key": "C", "text": f"{prompt_tail}处置要求"},
                {"key": "D", "text": "以上说法均不准确"},
            ]
            answer = "A" if question_type == "single" else ["A", "C"]

        content = f"{question_no}. 围绕“{topic}”的{primary_knowledge_point}要求，下列说法哪项最符合实战规范？"
        if question_type == "judge":
            content = f"{question_no}. 关于“{topic}”中的{primary_knowledge_point}要求，下列说法是否正确？"

        explanation = f"该题依据“{primary_knowledge_point}”抽取生成。{requirements or '请结合业务规范理解。'}"
        return self._sanitize_question_draft(
            AITaskQuestionDraft(
                temp_id=f"draft-{question_no}",
                origin="generated",
                type=question_type,
                content=content,
                options=options,
                answer=answer,
                explanation=explanation,
                difficulty=difficulty,
                knowledge_points=normalized_points,
                police_type_id=police_type_id,
                score=score,
            )
        )

    def _sanitize_paper_draft(self, draft: AITaskPaperDraft) -> AITaskPaperDraft:
        questions = self._sort_question_drafts([self._sanitize_question_draft(item) for item in draft.questions])
        return AITaskPaperDraft(
            title=draft.title,
            description=draft.description,
            type=draft.type,
            duration=draft.duration,
            passing_score=draft.passing_score,
            total_score=sum(int(item.score or 0) for item in questions),
            questions=questions,
        )

    def _sanitize_question_draft(self, draft: AITaskQuestionDraft) -> AITaskQuestionDraft:
        options = draft.options
        if draft.type == "judge":
            options = [
                {"key": "A", "text": "正确"},
                {"key": "B", "text": "错误"},
            ]
            answer = "A" if str(draft.answer) == "A" else "B"
        elif draft.type == "multi":
            answer = sorted(list(dict.fromkeys(list(draft.answer or []))))
        else:
            answer = str(draft.answer or "A")

        knowledge_points = self._normalize_knowledge_points(draft.knowledge_points or [])

        return AITaskQuestionDraft(
            temp_id=draft.temp_id,
            source_question_id=draft.source_question_id,
            origin=draft.origin,
            type=draft.type,
            content=draft.content.strip(),
            options=options,
            answer=answer,
            explanation=(draft.explanation or "").strip() or None,
            difficulty=draft.difficulty,
            knowledge_points=knowledge_points,
            police_type_id=draft.police_type_id,
            score=draft.score,
        )

    def _sort_question_drafts(self, drafts: List[AITaskQuestionDraft]) -> List[AITaskQuestionDraft]:
        return sorted(
            drafts,
            key=lambda item: self.QUESTION_TYPE_ORDER.get(item.type, len(self.QUESTION_TYPE_ORDER)),
        )

    def _materialize_paper_questions(self, drafts: List[AITaskQuestionDraft], current_user_id: int) -> List[int]:
        source_ids = [item.source_question_id for item in drafts if item.source_question_id]
        existing_questions = {}
        if source_ids:
            existing_questions = {
                item.id: item
                for item in self.db.query(Question).options(
                    selectinload(Question.knowledge_points)
                ).filter(Question.id.in_(source_ids)).all()
            }

        ordered_ids: List[int] = []
        for draft in drafts:
            draft = self._sanitize_question_draft(draft)
            source_question = existing_questions.get(draft.source_question_id or 0)
            if source_question and self._question_matches_draft(source_question, draft):
                ordered_ids.append(source_question.id)
                continue
            ordered_ids.append(self._persist_question_draft(draft, current_user_id).id)
        return ordered_ids

    def _persist_question_draft(self, draft: AITaskQuestionDraft, current_user_id: int) -> Question:
        question_service = QuestionService(self.db)
        return question_service._create_question_entity(
            QuestionCreate(
                type=draft.type,
                content=draft.content,
                options=draft.options,
                answer=draft.answer,
                explanation=draft.explanation,
                difficulty=draft.difficulty,
                knowledge_point_names=draft.knowledge_points,
                police_type_id=draft.police_type_id,
                score=draft.score,
            ),
            current_user_id,
        )

    def _question_matches_draft(self, question: Question, draft: AITaskQuestionDraft) -> bool:
        return (
            question.type == draft.type
            and (question.content or "").strip() == draft.content
            and (question.options or []) == (draft.options or [])
            and self._normalize_answer(question.answer) == self._normalize_answer(draft.answer)
            and ((question.explanation or "").strip() or None) == draft.explanation
            and int(question.difficulty or 0) == int(draft.difficulty or 0)
            and self._normalize_knowledge_points(
                item.name
                for item in sorted(
                    question.knowledge_points or [],
                    key=lambda knowledge_point: (knowledge_point.name or "", knowledge_point.id or 0),
                )
            ) == draft.knowledge_points
            and question.police_type_id == draft.police_type_id
            and int(question.score or 0) == int(draft.score or 0)
        )

    @staticmethod
    def _normalize_knowledge_points(knowledge_points: Iterable[str]) -> List[str]:
        normalized: List[str] = []
        seen = set()
        for raw_item in knowledge_points or []:
            item = str(raw_item or "").strip()
            if not item or item in seen:
                continue
            seen.add(item)
            normalized.append(item[:100])
        return normalized

    def _normalize_answer(self, answer):
        if isinstance(answer, list):
            return sorted(str(item) for item in answer)
        if answer is None:
            return None
        return str(answer)

    @staticmethod
    def _build_knowledge_point_like_pattern(keyword: str) -> str:
        escaped = str(keyword or "").replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        return f"%{escaped}%"

    @staticmethod
    def _type_label(question_type: str) -> str:
        return {
            "single": "单选题",
            "multi": "多选题",
            "judge": "判断题",
        }.get(question_type, question_type)
