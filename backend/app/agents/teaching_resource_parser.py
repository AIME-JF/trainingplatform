"""教学资源需求解析智能体"""
from __future__ import annotations

from app.agents.base import BaseAIAgent
from app.schemas import TeachingResourceGenerationParsedRequest, TeachingResourceGenerationTaskCreateRequest


class TeachingResourceParserAgent(BaseAIAgent):
    """将自然语言需求解析为结构化课件需求"""

    def parse_request(self, request: TeachingResourceGenerationTaskCreateRequest) -> TeachingResourceGenerationParsedRequest:
        subject_hint = self._derive_subject_hint(request.requirements)
        system_prompt = (
            "你是教学资源策划助手。"
            "请把用户的自然语言需求整理成结构化课件策划信息。"
            "仅返回 JSON 对象，不要输出额外解释。"
            'JSON 字段固定为 theme、target_audience、usage_scenario、tone、page_count、keywords、learning_goals、summary。'
            "page_count 建议在 6 到 10 之间。keywords 和 learning_goals 必须是数组。"
        )
        user_prompt = (
            f"主题参考：{subject_hint}\n"
            f"资源摘要：{request.resource_summary or '无'}\n"
            f"自然语言需求：{request.requirements}\n"
            "请结合以上信息输出结构化课件策划结果。"
        )

        try:
            payload = self._generate_json_payload(system_prompt=system_prompt, user_prompt=user_prompt)
            page_count = int(payload.get("page_count") or 8)
            page_count = max(6, min(page_count, 10))
            return TeachingResourceGenerationParsedRequest(
                theme=str(payload.get("theme") or subject_hint).strip() or subject_hint,
                target_audience=str(payload.get("target_audience") or "").strip() or None,
                usage_scenario=str(payload.get("usage_scenario") or "").strip() or None,
                tone=str(payload.get("tone") or "").strip() or None,
                page_count=page_count,
                keywords=payload.get("keywords") or [],
                learning_goals=payload.get("learning_goals") or [],
                summary=str(payload.get("summary") or "").strip() or None,
            )
        except Exception:
            return self._build_fallback_result(request)

    def _build_fallback_result(self, request: TeachingResourceGenerationTaskCreateRequest) -> TeachingResourceGenerationParsedRequest:
        subject_hint = self._derive_subject_hint(request.requirements)
        keywords = [
            item.strip()[:100]
            for item in request.requirements.replace("，", " ").replace("。", " ").split()
            if item.strip()
        ][:6]
        if not keywords:
            keywords = [subject_hint[:100]]

        return TeachingResourceGenerationParsedRequest(
            theme=subject_hint,
            target_audience="平台学员",
            usage_scenario="培训讲解",
            tone="正式、清晰、便于课堂展示",
            page_count=8,
            keywords=keywords,
            learning_goals=[
                f"理解“{subject_hint}”的核心概念",
                "掌握关键要点与常见风险",
                "能够在实际场景中正确应用",
            ],
            summary=f"围绕“{subject_hint}”生成一份适合培训展示的八页教学课件。",
        )

    @staticmethod
    def _derive_subject_hint(requirements: str) -> str:
        text = str(requirements or "").strip()
        if not text:
            return "教学课件"
        candidate = text.splitlines()[0].strip()
        for separator in ["，", "。", "；", "：", ",", ".", ";", ":"]:
            candidate = candidate.split(separator)[0].strip()
        candidate = candidate.removeprefix("请生成一份").removeprefix("请生成").removeprefix("生成一份").strip()
        return candidate[:80] or "教学课件"
