"""培训班总结报告 AI 智能体"""
from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAIAgent


class TrainingReportAgentService(BaseAIAgent):
    """基于培训班统计数据生成总结报告草稿"""

    def generate_report(
        self,
        *,
        training_name: str,
        metrics: dict[str, Any],
        focus_points: list[str] | None = None,
        extra_requirements: str | None = None,
    ) -> dict[str, Any]:
        focus_points = [str(item).strip() for item in (focus_points or []) if str(item).strip()]
        extra_requirements = str(extra_requirements or "").strip()
        system_prompt = (
            "你是公安培训运营分析助手，负责根据培训班真实统计数据生成总结报告。\n"
            "请严格遵守以下要求：\n"
            "1. 只依据提供的数据分析，不要虚构不存在的数据。\n"
            "2. 输出必须是 JSON 对象，字段固定为 title、report_markdown、risk_items、suggestions。\n"
            "3. title 是 200 字以内中文标题。\n"
            "4. report_markdown 必须是完整 Markdown 正文，使用中文，结构至少包含：培训概况、出勤与执行情况、考试分析、风险提示、改进建议。\n"
            "5. risk_items 和 suggestions 都是字符串数组，各输出 2 到 5 条，尽量具体可执行。\n"
            "6. 正式考试分析只围绕 purpose != quiz 的考试，随堂测试只能作为辅助说明，不能混入正式考试通过率。\n"
            "7. 如果数据不足，要明确写出“数据不足”或“暂无相关数据”，而不是编造结论。\n"
            "8. 语言要专业、客观、适合提交管理人员审核。"
        )
        user_prompt = (
            f"培训班名称：{training_name}\n"
            f"重点关注：{json.dumps(focus_points, ensure_ascii=False)}\n"
            f"补充要求：{extra_requirements or '无'}\n"
            f"统计数据：{json.dumps(metrics, ensure_ascii=False)}\n"
            "请基于以上信息输出 JSON。"
        )

        payload = self._generate_json_payload(system_prompt=system_prompt, user_prompt=user_prompt)
        title = str(payload.get("title") or "").strip() or f"{training_name}培训总结报告"
        report_markdown = str(payload.get("report_markdown") or "").strip()
        if not report_markdown:
            raise ValueError("AI 未生成有效的报告正文")
        return {
            "title": title[:200],
            "report_markdown": report_markdown,
            "risk_items": self._normalize_items(payload.get("risk_items")),
            "suggestions": self._normalize_items(payload.get("suggestions")),
        }

    @staticmethod
    def _normalize_items(value: Any) -> list[str]:
        if value is None:
            return []
        raw_items = value if isinstance(value, list) else [value]
        items: list[str] = []
        seen: set[str] = set()
        for raw_item in raw_items:
            item = str(raw_item or "").strip()
            if not item or item in seen:
                continue
            seen.add(item)
            items.append(item[:300])
        return items
