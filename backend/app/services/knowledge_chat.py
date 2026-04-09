"""
知识问答对话服务
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.agents.base import BaseAIAgent
from app.models.knowledge_chat_session import KnowledgeChatSession
from app.services.library import LibraryService


SYSTEM_PROMPTS = {
    "qa": (
        "你是一名专业的公安培训知识助手。\n"
        "{context_block}\n"
        "如果提供了已选知识点，请优先依据这些知识点回答；若当前问题与已选知识点不直接相关，"
        "请明确告知用户当前所选知识点可能不包含此内容，并建议重新选择知识点或改为通识问答。\n"
        "回答要准确、简洁、专业，不要编造。"
    ),
    "case": (
        "你是一名专业的公安培训案例分析助手。\n"
        "{context_block}\n"
        "请围绕用户输入生成具有教学价值的案例分析内容，优先依据已选知识点；"
        "如果知识点与问题不直接相关，要明确说明并避免脱离知识点随意扩写。\n"
        "输出建议包含案情概述、法律适用、执法要点和教学讨论点。"
    ),
}

VALID_MODES = {"qa", "case"}


class KnowledgeChatService:
    def __init__(self, db: Session):
        self.db = db
        self.library_service = LibraryService(db)
        self.ai_agent = BaseAIAgent()

    def create_session(self, user_id: int, knowledge_item_ids: Optional[list[int]], mode: str, *, is_admin: bool = False) -> dict:
        normalized_mode = str(mode or "qa").strip().lower() or "qa"
        if normalized_mode not in VALID_MODES:
            raise ValueError("不支持的知识问答模式")

        selected_items = self.library_service.resolve_accessible_knowledge_items(
            user_id,
            list(knowledge_item_ids or []),
            is_admin=is_admin,
            strict=True,
        )

        session = KnowledgeChatSession(
            user_id=user_id,
            knowledge_item_ids=[item.id for item in selected_items],
            mode=normalized_mode,
            messages=[],
        )
        self.db.add(session)
        self.db.flush()
        return self._to_session_dict(session)

    def send_message(self, session_id: int, user_id: int, content: str, *, is_admin: bool = False) -> dict:
        session = (
            self.db.query(KnowledgeChatSession)
            .filter(KnowledgeChatSession.id == session_id, KnowledgeChatSession.user_id == user_id)
            .first()
        )
        if not session:
            raise ValueError("会话不存在")

        messages = list(session.messages or [])
        messages.append({"role": "user", "content": content})

        selected_items = self.library_service.resolve_accessible_knowledge_items(
            user_id,
            list(session.knowledge_item_ids or []),
            is_admin=is_admin,
            strict=False,
        )
        knowledge_payload = self.library_service.build_knowledge_context(selected_items, content)

        if selected_items:
            context_block = f"【已选知识点参考内容】\n{knowledge_payload['context']}"
        else:
            context_block = "【当前模式】未选择知识点，请按通识问答回答。若无法确认，请明确说明。"

        system_prompt = SYSTEM_PROMPTS.get(session.mode, SYSTEM_PROMPTS["qa"]).format(context_block=context_block)
        recent_messages = messages[-20:]
        conversation = "\n".join(
            f"{'用户' if item['role'] == 'user' else 'AI助手'}: {item['content']}"
            for item in recent_messages
        )

        ai_reply = self.ai_agent._generate_text(
            system_prompt=system_prompt,
            user_prompt=conversation,
        )

        messages.append({"role": "assistant", "content": ai_reply})
        session.messages = messages
        self.db.flush()

        return {
            "sessionId": session.id,
            "reply": ai_reply,
            "knowledgeMatched": knowledge_payload["knowledgeMatched"],
            "knowledgeItemIds": knowledge_payload["knowledgeItemIds"],
            "knowledgeItemTitles": knowledge_payload["knowledgeItemTitles"],
            "messages": messages,
        }

    def list_sessions(self, user_id: int, page: int, size: int) -> dict:
        query = self.db.query(KnowledgeChatSession).filter(KnowledgeChatSession.user_id == user_id)
        total = query.count()
        items = query.order_by(KnowledgeChatSession.created_at.desc()).offset((page - 1) * size).limit(size).all()
        return {
            "total": total,
            "items": [self._to_session_summary(item) for item in items],
            "page": page,
            "size": size,
        }

    def get_session(self, session_id: int, user_id: int) -> Optional[dict]:
        session = (
            self.db.query(KnowledgeChatSession)
            .filter(KnowledgeChatSession.id == session_id, KnowledgeChatSession.user_id == user_id)
            .first()
        )
        if not session:
            return None
        return self._to_session_dict(session)

    def _to_session_dict(self, session: KnowledgeChatSession) -> dict:
        items = self.library_service.get_knowledge_items_by_ids(list(session.knowledge_item_ids or []))
        titles = [item.title for item in items]
        return {
            "id": session.id,
            "userId": session.user_id,
            "knowledgeBaseId": session.knowledge_base_id,
            "knowledgeItemIds": list(session.knowledge_item_ids or []),
            "knowledgeItemTitles": titles,
            "knowledgeSummary": "、".join(titles[:3]) if titles else "通识问答",
            "mode": session.mode,
            "messages": session.messages or [],
            "createdAt": str(session.created_at) if session.created_at else None,
            "updatedAt": str(session.updated_at) if session.updated_at else None,
        }

    def _to_session_summary(self, session: KnowledgeChatSession) -> dict:
        payload = self._to_session_dict(session)
        return {
            "id": payload["id"],
            "knowledgeBaseId": payload["knowledgeBaseId"],
            "knowledgeItemIds": payload["knowledgeItemIds"],
            "knowledgeItemTitles": payload["knowledgeItemTitles"],
            "knowledgeSummary": payload["knowledgeSummary"],
            "mode": payload["mode"],
            "messageCount": len(payload["messages"]),
            "createdAt": payload["createdAt"],
        }
