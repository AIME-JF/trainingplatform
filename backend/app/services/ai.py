"""
AI 任务服务
"""
from datetime import datetime
from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from app.models import AITask, ExamPaper, Question
from app.schemas import (
    AIPaperAssemblyTaskCreateRequest,
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
)
from app.services.exam import ExamService
from app.services.question import QuestionService
from logger import logger


class AIService:
    """AI 任务服务"""

    QUESTION_TASK_TYPE = "question_generation"
    PAPER_ASSEMBLY_TASK_TYPE = "paper_assembly"
    PAPER_GENERATION_TASK_TYPE = "paper_generation"
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
        task = self._create_task_entity(data.task_name, self.QUESTION_TASK_TYPE, data.model_dump(mode="python"), current_user_id)
        try:
            questions = self._simulate_question_task_result(data)
            task.result_payload = {
                "questions": [item.model_dump(mode="python") for item in questions],
            }
            self._mark_task_completed(task)
        except Exception as exc:
            self._mark_task_failed(task, str(exc))
            logger.error("AI 智能出题任务失败: %s", exc)
        self.db.commit()
        return self.get_question_task_detail(task.id, current_user_id)

    def create_paper_assembly_task(
        self,
        data: AIPaperAssemblyTaskCreateRequest,
        current_user_id: int,
    ) -> AIPaperAssemblyTaskDetailResponse:
        task = self._create_task_entity(data.task_name, self.PAPER_ASSEMBLY_TASK_TYPE, data.model_dump(mode="python"), current_user_id)
        try:
            paper_draft = self._simulate_paper_assembly_result(data)
            task.result_payload = {"paper_draft": paper_draft.model_dump(mode="python")}
            self._mark_task_completed(task)
        except Exception as exc:
            self._mark_task_failed(task, str(exc))
            logger.error("AI 自动组卷任务失败: %s", exc)
        self.db.commit()
        return self.get_paper_assembly_task_detail(task.id, current_user_id)

    def create_paper_generation_task(
        self,
        data: AIPaperGenerationTaskCreateRequest,
        current_user_id: int,
    ) -> AIPaperGenerationTaskDetailResponse:
        task = self._create_task_entity(data.task_name, self.PAPER_GENERATION_TASK_TYPE, data.model_dump(mode="python"), current_user_id)
        try:
            paper_draft = self._simulate_paper_generation_result(data)
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
        task.result_payload = {
            "paper_draft": self._sanitize_paper_draft(data.paper_draft).model_dump(mode="python"),
        }
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

    def _create_task_entity(self, task_name: str, task_type: str, request_payload: dict, current_user_id: int) -> AITask:
        task = AITask(
            task_name=task_name,
            task_type=task_type,
            status="processing",
            request_payload=request_payload,
            created_by=current_user_id,
            started_at=datetime.now(),
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
        paper_draft = self._extract_paper_draft(task)
        return AIPaperAssemblyTaskDetailResponse(
            **self._to_task_summary(task).model_dump(),
            request_payload=AIPaperAssemblyTaskCreateRequest.model_validate(task.request_payload or {}),
            paper_draft=paper_draft,
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

    def _simulate_question_task_result(self, data: AIQuestionTaskCreateRequest) -> List[AITaskQuestionDraft]:
        question_types = data.question_types or ["single", "multi", "judge"]
        knowledge_points = data.knowledge_points or [data.topic]
        questions: List[AITaskQuestionDraft] = []
        for index in range(data.question_count):
            question_type = question_types[index % len(question_types)]
            knowledge_point = knowledge_points[index % len(knowledge_points)]
            questions.append(
                self._build_generated_question_draft(
                    index=index,
                    question_type=question_type,
                    topic=data.topic,
                    knowledge_point=knowledge_point,
                    difficulty=data.difficulty,
                    police_type_id=data.police_type_id,
                    score=data.score,
                    source_text=data.source_text,
                    requirements=data.requirements,
                )
            )
        return self._sort_question_drafts(questions)

    def _simulate_paper_assembly_result(self, data: AIPaperAssemblyTaskCreateRequest) -> AITaskPaperDraft:
        type_configs = data.type_configs or list(self.DEFAULT_TYPE_CONFIGS)
        candidate_questions = self._load_candidate_questions(
            police_type_id=data.police_type_id,
            knowledge_points=data.knowledge_points,
            exclude_question_ids=data.exclude_question_ids,
        )
        drafts: List[AITaskQuestionDraft] = []
        used_question_ids: set[int] = set()
        knowledge_points = data.knowledge_points or [data.paper_title]

        for config in type_configs:
            typed_candidates = [
                item
                for item in candidate_questions
                if item.type == config.type and item.id not in used_question_ids
            ]
            for item_index in range(config.count):
                if typed_candidates:
                    question = typed_candidates.pop(0)
                    used_question_ids.add(question.id)
                    drafts.append(
                        self._question_to_draft(
                            question,
                            origin="existing",
                            difficulty=config.difficulty,
                            score=config.score,
                        )
                    )
                    continue

                knowledge_point = knowledge_points[(len(drafts) + item_index) % len(knowledge_points)]
                drafts.append(
                    self._build_generated_question_draft(
                        index=len(drafts),
                        question_type=config.type,
                        topic=data.paper_title,
                        knowledge_point=knowledge_point,
                        difficulty=config.difficulty or 3,
                        police_type_id=data.police_type_id,
                        score=config.score,
                        source_text=data.requirements,
                        requirements=f"组卷模式：{data.assembly_mode}",
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
                        knowledge_point=knowledge_point,
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

    def _load_candidate_questions(
        self,
        police_type_id: Optional[int],
        knowledge_points: Iterable[str],
        exclude_question_ids: Iterable[int],
    ) -> List[Question]:
        query = self.db.query(Question).order_by(Question.created_at.desc(), Question.id.desc())
        if police_type_id:
            query = query.filter(Question.police_type_id == police_type_id)
        excluded = [item for item in exclude_question_ids if item]
        if excluded:
            query = query.filter(~Question.id.in_(excluded))
        candidates = query.all()
        knowledge_points = [item for item in knowledge_points if item]
        if not knowledge_points:
            return candidates

        matched = [
            item
            for item in candidates
            if any(point in (item.knowledge_point or "") for point in knowledge_points)
        ]
        return matched or candidates

    def _question_to_draft(
        self,
        question: Question,
        origin: str,
        difficulty: Optional[int],
        score: Optional[int],
    ) -> AITaskQuestionDraft:
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
                knowledge_point=question.knowledge_point,
                police_type_id=question.police_type_id,
                score=score or int(question.score or 1),
            )
        )

    def _build_generated_question_draft(
        self,
        index: int,
        question_type: str,
        topic: str,
        knowledge_point: str,
        difficulty: int,
        police_type_id: Optional[int],
        score: int,
        source_text: Optional[str],
        requirements: Optional[str],
    ) -> AITaskQuestionDraft:
        question_no = index + 1
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
                {"key": "B", "text": f"{knowledge_point}常见误区"},
                {"key": "C", "text": f"{prompt_tail}处置要求"},
                {"key": "D", "text": "以上说法均不准确"},
            ]
            answer = "A" if question_type == "single" else ["A", "C"]

        content = f"{question_no}. 围绕“{topic}”的{knowledge_point}要求，下列说法哪项最符合实战规范？"
        if question_type == "judge":
            content = f"{question_no}. 关于“{topic}”中的{knowledge_point}要求，下列说法是否正确？"

        explanation = f"该题依据“{knowledge_point}”抽取生成。{requirements or '请结合业务规范理解。'}"
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
                knowledge_point=knowledge_point,
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
            knowledge_point=(draft.knowledge_point or "").strip() or None,
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
                for item in self.db.query(Question).filter(Question.id.in_(source_ids)).all()
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
        question_service._ensure_actor_can_assign_question_scope(current_user_id, draft.police_type_id)
        question_service._ensure_police_type(draft.police_type_id)

        question = Question(
            type=draft.type,
            content=draft.content,
            options=draft.options,
            answer=draft.answer,
            explanation=draft.explanation,
            difficulty=draft.difficulty,
            knowledge_point=draft.knowledge_point,
            police_type_id=draft.police_type_id,
            score=draft.score,
            created_by=current_user_id,
        )
        self.db.add(question)
        self.db.flush()
        return question

    def _question_matches_draft(self, question: Question, draft: AITaskQuestionDraft) -> bool:
        return (
            question.type == draft.type
            and (question.content or "").strip() == draft.content
            and (question.options or []) == (draft.options or [])
            and self._normalize_answer(question.answer) == self._normalize_answer(draft.answer)
            and ((question.explanation or "").strip() or None) == draft.explanation
            and int(question.difficulty or 0) == int(draft.difficulty or 0)
            and ((question.knowledge_point or "").strip() or None) == draft.knowledge_point
            and question.police_type_id == draft.police_type_id
            and int(question.score or 0) == int(draft.score or 0)
        )

    def _normalize_answer(self, answer):
        if isinstance(answer, list):
            return sorted(str(item) for item in answer)
        if answer is None:
            return None
        return str(answer)
