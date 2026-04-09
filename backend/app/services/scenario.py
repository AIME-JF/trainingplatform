"""
场景模拟服务
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.agents.base import BaseAIAgent
from app.models.scenario_session import ScenarioSession
from app.models.scenario_template import ScenarioTemplate
from app.services.library import LibraryService
from app.utils.authz import is_admin_user


class ScenarioService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_agent = BaseAIAgent()
        self.library_service = LibraryService(db)

    def list_templates(
        self,
        page: int,
        size: int,
        category: Optional[str],
        status_filter: Optional[str],
        user_id: Optional[int],
        *,
        is_admin: bool = False,
    ) -> dict:
        query = self.db.query(ScenarioTemplate)
        if category:
            query = query.filter(ScenarioTemplate.category == category)
        if status_filter:
            query = query.filter(ScenarioTemplate.status == status_filter)
        if user_id and not is_admin:
            query = query.filter(ScenarioTemplate.created_by == user_id)

        total = query.count()
        items = (
            query.order_by(ScenarioTemplate.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        return {
            "total": total,
            "items": [self._to_template_dict(item) for item in items],
            "page": page,
            "size": size,
        }

    def list_available_templates(self, category: Optional[str]) -> list[dict]:
        query = self.db.query(ScenarioTemplate).filter(ScenarioTemplate.status == "published")
        if category:
            query = query.filter(ScenarioTemplate.category == category)
        items = query.order_by(ScenarioTemplate.created_at.desc()).all()
        return [self._to_template_dict(item) for item in items]

    def get_template(self, template_id: int) -> Optional[dict]:
        template = self.db.query(ScenarioTemplate).filter(ScenarioTemplate.id == template_id).first()
        return self._to_template_dict(template) if template else None

    def create_template(self, data: dict, user_id: int) -> dict:
        knowledge_item_ids = self._normalize_id_list(self._read_value(data, "knowledgeItemIds", "knowledge_item_ids"))
        selected_items = self.library_service.resolve_accessible_knowledge_items(
            user_id,
            knowledge_item_ids,
            is_admin=is_admin_user(self.db, user_id),
            strict=True,
        )
        template = ScenarioTemplate(
            title=self._read_required(data, "title"),
            description=self._read_value(data, "description"),
            category=self._read_required(data, "category"),
            difficulty=self._read_value(data, "difficulty", default=3),
            estimated_minutes=self._read_value(data, "estimatedMinutes", "estimated_minutes", default=15),
            background=self._read_required(data, "background"),
            npc_role=self._read_required(data, "npcRole", "npc_role"),
            npc_name=self._read_value(data, "npcName", "npc_name"),
            npc_opening=self._read_value(data, "npcOpening", "npc_opening"),
            knowledge_base_id=self._read_value(data, "knowledgeBaseId", "knowledge_base_id"),
            knowledge_item_ids=[item.id for item in selected_items],
            checkpoints=self._read_value(data, "checkpoints", default=[]),
            created_by=user_id,
        )
        self.db.add(template)
        self.db.flush()
        return self._to_template_dict(template)

    def update_template(self, template_id: int, data: dict, user_id: int, *, is_admin: bool = False) -> Optional[dict]:
        template = self._get_manageable_template(template_id, user_id, is_admin=is_admin)
        if not template:
            return None

        field_map = {
            ("title",): "title",
            ("description",): "description",
            ("category",): "category",
            ("difficulty",): "difficulty",
            ("estimatedMinutes", "estimated_minutes"): "estimated_minutes",
            ("background",): "background",
            ("npcRole", "npc_role"): "npc_role",
            ("npcName", "npc_name"): "npc_name",
            ("npcOpening", "npc_opening"): "npc_opening",
            ("knowledgeBaseId", "knowledge_base_id"): "knowledge_base_id",
            ("checkpoints",): "checkpoints",
        }
        for source_fields, target_field in field_map.items():
            if not self._has_any_key(data, *source_fields):
                continue
            value = self._read_value(data, *source_fields)
            if value is not None:
                setattr(template, target_field, value)

        if self._has_any_key(data, "knowledgeItemIds", "knowledge_item_ids"):
            selected_items = self.library_service.resolve_accessible_knowledge_items(
                user_id,
                self._normalize_id_list(self._read_value(data, "knowledgeItemIds", "knowledge_item_ids")),
                is_admin=is_admin,
                strict=True,
            )
            template.knowledge_item_ids = [item.id for item in selected_items]

        self.db.flush()
        return self._to_template_dict(template)

    def delete_template(self, template_id: int, user_id: int, *, is_admin: bool = False) -> bool:
        template = self._get_manageable_template(template_id, user_id, is_admin=is_admin)
        if not template:
            return False
        self.db.delete(template)
        self.db.flush()
        return True

    def publish_template(self, template_id: int, user_id: int, *, is_admin: bool = False) -> Optional[dict]:
        template = self._get_manageable_template(template_id, user_id, is_admin=is_admin)
        if not template:
            return None
        template.status = "published"
        self.db.flush()
        return self._to_template_dict(template)

    def start_session(self, template_id: int, user_id: int) -> dict:
        template = self.db.query(ScenarioTemplate).filter(ScenarioTemplate.id == template_id).first()
        if not template:
            raise ValueError("场景模板不存在")
        if template.status != "published" and template.created_by != user_id and not is_admin_user(self.db, user_id):
            raise ValueError("该场景尚未发布")

        initial_messages = [{"role": "system", "content": f"场景开始：{template.background}"}]
        if template.npc_opening:
            initial_messages.append(
                {"role": "npc", "content": template.npc_opening, "npcName": template.npc_name or "当事人"}
            )

        session = ScenarioSession(
            scenario_template_id=template_id,
            user_id=user_id,
            messages=initial_messages,
        )
        self.db.add(session)
        self.db.flush()

        template.usage_count = (template.usage_count or 0) + 1
        self.db.flush()

        session = self._load_session_with_relations(session.id)
        return self._to_session_dict(session)

    def send_session_message(self, session_id: int, user_id: int, content: str) -> dict:
        session = (
            self.db.query(ScenarioSession)
            .options(joinedload(ScenarioSession.scenario_template))
            .filter(ScenarioSession.id == session_id, ScenarioSession.user_id == user_id)
            .first()
        )
        if not session:
            raise ValueError("模拟会话不存在")
        if session.status == "completed":
            raise ValueError("模拟已结束")

        template = session.scenario_template
        if not template:
            raise ValueError("场景模板不存在")

        messages = list(session.messages or [])
        messages.append({"role": "user", "content": content})

        knowledge_prompt = ""
        selected_items = self.library_service.get_knowledge_items_by_ids(list(template.knowledge_item_ids or []))
        knowledge_payload = self.library_service.build_knowledge_context(selected_items, content)
        if selected_items and knowledge_payload["context"]:
            knowledge_prompt = f"【关联知识点参考】\n{knowledge_payload['context']}\n"
        elif template.knowledge_item_ids:
            knowledge_prompt = (
                "【关联知识点参考】\n"
                "当前没有检索到与本轮对话直接相关的知识点内容，请继续保持角色一致性，"
                "不要编造具体法规、程序依据或事实细节。\n"
            )

        system_prompt = (
            "你正在扮演一个角色进行执法场景模拟训练。\n"
            f"【你的角色】{template.npc_role}\n"
            f"【角色名称】{template.npc_name or '当事人'}\n"
            f"【场景背景】{template.background}\n"
            f"{knowledge_prompt}"
            "请保持角色一致性，根据对方的表现做出合理反应。"
            "你的回复应该简短自然，符合角色身份，不要跳出角色。"
        )

        conversation_lines = []
        for item in messages:
            if item["role"] == "user":
                conversation_lines.append(f"执法人员: {item['content']}")
            elif item["role"] == "npc":
                conversation_lines.append(f"{template.npc_name or '当事人'}: {item['content']}")
            elif item["role"] == "system":
                conversation_lines.append(f"[旁白: {item['content']}]")

        npc_reply = self.ai_agent._generate_text(
            system_prompt=system_prompt,
            user_prompt="\n".join(conversation_lines[-30:]),
        )

        messages.append({"role": "npc", "content": npc_reply, "npcName": template.npc_name or "当事人"})
        session.messages = messages
        self.db.flush()

        return {
            "sessionId": session.id,
            "reply": npc_reply,
            "npcName": template.npc_name or "当事人",
            "messages": messages,
        }

    def end_session(self, session_id: int, user_id: int) -> dict:
        session = (
            self.db.query(ScenarioSession)
            .options(joinedload(ScenarioSession.scenario_template))
            .filter(ScenarioSession.id == session_id, ScenarioSession.user_id == user_id)
            .first()
        )
        if not session:
            raise ValueError("模拟会话不存在")

        template = session.scenario_template
        if not template:
            raise ValueError("场景模板不存在")

        checkpoints = template.checkpoints or []
        checkpoint_labels = "\n".join(f"- {item['label']}（{item.get('score', 10)}分）" for item in checkpoints)
        messages_text = "\n".join(
            f"{'执法人员' if item['role'] == 'user' else (item.get('npcName', '当事人') if item['role'] == 'npc' else '系统')}: {item['content']}"
            for item in (session.messages or [])
        )

        eval_prompt = (
            "请对以下执法场景模拟的对话进行评估。\n\n"
            f"【场景背景】{template.background}\n"
            f"【考察要点】\n{checkpoint_labels}\n\n"
            f"【对话记录】\n{messages_text}\n\n"
            '请以 JSON 格式返回评估结果：{"score": 0-100, "checkpoints": [{"label": "要点名称", "passed": true}], "feedback": "详细反馈"}'
        )

        try:
            result = self.ai_agent._generate_json_payload(
                system_prompt="你是一位资深的公安执法培训评估专家，请严格依据考察要点评分。",
                user_prompt=eval_prompt,
            )
            score = int(result.get("score", 0))
            checkpoint_results = result.get("checkpoints", [])
            feedback = result.get("feedback", "")
        except Exception:
            score = 60
            checkpoint_results = [{"label": item["label"], "passed": False} for item in checkpoints]
            feedback = "AI 评分暂时不可用，请联系管理员。"

        duration = None
        if session.started_at:
            now = datetime.now(timezone.utc)
            duration = max(1, int((now - session.started_at).total_seconds() / 60))

        session.status = "completed"
        session.score = score
        session.checkpoint_results = checkpoint_results
        session.feedback = feedback
        session.duration_minutes = duration
        session.completed_at = datetime.now(timezone.utc)
        self.db.flush()

        session = self._load_session_with_relations(session.id)
        return self._to_session_dict(session)

    def list_user_sessions(self, user_id: int, page: int, size: int) -> dict:
        query = (
            self.db.query(ScenarioSession)
            .options(
                joinedload(ScenarioSession.scenario_template),
                joinedload(ScenarioSession.user),
            )
            .filter(ScenarioSession.user_id == user_id)
        )
        total = query.count()
        items = (
            query.order_by(ScenarioSession.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        return {
            "total": total,
            "items": [self._to_session_summary(item) for item in items],
            "page": page,
            "size": size,
        }

    def list_template_sessions(
        self,
        template_id: int,
        page: int,
        size: int,
        user_id: int,
        *,
        is_admin: bool = False,
    ) -> dict:
        self._get_manageable_template(template_id, user_id, is_admin=is_admin)
        query = (
            self.db.query(ScenarioSession)
            .options(
                joinedload(ScenarioSession.scenario_template),
                joinedload(ScenarioSession.user),
            )
            .filter(ScenarioSession.scenario_template_id == template_id)
        )
        total = query.count()
        items = (
            query.order_by(ScenarioSession.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        return {
            "total": total,
            "items": [self._to_session_summary(item) for item in items],
            "page": page,
            "size": size,
        }

    def get_session_detail(
        self,
        session_id: int,
        user_id: int,
        *,
        is_admin: bool = False,
        is_instructor: bool = False,
    ) -> Optional[dict]:
        session = self._load_session_with_relations(session_id)
        if not session:
            return None

        if session.user_id == user_id or is_admin:
            return self._to_session_dict(session)

        template = session.scenario_template
        if is_instructor and template and template.created_by == user_id:
            return self._to_session_dict(session)

        raise PermissionError("无权限查看该模拟会话")

    def _get_manageable_template(self, template_id: int, user_id: int, *, is_admin: bool = False) -> Optional[ScenarioTemplate]:
        template = self.db.query(ScenarioTemplate).filter(ScenarioTemplate.id == template_id).first()
        if not template:
            return None
        if is_admin or template.created_by == user_id:
            return template
        raise PermissionError("无权限操作该场景模板")

    def _load_session_with_relations(self, session_id: int) -> Optional[ScenarioSession]:
        return (
            self.db.query(ScenarioSession)
            .options(
                joinedload(ScenarioSession.scenario_template),
                joinedload(ScenarioSession.user),
            )
            .filter(ScenarioSession.id == session_id)
            .first()
        )

    @staticmethod
    def _normalize_id_list(value: Optional[list[int]]) -> list[int]:
        normalized: list[int] = []
        seen = set()
        for raw_item in value or []:
            try:
                item_id = int(raw_item)
            except (TypeError, ValueError):
                continue
            if item_id <= 0 or item_id in seen:
                continue
            seen.add(item_id)
            normalized.append(item_id)
        return normalized

    @staticmethod
    def _read_required(data: dict, *keys: str):
        value = ScenarioService._read_value(data, *keys)
        if value is None:
            raise KeyError(keys[0] if keys else "field")
        return value

    @staticmethod
    def _read_value(data: dict, *keys: str, default=None):
        for key in keys:
            if key in data:
                return data[key]
        return default

    @staticmethod
    def _has_any_key(data: dict, *keys: str) -> bool:
        return any(key in data for key in keys)

    @staticmethod
    def _display_user_name(session: ScenarioSession) -> str:
        user = session.user
        if not user:
            return f"用户{session.user_id}"
        return user.nickname or user.username or f"用户{session.user_id}"

    @staticmethod
    def _to_template_dict(template: ScenarioTemplate) -> dict:
        return {
            "id": template.id,
            "title": template.title,
            "description": template.description,
            "category": template.category,
            "difficulty": template.difficulty,
            "estimatedMinutes": template.estimated_minutes,
            "background": template.background,
            "npcRole": template.npc_role,
            "npcName": template.npc_name,
            "npcOpening": template.npc_opening,
            "knowledgeBaseId": template.knowledge_base_id,
            "knowledgeItemIds": list(template.knowledge_item_ids or []),
            "checkpoints": template.checkpoints or [],
            "status": template.status,
            "usageCount": template.usage_count,
            "createdBy": template.created_by,
            "createdAt": str(template.created_at) if template.created_at else None,
            "updatedAt": str(template.updated_at) if template.updated_at else None,
        }

    def _to_session_dict(self, session: ScenarioSession) -> dict:
        template = session.scenario_template
        knowledge_item_titles = []
        if template and template.knowledge_item_ids:
            knowledge_items = self.library_service.get_knowledge_items_by_ids(list(template.knowledge_item_ids or []))
            knowledge_item_titles = [item.title for item in knowledge_items]
        return {
            "id": session.id,
            "scenarioTemplateId": session.scenario_template_id,
            "scenarioTitle": template.title if template else None,
            "category": template.category if template else None,
            "background": template.background if template else None,
            "estimatedMinutes": template.estimated_minutes if template else None,
            "checkpoints": template.checkpoints or [] if template else [],
            "knowledgeItemTitles": knowledge_item_titles,
            "userId": session.user_id,
            "studentName": self._display_user_name(session),
            "messages": session.messages or [],
            "status": session.status,
            "score": session.score,
            "checkpointResults": session.checkpoint_results,
            "feedback": session.feedback,
            "durationMinutes": session.duration_minutes,
            "startedAt": str(session.started_at) if session.started_at else None,
            "completedAt": str(session.completed_at) if session.completed_at else None,
            "createdAt": str(session.created_at) if session.created_at else None,
        }

    def _to_session_summary(self, session: ScenarioSession) -> dict:
        payload = self._to_session_dict(session)
        return {
            "id": payload["id"],
            "scenarioTemplateId": payload["scenarioTemplateId"],
            "scenarioTitle": payload["scenarioTitle"],
            "category": payload["category"],
            "userId": payload["userId"],
            "studentName": payload["studentName"],
            "status": payload["status"],
            "score": payload["score"],
            "durationMinutes": payload["durationMinutes"],
            "createdAt": payload["createdAt"],
        }
