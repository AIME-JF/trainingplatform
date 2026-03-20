"""
培训班排课规则归一化服务
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List

from app.services.system import get_config_value


class TrainingScheduleRuleService:
    """统一处理培训班排课规则的默认值、归一化与覆盖合并"""

    DEFAULT_RULE_CONFIG = {
        "lesson_unit_minutes": 40,
        "break_minutes": 10,
        "max_units_per_session": 3,
        "daily_max_units": 6,
        "preferred_planning_mode": "fill_workdays",
        "split_strategy": "balanced",
        "teaching_windows": [
            {"label": "上午", "start_time": "08:30", "end_time": "12:30"},
            {"label": "下午", "start_time": "14:00", "end_time": "17:30"},
        ],
    }
    VALID_PLANNING_MODES = {"fill_all_days", "fill_workdays", "by_hours"}
    VALID_SPLIT_STRATEGIES = {"balanced"}

    @classmethod
    def get_system_default_rule_config(cls) -> Dict[str, Any]:
        base = deepcopy(cls.DEFAULT_RULE_CONFIG)
        base["lesson_unit_minutes"] = cls._normalize_int(
            get_config_value("training_schedule", "lesson_unit_minutes", base["lesson_unit_minutes"]),
            base["lesson_unit_minutes"],
            minimum=20,
            maximum=180,
        )
        base["break_minutes"] = cls._normalize_int(
            get_config_value("training_schedule", "break_minutes", base["break_minutes"]),
            base["break_minutes"],
            minimum=0,
            maximum=60,
        )
        base["max_units_per_session"] = cls._normalize_int(
            get_config_value("training_schedule", "max_units_per_session", base["max_units_per_session"]),
            base["max_units_per_session"],
            minimum=1,
            maximum=12,
        )
        base["daily_max_units"] = cls._normalize_int(
            get_config_value("training_schedule", "daily_max_units", base["daily_max_units"]),
            base["daily_max_units"],
            minimum=1,
            maximum=24,
        )
        preferred_planning_mode = str(
            get_config_value("training_schedule", "preferred_planning_mode", base["preferred_planning_mode"])
            or base["preferred_planning_mode"]
        ).strip()
        if preferred_planning_mode in cls.VALID_PLANNING_MODES:
            base["preferred_planning_mode"] = preferred_planning_mode
        split_strategy = str(
            get_config_value("training_schedule", "split_strategy", base["split_strategy"])
            or base["split_strategy"]
        ).strip()
        if split_strategy in cls.VALID_SPLIT_STRATEGIES:
            base["split_strategy"] = split_strategy
        base["teaching_windows"] = cls._normalize_windows(
            get_config_value("training_schedule", "teaching_windows", None),
            deepcopy(base["teaching_windows"]),
        )
        return cls.normalize_rule_config(base, fallback=cls.DEFAULT_RULE_CONFIG)

    @classmethod
    def normalize_rule_config(
        cls,
        value: Any,
        fallback: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        base = deepcopy(fallback or cls.get_system_default_rule_config())
        payload = value if isinstance(value, dict) else {}
        normalized = deepcopy(base)
        normalized["lesson_unit_minutes"] = cls._normalize_int(
            payload.get("lesson_unit_minutes"),
            base["lesson_unit_minutes"],
            minimum=20,
            maximum=180,
        )
        normalized["break_minutes"] = cls._normalize_int(
            payload.get("break_minutes"),
            base["break_minutes"],
            minimum=0,
            maximum=60,
        )
        normalized["max_units_per_session"] = cls._normalize_int(
            payload.get("max_units_per_session"),
            base["max_units_per_session"],
            minimum=1,
            maximum=12,
        )
        normalized["daily_max_units"] = cls._normalize_int(
            payload.get("daily_max_units"),
            base["daily_max_units"],
            minimum=1,
            maximum=24,
        )
        preferred_planning_mode = str(payload.get("preferred_planning_mode") or base["preferred_planning_mode"]).strip()
        normalized["preferred_planning_mode"] = (
            preferred_planning_mode if preferred_planning_mode in cls.VALID_PLANNING_MODES else base["preferred_planning_mode"]
        )
        split_strategy = str(payload.get("split_strategy") or base["split_strategy"]).strip()
        normalized["split_strategy"] = split_strategy if split_strategy in cls.VALID_SPLIT_STRATEGIES else base["split_strategy"]
        normalized["teaching_windows"] = cls._normalize_windows(
            payload.get("teaching_windows"),
            deepcopy(base["teaching_windows"]),
        )
        return normalized

    @classmethod
    def resolve_effective_rule_config(
        cls,
        training_rule_config: Any,
        override_rule_config: Any = None,
    ) -> Dict[str, Any]:
        system_default = cls.get_system_default_rule_config()
        training_rule = cls.normalize_rule_config(training_rule_config, fallback=system_default)
        if override_rule_config is None:
            return training_rule
        return cls.normalize_rule_config(override_rule_config, fallback=training_rule)

    @classmethod
    def windows_to_text(cls, windows: List[Dict[str, Any]] | None) -> str:
        lines: List[str] = []
        for window in cls._normalize_windows(windows, []):
            label = str(window.get("label") or "").strip()
            range_text = f"{window['start_time']}-{window['end_time']}"
            lines.append(f"{label}|{range_text}" if label else range_text)
        return "\n".join(lines)

    @classmethod
    def _normalize_windows(
        cls,
        value: Any,
        fallback: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if isinstance(value, str):
            parsed = cls._parse_windows_text(value)
        elif isinstance(value, list):
            parsed = []
            for item in value:
                if not isinstance(item, dict):
                    continue
                start_time = cls._normalize_clock(item.get("start_time"))
                end_time = cls._normalize_clock(item.get("end_time"))
                if not start_time or not end_time or start_time >= end_time:
                    continue
                parsed.append(
                    {
                        "label": str(item.get("label") or "").strip(),
                        "start_time": start_time,
                        "end_time": end_time,
                    }
                )
        else:
            parsed = []

        if not parsed:
            parsed = deepcopy(fallback)
        parsed = sorted(parsed, key=lambda item: item["start_time"])
        deduped: List[Dict[str, Any]] = []
        seen = set()
        for item in parsed:
            key = (item["start_time"], item["end_time"], item.get("label") or "")
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped or deepcopy(fallback)

    @classmethod
    def _parse_windows_text(cls, value: str) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for raw_line in str(value or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            label = ""
            range_text = line
            if "|" in line:
                label, range_text = [part.strip() for part in line.split("|", 1)]
            separator = "-" if "-" in range_text else ("~" if "~" in range_text else None)
            if not separator:
                continue
            start_raw, end_raw = [part.strip() for part in range_text.split(separator, 1)]
            start_time = cls._normalize_clock(start_raw)
            end_time = cls._normalize_clock(end_raw)
            if not start_time or not end_time or start_time >= end_time:
                continue
            result.append(
                {
                    "label": label,
                    "start_time": start_time,
                    "end_time": end_time,
                }
            )
        return result

    @staticmethod
    def _normalize_int(value: Any, default: int, minimum: int, maximum: int) -> int:
        try:
            numeric = int(float(value))
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, numeric))

    @staticmethod
    def _normalize_clock(value: Any) -> str | None:
        if not value:
            return None
        try:
            parsed = datetime.strptime(str(value).strip(), "%H:%M")
        except ValueError:
            return None
        return parsed.strftime("%H:%M")
