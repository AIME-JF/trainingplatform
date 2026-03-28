"""培训班智能创建解析智能体"""
import json
import re
import threading
from datetime import date, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.agents.base import BaseAIAgent
from app.models import Department, PoliceType, TrainingBase, User
from logger import logger


REQUIRED_FIELDS = {"name", "start_date", "end_date", "location"}

TYPE_ALIASES = {
    "基础": "basic", "基础培训": "basic", "初任": "basic", "新警": "basic",
    "专项": "special", "专题": "special", "专项培训": "special",
    "晋升": "promotion", "晋升培训": "promotion", "提拔": "promotion",
    "线上": "online", "网络": "online", "远程": "online",
}


class TrainingCreateParser(BaseAIAgent):
    """解析自然语言为培训班创建字段，支持多轮补全"""

    def __init__(self, db: Session):
        self.db = db
        self._cancel_event = threading.Event()

    def cancel(self):
        self._cancel_event.set()

    @property
    def cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def parse_round(
        self,
        user_input: str,
        context: dict[str, Any],
        conversation: list[dict[str, str]],
    ) -> dict[str, Any]:
        """
        单轮解析。合并新输入到已有上下文。
        返回: { fields: {...}, missing: [...], questions: [...], complete: bool }
        """
        if self.cancelled:
            return {"fields": context, "missing": [], "questions": [], "complete": False, "cancelled": True}

        # LLM 解析
        new_fields = self._parse_with_llm(user_input, context, conversation)

        if self.cancelled:
            return {"fields": context, "missing": [], "questions": [], "complete": False, "cancelled": True}

        # 合并到上下文
        for key, value in new_fields.items():
            if value is not None and value != "":
                context[key] = value

        # 实体匹配
        self._resolve_entities(context)

        if self.cancelled:
            return {"fields": context, "missing": [], "questions": [], "complete": False, "cancelled": True}

        # 检查必填项
        missing = []
        questions = []
        for field in REQUIRED_FIELDS:
            if not context.get(field):
                missing.append(field)

        if missing:
            questions = self._build_questions(missing, context)

        return {
            "fields": context,
            "missing": missing,
            "questions": questions,
            "complete": len(missing) == 0,
        }

    def _parse_with_llm(
        self,
        user_input: str,
        context: dict[str, Any],
        conversation: list[dict[str, str]],
    ) -> dict[str, Any]:
        today = date.today()
        context_hint = ""
        if context:
            context_hint = f"\n\n当前已提取的信息：\n{json.dumps(context, ensure_ascii=False, default=str)}\n请在此基础上合并用户新提供的字段。"

        system_prompt = (
            "你是培训班创建助手。根据用户输入提取培训班信息，仅返回 JSON 对象。\n"
            f"今天日期：{today.isoformat()}（{['周一','周二','周三','周四','周五','周六','周日'][today.weekday()]}）\n"
            "可提取的字段：\n"
            "- name: 培训班名称\n"
            "- type: 培训类型（basic/special/promotion/online）\n"
            "- start_date: 开始日期（YYYY-MM-DD）\n"
            "- end_date: 结束日期（YYYY-MM-DD）\n"
            "- location: 培训地点\n"
            "- training_base_name: 培训基地名称（如果用户提到了基地）\n"
            "- capacity: 容量（整数）\n"
            "- department_name: 部门名称\n"
            "- police_type_name: 警种名称\n"
            "- instructor_name: 主讲教官姓名\n"
            "- description: 培训简介\n"
            "- enrollment_requires_approval: 是否需要报名审批（true/false）\n"
            "\n规则：\n"
            "- 日期要转为具体的 YYYY-MM-DD 格式，如「下周一」要算出具体日期\n"
            "- 如果说「两周」「10天」等时长，结合开始日期推算结束日期\n"
            "- 只返回用户明确提到的字段，未提到的不要返回\n"
            "- 仅返回 JSON，不要附加任何解释文字\n"
            + context_hint
        )

        # 构建多轮对话：1 个 system + 历史 user/assistant 交替 + 当前 user
        messages = [{"role": "system", "content": system_prompt}]
        # 取最近的对话历史（不含本轮，因为本轮 user 单独追加）
        # conversation 中最后一条是本轮 user 消息（由 views 层追加），取之前的历史
        history = conversation[:-1] if conversation else []
        for msg in history:
            if msg.get("role") in ("user", "assistant"):
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_input})

        try:
            config = self._load_runtime_config()
            raw = self._call_provider(config, messages)
            return self._parse_json_payload(raw)
        except Exception as e:
            logger.warning(f"培训班智能创建 LLM 解析失败: {e}")
            return self._parse_with_rules(user_input)

    def _parse_with_rules(self, text: str) -> dict[str, Any]:
        """正则兜底解析"""
        result: dict[str, Any] = {}

        # 容量
        cap_match = re.search(r"(\d+)\s*人", text)
        if cap_match:
            result["capacity"] = int(cap_match.group(1))

        # 类型
        for alias, code in TYPE_ALIASES.items():
            if alias in text:
                result["type"] = code
                break

        return result

    def _resolve_entities(self, context: dict[str, Any]):
        """将名称字段匹配为数据库 ID"""
        # 培训基地
        base_name = context.pop("training_base_name", None)
        if base_name and not context.get("training_base_id"):
            base = self.db.query(TrainingBase).filter(
                TrainingBase.name.ilike(f"%{base_name}%")
            ).first()
            if base:
                context["training_base_id"] = base.id
                if not context.get("location"):
                    context["location"] = base.location or base.name
                if not context.get("department_id") and base.department_id:
                    context["department_id"] = base.department_id

        # 部门
        dept_name = context.pop("department_name", None)
        if dept_name and not context.get("department_id"):
            dept = self.db.query(Department).filter(
                Department.name.ilike(f"%{dept_name}%"),
                Department.is_active.is_(True),
            ).first()
            if dept:
                context["department_id"] = dept.id

        # 警种
        pt_name = context.pop("police_type_name", None)
        if pt_name and not context.get("police_type_id"):
            pt = self.db.query(PoliceType).filter(
                PoliceType.name.ilike(f"%{pt_name}%"),
                PoliceType.is_active.is_(True),
            ).first()
            if pt:
                context["police_type_id"] = pt.id

        # 教官
        inst_name = context.pop("instructor_name", None)
        if inst_name and not context.get("instructor_id"):
            instructor = self.db.query(User).filter(
                User.nickname.ilike(f"%{inst_name}%"),
                User.is_active.is_(True),
            ).first()
            if instructor:
                context["instructor_id"] = instructor.id

    def _build_questions(self, missing: list[str], context: dict[str, Any]) -> list[str]:
        """根据缺失字段生成追问"""
        field_labels = {
            "name": "培训班名称",
            "start_date": "开始日期",
            "end_date": "结束日期",
            "location": "培训地点",
        }
        parts = [field_labels.get(f, f) for f in missing]
        return [f"还需要以下信息：{' / '.join(parts)}"]

    def build_training_create_payload(self, context: dict[str, Any]) -> dict[str, Any]:
        """将解析上下文转为 TrainingCreate 可接受的 payload"""
        payload: dict[str, Any] = {
            "name": context.get("name", ""),
            "type": context.get("type", "basic"),
            "start_date": context.get("start_date"),
            "end_date": context.get("end_date"),
            "location": context.get("location"),
        }
        optional_fields = [
            "capacity", "department_id", "police_type_id", "training_base_id",
            "instructor_id", "description", "enrollment_requires_approval",
        ]
        for field in optional_fields:
            value = context.get(field)
            if value is not None:
                payload[field] = value

        # 默认值
        if not payload.get("capacity"):
            payload["capacity"] = 0

        return payload
