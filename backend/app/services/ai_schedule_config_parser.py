"""
AI 自然语言转排课配置服务
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List

from openai import OpenAI

from app.models import Training
from app.schemas import AIScheduleTaskCreateRequest
from app.services.system import get_config_value
from app.services.training_schedule_rule import TrainingScheduleRuleService


@dataclass
class AIRuntimeConfig:
    provider: str
    base_url: str | None
    api_key: str | None
    model: str
    max_tokens: int | None
    temperature: float | None
    timeout: int | float | None


class AIScheduleConfigParserService:
    """将自然语言排课要求解析为结构化配置，并用规则做兜底归一化"""

    def parse_task_request(self, training: Training, request: AIScheduleTaskCreateRequest) -> dict[str, Any]:
        prompt = str(request.natural_language_prompt or "").strip()
        base_request = request.model_dump(mode="json")
        if not prompt:
            return {
                "request": AIScheduleTaskCreateRequest.model_validate(base_request),
                "summary": None,
                "warnings": [],
            }

        heuristic_payload = self._parse_with_rules(prompt)
        ai_payload, warnings = self._parse_with_llm(prompt, training)
        merged_payload = self._merge_dicts(heuristic_payload, ai_payload)
        next_request_payload = self._apply_prompt_payload(base_request, merged_payload, training)
        summary = self._build_parse_summary(prompt, next_request_payload)
        return {
            "request": AIScheduleTaskCreateRequest.model_validate(next_request_payload),
            "summary": summary,
            "warnings": warnings,
        }

    def _parse_with_llm(self, prompt: str, training: Training) -> tuple[dict[str, Any], list[str]]:
        warnings: List[str] = []
        try:
            config = self._load_runtime_config()
        except Exception as exc:
            return {}, [f"AI 解析未启用，已按规则兜底：{exc}"]

        request_kwargs: dict[str, Any] = {
            "model": config.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是警务培训排课配置解析器。你只能输出合法 JSON 对象，不能输出 Markdown 或说明文字。",
                },
                {
                    "role": "user",
                    "content": self._build_llm_prompt(prompt, training),
                },
            ],
        }
        if config.max_tokens:
            request_kwargs["max_tokens"] = config.max_tokens
        if config.temperature is not None:
            request_kwargs["temperature"] = config.temperature

        try:
            if config.provider == "ollama":
                from ollama import Client

                client = Client(host=config.base_url, timeout=config.timeout)
                ollama_kwargs: dict[str, Any] = {
                    "model": config.model,
                    "messages": request_kwargs["messages"],
                }
                options: dict[str, Any] = {}
                if config.temperature is not None:
                    options["temperature"] = config.temperature
                if config.max_tokens:
                    options["num_predict"] = config.max_tokens
                if options:
                    ollama_kwargs["options"] = options
                response = client.chat(**ollama_kwargs)
                content = (response.get("message") or {}).get("content", "")
            else:
                client = OpenAI(
                    api_key=config.api_key,
                    base_url=config.base_url,
                    timeout=config.timeout,
                    max_retries=0,
                )
                response = client.chat.completions.create(**request_kwargs)
                content = response.choices[0].message.content if response.choices else ""
            if not content:
                raise ValueError("AI 未返回有效配置")
            return self._parse_json_payload(str(content).strip()), warnings
        except Exception as exc:
            warnings.append(f"AI 解析失败，已按规则兜底：{exc}")
            return {}, warnings

    def _parse_with_rules(self, prompt: str) -> dict[str, Any]:
        payload: Dict[str, Any] = {}
        lower_prompt = prompt.lower()

        if any(keyword in prompt for keyword in ("仅未排课", "未排课课次", "补排")):
            payload["scope_type"] = "unscheduled"
        elif any(keyword in prompt for keyword in ("本周", "这周", "指定周")):
            payload["scope_type"] = "current_week"
        elif any(keyword in prompt for keyword in ("全班次", "全部课次", "整个班")):
            payload["scope_type"] = "all"

        if any(keyword in prompt for keyword in ("考前", "冲刺", "考前强化")):
            payload["goal"] = "exam_intensive"
        elif "实战" in prompt:
            payload["goal"] = "practice_first"
        elif "理论" in prompt:
            payload["goal"] = "theory_first"

        if "按课时" in prompt:
            payload["planning_mode"] = "by_hours"
        elif "工作日" in prompt:
            payload["planning_mode"] = "fill_workdays"
        elif "排满" in prompt or "排满所有" in prompt or "排满全部" in prompt:
            payload["planning_mode"] = "fill_all_days"

        if any(keyword in prompt for keyword in ("避开考试", "不要和考试冲突", "避开考试日")):
            payload.setdefault("constraint_payload", {})["avoid_exam_days"] = True
        elif any(keyword in prompt for keyword in ("不避开考试", "无需避开考试")):
            payload.setdefault("constraint_payload", {})["avoid_exam_days"] = False

        daily_limit_match = re.search(r"单日[^0-9]{0,6}(\d+(?:\.\d+)?)\s*课时", prompt)
        if daily_limit_match:
            payload.setdefault("constraint_payload", {})["daily_max_hours"] = float(daily_limit_match.group(1))

        rule_payload: Dict[str, Any] = {}
        lesson_unit_match = (
            re.search(r"(?:一|每|单个?)课时[^0-9]{0,6}(\d+)\s*分钟", prompt)
            or re.search(r"(\d+)\s*分钟[^。；，,\n]{0,20}(?:一|每)课时", prompt)
        )
        if lesson_unit_match:
            rule_payload["lesson_unit_minutes"] = int(lesson_unit_match.group(1))

        break_match = re.search(r"课间[^0-9]{0,6}(\d+)\s*分钟", prompt)
        if break_match:
            rule_payload["break_minutes"] = int(break_match.group(1))

        max_units_match = re.search(r"一节课最多[^0-9]{0,6}(\d+)\s*课时", prompt)
        if max_units_match:
            rule_payload["max_units_per_session"] = int(max_units_match.group(1))

        daily_units_match = re.search(r"单日最多[^0-9]{0,6}(\d+)\s*课时", prompt)
        if daily_units_match:
            rule_payload["daily_max_units"] = int(daily_units_match.group(1))

        if any(keyword in lower_prompt for keyword in ("均衡", "平分", "尽量平均")):
            rule_payload["split_strategy"] = "balanced"

        windows = self._extract_windows(prompt)
        if windows:
            rule_payload["teaching_windows"] = windows

        course_keys = re.findall(r"course[_-]?key[:：]?\s*([0-9a-zA-Z-]+)", prompt, re.IGNORECASE)
        if course_keys:
            payload.setdefault("constraint_payload", {})["fixed_course_keys"] = list(dict.fromkeys(course_keys))

        if rule_payload:
            payload["schedule_rule_override"] = rule_payload
        return payload

    def _apply_prompt_payload(
        self,
        base_request_payload: dict[str, Any],
        parsed_payload: dict[str, Any],
        training: Training,
    ) -> dict[str, Any]:
        result = self._merge_dicts(base_request_payload, parsed_payload)
        training_rule = TrainingScheduleRuleService.resolve_effective_rule_config(training.schedule_rule_config)
        existing_override = result.get("schedule_rule_override")
        if existing_override is not None:
            result["schedule_rule_override"] = TrainingScheduleRuleService.normalize_rule_config(
                existing_override,
                fallback=training_rule,
            )
        elif parsed_payload.get("schedule_rule_override") is not None:
            result["schedule_rule_override"] = TrainingScheduleRuleService.normalize_rule_config(
                parsed_payload.get("schedule_rule_override"),
                fallback=training_rule,
            )

        constraint_payload = dict(result.get("constraint_payload") or {})
        if not constraint_payload.get("daily_max_hours"):
            fallback_rule = TrainingScheduleRuleService.resolve_effective_rule_config(
                training.schedule_rule_config,
                result.get("schedule_rule_override"),
            )
            constraint_payload["daily_max_hours"] = fallback_rule.get("daily_max_units", 6)
        result["constraint_payload"] = constraint_payload
        return result

    def _build_llm_prompt(self, prompt: str, training: Training) -> str:
        training_rule = TrainingScheduleRuleService.resolve_effective_rule_config(training.schedule_rule_config)
        return "\n".join(
            [
                "请把下面的自然语言排课要求解析成 JSON 配置。",
                "只输出 JSON 对象，不要输出其他文字。",
                "字段说明：",
                '- scope_type: all/current_week/unscheduled，可省略',
                '- goal: balanced/practice_first/theory_first/exam_intensive，可省略',
                '- planning_mode: fill_all_days/fill_workdays/by_hours，可省略',
                '- constraint_payload.daily_max_hours: 数字，可省略',
                "- constraint_payload.avoid_exam_days: true/false，可省略",
                '- constraint_payload.fixed_course_keys: 字符串数组，可省略',
                "- schedule_rule_override: 对象，可包含 lesson_unit_minutes, break_minutes, max_units_per_session, daily_max_units, preferred_planning_mode, split_strategy, teaching_windows",
                '- teaching_windows: [{"label":"上午","start_time":"08:30","end_time":"12:30"}]',
                f"当前培训班默认规则：{json.dumps(training_rule, ensure_ascii=False)}",
                f"培训班名称：{training.name}",
                f"培训周期：{training.start_date} 至 {training.end_date}",
                "用户要求：",
                prompt,
            ]
        )

    def _build_parse_summary(self, prompt: str, request_payload: dict[str, Any]) -> str:
        rule_override = request_payload.get("schedule_rule_override") or {}
        windows = rule_override.get("teaching_windows") or []
        window_text = "、".join(
            f"{item.get('label') or '时段'} {item.get('start_time')}-{item.get('end_time')}"
            for item in windows[:3]
        ) or "未覆盖培训班默认时间段"
        return (
            f"已根据自然语言要求解析排课配置：排课方式 {request_payload.get('planning_mode')}，"
            f"单日最大课时 {((request_payload.get('constraint_payload') or {}).get('daily_max_hours') or 0)}，"
            f"时间段 {window_text}。"
        )

    def _extract_windows(self, prompt: str) -> List[Dict[str, Any]]:
        windows: List[Dict[str, Any]] = []
        for match in re.finditer(r"(\d{1,2}:\d{2})\s*[-~到至]\s*(\d{1,2}:\d{2})", prompt):
            start_time = TrainingScheduleRuleService._normalize_clock(match.group(1))
            end_time = TrainingScheduleRuleService._normalize_clock(match.group(2))
            if not start_time or not end_time or start_time >= end_time:
                continue
            label = ""
            prefix = prompt[max(match.start() - 6, 0):match.start()]
            if "上午" in prefix:
                label = "上午"
            elif "下午" in prefix:
                label = "下午"
            elif "晚上" in prefix or "晚间" in prefix:
                label = "晚上"
            windows.append(
                {
                    "label": label,
                    "start_time": start_time,
                    "end_time": end_time,
                }
            )
        return windows

    @staticmethod
    def _merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        result = json.loads(json.dumps(base, ensure_ascii=False))
        for key, value in (override or {}).items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = AIScheduleConfigParserService._merge_dicts(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _parse_json_payload(raw_content: str) -> dict[str, Any]:
        json_text = raw_content.strip()
        if json_text.startswith("```"):
            json_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", json_text, flags=re.IGNORECASE | re.DOTALL).strip()
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", json_text)
            if not match:
                raise ValueError("AI 返回内容不是合法 JSON")
            payload = json.loads(match.group(0))
        if not isinstance(payload, dict):
            raise ValueError("AI 返回的 JSON 顶层必须是对象")
        return payload

    @staticmethod
    def _to_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _load_runtime_config(self) -> AIRuntimeConfig:
        provider = str(get_config_value("ai", "llm_type", "openai") or "openai").strip().lower()
        if provider not in {"openai", "ollama"}:
            raise ValueError(f"未支持的 AI 提供商类型: {provider}")

        model = str(get_config_value("ai", "default_text_model", "") or "").strip()
        if not model:
            raise ValueError("请先配置 AI 默认文本模型名称")

        base_url = str(get_config_value("ai", "api_base_url", "") or "").strip() or None
        api_key = str(get_config_value("ai", "api_key", "") or "").strip() or None
        max_tokens = self._to_int(get_config_value("ai", "max_tokens"))
        temperature = self._to_float(get_config_value("ai", "temperature"))
        timeout = self._to_int(get_config_value("ai", "timeout")) or 600
        if provider == "openai" and not api_key:
            raise ValueError("OpenAI 模式下请先配置 API 密钥")

        return AIRuntimeConfig(
            provider=provider,
            base_url=base_url,
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )
