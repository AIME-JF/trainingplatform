"""智能体A：从课表文件纯文本中提取班级信息"""
from __future__ import annotations

from app.agents.base import BaseAIAgent


class ScheduleFileClassInfoAgent(BaseAIAgent):
    """从课表 xlsx 提取的纯文本中结构化提取班级信息"""

    def extract(self, raw_text: str) -> dict:
        """返回 dict，包含 name/start_date/end_date/capacity/location/headteachers"""
        system_prompt = (
            "你是警务训练平台的课表解析助手，专门从课表文件文本中提取班级基础信息。\n"
            "仅返回 JSON 对象，不要输出任何额外解释、注释或 markdown 格式。\n"
            "\n"
            "【输出格式】\n"
            "JSON 字段固定为：\n"
            "  name        - 班级名称（字符串，最多100字，提取不到返回 null）\n"
            "  start_date  - 培训起始日期，格式 YYYY-MM-DD（提取不到返回 null）\n"
            "  end_date    - 培训结束日期，格式 YYYY-MM-DD（提取不到返回 null）\n"
            "  capacity    - 班级容量/人数（整数，提取不到返回 null）\n"
            "  location    - 培训地点名称（字符串，最多50字，提取不到返回 null）\n"
            "  headteachers - 班主任列表（数组，最多5人），每个元素包含：\n"
            "    name       - 姓名（字符串，最多10字）\n"
            "    role_label - 称呼（字符串，最多10字，如'带班队长'、'班主任'）\n"
            "\n"
            "【提取规则】\n"
            "1. 班级名称通常出现在表头、首行或文件标题区域\n"
            "2. 起止日期从课表第一天和最后一天推断，格式必须为 YYYY-MM-DD\n"
            "3. 班主任称呼包括：班主任、带班队长、带班教官、带班民警等\n"
            "4. 字段确实找不到时返回 null，不要猜测\n"
            "5. 输出必须是完整合法的 JSON，不得截断\n"
        )
        user_prompt = f"以下是课表文件提取的纯文本内容，请提取班级信息：\n\n{raw_text[:8000]}"

        try:
            payload = self._generate_json_payload(system_prompt=system_prompt, user_prompt=user_prompt)
            return self._normalize_result(payload)
        except Exception:
            return self._build_fallback()

    def _normalize_result(self, payload: dict) -> dict:
        headteachers_raw = payload.get("headteachers") or []
        headteachers = []
        for ht in headteachers_raw:
            if not isinstance(ht, dict):
                continue
            name = str(ht.get("name") or "").strip()
            if not name:
                continue
            headteachers.append({
                "name": name[:100],
                "role_label": str(ht.get("role_label") or "班主任").strip()[:50],
            })

        name = payload.get("name")
        if name is not None:
            name = str(name).strip()[:200] or None

        start_date = self._normalize_date(payload.get("start_date"))
        end_date = self._normalize_date(payload.get("end_date"))

        capacity = None
        cap_raw = payload.get("capacity")
        if cap_raw is not None:
            try:
                capacity = int(cap_raw)
                if capacity <= 0 or capacity > 9999:
                    capacity = None
            except (ValueError, TypeError):
                capacity = None

        location = payload.get("location")
        if location is not None:
            location = str(location).strip()[:200] or None

        return {
            "name": name,
            "start_date": start_date,
            "end_date": end_date,
            "capacity": capacity,
            "location": location,
            "headteachers": headteachers,
        }

    @staticmethod
    def _normalize_date(value) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text or text.lower() == "null":
            return None
        # 只保留合法日期格式
        import re
        if re.match(r"^\d{4}-\d{2}-\d{2}$", text):
            return text
        return None

    @staticmethod
    def _build_fallback() -> dict:
        return {
            "name": None,
            "start_date": None,
            "end_date": None,
            "capacity": None,
            "location": None,
            "headteachers": [],
        }
