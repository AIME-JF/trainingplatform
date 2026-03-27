"""教学资源生成任务服务"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.agents.teaching_resource_content_agent import TeachingResourceContentAgent
from app.agents.teaching_resource_parser import TeachingResourceParserAgent
from app.models import AITask, TeachingResourceGenerationSnapshot
from app.schemas import (
    TeachingResourceGenerationMetaUpdateRequest,
    TeachingResourceGenerationPagePlan,
    TeachingResourceGenerationParsedRequest,
    TeachingResourceGenerationResourceMeta,
    TeachingResourceGenerationTaskCreateRequest,
    TeachingResourceGenerationTaskDetailResponse,
    TeachingResourceGenerationTemplatePayload,
    AITaskSummaryResponse,
    PaginatedResponse,
    ResourceCreate,
)
from app.services.media import MediaService
from app.services.resource import ResourceService
from app.services.teaching_resource_renderer import TeachingResourceRenderer
from app.services.teaching_resource_template_registry import (
    GENERAL_TEACHING_TEMPLATE_CODE,
    TeachingResourceTemplateRegistry,
)
from logger import logger


class TeachingResourceGenerationService:
    """教学资源生成任务服务"""

    TASK_TYPE = "resource_generation"

    def __init__(self, db: Session):
        self.db = db
        self.parser = TeachingResourceParserAgent()
        self.content_agent = TeachingResourceContentAgent()
        self.template_registry = TeachingResourceTemplateRegistry()
        self.renderer = TeachingResourceRenderer()

    def list_tasks(
        self,
        page: int,
        size: int,
        status: Optional[str],
        current_user_id: int,
    ) -> PaginatedResponse[AITaskSummaryResponse]:
        query = self.db.query(AITask).filter(
            AITask.task_type == self.TASK_TYPE,
            AITask.created_by == current_user_id,
        )
        if status:
            query = query.filter(AITask.status == status)
        query = query.order_by(AITask.created_at.desc(), AITask.id.desc())

        total = query.count()
        items_query = query
        if size != -1:
            items_query = items_query.offset((page - 1) * size).limit(size)

        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=[self._to_task_summary(item) for item in items_query.all()],
        )

    def create_task(
        self,
        data: TeachingResourceGenerationTaskCreateRequest,
        current_user_id: int,
    ) -> TeachingResourceGenerationTaskDetailResponse:
        normalized_data = self._normalize_request(data)
        pending_task_name = normalized_data.task_name or self._build_pending_task_name(normalized_data.requirements)
        task = AITask(
            task_name=pending_task_name,
            task_type=self.TASK_TYPE,
            status="pending",
            request_payload=normalized_data.model_dump(mode="python"),
            result_payload=self._build_result_payload(
                resource_meta=self._build_resource_meta_from_request(normalized_data),
            ),
            created_by=current_user_id,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        try:
            from app.tasks.teaching_resource_generation import schedule_teaching_resource_generation_task

            schedule_teaching_resource_generation_task(preferred_task_id=task.id, db=self.db)
            self.db.refresh(task)
        except Exception as exc:
            logger.error("调度教学资源生成任务失败: %s", exc)

        return self.get_task_detail(task.id, current_user_id)

    def get_task_detail(self, task_id: int, current_user_id: int) -> TeachingResourceGenerationTaskDetailResponse:
        task = self._get_task_or_raise(task_id, current_user_id)
        result_payload = task.result_payload or {}

        parsed_request = None
        if result_payload.get("parsed_request"):
            parsed_request = TeachingResourceGenerationParsedRequest.model_validate(result_payload["parsed_request"])

        selected_template = None
        if result_payload.get("selected_template"):
            selected_template = TeachingResourceGenerationTemplatePayload.model_validate(result_payload["selected_template"])

        page_plan = [
            TeachingResourceGenerationPagePlan.model_validate(item)
            for item in (result_payload.get("page_plan") or [])
        ]

        return TeachingResourceGenerationTaskDetailResponse(
            **self._to_task_summary(task).model_dump(),
            request_payload=TeachingResourceGenerationTaskCreateRequest.model_validate(task.request_payload or {}),
            resource_meta=self._extract_resource_meta(task),
            parsed_request=parsed_request,
            selected_template=selected_template,
            page_plan=page_plan,
            html_content=result_payload.get("html_content"),
            preview_title=result_payload.get("preview_title"),
            confirmed_resource_id=result_payload.get("confirmed_resource_id"),
            error_message=task.error_message,
        )

    def execute_task(self, task_id: int) -> None:
        task = self.db.query(AITask).filter(
            AITask.id == task_id,
            AITask.task_type == self.TASK_TYPE,
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

        request_payload = TeachingResourceGenerationTaskCreateRequest.model_validate(task.request_payload or {})
        normalized_request = self._normalize_request(request_payload)
        task.request_payload = normalized_request.model_dump(mode="python")

        parsed_request = self.parser.parse_request(normalized_request)
        selected_template = self.template_registry.get_template(normalized_request.template_code)
        page_plan = self.content_agent.fill_template(normalized_request, parsed_request, selected_template)
        generated_title = self._generate_resource_title(parsed_request, page_plan)
        task.task_name = f"教学资源生成：{generated_title}"
        html_content = self.renderer.render(
            title=generated_title,
            summary=normalized_request.resource_summary,
            pages=page_plan,
        )
        resource_meta = self._build_resource_meta_from_request(
            normalized_request,
            generated_title=generated_title,
        )

        task.result_payload = self._build_result_payload(
            parsed_request=parsed_request,
            selected_template=selected_template,
            page_plan=page_plan,
            html_content=html_content,
            preview_title=generated_title,
            resource_meta=resource_meta,
        )
        task.status = "completed"
        task.completed_at = datetime.now()
        task.error_message = None
        self.db.commit()

    def update_task_meta(
        self,
        task_id: int,
        data: TeachingResourceGenerationMetaUpdateRequest,
        current_user_id: int,
    ) -> TeachingResourceGenerationTaskDetailResponse:
        task = self._get_task_or_raise(task_id, current_user_id)
        if task.status == "confirmed":
            raise ValueError("任务已确认完成，不能继续修改资源基础信息")
        if task.status != "completed":
            raise ValueError("任务尚未生成预览，暂不能设置资源基础信息")

        current_meta = self._extract_resource_meta(task)
        next_meta = TeachingResourceGenerationResourceMeta(
            resource_title=current_meta.resource_title,
            resource_summary=(str(data.resource_summary or "").strip() or None),
            tags=data.tags,
            scope_type=data.scope_type,
            scope_target_ids=data.scope_target_ids,
        )

        result_payload = dict(task.result_payload or {})
        result_payload["resource_meta"] = next_meta.model_dump(mode="python")
        task.result_payload = result_payload
        self.db.commit()
        return self.get_task_detail(task_id, current_user_id)

    def confirm_task(self, task_id: int, current_user_id: int) -> TeachingResourceGenerationTaskDetailResponse:
        task = self._get_task_or_raise(task_id, current_user_id)
        self._ensure_task_confirmable(task)

        result_payload = dict(task.result_payload or {})
        resource_meta = self._extract_resource_meta(task)
        if not resource_meta.resource_title:
            raise ValueError("任务尚未生成资源标题，不能确认")
        html_content = str(result_payload.get("html_content") or "").strip()
        if not html_content:
            raise ValueError("任务结果中没有可确认的 HTML 课件")

        media_service = MediaService(self.db)
        resource_service = ResourceService(self.db)
        media_file = media_service.create_generated_text_file(
            filename=self._build_html_filename(task.id, resource_meta.resource_title),
            content=html_content,
            uploader_id=current_user_id,
            mime_type="text/html; charset=utf-8",
        )

        resource = resource_service.create_resource_entity(
            ResourceCreate(
                title=resource_meta.resource_title,
                summary=resource_meta.resource_summary,
                content_type="document",
                source_type="ugc",
                scope_type=resource_meta.scope_type,
                scope_target_ids=resource_meta.scope_target_ids,
                tags=resource_meta.tags,
                media_links=[
                    {
                        "media_file_id": media_file.id,
                        "media_role": "main",
                        "sort_order": 0,
                    }
                ],
            ),
            current_user_id,
        )
        resource.metadata_json = {
            "ai_generated": True,
            "source_task_id": task.id,
            "template_code": (task.request_payload or {}).get("template_code") or GENERAL_TEACHING_TEMPLATE_CODE,
        }
        self.db.flush()

        snapshot = TeachingResourceGenerationSnapshot(
            ai_task_id=task.id,
            resource_id=resource.id,
            media_file_id=media_file.id,
            template_code=(task.request_payload or {}).get("template_code") or GENERAL_TEACHING_TEMPLATE_CODE,
            task_name=task.task_name,
            resource_title=resource_meta.resource_title,
            request_payload=task.request_payload,
            parsed_request=result_payload.get("parsed_request"),
            template_payload=result_payload.get("selected_template"),
            page_plan=result_payload.get("page_plan"),
            html_content=html_content,
            created_by=task.created_by,
            confirmed_by=current_user_id,
        )
        self.db.add(snapshot)
        self.db.flush()

        result_payload["confirmed_resource_id"] = resource.id
        result_payload["confirmed_snapshot_id"] = snapshot.id
        task.result_payload = result_payload
        task.status = "confirmed"
        task.confirmed_at = datetime.now()
        task.completed_at = task.completed_at or datetime.now()
        task.error_message = None

        self.db.commit()
        return self.get_task_detail(task_id, current_user_id)

    def mark_task_failed(self, task_id: int, error_message: str) -> None:
        task = self.db.query(AITask).filter(
            AITask.id == task_id,
            AITask.task_type == self.TASK_TYPE,
        ).first()
        if not task:
            return
        task.status = "failed"
        task.completed_at = datetime.now()
        task.error_message = error_message
        self.db.commit()

    def _normalize_request(self, data: TeachingResourceGenerationTaskCreateRequest) -> TeachingResourceGenerationTaskCreateRequest:
        requirements = str(data.requirements or "").strip()
        if not requirements:
            raise ValueError("请填写教学资源生成要求")
        return TeachingResourceGenerationTaskCreateRequest.model_validate(
            {
                **data.model_dump(mode="python"),
                "task_name": (str(data.task_name or "").strip() or None),
                "resource_title": (str(data.resource_title or "").strip() or None),
                "resource_summary": (str(data.resource_summary or "").strip() or None),
                "requirements": requirements,
                "template_code": str(data.template_code or GENERAL_TEACHING_TEMPLATE_CODE).strip() or GENERAL_TEACHING_TEMPLATE_CODE,
            }
        )

    def _build_result_payload(
        self,
        *,
        parsed_request: TeachingResourceGenerationParsedRequest | None = None,
        selected_template: TeachingResourceGenerationTemplatePayload | None = None,
        page_plan: list[TeachingResourceGenerationPagePlan] | None = None,
        html_content: str | None = None,
        preview_title: str | None = None,
        resource_meta: TeachingResourceGenerationResourceMeta | None = None,
    ) -> dict:
        return {
            "parse_summary": parsed_request.summary if parsed_request else None,
            "parsed_request": parsed_request.model_dump(mode="python") if parsed_request else None,
            "selected_template": selected_template.model_dump(mode="python") if selected_template else None,
            "page_plan": [item.model_dump(mode="python") for item in (page_plan or [])],
            "html_content": html_content,
            "preview_title": preview_title,
            "resource_meta": resource_meta.model_dump(mode="python") if resource_meta else None,
        }

    def _get_task_or_raise(self, task_id: int, current_user_id: int) -> AITask:
        task = self.db.query(AITask).filter(
            AITask.id == task_id,
            AITask.task_type == self.TASK_TYPE,
            AITask.created_by == current_user_id,
        ).first()
        if not task:
            raise ValueError("任务不存在")
        return task

    @staticmethod
    def _ensure_task_confirmable(task: AITask) -> None:
        if task.status == "confirmed":
            raise ValueError("任务已确认完成")
        if task.status != "completed":
            raise ValueError("任务未完成，不能确认")

    def _to_task_summary(self, task: AITask) -> AITaskSummaryResponse:
        result_payload = task.result_payload or {}
        resource_meta = self._extract_resource_meta(task)
        return AITaskSummaryResponse(
            id=task.id,
            task_name=task.task_name,
            task_type=task.task_type,
            status=task.status,
            item_count=len(result_payload.get("page_plan") or []),
            summary_text=resource_meta.resource_title or result_payload.get("parse_summary"),
            created_by=task.created_by,
            confirmed_question_ids=list(task.confirmed_question_ids or []),
            confirmed_paper_id=task.confirmed_paper_id,
            confirmed_snapshot_id=result_payload.get("confirmed_snapshot_id"),
            created_at=task.created_at,
            completed_at=task.completed_at,
            confirmed_at=task.confirmed_at,
            updated_at=task.updated_at,
        )

    def _extract_resource_meta(self, task: AITask) -> TeachingResourceGenerationResourceMeta:
        result_payload = task.result_payload or {}
        raw_meta = result_payload.get("resource_meta")
        if raw_meta:
            return TeachingResourceGenerationResourceMeta.model_validate(raw_meta)

        request_payload = TeachingResourceGenerationTaskCreateRequest.model_validate(task.request_payload or {})
        return self._build_resource_meta_from_request(
            request_payload,
            generated_title=result_payload.get("preview_title"),
        )

    def _build_resource_meta_from_request(
        self,
        request_payload: TeachingResourceGenerationTaskCreateRequest,
        *,
        generated_title: str | None = None,
    ) -> TeachingResourceGenerationResourceMeta:
        return TeachingResourceGenerationResourceMeta(
            resource_title=(generated_title or request_payload.resource_title or None),
            resource_summary=request_payload.resource_summary,
            tags=request_payload.tags or [],
            scope_type=request_payload.scope_type,
            scope_target_ids=request_payload.scope_target_ids,
        )

    @staticmethod
    def _build_pending_task_name(requirements: str) -> str:
        keyword = str(requirements or "").strip().replace("\n", " ")
        if keyword:
            keyword = keyword[:18].strip()
            return f"教学资源生成：{keyword}"
        return "教学资源生成任务"

    @staticmethod
    def _generate_resource_title(
        parsed_request: TeachingResourceGenerationParsedRequest,
        page_plan: list[TeachingResourceGenerationPagePlan],
    ) -> str:
        candidates = [
            next((item.title for item in page_plan if item.slot_key == "cover" and item.title), None),
            parsed_request.theme,
        ]
        base_title = next((str(item or "").strip() for item in candidates if str(item or "").strip()), "教学资源")
        if not re.search(r"(课件|讲义|培训|教程|学习)", base_title):
            base_title = f"{base_title}课件"
        return base_title[:200]

    @staticmethod
    def _build_html_filename(task_id: int, title: str) -> str:
        base_name = re.sub(r"[\\\\/:*?\"<>|]+", "_", str(title or "").strip())[:80].strip(" ._")
        if not base_name:
            base_name = f"teaching-resource-{task_id}"
        return f"{base_name}.html"
