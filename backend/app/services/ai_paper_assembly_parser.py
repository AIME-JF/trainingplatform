"""
AI 自动组卷需求解析器。
"""
from __future__ import annotations

import json
from typing import Any, Iterable, Optional

from app.schemas import (
    AIPaperAssemblyParsedRequest,
    AIPaperAssemblyParsedTypeConfig,
    AIPaperAssemblyTaskCreateRequest,
    AIPaperAssemblyTypeConfig,
)
from logger import logger

from .ai_question_generator import AIQuestionGenerator


class AIPaperAssemblyParser:
    """将自动组卷请求解析成结构化查题条件。"""

    SUPPORTED_TYPES = ("single", "multi", "judge")

    def __init__(self) -> None:
        self._runtime_helper = AIQuestionGenerator()

    def parse_request(
        self,
        request: AIPaperAssemblyTaskCreateRequest,
        default_type_configs: Iterable[AIPaperAssemblyTypeConfig],
    ) -> AIPaperAssemblyParsedRequest:
        fallback = self._build_fallback_result(request, default_type_configs)
        if not self._should_use_ai(request):
            return fallback

        try:
            prompt = self._build_parse_prompt(request, fallback)
            runtime_config = self._runtime_helper._load_runtime_config()
            raw_content = self._runtime_helper._call_provider(runtime_config, prompt)
            payload = self._runtime_helper._parse_json_payload(raw_content)
            return self._build_parsed_result(payload, request, fallback)
        except Exception as exc:
            logger.warning("AI 自动组卷需求解析失败，回退到显式字段: %s", exc)
            warnings = list(fallback.warnings)
            warnings.append(f"AI 解析失败，已按表单字段组卷：{exc}")
            return fallback.model_copy(update={"warnings": warnings})

    def _should_use_ai(self, request: AIPaperAssemblyTaskCreateRequest) -> bool:
        return bool(
            str(request.requirements or "").strip()
            or str(request.description or "").strip()
        )

    def _build_fallback_result(
        self,
        request: AIPaperAssemblyTaskCreateRequest,
        default_type_configs: Iterable[AIPaperAssemblyTypeConfig],
    ) -> AIPaperAssemblyParsedRequest:
        normalized_global_points = self._normalize_keywords(request.knowledge_points)
        base_type_configs = list(request.type_configs or list(default_type_configs))
        parsed_type_configs = [
            AIPaperAssemblyParsedTypeConfig(
                type=item.type,
                count=int(item.count),
                difficulty=item.difficulty,
                score=int(item.score),
                knowledge_points=normalized_global_points,
                police_type_id=request.police_type_id,
            )
            for item in base_type_configs
            if item.type in self.SUPPORTED_TYPES
        ]

        understood_items = [
            f"题型 {self._type_label(item.type)} {item.count} 道"
            + (f"，难度 {item.difficulty}" if item.difficulty else "")
            + f"，单题 {item.score} 分"
            for item in parsed_type_configs
        ]
        if request.police_type_id is not None:
            understood_items.append(f"警种 ID {request.police_type_id}")
        if normalized_global_points:
            understood_items.append(f"知识点关键词：{'、'.join(normalized_global_points)}")
        if request.requirements:
            understood_items.append(f"补充要求：{str(request.requirements).strip()[:200]}")

        summary = f"按表单字段组卷：{request.paper_title}"
        if request.requirements:
            summary = f"{summary}，并结合补充要求细化筛题"

        return AIPaperAssemblyParsedRequest(
            summary=summary,
            police_type_id=request.police_type_id,
            knowledge_points=normalized_global_points,
            type_configs=parsed_type_configs,
            understood_items=understood_items,
            warnings=[],
        )

    def _build_parse_prompt(
        self,
        request: AIPaperAssemblyTaskCreateRequest,
        fallback: AIPaperAssemblyParsedRequest,
    ) -> str:
        prompt_lines = [
            "你是警务训练平台的自动组卷需求解析助手。",
            "你必须严格输出一个合法 JSON 对象，不允许输出 Markdown、代码块、额外说明或前后缀文本。",
            "你的任务是把用户的组卷需求解析成后端可以直接执行的查题条件。",
            "后端实际只支持以下筛题字段：",
            "- type：题型，只能是 single / multi / judge。",
            "- police_type_id：警种 ID。只能使用输入里已经给出的 ID，不能猜测新的 ID。",
            "- difficulty：难度，必须是 1-5 整数。",
            "- knowledge_points：知识点关键词数组。后端会按 knowledge_point LIKE '%关键词%' 模糊匹配。",
            "请严格输出如下 JSON：",
            "{",
            '  "summary": "一句话概括解析结果",',
            '  "police_type_id": 1,',
            '  "knowledge_points": ["关键词1", "关键词2"],',
            '  "type_configs": [',
            '    {"type": "single", "count": 5, "difficulty": 3, "score": 2, "knowledge_points": ["关键词1"], "police_type_id": 1}',
            "  ],",
            '  "understood_items": ["需求点1", "需求点2"],',
            '  "warnings": ["如果有不确定项写在这里，没有就返回空数组"]',
            "}",
            "解析规则：",
            "- 如果表单已经给出题型数量、难度、分值，它们是默认值；只有自然语言要求非常明确时才覆盖。",
            "- police_type_id 如果输入为空就返回 null，不允许凭空编造 ID。",
            "- knowledge_points 必须输出适合模糊匹配的短关键词，不要输出长句。",
            "- type_configs 至少保留一个题型，且 count 必须为正整数。",
            "- 如果自然语言没有给出更细条件，就沿用默认值。",
            "- 所有输出必须使用简体中文。",
            "当前表单默认值：",
            json.dumps(
                {
                    "task_name": request.task_name,
                    "paper_title": request.paper_title,
                    "paper_type": request.paper_type,
                    "description": request.description,
                    "duration": request.duration,
                    "passing_score": request.passing_score,
                    "assembly_mode": request.assembly_mode,
                    "police_type_id": request.police_type_id,
                    "knowledge_points": request.knowledge_points,
                    "type_configs": [item.model_dump(mode="python") for item in (request.type_configs or [])],
                    "requirements": request.requirements,
                },
                ensure_ascii=False,
            ),
            "兜底解析参考：",
            json.dumps(fallback.model_dump(mode="python"), ensure_ascii=False),
            "请现在直接输出 JSON 对象。",
        ]
        return "\n".join(prompt_lines)

    def _build_parsed_result(
        self,
        payload: dict[str, Any],
        request: AIPaperAssemblyTaskCreateRequest,
        fallback: AIPaperAssemblyParsedRequest,
    ) -> AIPaperAssemblyParsedRequest:
        summary = str(payload.get("summary") or "").strip() or fallback.summary
        global_points = self._normalize_keywords(payload.get("knowledge_points")) or list(fallback.knowledge_points)

        payload_police_type_id = self._to_int(payload.get("police_type_id"))
        police_type_id = request.police_type_id if request.police_type_id is not None else payload_police_type_id

        fallback_map = {item.type: item for item in fallback.type_configs}
        parsed_type_configs: list[AIPaperAssemblyParsedTypeConfig] = []
        parsed_types: set[str] = set()
        for raw_item in payload.get("type_configs") or []:
            parsed_item = self._normalize_type_config_item(
                raw_item,
                fallback_map=fallback_map,
                police_type_id=police_type_id,
                global_points=global_points,
            )
            if not parsed_item or parsed_item.type in parsed_types:
                continue
            parsed_type_configs.append(parsed_item)
            parsed_types.add(parsed_item.type)

        for fallback_item in fallback.type_configs:
            if fallback_item.type in parsed_types:
                continue
            parsed_type_configs.append(
                fallback_item.model_copy(
                    update={
                        "knowledge_points": fallback_item.knowledge_points or global_points,
                        "police_type_id": fallback_item.police_type_id or police_type_id,
                    }
                )
            )

        understood_items = self._normalize_string_list(payload.get("understood_items")) or list(fallback.understood_items)
        warnings = self._normalize_string_list(payload.get("warnings"))

        return AIPaperAssemblyParsedRequest(
            summary=summary,
            police_type_id=police_type_id,
            knowledge_points=global_points,
            type_configs=parsed_type_configs or list(fallback.type_configs),
            understood_items=understood_items,
            warnings=warnings,
        )

    def _normalize_type_config_item(
        self,
        raw_item: Any,
        *,
        fallback_map: dict[str, AIPaperAssemblyParsedTypeConfig],
        police_type_id: Optional[int],
        global_points: list[str],
    ) -> Optional[AIPaperAssemblyParsedTypeConfig]:
        if not isinstance(raw_item, dict):
            return None

        question_type = str(raw_item.get("type") or "").strip()
        if question_type not in self.SUPPORTED_TYPES:
            return None

        fallback_item = fallback_map.get(question_type)
        count = self._to_int(raw_item.get("count")) or (fallback_item.count if fallback_item else None) or 1
        score = self._to_int(raw_item.get("score")) or (fallback_item.score if fallback_item else None) or 2
        difficulty = self._normalize_difficulty(raw_item.get("difficulty"))
        if difficulty is None and fallback_item:
            difficulty = fallback_item.difficulty

        item_police_type_id = police_type_id
        if item_police_type_id is None:
            item_police_type_id = self._to_int(raw_item.get("police_type_id"))
            if item_police_type_id is None and fallback_item:
                item_police_type_id = fallback_item.police_type_id

        item_points = self._normalize_keywords(raw_item.get("knowledge_points"))
        if not item_points and fallback_item:
            item_points = list(fallback_item.knowledge_points)
        if not item_points:
            item_points = list(global_points)

        return AIPaperAssemblyParsedTypeConfig(
            type=question_type,
            count=max(1, count),
            difficulty=difficulty,
            score=max(1, score),
            knowledge_points=item_points,
            police_type_id=item_police_type_id,
        )

    @staticmethod
    def _normalize_keywords(raw_value: Any) -> list[str]:
        raw_items = [raw_value] if isinstance(raw_value, str) else list(raw_value or [])
        normalized: list[str] = []
        seen = set()
        for raw_item in raw_items:
            item = str(raw_item or "").strip()
            if not item or item in seen:
                continue
            seen.add(item)
            normalized.append(item[:100])
        return normalized

    @staticmethod
    def _normalize_string_list(raw_value: Any) -> list[str]:
        raw_items = [raw_value] if isinstance(raw_value, str) else list(raw_value or [])
        normalized: list[str] = []
        seen = set()
        for raw_item in raw_items:
            item = str(raw_item or "").strip()
            if not item or item in seen:
                continue
            seen.add(item)
            normalized.append(item[:200])
        return normalized

    def _normalize_difficulty(self, value: Any) -> Optional[int]:
        difficulty = self._to_int(value)
        if difficulty is None:
            return None
        if 1 <= difficulty <= 5:
            return difficulty
        return None

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _type_label(question_type: str) -> str:
        return {
            "single": "单选题",
            "multi": "多选题",
            "judge": "判断题",
        }.get(question_type, question_type)
