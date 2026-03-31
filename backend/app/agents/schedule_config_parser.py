"""
AI 自然语言转排课配置服务
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.models import Training
from app.schemas import AIScheduleTaskCreateRequest
from app.services.training_schedule_rule import TrainingScheduleRuleService

from .base import BaseAIAgent

class AIScheduleConfigParserService(BaseAIAgent):
    """将自然语言排课要求解析为结构化配置，并用规则做兜底归一化"""

    DEFAULT_WINDOW_MAP = {
        "上午": ("08:30", "12:30"),
        "早上": ("08:30", "12:30"),
        "下午": ("14:00", "17:30"),
        "晚上": ("19:00", "21:00"),
        "晚间": ("19:00", "21:00"),
    }
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
    WEEKDAY_CHAR_MAP = {
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "日": 7,
        "天": 7,
    }
    UNAVAILABLE_KEYWORDS = ("不可用", "不能用", "禁用", "禁排", "不排课", "不上课")

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
            heuristic_payload = self._parse_with_rules(prompt, training, base_request)
            ai_payload, warnings = self._parse_with_llm(prompt, training, base_request)
            merged_payload = self._merge_dicts(heuristic_payload, ai_payload)
            next_request_payload = self._apply_prompt_payload(base_request, merged_payload, training)
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
            return {}, [f"AI 解析未启用，已按规则兜底：{exc}"]

        try:
            payload = self._call_provider(
                config,
                [
                    {
                        "role": "system",
                        "content": "你是警务培训排课配置解析器。你只能输出合法 JSON 对象，不能输出 Markdown 或说明文字。",
                    },
                    {
                        "role": "user",
                        "content": self._build_llm_prompt(prompt, training, request_payload),
                    },
                ],
            )
            return self._parse_json_payload(payload), warnings
        except Exception as exc:
            warnings.append(f"AI 解析失败，已按规则兜底：{exc}")
            return {}, warnings

    def _parse_with_rules(
        self,
        prompt: str,
        training: Training,
        base_request_payload: dict[str, Any],
    ) -> dict[str, Any]:
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
        elif "实战" in prompt or "实操" in prompt:
            payload["goal"] = "practice_first"
        elif "理论" in prompt:
            payload["goal"] = "theory_first"

        constraint_payload = payload.setdefault("constraint_payload", {})
        if "按课时" in prompt:
            payload["planning_mode"] = "by_hours"
        elif "工作日" in prompt:
            payload["planning_mode"] = "fill_workdays"
        elif "排满" in prompt or "排满所有" in prompt or "排满全部" in prompt:
            payload["planning_mode"] = "fill_all_days"

        if any(keyword in prompt for keyword in ("避开考试", "不要和考试冲突", "避开考试日")):
            constraint_payload["avoid_exam_days"] = True
        elif any(keyword in prompt for keyword in ("不避开考试", "无需避开考试")):
            constraint_payload["avoid_exam_days"] = False

        daily_limit_match = re.search(r"单日[^0-9]{0,6}(\d+(?:\.\d+)?)\s*课时", prompt)
        if daily_limit_match:
            constraint_payload["daily_max_hours"] = float(daily_limit_match.group(1))

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
            constraint_payload["fixed_course_keys"] = list(dict.fromkeys(course_keys))

        if rule_payload:
            payload["schedule_rule_override"] = rule_payload

        temp_request_payload = self._apply_prompt_payload(base_request_payload, payload, training)
        temp_rule_config = TrainingScheduleRuleService.resolve_effective_rule_config(
            training.schedule_rule_config,
            temp_request_payload.get("schedule_rule_override"),
        )

        blocked_time_slots = self._extract_blocked_time_slots(prompt, training, temp_request_payload, temp_rule_config)
        if blocked_time_slots:
            constraint_payload["blocked_time_slots"] = blocked_time_slots

        course_type_preferences = self._extract_course_type_preferences(prompt, temp_rule_config)
        if course_type_preferences:
            constraint_payload["course_type_time_preferences"] = course_type_preferences

        instructor_slots = self._extract_named_unavailable_slots(
            prompt,
            training,
            temp_request_payload,
            temp_rule_config,
            resource_type="instructor",
        )
        if instructor_slots:
            constraint_payload["instructor_unavailable_slots"] = instructor_slots

        location_slots = self._extract_named_unavailable_slots(
            prompt,
            training,
            temp_request_payload,
            temp_rule_config,
            resource_type="location",
        )
        if location_slots:
            constraint_payload["location_unavailable_slots"] = location_slots

        exam_week_focus = self._extract_exam_week_focus(prompt)
        if exam_week_focus:
            constraint_payload["exam_week_focus"] = exam_week_focus
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

    def _build_llm_prompt(self, prompt: str, training: Training, request_payload: dict[str, Any]) -> str:
        training_rule = TrainingScheduleRuleService.resolve_effective_rule_config(training.schedule_rule_config)
        preserve_existing_schedule = not bool(request_payload.get("overwrite_existing_schedule"))
        existing_schedule_context = self._build_existing_schedule_context(training) if preserve_existing_schedule else ""
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
                '- constraint_payload.blocked_time_slots: [{"date":"2026-03-25","time_range":"14:00~17:30","label":"周三下午"}]',
                '- constraint_payload.course_type_time_preferences: [{"course_type":"theory","start_time":"08:30","end_time":"12:30","weekdays":[1,2,3,4,5],"priority":"only","label":"上午只排理论"}]',
                '- constraint_payload.instructor_unavailable_slots: [{"date":"2026-03-25","time_range":"14:00~17:30","label":"张三"}]',
                '- constraint_payload.location_unavailable_slots: [{"date":"2026-03-25","time_range":"14:00~17:30","label":"靶场"}]',
                '- constraint_payload.exam_week_focus: {"course_type":"practice","course_keywords":["警械"],"days_before_exam":7,"label":"考前强化"}',
                "- schedule_rule_override: 对象，可包含 lesson_unit_minutes, break_minutes, max_units_per_session, daily_max_units, preferred_planning_mode, split_strategy, teaching_windows",
                '- teaching_windows: [{\"label\":\"上午\",\"start_time\":\"08:30\",\"end_time\":\"12:30\"}]',
                "- overwrite_existing_schedule: true/false，可省略",
                f"当前培训班默认规则：{json.dumps(training_rule, ensure_ascii=False)}",
                f"培训班名称：{training.name}",
                f"培训周期：{training.start_date} 至 {training.end_date}",
                (
                    "当前课表处理策略：保留当前课表，已有课次需要在后续排课中尽量避开。"
                    if preserve_existing_schedule
                    else "当前课表处理策略：允许覆盖当前课表，重新生成新的排课方案。"
                ),
                existing_schedule_context or "当前已有课次：无或无需额外参考。",
                "用户要求：",
                prompt,
            ]
        )

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

    def _extract_course_type_preferences(self, prompt: str, rule_config: dict[str, Any]) -> List[dict[str, Any]]:
        preferences: List[dict[str, Any]] = []
        for fragment in self._split_prompt_fragments(prompt):
            course_type = self._extract_course_type(fragment)
            if not course_type:
                continue
            if any(keyword in fragment for keyword in self.UNAVAILABLE_KEYWORDS):
                continue
            time_window = self._resolve_window_from_text(fragment, rule_config)
            if not time_window:
                continue
            has_preference_intent = any(keyword in fragment for keyword in ("只排", "仅排", "只能排", "优先", "尽量", "安排", "放在", "集中"))
            has_window_mapping_intent = bool(
                re.search(r"(上午|早上|下午|晚上|晚间).{0,6}(理论|实操|实战)", fragment)
                or re.search(r"(理论|实操|实战).{0,6}(上午|早上|下午|晚上|晚间)", fragment)
            )
            if not has_preference_intent and not has_window_mapping_intent:
                continue
            weekdays = self._extract_weekdays(fragment)
            priority = "only" if any(keyword in fragment for keyword in ("只排", "仅排", "只能排")) else "prefer"
            preferences.append(
                {
                    "course_type": course_type,
                    "start_time": time_window["start_time"],
                    "end_time": time_window["end_time"],
                    "weekdays": weekdays,
                    "priority": priority,
                    "label": fragment[:40],
                }
            )
        return self._normalize_course_type_preferences(preferences)

    def _extract_blocked_time_slots(
        self,
        prompt: str,
        training: Training,
        request_payload: dict[str, Any],
        rule_config: dict[str, Any],
    ) -> List[dict[str, Any]]:
        slots: List[dict[str, Any]] = []
        for fragment in self._split_prompt_fragments(prompt):
            if not any(keyword in fragment for keyword in self.UNAVAILABLE_KEYWORDS):
                continue
            if "教官" in fragment or "场地" in fragment:
                continue
            dates = self._resolve_dates_from_fragment(fragment, training, request_payload)
            if not dates:
                continue
            time_window = self._resolve_window_from_text(fragment, rule_config, full_day_default=True)
            if not time_window:
                continue
            for slot_date in dates:
                slots.append(
                    {
                        "date": slot_date.isoformat(),
                        "time_range": f"{time_window['start_time']}~{time_window['end_time']}",
                        "label": fragment[:40],
                    }
                )
        return self._normalize_unavailable_slots(slots)

    def _extract_named_unavailable_slots(
        self,
        prompt: str,
        training: Training,
        request_payload: dict[str, Any],
        rule_config: dict[str, Any],
        resource_type: str,
    ) -> List[dict[str, Any]]:
        keyword = "教官" if resource_type == "instructor" else "场地"
        slots: List[dict[str, Any]] = []
        for fragment in self._split_prompt_fragments(prompt):
            if keyword not in fragment or not any(item in fragment for item in self.UNAVAILABLE_KEYWORDS):
                continue
            label = self._extract_resource_label(fragment, keyword)
            if not label:
                continue
            dates = self._resolve_dates_from_fragment(fragment, training, request_payload)
            if not dates:
                continue
            time_window = self._resolve_window_from_text(fragment, rule_config, full_day_default=True)
            if not time_window:
                continue
            for slot_date in dates:
                slots.append(
                    {
                        "date": slot_date.isoformat(),
                        "time_range": f"{time_window['start_time']}~{time_window['end_time']}",
                        "label": label,
                    }
                )
        return self._normalize_unavailable_slots(slots)

    def _extract_exam_week_focus(self, prompt: str) -> Optional[dict[str, Any]]:
        if not (
            re.search(r"(?:考前|考试前)\s*\d+\s*天", prompt)
            or any(keyword in prompt for keyword in ("考前一周", "考试前一周", "考前强化", "冲刺阶段"))
        ):
            return None
        focus_payload: dict[str, Any] = {
            "days_before_exam": 7,
            "course_keywords": [],
            "label": "考前强化",
        }
        day_match = re.search(r"(?:考前|考试前)\s*(\d+)\s*天", prompt)
        if day_match:
            focus_payload["days_before_exam"] = max(1, min(int(day_match.group(1)), 30))
        elif "考前一周" in prompt or "考试前一周" in prompt:
            focus_payload["days_before_exam"] = 7
        course_type = self._extract_course_type(prompt)
        if course_type:
            focus_payload["course_type"] = course_type
        keyword_match = re.search(
            r"(?:考前|考试前)(?:一周|\s*\d+\s*天)?[^。；，,\n]{0,12}(?:优先|重点|强化)(.*?)(?:课程|训练|科目)",
            prompt,
        )
        if keyword_match:
            focus_payload["course_keywords"] = list(dict.fromkeys(
                item.strip()
                for item in re.split(r"[、,，/和及]", keyword_match.group(1))
                if item and item.strip() and item.strip() not in {"某类", "某些", "相关", "专项"}
            ))
        if not focus_payload.get("course_type") and not focus_payload.get("course_keywords"):
            focus_payload["course_type"] = "practice" if "实" in prompt else "theory"
        return self._normalize_exam_week_focus(focus_payload)

    def _resolve_dates_from_fragment(
        self,
        fragment: str,
        training: Training,
        request_payload: dict[str, Any],
    ) -> List[date]:
        explicit_dates = self._extract_explicit_dates(fragment)
        if explicit_dates:
            return explicit_dates
        weekdays = self._extract_weekdays(fragment)
        if not weekdays:
            return []
        planning_dates = self._resolve_preview_dates(training, request_payload)
        return [item for item in planning_dates if item.isoweekday() in weekdays]

    def _resolve_preview_dates(self, training: Training, request_payload: dict[str, Any]) -> List[date]:
        start_date = training.start_date
        end_date = training.end_date
        if request_payload.get("scope_type") == "current_week":
            start_date = self._resolve_scope_week_start(training, request_payload.get("scope_start_date"))
            end_date = min(training.end_date, start_date + timedelta(days=6))
        dates: List[date] = []
        current = start_date
        while current <= end_date:
            if training.start_date <= current <= training.end_date:
                dates.append(current)
            current += timedelta(days=1)
        return dates

    def _resolve_scope_week_start(self, training: Training, raw_value: Any) -> date:
        requested_date = self._parse_date(raw_value)
        current_week_start = date.today() - timedelta(days=date.today().weekday())
        min_week_start = training.start_date - timedelta(days=training.start_date.weekday())
        max_week_start = training.end_date - timedelta(days=training.end_date.weekday())
        default_week_start = min(max(current_week_start, min_week_start), max_week_start)
        if requested_date is None:
            return default_week_start
        normalized_requested = requested_date - timedelta(days=requested_date.weekday())
        return min(max(normalized_requested, min_week_start), max_week_start)

    def _resolve_window_from_text(
        self,
        text: str,
        rule_config: dict[str, Any],
        full_day_default: bool = False,
    ) -> Optional[dict[str, str]]:
        time_match = re.search(r"(\d{1,2}:\d{2})\s*[-~到至]\s*(\d{1,2}:\d{2})", text)
        if time_match:
            start_time = TrainingScheduleRuleService._normalize_clock(time_match.group(1))
            end_time = TrainingScheduleRuleService._normalize_clock(time_match.group(2))
            if start_time and end_time and start_time < end_time:
                return {
                    "label": "",
                    "start_time": start_time,
                    "end_time": end_time,
                }

        for label in ("上午", "早上", "下午", "晚上", "晚间"):
            if label not in text:
                continue
            normalized_label = "上午" if label == "早上" else "晚上" if label == "晚间" else label
            matched = self._match_window_by_label(rule_config, normalized_label)
            if matched:
                return matched
            start_time, end_time = self.DEFAULT_WINDOW_MAP.get(normalized_label, ("08:30", "12:30"))
            return {
                "label": normalized_label,
                "start_time": start_time,
                "end_time": end_time,
            }

        if full_day_default:
            return {
                "label": "全天",
                "start_time": "00:00",
                "end_time": "23:59",
            }
        return None

    def _match_window_by_label(self, rule_config: dict[str, Any], target_label: str) -> Optional[dict[str, str]]:
        normalized_target = target_label.strip()
        for item in rule_config.get("teaching_windows") or []:
            label = str(item.get("label") or "").strip()
            if not label:
                continue
            if normalized_target in label or label in normalized_target:
                return {
                    "label": label,
                    "start_time": item.get("start_time"),
                    "end_time": item.get("end_time"),
                }
        return None

    def _extract_course_type(self, text: str) -> Optional[str]:
        if any(keyword in text for keyword in ("实操", "实战")):
            return "practice"
        if "理论" in text:
            return "theory"
        return None

    def _extract_resource_label(self, fragment: str, keyword: str) -> str:
        prefix_match = re.search(rf"{keyword}\s*([^\s，。；,;]+)", fragment)
        if prefix_match:
            return prefix_match.group(1).strip()
        suffix_match = re.search(rf"([^\s，。；,;]+)\s*{keyword}", fragment)
        if suffix_match:
            return suffix_match.group(1).strip()
        return ""

    def _extract_weekdays(self, text: str) -> List[int]:
        weekdays: List[int] = []
        if "工作日" in text:
            weekdays.extend([1, 2, 3, 4, 5])
        if "周末" in text:
            weekdays.extend([6, 7])

        range_match = re.search(r"(?:周|星期)([一二三四五六日天])\s*[到至-]\s*(?:周|星期)?([一二三四五六日天])", text)
        if range_match:
            start_value = self.WEEKDAY_CHAR_MAP.get(range_match.group(1))
            end_value = self.WEEKDAY_CHAR_MAP.get(range_match.group(2))
            if start_value and end_value:
                if start_value <= end_value:
                    weekdays.extend(range(start_value, end_value + 1))
                else:
                    weekdays.extend(list(range(start_value, 8)) + list(range(1, end_value + 1)))

        for match in re.finditer(r"(?:周|星期)([一二三四五六日天])", text):
            mapped = self.WEEKDAY_CHAR_MAP.get(match.group(1))
            if mapped:
                weekdays.append(mapped)
        return sorted(dict.fromkeys(weekdays))

    def _extract_explicit_dates(self, text: str) -> List[date]:
        dates: List[date] = []
        for match in re.finditer(r"(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})", text):
            try:
                dates.append(date(int(match.group(1)), int(match.group(2)), int(match.group(3))))
            except ValueError:
                continue
        return dates

    @staticmethod
    def _split_prompt_fragments(prompt: str) -> List[str]:
        fragments = [item.strip() for item in re.split(r"[。；;\n]", prompt) if item and item.strip()]
        result: List[str] = []
        for fragment in fragments:
            result.extend([item.strip() for item in re.split(r"[，,]", fragment) if item and item.strip()])
        return result

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
