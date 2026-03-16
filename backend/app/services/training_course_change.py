"""
培训班课程/课次变更留痕服务
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.models import TrainingCourse, TrainingCourseChangeLog


class TrainingCourseChangeService:
    """统一处理培训班课程与课次变更快照、diff 和日志写入。"""

    COURSE_TARGET = "course"
    SESSION_TARGET = "session"

    COURSE_FIELDS = ("name", "instructor", "primary_instructor_id", "assistant_instructor_ids", "hours", "type")
    SESSION_FIELDS = (
        "date",
        "time_range",
        "hours",
        "location",
        "status",
        "started_at",
        "checkin_started_at",
        "checkin_ended_at",
        "checkout_started_at",
        "checkout_ended_at",
        "ended_at",
        "skipped_at",
        "skipped_by",
        "skip_reason",
    )
    SESSION_STATUS_FIELDS = {
        "status",
        "started_at",
        "checkin_started_at",
        "checkin_ended_at",
        "checkout_started_at",
        "checkout_ended_at",
        "ended_at",
        "skipped_at",
        "skipped_by",
        "skip_reason",
    }
    FIELD_LABELS = {
        "name": "课程名称",
        "instructor": "主讲教官",
        "primary_instructor_id": "主讲教官账号",
        "assistant_instructor_ids": "带教教官",
        "hours": "课时",
        "type": "课程类型",
        "date": "日期",
        "time_range": "时间段",
        "location": "地点",
        "status": "状态",
        "started_at": "开始时间",
        "checkin_started_at": "签到开始时间",
        "checkin_ended_at": "签到结束时间",
        "checkout_started_at": "签退开始时间",
        "checkout_ended_at": "签退结束时间",
        "ended_at": "结束时间",
        "skipped_at": "跳过时间",
        "skipped_by": "跳过人",
        "skip_reason": "跳过原因",
    }

    def __init__(self, db: Session):
        self.db = db

    def ensure_course_keys(self, courses: Iterable[TrainingCourse]) -> bool:
        """为缺失 course_key 的课程补稳定键。"""
        changed = False
        used_keys = set()
        for course in courses or []:
            key = str(getattr(course, "course_key", "") or "").strip()
            if not key or key in used_keys:
                key = str(uuid.uuid4())
                course.course_key = key
                changed = True
            used_keys.add(key)
        return changed

    def snapshot_course_entities(self, courses: Iterable[TrainingCourse]) -> List[Dict[str, Any]]:
        return [self._normalize_course(course) for course in courses or []]

    def snapshot_course_payloads(self, courses: Iterable[Any]) -> List[Dict[str, Any]]:
        return [self._normalize_course(course) for course in courses or []]

    def record_changes(
        self,
        training_id: int,
        before_courses: Iterable[Any],
        after_courses: Iterable[Any],
        actor_id: Optional[int],
        source: str,
    ) -> int:
        before_items = self._sorted_courses([self._normalize_course(item) for item in before_courses or []])
        after_items = self._sorted_courses([self._normalize_course(item) for item in after_courses or []])
        logs = self._build_logs(training_id, before_items, after_items, actor_id, source)
        for log in logs:
            self.db.add(log)
        return len(logs)

    def _build_logs(
        self,
        training_id: int,
        before_courses: List[Dict[str, Any]],
        after_courses: List[Dict[str, Any]],
        actor_id: Optional[int],
        source: str,
    ) -> List[TrainingCourseChangeLog]:
        logs: List[TrainingCourseChangeLog] = []
        batch_id = str(uuid.uuid4())

        before_map = {self._course_identity(item): item for item in before_courses}
        after_map = {self._course_identity(item): item for item in after_courses}

        all_course_keys = list(dict.fromkeys([*before_map.keys(), *after_map.keys()]))
        for course_key in all_course_keys:
            before_course = before_map.get(course_key)
            after_course = after_map.get(course_key)
            if before_course and not after_course:
                logs.append(self._make_course_log(training_id, actor_id, source, batch_id, "delete", before_course, None))
                logs.extend(self._make_schedule_logs(training_id, actor_id, source, batch_id, before_course, None))
                continue
            if after_course and not before_course:
                logs.append(self._make_course_log(training_id, actor_id, source, batch_id, "create", None, after_course))
                logs.extend(self._make_schedule_logs(training_id, actor_id, source, batch_id, None, after_course))
                continue
            if not before_course or not after_course:
                continue

            changed_course_fields = [
                field for field in self.COURSE_FIELDS if before_course.get(field) != after_course.get(field)
            ]
            if changed_course_fields:
                logs.append(
                    self._make_course_log(
                        training_id,
                        actor_id,
                        source,
                        batch_id,
                        "update",
                        before_course,
                        after_course,
                        changed_fields=changed_course_fields,
                    )
                )

            logs.extend(self._make_schedule_logs(training_id, actor_id, source, batch_id, before_course, after_course))

        return logs

    def _make_schedule_logs(
        self,
        training_id: int,
        actor_id: Optional[int],
        source: str,
        batch_id: str,
        before_course: Optional[Dict[str, Any]],
        after_course: Optional[Dict[str, Any]],
    ) -> List[TrainingCourseChangeLog]:
        logs: List[TrainingCourseChangeLog] = []
        before_map = {
            self._schedule_identity(item): item for item in (before_course or {}).get("schedules", [])
        }
        after_map = {
            self._schedule_identity(item): item for item in (after_course or {}).get("schedules", [])
        }
        all_schedule_keys = list(dict.fromkeys([*before_map.keys(), *after_map.keys()]))

        for schedule_key in all_schedule_keys:
            before_schedule = before_map.get(schedule_key)
            after_schedule = after_map.get(schedule_key)
            course_snapshot = after_course or before_course or {}
            course_name = course_snapshot.get("name")
            course_key = course_snapshot.get("course_key")
            if before_schedule and not after_schedule:
                logs.append(
                    self._make_session_log(
                        training_id,
                        actor_id,
                        source,
                        batch_id,
                        "delete",
                        course_key,
                        course_name,
                        before_schedule,
                        None,
                    )
                )
                continue
            if after_schedule and not before_schedule:
                logs.append(
                    self._make_session_log(
                        training_id,
                        actor_id,
                        source,
                        batch_id,
                        "create",
                        course_key,
                        course_name,
                        None,
                        after_schedule,
                    )
                )
                continue
            if not before_schedule or not after_schedule:
                continue

            changed_fields = [
                field for field in self.SESSION_FIELDS if before_schedule.get(field) != after_schedule.get(field)
            ]
            if not changed_fields:
                continue
            action = "status_change" if set(changed_fields).issubset(self.SESSION_STATUS_FIELDS) else "update"
            logs.append(
                self._make_session_log(
                    training_id,
                    actor_id,
                    source,
                    batch_id,
                    action,
                    course_key,
                    course_name,
                    before_schedule,
                    after_schedule,
                    changed_fields=changed_fields,
                )
            )
        return logs

    def _make_course_log(
        self,
        training_id: int,
        actor_id: Optional[int],
        source: str,
        batch_id: str,
        action: str,
        before_course: Optional[Dict[str, Any]],
        after_course: Optional[Dict[str, Any]],
        changed_fields: Optional[List[str]] = None,
    ) -> TrainingCourseChangeLog:
        course_snapshot = after_course or before_course or {}
        course_name = course_snapshot.get("name")
        summary = {
            "create": f"新增课程：{course_name or '未命名课程'}",
            "delete": f"删除课程：{course_name or '未命名课程'}",
        }.get(action)
        if summary is None:
            labels = self._format_changed_fields(changed_fields or [])
            summary = f"更新课程「{course_name or '未命名课程'}」：{labels}"
        return TrainingCourseChangeLog(
            training_id=training_id,
            course_key=course_snapshot.get("course_key"),
            actor_id=actor_id,
            target_type=self.COURSE_TARGET,
            action=action,
            source=source,
            batch_id=batch_id,
            course_name=course_name,
            summary=summary,
            before_json=deepcopy(before_course) if before_course is not None else None,
            after_json=deepcopy(after_course) if after_course is not None else None,
        )

    def _make_session_log(
        self,
        training_id: int,
        actor_id: Optional[int],
        source: str,
        batch_id: str,
        action: str,
        course_key: Optional[str],
        course_name: Optional[str],
        before_schedule: Optional[Dict[str, Any]],
        after_schedule: Optional[Dict[str, Any]],
        changed_fields: Optional[List[str]] = None,
    ) -> TrainingCourseChangeLog:
        schedule_snapshot = after_schedule or before_schedule or {}
        session_label = self._build_session_label(schedule_snapshot)
        if action == "create":
            summary = f"新增课次：{session_label}"
        elif action == "delete":
            summary = f"删除课次：{session_label}"
        elif action == "status_change":
            labels = self._format_changed_fields(changed_fields or [])
            summary = f"课次状态变更「{session_label}」：{labels}"
        else:
            labels = self._format_changed_fields(changed_fields or [])
            summary = f"更新课次「{session_label}」：{labels}"
        return TrainingCourseChangeLog(
            training_id=training_id,
            course_key=course_key,
            session_key=schedule_snapshot.get("session_id"),
            actor_id=actor_id,
            target_type=self.SESSION_TARGET,
            action=action,
            source=source,
            batch_id=batch_id,
            course_name=course_name,
            session_label=session_label,
            summary=summary,
            before_json=deepcopy(before_schedule) if before_schedule is not None else None,
            after_json=deepcopy(after_schedule) if after_schedule is not None else None,
        )

    def _normalize_course(self, course: Any) -> Dict[str, Any]:
        if isinstance(course, dict):
            raw = dict(course)
            schedules = raw.get("schedules") or []
            course_key = raw.get("course_key") or raw.get("courseKey")
            primary_instructor_id = raw.get("primary_instructor_id", raw.get("primaryInstructorId"))
            assistant_instructor_ids = raw.get("assistant_instructor_ids", raw.get("assistantInstructorIds")) or []
        else:
            raw = course
            schedules = getattr(raw, "schedules", None) or []
            course_key = getattr(raw, "course_key", None)
            primary_instructor_id = getattr(raw, "primary_instructor_id", None)
            assistant_instructor_ids = getattr(raw, "assistant_instructor_ids", None) or []

        normalized = {
            "course_key": self._clean_text(course_key),
            "name": self._clean_text(self._read_value(raw, "name")),
            "instructor": self._clean_text(self._read_value(raw, "instructor")),
            "primary_instructor_id": self._to_int(primary_instructor_id),
            "assistant_instructor_ids": self._normalize_id_list(assistant_instructor_ids),
            "hours": self._to_float(self._read_value(raw, "hours")),
            "type": self._clean_text(self._read_value(raw, "type")) or "theory",
            "schedules": self._sorted_schedules([self._normalize_schedule(item) for item in schedules]),
        }
        return normalized

    def _normalize_schedule(self, schedule: Any) -> Dict[str, Any]:
        if isinstance(schedule, dict):
            raw = dict(schedule)
            session_id = raw.get("session_id") or raw.get("sessionId")
        else:
            raw = schedule
            session_id = getattr(raw, "session_id", None)
        return {
            "session_id": self._clean_text(session_id),
            "date": self._serialize_value(self._read_value(raw, "date")),
            "time_range": self._clean_text(self._read_value(raw, "time_range", "timeRange")) or "",
            "hours": self._to_float(self._read_value(raw, "hours")),
            "location": self._clean_text(self._read_value(raw, "location")),
            "status": self._clean_text(self._read_value(raw, "status")) or "pending",
            "started_at": self._serialize_value(self._read_value(raw, "started_at", "startedAt")),
            "checkin_started_at": self._serialize_value(self._read_value(raw, "checkin_started_at", "checkinStartedAt")),
            "checkin_ended_at": self._serialize_value(self._read_value(raw, "checkin_ended_at", "checkinEndedAt")),
            "checkout_started_at": self._serialize_value(self._read_value(raw, "checkout_started_at", "checkoutStartedAt")),
            "checkout_ended_at": self._serialize_value(self._read_value(raw, "checkout_ended_at", "checkoutEndedAt")),
            "ended_at": self._serialize_value(self._read_value(raw, "ended_at", "endedAt")),
            "skipped_at": self._serialize_value(self._read_value(raw, "skipped_at", "skippedAt")),
            "skipped_by": self._to_int(self._read_value(raw, "skipped_by", "skippedBy")),
            "skip_reason": self._clean_text(self._read_value(raw, "skip_reason", "skipReason")),
        }

    def _course_identity(self, course: Dict[str, Any]) -> str:
        return course.get("course_key") or f"{course.get('name') or ''}|{course.get('type') or ''}|{course.get('primary_instructor_id') or ''}"

    def _schedule_identity(self, schedule: Dict[str, Any]) -> str:
        return schedule.get("session_id") or (
            f"{schedule.get('date') or ''}|{schedule.get('time_range') or ''}|"
            f"{schedule.get('location') or ''}|{schedule.get('hours') or 0}"
        )

    def _build_session_label(self, schedule: Dict[str, Any]) -> str:
        return f"{schedule.get('date') or '-'} {schedule.get('time_range') or '-'}".strip()

    def _sorted_courses(self, courses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(courses, key=lambda item: (item.get("course_key") or "", item.get("name") or ""))

    def _sorted_schedules(self, schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            schedules,
            key=lambda item: (
                item.get("date") or "",
                item.get("time_range") or "",
                self._schedule_identity(item),
            ),
        )

    def _format_changed_fields(self, changed_fields: List[str]) -> str:
        if not changed_fields:
            return "内容变更"
        labels = [self.FIELD_LABELS.get(field, field) for field in changed_fields]
        return "、".join(labels)

    @staticmethod
    def _read_value(raw: Any, *keys: str) -> Any:
        for key in keys:
            if isinstance(raw, dict):
                if key in raw:
                    return raw.get(key)
            else:
                if hasattr(raw, key):
                    return getattr(raw, key)
        return None

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return str(value)

    @staticmethod
    def _clean_text(value: Any) -> Optional[str]:
        text = str(value or "").strip()
        return text or None

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        if value in (None, ""):
            return None
        return int(value)

    @staticmethod
    def _to_float(value: Any) -> float:
        if value in (None, ""):
            return 0.0
        return round(float(value), 2)

    def _normalize_id_list(self, values: Iterable[Any]) -> List[int]:
        normalized = []
        seen = set()
        for item in values or []:
            if item in (None, ""):
                continue
            value = int(item)
            if value in seen:
                continue
            seen.add(value)
            normalized.append(value)
        return sorted(normalized)
