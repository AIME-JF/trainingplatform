"""
AI 自然语言转排课配置服务
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.models import Training
from app.schemas import AIScheduleTaskCreateRequest
from app.services.training_schedule_rule import TrainingScheduleRuleService

from .base import BaseAIAgent


class AIScheduleConfigParserService(BaseAIAgent):
    """将自然语言排课要求通过 LLM 解析为结构化配置"""

    SCOPE_LABELS = {
        "all": "全班次",
        "current_week": "指定周",
        "unscheduled": "仅未排课课次",
    }
    GOAL_LABELS = {
        "balanced": "均衡排课",
        "practice_first": "优先实战",
        "theory_first": "优先理论",
        "exam_intensive": "考前强化",
    }
    PLANNING_MODE_LABELS = {
        "auto": "按课程计划自动判断",
        "fill_all_days": "排满",
        "fill_workdays": "排满工作日",
        "by_hours": "按课时排",
    }
    COURSE_TYPE_LABELS = {
        "theory": "理论课",
        "practice": "实操课",
    }
    WEEKDAY_LABELS = {
        1: "周一",
        2: "周二",
        3: "周三",
        4: "周四",
        5: "周五",
        6: "周六",
        7: "周日",
    }

    def preview_task_request(
        self,
        training: Training,
        request: AIScheduleTaskCreateRequest,
        parse_prompt: Optional[bool] = None,
    ) -> dict[str, Any]:
        prompt = str(request.natural_language_prompt or "").strip()
        base_request = request.model_dump(mode="json")
        should_parse_prompt = parse_prompt if parse_prompt is not None else (bool(prompt) and not request.parsed_request_confirmed)
        warnings: List[str] = []

        if should_parse_prompt:
            parsed_payload, warnings = self._parse_with_llm(prompt, training, base_request)
            next_request_payload = self._apply_prompt_payload(base_request, parsed_payload, training)
        else:
            next_request_payload = self._apply_prompt_payload(base_request, {}, training)

        validated_request = AIScheduleTaskCreateRequest.model_validate(next_request_payload)
        preview_payload = validated_request.model_dump(mode="json")
        training_rule_config = TrainingScheduleRuleService.resolve_effective_rule_config(training.schedule_rule_config)
        effective_rule_config = TrainingScheduleRuleService.resolve_effective_rule_config(
            training.schedule_rule_config,
            preview_payload.get("schedule_rule_override"),
        )
        has_parse_context = bool(prompt) or bool(request.parsed_request_confirmed)
        return {
            "request": validated_request,
            "summary": self._build_parse_summary(preview_payload) if has_parse_context else None,
            "warnings": warnings,
            "understood_items": self._build_understood_items(preview_payload) if has_parse_context else [],
            "training_rule_config": training_rule_config,
            "effective_rule_config": effective_rule_config,
        }

    def parse_task_request(self, training: Training, request: AIScheduleTaskCreateRequest) -> dict[str, Any]:
        preview = self.preview_task_request(training, request)
        return {
            "request": preview["request"],
            "summary": preview["summary"],
            "warnings": preview["warnings"],
            "understood_items": preview["understood_items"],
            "training_rule_config": preview["training_rule_config"],
            "effective_rule_config": preview["effective_rule_config"],
        }

    # ------------------------------------------------------------------
    # LLM 解析
    # ------------------------------------------------------------------

    def _parse_with_llm(
        self,
        prompt: str,
        training: Training,
        request_payload: dict[str, Any],
    ) -> tuple[dict[str, Any], list[str]]:
        warnings: List[str] = []
        try:
            config = self._load_runtime_config()
        except Exception as exc:
            return {}, [f"AI 解析未启用：{exc}"]

        try:
            payload = self._call_provider(
                config,
                [
                    {
                        "role": "system",
                        "content": self._build_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": self._build_user_prompt(prompt, training, request_payload),
                    },
                ],
            )
            return self._parse_json_payload(payload), warnings
        except Exception as exc:
            warnings.append(f"AI 解析失败：{exc}")
            return {}, warnings

    def _build_system_prompt(self) -> str:
        return (
            "你是警务培训排课配置解析器。\n"
            "用户会用自然语言描述排课要求，你需要将其转换为结构化 JSON 配置。\n"
            "你只能输出合法 JSON 对象，不要输出 Markdown 代码块、说明文字或任何其他非 JSON 内容。\n"
            "对于用户未明确提及的字段，不要在 JSON 中输出该字段（即省略它），让系统使用默认值。\n"
            "只输出你有信心从用户要求中提取到的字段。"
        )

    def _build_user_prompt(self, prompt: str, training: Training, request_payload: dict[str, Any]) -> str:
        training_rule = TrainingScheduleRuleService.resolve_effective_rule_config(training.schedule_rule_config)
        preserve_existing_schedule = not bool(request_payload.get("overwrite_existing_schedule"))
        existing_schedule_context = self._build_existing_schedule_context(training) if preserve_existing_schedule else ""

        date_reference = self._build_date_reference(training)

        return "\n".join([
            "请将下面的自然语言排课要求解析成 JSON 配置。只输出 JSON 对象，不要输出其他文字。",
            "",
            "# 可输出的顶层字段",
            "",
            "## scope_type (string, 可省略)",
            "排课范围。可选值：",
            '- "all": 全班次，对培训周期内全部日期排课',
            '- "current_week": 仅对指定周排课',
            '- "unscheduled": 仅对未排课的课次排课',
            "",
            "## scope_start_date (string, 可省略)",
            '仅当 scope_type 为 "current_week" 时有效，格式 YYYY-MM-DD，表示指定周内的任意一天',
            "",
            "## goal (string, 可省略)",
            "排课优化目标。可选值：",
            '- "balanced": 均衡排课（默认）',
            '- "practice_first": 优先安排实操/实战课程',
            '- "theory_first": 优先安排理论课程',
            '- "exam_intensive": 考前强化模式',
            "",
            "## planning_mode (string, 可省略)",
            "排课方式。可选值：",
            '- "fill_all_days": 排满所有日期（含周末）',
            '- "fill_workdays": 只排满工作日',
            '- "by_hours": 按每门课程声明的计划课时来排',
            "",
            "## overwrite_existing_schedule (boolean, 可省略)",
            "是否覆盖当前已有课表。true 表示重新排课，false 表示保留已有课次",
            "",
            "## constraint_payload (object, 可省略)",
            "排课约束参数，包含以下子字段：",
            "",
            "### daily_max_hours (number, 可省略)",
            "单日最大课时数，范围 1-12",
            "",
            "### avoid_exam_days (boolean, 可省略)",
            "是否避开考试日排课",
            "",
            "### fixed_course_keys (string[], 可省略)",
            "需要锁定不动的课程键列表",
            "",
            "### blocked_time_slots (array, 可省略)",
            "全局禁止排课的时间段列表。每项格式：",
            '  {"date": "YYYY-MM-DD", "time_range": "HH:MM~HH:MM", "label": "描述"}',
            "如果用户说某个日期或星期几不排课，需要展开为培训周期内所有匹配的具体日期。",
            "如果用户没有指定具体时间段，则 time_range 设为 \"00:00~23:59\" 表示全天禁排。",
            "",
            "### instructor_unavailable_slots (array, 可省略)",
            "教官不可用时间段列表，格式同 blocked_time_slots。label 填教官姓名。",
            "",
            "### location_unavailable_slots (array, 可省略)",
            "场地不可用时间段列表，格式同 blocked_time_slots。label 填场地名称。",
            "",
            "### course_type_time_preferences (array, 可省略)",
            "课程类型的时间段偏好列表。每项格式：",
            "  {",
            '    "course_type": "theory" 或 "practice",',
            '    "start_time": "HH:MM",',
            '    "end_time": "HH:MM",',
            '    "weekdays": [1,2,3,4,5],  // 1=周一 ... 7=周日，空数组表示所有日期',
            '    "priority": "prefer" 或 "only",  // prefer=优先, only=仅允许在此时段',
            '    "label": "描述"',
            "  }",
            "",
            "### exam_week_focus (object, 可省略)",
            "考前强化偏好。格式：",
            "  {",
            '    "course_type": "theory" 或 "practice",  // 可省略',
            '    "course_keywords": ["关键词1", "关键词2"],  // 可省略',
            '    "days_before_exam": 7,  // 考前多少天，1-30',
            '    "label": "描述"',
            "  }",
            "",
            "## schedule_rule_override (object, 可省略)",
            "任务级排课规则覆盖，可包含以下字段：",
            "- lesson_unit_minutes: 每课时分钟数（如 40、45）",
            "- break_minutes: 课间休息分钟数",
            "- max_units_per_session: 一节课最多几个课时",
            "- daily_max_units: 单日最多几个课时",
            "- preferred_planning_mode: fill_all_days / fill_workdays / by_hours",
            "- split_strategy: balanced",
            '- teaching_windows: [{"label": "上午", "start_time": "08:30", "end_time": "12:30"}, ...]',
            "",
            "# 上下文信息",
            "",
            f"培训班名称：{training.name}",
            f"培训周期：{training.start_date} 至 {training.end_date}",
            f"当前培训班默认排课规则：{json.dumps(training_rule, ensure_ascii=False)}",
            "",
            date_reference,
            "",
            (
                "当前课表处理策略：保留当前课表，已有课次需要在排课中避开。"
                if preserve_existing_schedule
                else "当前课表处理策略：允许覆盖当前课表，重新生成新的排课方案。"
            ),
            existing_schedule_context or "当前已有课次：无。",
            "",
            "# 用户的排课要求",
            "",
            prompt,
        ])

    # ------------------------------------------------------------------
    # 请求归一化
    # ------------------------------------------------------------------

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
        constraint_payload["fixed_course_keys"] = list(dict.fromkeys(
            str(item).strip()
            for item in (constraint_payload.get("fixed_course_keys") or [])
            if str(item).strip()
        ))
        constraint_payload["blocked_time_slots"] = self._normalize_unavailable_slots(constraint_payload.get("blocked_time_slots"))
        constraint_payload["instructor_unavailable_slots"] = self._normalize_unavailable_slots(constraint_payload.get("instructor_unavailable_slots"))
        constraint_payload["location_unavailable_slots"] = self._normalize_unavailable_slots(constraint_payload.get("location_unavailable_slots"))
        constraint_payload["course_type_time_preferences"] = self._normalize_course_type_preferences(
            constraint_payload.get("course_type_time_preferences"),
        )
        constraint_payload["exam_week_focus"] = self._normalize_exam_week_focus(constraint_payload.get("exam_week_focus"))
        result["constraint_payload"] = constraint_payload
        result["parsed_request_confirmed"] = bool(result.get("parsed_request_confirmed"))
        return result

    # ------------------------------------------------------------------
    # 展示与摘要
    # ------------------------------------------------------------------

    def _build_parse_summary(self, request_payload: dict[str, Any]) -> str:
        rule_override = request_payload.get("schedule_rule_override") or {}
        constraint_payload = request_payload.get("constraint_payload") or {}
        windows = rule_override.get("teaching_windows") or []
        window_text = "、".join(
            f"{item.get('label') or '时段'} {item.get('start_time')}-{item.get('end_time')}"
            for item in windows[:3]
        ) or "未覆盖培训班默认时间段"
        extras: List[str] = []
        if constraint_payload.get("blocked_time_slots"):
            extras.append(f"禁排时段 {len(constraint_payload.get('blocked_time_slots') or [])} 条")
        if constraint_payload.get("course_type_time_preferences"):
            extras.append(f"课程类型时段偏好 {len(constraint_payload.get('course_type_time_preferences') or [])} 条")
        if constraint_payload.get("exam_week_focus"):
            extras.append("已识别考前强化偏好")
        if request_payload.get("overwrite_existing_schedule"):
            extras.append("最终确认时将覆盖当前课表")
        else:
            extras.append("会保留当前已有课次并尽量绕开")
        extra_text = f"，{'，'.join(extras)}" if extras else ""
        return (
            f"已解析排课配置：范围 {self.SCOPE_LABELS.get(request_payload.get('scope_type'), request_payload.get('scope_type'))}，"
            f"排课方式 {self.PLANNING_MODE_LABELS.get(request_payload.get('planning_mode'), request_payload.get('planning_mode'))}，"
            f"单日最大课时 {(constraint_payload.get('daily_max_hours') or 0)}，"
            f"时间段 {window_text}{extra_text}。"
        )

    def _build_understood_items(self, request_payload: dict[str, Any]) -> List[str]:
        constraint_payload = request_payload.get("constraint_payload") or {}
        items = [
            f"排课范围：{self.SCOPE_LABELS.get(request_payload.get('scope_type'), request_payload.get('scope_type') or '未指定')}",
            f"排课目标：{self.GOAL_LABELS.get(request_payload.get('goal'), request_payload.get('goal') or '未指定')}",
            f"排课方式：{self.PLANNING_MODE_LABELS.get(request_payload.get('planning_mode'), request_payload.get('planning_mode') or '未指定')}",
            f"单日最大课时：{constraint_payload.get('daily_max_hours') or 0}",
            f"避开考试日：{'是' if constraint_payload.get('avoid_exam_days') else '否'}",
            f"当前课表处理：{'覆盖当前课表' if request_payload.get('overwrite_existing_schedule') else '保留当前课表并绕开已有课次'}",
        ]
        if request_payload.get("scope_type") == "current_week" and request_payload.get("scope_start_date"):
            items.append(f"指定周：{request_payload.get('scope_start_date')}")
        fixed_course_keys = constraint_payload.get("fixed_course_keys") or []
        if fixed_course_keys:
            items.append(f"固定课程键：{', '.join(fixed_course_keys[:5])}")
        for preference in constraint_payload.get("course_type_time_preferences") or []:
            weekdays = self._format_weekdays(preference.get("weekdays") or [])
            priority_text = "仅允许" if preference.get("priority") == "only" else "优先"
            items.append(
                f"{self.COURSE_TYPE_LABELS.get(preference.get('course_type'), preference.get('course_type'))}"
                f"{priority_text}安排在 {preference.get('start_time')}-{preference.get('end_time')}"
                f"{f'（{weekdays}）' if weekdays else ''}"
            )
        blocked_slots = constraint_payload.get("blocked_time_slots") or []
        if blocked_slots:
            items.append(f"全局禁排时段：{self._format_slot_preview(blocked_slots)}")
        instructor_slots = constraint_payload.get("instructor_unavailable_slots") or []
        if instructor_slots:
            items.append(f"教官不可用：{self._format_slot_preview(instructor_slots)}")
        location_slots = constraint_payload.get("location_unavailable_slots") or []
        if location_slots:
            items.append(f"场地不可用：{self._format_slot_preview(location_slots)}")
        exam_week_focus = constraint_payload.get("exam_week_focus") or {}
        if exam_week_focus:
            focus_parts = []
            if exam_week_focus.get("course_type"):
                focus_parts.append(self.COURSE_TYPE_LABELS.get(exam_week_focus.get("course_type"), exam_week_focus.get("course_type")))
            if exam_week_focus.get("course_keywords"):
                focus_parts.append("、".join(exam_week_focus.get("course_keywords") or []))
            items.append(
                f"考前 {exam_week_focus.get('days_before_exam') or 7} 天优先强化："
                f"{' / '.join(focus_parts) if focus_parts else '指定课程'}"
            )
        return items

    def _build_existing_schedule_context(self, training: Training) -> str:
        summaries: List[str] = []
        for course in training.courses or []:
            course_name = str(getattr(course, "name", "") or "未命名课程")
            instructor = str(getattr(course, "instructor", "") or "").strip() or "未指定教官"
            for schedule in getattr(course, "schedules", None) or []:
                schedule_payload = schedule if isinstance(schedule, dict) else {}
                schedule_date = getattr(schedule, "date", None) or schedule_payload.get("date")
                time_range = getattr(schedule, "time_range", None) or schedule_payload.get("time_range")
                if not schedule_date or not time_range:
                    continue
                location = getattr(schedule, "location", None) or schedule_payload.get("location") or "未指定地点"
                summaries.append(f"- {schedule_date} {time_range} | {course_name} | {instructor} | {location}")
        if not summaries:
            return ""
        preview_lines = summaries[:40]
        if len(summaries) > len(preview_lines):
            preview_lines.append(f"- 其余 {len(summaries) - len(preview_lines)} 条已有课次省略")
        return "当前已有课次：\n" + "\n".join(preview_lines)

    def _build_date_reference(self, training: Training) -> str:
        """构建培训周期内的日期与星期参考信息，帮助 LLM 将星期几映射为具体日期"""
        if not training.start_date or not training.end_date:
            return ""
        weekday_names = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"}
        lines: List[str] = []
        current = training.start_date
        count = 0
        while current <= training.end_date and count < 120:
            lines.append(f"  {current.isoformat()} ({weekday_names[current.weekday()]})")
            current += timedelta(days=1)
            count += 1
        if current <= training.end_date:
            lines.append(f"  ... 后续日期省略，培训结束日期为 {training.end_date.isoformat()}")
        return "培训周期内的日期列表（供你将星期几、工作日等映射为具体日期）：\n" + "\n".join(lines)

    # ------------------------------------------------------------------
    # 归一化方法
    # ------------------------------------------------------------------

    def _normalize_unavailable_slots(self, raw_slots: Any) -> List[dict[str, Any]]:
        normalized: List[dict[str, Any]] = []
        seen = set()
        for item in raw_slots or []:
            slot_date = self._parse_date(getattr(item, "date", None) or item.get("date"))
            time_range = self._normalize_time_range(getattr(item, "time_range", None) or item.get("time_range"))
            label = str(getattr(item, "label", None) or item.get("label") or "").strip() or None
            if not slot_date or not time_range:
                continue
            key = (slot_date.isoformat(), time_range, label or "")
            if key in seen:
                continue
            seen.add(key)
            normalized.append(
                {
                    "date": slot_date.isoformat(),
                    "time_range": time_range,
                    "label": label,
                }
            )
        return normalized

    def _normalize_course_type_preferences(self, raw_preferences: Any) -> List[dict[str, Any]]:
        normalized: List[dict[str, Any]] = []
        seen = set()
        for item in raw_preferences or []:
            course_type = str(getattr(item, "course_type", None) or item.get("course_type") or "").strip()
            if course_type not in {"theory", "practice"}:
                continue
            start_time = TrainingScheduleRuleService._normalize_clock(getattr(item, "start_time", None) or item.get("start_time"))
            end_time = TrainingScheduleRuleService._normalize_clock(getattr(item, "end_time", None) or item.get("end_time"))
            if not start_time or not end_time or start_time >= end_time:
                continue
            weekdays = sorted({
                int(day)
                for day in (getattr(item, "weekdays", None) or item.get("weekdays") or [])
                if str(day).isdigit() and 1 <= int(day) <= 7
            })
            priority = str(getattr(item, "priority", None) or item.get("priority") or "prefer").strip()
            if priority not in {"prefer", "only"}:
                priority = "prefer"
            label = str(getattr(item, "label", None) or item.get("label") or "").strip() or None
            key = (course_type, start_time, end_time, tuple(weekdays), priority)
            if key in seen:
                continue
            seen.add(key)
            normalized.append(
                {
                    "course_type": course_type,
                    "start_time": start_time,
                    "end_time": end_time,
                    "weekdays": weekdays,
                    "priority": priority,
                    "label": label,
                }
            )
        return normalized

    def _normalize_exam_week_focus(self, raw_focus: Any) -> Optional[dict[str, Any]]:
        if not raw_focus:
            return None
        if hasattr(raw_focus, "model_dump"):
            raw_focus = raw_focus.model_dump(mode="json")
        if not isinstance(raw_focus, dict):
            return None
        course_type = str(raw_focus.get("course_type") or "").strip() or None
        if course_type not in {"theory", "practice"}:
            course_type = None
        course_keywords = list(dict.fromkeys(
            str(item).strip()
            for item in (raw_focus.get("course_keywords") or [])
            if str(item).strip()
        ))
        try:
            days_before_exam = int(raw_focus.get("days_before_exam") or 7)
        except (TypeError, ValueError):
            days_before_exam = 7
        days_before_exam = max(1, min(days_before_exam, 30))
        label = str(raw_focus.get("label") or "").strip() or None
        if not course_type and not course_keywords:
            return None
        return {
            "course_type": course_type,
            "course_keywords": course_keywords,
            "days_before_exam": days_before_exam,
            "label": label,
        }

    def _normalize_time_range(self, raw_value: Any) -> Optional[str]:
        value = str(raw_value or "").strip()
        if "~" not in value:
            return None
        start_text, end_text = [item.strip() for item in value.split("~", 1)]
        start_time = TrainingScheduleRuleService._normalize_clock(start_text)
        end_time = TrainingScheduleRuleService._normalize_clock(end_text)
        if not start_time or not end_time or start_time >= end_time:
            return None
        return f"{start_time}~{end_time}"

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    def _parse_date(self, raw_value: Any) -> Optional[date]:
        if raw_value is None:
            return None
        if isinstance(raw_value, date):
            return raw_value
        value = str(raw_value).strip()
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def _format_weekdays(self, weekdays: List[int]) -> str:
        labels = [self.WEEKDAY_LABELS.get(int(day)) for day in weekdays if self.WEEKDAY_LABELS.get(int(day))]
        return "、".join(labels)

    def _format_slot_preview(self, slots: List[dict[str, Any]]) -> str:
        parts: List[str] = []
        for item in (slots or [])[:3]:
            prefix = f"{item.get('label')} " if item.get("label") else ""
            parts.append(f"{prefix}{item.get('date')} {item.get('time_range')}")
        suffix = " 等" if len(slots or []) > 3 else ""
        return "；".join(parts) + suffix

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
