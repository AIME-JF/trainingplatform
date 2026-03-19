"""
智慧排课智能体服务
"""
from copy import deepcopy
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session, joinedload

from app.models import AITask, Exam, Training, TrainingCourse
from app.schemas import (
    AIScheduleConflictItem,
    AISchedulePlan,
    AISchedulePlanMetrics,
    AIScheduleTaskConstraintPayload,
    AIScheduleTaskCreateRequest,
    AIScheduleTaskUpdateRequest,
    TrainingUpdate,
)
from app.services.training import TrainingService
from app.services.training_course_change import TrainingCourseChangeService
from app.utils.authz import can_manage_training


class ScheduleAgentService:
    """基于规则的排课建议服务"""

    SLOT_STARTS = ["09:00", "14:00", "19:00"]
    IMMUTABLE_STATUSES = {"checkin_open", "checkin_closed", "checkout_open", "completed", "skipped", "missed"}
    LIFECYCLE_FIELDS = (
        "started_at",
        "checkin_started_at",
        "checkin_ended_at",
        "checkout_started_at",
        "checkout_ended_at",
        "ended_at",
        "skipped_at",
    )

    def __init__(self, db: Session):
        self.db = db
        self.training_service = TrainingService(db)
        self.course_change_service = TrainingCourseChangeService(db)

    def build_task_result(self, data: AIScheduleTaskCreateRequest, current_user_id: int) -> dict:
        training = self._load_training_or_raise(data.training_id)
        self._ensure_manage_permission(training, current_user_id)
        self.course_change_service.ensure_course_keys(training.courses or [])
        self.db.flush()

        template_courses, units, base_conflicts = self._prepare_plan_materials(training, data)
        plans: List[AISchedulePlan] = []
        plan_conflict_map: Dict[str, List[AIScheduleConflictItem]] = {}
        for plan_index in range(3):
            plan_courses = deepcopy(template_courses)
            conflicts = [AIScheduleConflictItem.model_validate(item) for item in base_conflicts]
            conflicts.extend(self._assign_units_to_courses(training, plan_courses, units, data, plan_index))
            metrics = self._build_plan_metrics(plan_courses)
            title = "主方案" if plan_index == 0 else f"备选方案{'AB'[plan_index - 1]}"
            plan_id = f"plan-{plan_index + 1}"
            plan_conflict_map[plan_id] = conflicts
            plans.append(
                AISchedulePlan(
                    plan_id=plan_id,
                    title=title,
                    summary=self._build_plan_summary(training, data, metrics, conflicts),
                    score=self._build_plan_score(metrics, conflicts),
                    courses=plan_courses,
                    metrics=metrics,
                )
            )

        main_plan = plans[0] if plans else None
        alternative_plans = plans[1:] if len(plans) > 1 else []
        conflicts: List[dict] = []
        if main_plan:
            main_plan_payload = main_plan.model_dump(mode="json")
            self._normalize_plan_courses(main_plan_payload.get("courses") or [])
            main_plan_payload["metrics"] = self._build_plan_metrics(main_plan_payload.get("courses") or []).model_dump(mode="json")
            merged_conflicts = self._merge_conflicts(
                plan_conflict_map.get(main_plan.plan_id) or [],
                self._validate_plan_courses(training, main_plan_payload.get("courses") or [], data.constraint_payload),
            )
            main_plan_payload["summary"] = self._build_plan_summary(
                training,
                data,
                AISchedulePlanMetrics.model_validate(main_plan_payload.get("metrics") or {}),
                merged_conflicts,
            )
            main_plan_payload["score"] = self._build_plan_score(
                AISchedulePlanMetrics.model_validate(main_plan_payload.get("metrics") or {}),
                merged_conflicts,
            )
            main_plan = AISchedulePlan.model_validate(main_plan_payload)
            conflicts = [item.model_dump(mode="json") for item in merged_conflicts]
        explanation = self._build_explanation(training, data, main_plan, conflicts)

        return {
            "main_plan": main_plan.model_dump(mode="json") if main_plan else None,
            "alternative_plans": [item.model_dump(mode="json") for item in alternative_plans],
            "conflicts": conflicts,
            "explanation": explanation,
        }

    def validate_task_update(
        self,
        task: AITask,
        data: AIScheduleTaskUpdateRequest,
        current_user_id: int,
    ) -> AIScheduleTaskUpdateRequest:
        training = self._load_training_or_raise(int((task.request_payload or {}).get("training_id") or 0))
        self._ensure_manage_permission(training, current_user_id)
        request_payload = AIScheduleTaskCreateRequest.model_validate(task.request_payload or {})
        main_plan_payload = data.main_plan.model_dump(mode="json")
        self._normalize_plan_courses(main_plan_payload.get("courses") or [])
        conflicts = self._validate_plan_courses(training, main_plan_payload.get("courses") or [], request_payload.constraint_payload)
        if any(item.severity == "error" for item in conflicts):
            raise ValueError("；".join(item.message for item in conflicts[:3]) or "排课方案存在冲突，不能保存")
        return data.model_copy(update={"main_plan": AISchedulePlan.model_validate(main_plan_payload)})

    def confirm_task(self, task: AITask, current_user_id: int) -> None:
        training = self._load_training_or_raise(int((task.request_payload or {}).get("training_id") or 0))
        self._ensure_manage_permission(training, current_user_id)
        main_plan_payload = (task.result_payload or {}).get("main_plan")
        if not main_plan_payload:
            raise ValueError("任务结果中没有可应用的排课方案")

        request_payload = AIScheduleTaskCreateRequest.model_validate(task.request_payload or {})
        main_plan_payload = deepcopy(main_plan_payload)
        self._normalize_plan_courses(main_plan_payload.get("courses") or [])
        main_plan = AISchedulePlan.model_validate(main_plan_payload)
        conflicts = self._validate_plan_courses(training, main_plan_payload.get("courses") or [], request_payload.constraint_payload)
        if any(item.severity == "error" for item in conflicts):
            raise ValueError("当前主方案仍存在硬冲突，请调整后再确认")

        detail = self.training_service.update_training(
            training.id,
            TrainingUpdate(courses=main_plan.courses),
            actor_id=current_user_id,
        )
        if detail is None:
            raise ValueError("回写培训课程失败")

    def _load_training_or_raise(self, training_id: int) -> Training:
        training = self.db.query(Training).options(
            joinedload(Training.courses),
            joinedload(Training.exam_sessions),
        ).filter(Training.id == training_id).first()
        if not training:
            raise ValueError("培训班不存在")
        if not training.start_date or not training.end_date:
            raise ValueError("培训班未配置完整培训周期，无法生成排课建议")
        return training

    def _ensure_manage_permission(self, training: Training, current_user_id: int) -> None:
        if not can_manage_training(self.db, training, current_user_id):
            raise ValueError("当前用户无权为该培训班生成排课方案")

    def _prepare_plan_materials(
        self,
        training: Training,
        data: AIScheduleTaskCreateRequest,
    ) -> tuple[List[dict], List[dict], List[dict]]:
        normalized_courses = self.course_change_service.snapshot_course_entities(training.courses or [])
        original_course_map = {
            (course.course_key or f"course-{course.id}"): course
            for course in (training.courses or [])
        }

        template_courses: List[dict] = []
        units: List[dict] = []
        planning_dates = {item.isoformat() for item in self._resolve_planning_dates(training, data)}
        fixed_course_keys = set(data.constraint_payload.fixed_course_keys or [])

        for course_data in normalized_courses:
            course_key = course_data.get("course_key") or f"course-{uuid4()}"
            original_course = original_course_map.get(course_key)
            template_course = deepcopy(course_data)
            template_course["schedules"] = []
            raw_schedule_map = self._build_raw_schedule_map(original_course)
            existing_schedules = course_data.get("schedules") or []

            for schedule in existing_schedules:
                raw_schedule = raw_schedule_map.get(self._schedule_identity(schedule), schedule)
                if self._is_schedule_locked(course_key, raw_schedule, data, planning_dates, fixed_course_keys):
                    template_course["schedules"].append(deepcopy(schedule))
                    continue
                units.append(self._build_plan_unit(template_course, schedule))

            if not existing_schedules and self._should_schedule_empty_course(data.scope_type):
                for hours in self._split_hours(float(course_data.get("hours") or 0) or 3):
                    units.append(self._build_plan_unit(template_course, None, hours))

            template_courses.append(template_course)

        return template_courses, self._sort_units(units, data.goal), []

    def _should_schedule_empty_course(self, scope_type: str) -> bool:
        return scope_type in {"all", "current_week", "unscheduled"}

    def _build_raw_schedule_map(self, course: Optional[TrainingCourse]) -> Dict[str, dict]:
        raw_map: Dict[str, dict] = {}
        if not course:
            return raw_map
        for item in course.schedules or []:
            raw_map[self._schedule_identity(item)] = item
        return raw_map

    def _is_schedule_locked(
        self,
        course_key: str,
        schedule: dict,
        data: AIScheduleTaskCreateRequest,
        planning_dates: set[str],
        fixed_course_keys: set[str],
    ) -> bool:
        if course_key in fixed_course_keys:
            return True
        if any(schedule.get(field) for field in self.LIFECYCLE_FIELDS):
            return True
        if (schedule.get("status") or "pending") in self.IMMUTABLE_STATUSES:
            return True
        if data.scope_type == "unscheduled":
            return True
        schedule_date = str(schedule.get("date") or "")
        if data.scope_type == "current_week" and schedule_date not in planning_dates:
            return True
        return self._is_past_schedule(schedule)

    def _is_past_schedule(self, schedule: dict) -> bool:
        schedule_date = self._parse_date(schedule.get("date"))
        if not schedule_date:
            return False
        _, end_time = self._parse_time_range(schedule.get("time_range"))
        deadline = datetime.combine(schedule_date, end_time or time(23, 59))
        return datetime.now() > deadline

    def _build_plan_unit(
        self,
        course: dict,
        schedule: Optional[dict],
        fallback_hours: Optional[float] = None,
    ) -> dict:
        minutes = self._resolve_duration_minutes(schedule, fallback_hours or float(course.get("hours") or 0) or 3)
        return {
            "course_key": course.get("course_key"),
            "course_name": course.get("name"),
            "course_type": course.get("type") or "theory",
            "instructor": course.get("instructor"),
            "location": (schedule or {}).get("location") or course.get("location"),
            "primary_instructor_id": course.get("primary_instructor_id"),
            "session_id": (schedule or {}).get("session_id") or f"ai-session-{uuid4()}",
            "hours": round(minutes / 60, 1),
            "minutes": minutes,
            "source_schedule": deepcopy(schedule) if schedule else None,
        }

    def _sort_units(self, units: List[dict], goal: str) -> List[dict]:
        if goal == "practice_first":
            return sorted(units, key=lambda item: (0 if item.get("course_type") == "practice" else 1, -item.get("minutes", 0)))
        if goal == "theory_first":
            return sorted(units, key=lambda item: (0 if item.get("course_type") == "theory" else 1, -item.get("minutes", 0)))
        if goal == "exam_intensive":
            return sorted(
                units,
                key=lambda item: (
                    0 if "考" in str(item.get("course_name") or "") else 1,
                    0 if item.get("course_type") == "theory" else 1,
                    -item.get("minutes", 0),
                ),
            )
        return sorted(units, key=lambda item: (-item.get("minutes", 0), item.get("course_name") or ""))

    def _assign_units_to_courses(
        self,
        training: Training,
        plan_courses: List[dict],
        units: List[dict],
        data: AIScheduleTaskCreateRequest,
        plan_index: int,
    ) -> List[AIScheduleConflictItem]:
        planning_dates = self._resolve_planning_dates(training, data)
        if not planning_dates:
            return [
                AIScheduleConflictItem(
                    severity="error",
                    conflict_type="training_window_missing",
                    message="培训周期内没有可用日期",
                    suggestion="请检查培训开始和结束日期",
                )
            ]

        date_sequence = planning_dates[plan_index:] + planning_dates[:plan_index]
        slot_sequence = self.SLOT_STARTS[plan_index:] + self.SLOT_STARTS[:plan_index]
        course_map = {item.get("course_key"): item for item in plan_courses}
        occupied = self._build_occupied_index(training, plan_courses, data.constraint_payload)
        conflicts: List[AIScheduleConflictItem] = []

        for unit in units:
            placed = False
            for target_date in date_sequence:
                if self._day_hours(occupied, target_date) + unit["hours"] > data.constraint_payload.daily_max_hours + 1e-6:
                    continue
                for slot_start in slot_sequence:
                    slot_range = self._build_slot_range(slot_start, unit["minutes"])
                    if not slot_range:
                        continue
                    start_minutes, end_minutes, time_range = slot_range
                    if self._has_overlap(occupied, target_date, start_minutes, end_minutes):
                        continue

                    schedule_item = deepcopy(unit.get("source_schedule") or {})
                    schedule_item["session_id"] = unit["session_id"]
                    schedule_item["date"] = target_date.isoformat()
                    schedule_item["time_range"] = time_range
                    schedule_item["hours"] = unit["hours"]
                    schedule_item["location"] = unit.get("location")
                    schedule_item["status"] = schedule_item.get("status") or "pending"

                    target_course = course_map.get(unit["course_key"])
                    if not target_course:
                        continue
                    target_course.setdefault("schedules", []).append(schedule_item)
                    self._append_occupied(occupied, target_date, start_minutes, end_minutes, unit)
                    placed = True
                    break
                if placed:
                    break

            if not placed:
                conflicts.append(
                    AIScheduleConflictItem(
                        severity="error",
                        conflict_type="slot_not_found",
                        course_key=unit.get("course_key"),
                        session_id=unit.get("session_id"),
                        message=f"课程“{unit.get('course_name') or '未命名课程'}”未找到可用排课时段",
                        suggestion="调整单日课时、缩小排课范围或释放固定约束后重试",
                    )
                )

        for course in plan_courses:
            course["schedules"] = self._sort_schedules(course.get("schedules") or [])
            course["hours"] = round(sum(self._resolve_schedule_hours(item) for item in course["schedules"]), 1)
        return conflicts

    def _validate_plan_courses(
        self,
        training: Training,
        courses: List[dict],
        constraint_payload: AIScheduleTaskConstraintPayload,
    ) -> List[AIScheduleConflictItem]:
        conflicts: List[AIScheduleConflictItem] = []
        immutable_sessions = self._build_immutable_session_map(training)
        occupied: Dict[str, List[dict]] = {}
        exam_blocks = self._build_exam_blocks(training, constraint_payload)
        global_daily_hours: Dict[str, float] = {}
        course_map = {item.get("course_key"): item for item in courses}
        original_course_map = {
            (course.course_key or f"course-{course.id}"): course
            for course in (training.courses or [])
        }

        for course_key, course in course_map.items():
            planned_total_hours = 0.0
            for schedule in course.get("schedules") or []:
                schedule_date = self._parse_date(schedule.get("date"))
                if not schedule_date:
                    conflicts.append(
                        AIScheduleConflictItem(
                            severity="error",
                            conflict_type="invalid_date",
                            course_key=course_key,
                            session_id=schedule.get("session_id"),
                            message=f"课程“{course.get('name') or '未命名课程'}”存在无效日期",
                            suggestion="请补充合法的课次日期",
                        )
                    )
                    continue
                if schedule_date < training.start_date or schedule_date > training.end_date:
                    conflicts.append(
                        AIScheduleConflictItem(
                            severity="error",
                            conflict_type="out_of_training_window",
                            course_key=course_key,
                            session_id=schedule.get("session_id"),
                            message=f"课程“{course.get('name') or '未命名课程'}”超出培训周期",
                            suggestion="请将课次调整到培训周期内",
                        )
                    )
                start_time, end_time = self._parse_time_range(schedule.get("time_range"))
                if not start_time or not end_time or end_time <= start_time:
                    conflicts.append(
                        AIScheduleConflictItem(
                            severity="error",
                            conflict_type="invalid_time_range",
                            course_key=course_key,
                            session_id=schedule.get("session_id"),
                            message=f"课程“{course.get('name') or '未命名课程'}”时间范围无效",
                            suggestion="请按 HH:MM~HH:MM 填写，且结束时间晚于开始时间",
                        )
                    )
                    continue

                start_minutes = self._time_to_minutes(start_time)
                end_minutes = self._time_to_minutes(end_time)
                schedule_hours = self._resolve_schedule_hours(schedule)
                planned_total_hours += schedule_hours
                global_daily_hours[schedule_date.isoformat()] = global_daily_hours.get(schedule_date.isoformat(), 0) + schedule_hours
                for block in exam_blocks.get(schedule_date.isoformat(), []):
                    if self._interval_overlap(start_minutes, end_minutes, block["start"], block["end"]):
                        conflicts.append(
                            AIScheduleConflictItem(
                                severity="error",
                                conflict_type="exam_conflict",
                                course_key=course_key,
                                session_id=schedule.get("session_id"),
                                message=f"课程“{course.get('name') or '未命名课程'}”与考试时段冲突",
                                suggestion="请避开考试日或调整考试安排",
                            )
                        )
                        break

                if self._has_overlap(occupied, schedule_date, start_minutes, end_minutes):
                    conflicts.append(
                        AIScheduleConflictItem(
                            severity="error",
                            conflict_type="session_overlap",
                            course_key=course_key,
                            session_id=schedule.get("session_id"),
                            message=f"课程“{course.get('name') or '未命名课程'}”与其他课次重叠",
                            suggestion="请错开课次时间",
                        )
                    )
                self._append_occupied(
                    occupied,
                    schedule_date,
                    start_minutes,
                    end_minutes,
                    {"course_key": course_key},
                )

            original_course = original_course_map.get(course_key)
            expected_hours = self._resolve_expected_course_hours(original_course)
            if expected_hours > planned_total_hours + 1e-6:
                conflicts.append(
                    AIScheduleConflictItem(
                        severity="error",
                        conflict_type="course_hours_insufficient",
                        course_key=course_key,
                        message=f"课程“{course.get('name') or '未命名课程'}”当前仅排入 {planned_total_hours:.1f} / {expected_hours:.1f} 课时",
                        suggestion="请补齐缺失课次后再保存或确认",
                    )
                )
            elif planned_total_hours > expected_hours + 1e-6:
                conflicts.append(
                    AIScheduleConflictItem(
                        severity="warning",
                        conflict_type="course_hours_exceeded",
                        course_key=course_key,
                        message=f"课程“{course.get('name') or '未命名课程'}”当前排入 {planned_total_hours:.1f} 课时，高于原计划 {expected_hours:.1f} 课时",
                        suggestion="请确认是否需要额外延长该课程时长",
                    )
                )

        for date_key, hours in global_daily_hours.items():
            if hours > constraint_payload.daily_max_hours + 1e-6:
                conflicts.append(
                    AIScheduleConflictItem(
                        severity="error",
                        conflict_type="daily_hours_exceeded",
                        message=f"{date_key} 单日排课 {hours:.1f} 课时，超过限制",
                        suggestion="请减少当日课次或提高单日最大课时限制",
                    )
                )

        for course_key, sessions in immutable_sessions.items():
            planned_map = {
                item.get("session_id"): item
                for item in (course_map.get(course_key, {}).get("schedules") or [])
                if item.get("session_id")
            }
            for session_id, immutable_schedule in sessions.items():
                planned_schedule = planned_map.get(session_id)
                if not planned_schedule:
                    conflicts.append(
                        AIScheduleConflictItem(
                            severity="error",
                            conflict_type="immutable_session_missing",
                            course_key=course_key,
                            session_id=session_id,
                            message="已开始或已完成课次不能删除",
                            suggestion="请保留原课次",
                        )
                    )
                    continue
                if (
                    str(planned_schedule.get("date")) != str(immutable_schedule.get("date"))
                    or str(planned_schedule.get("time_range")) != str(immutable_schedule.get("time_range"))
                ):
                    conflicts.append(
                        AIScheduleConflictItem(
                            severity="error",
                            conflict_type="immutable_session_changed",
                            course_key=course_key,
                            session_id=session_id,
                            message="已开始或已完成课次不能改动时间",
                            suggestion="请恢复原课次时间",
                        )
                    )

        return conflicts

    def _merge_conflicts(self, *conflict_groups: List[AIScheduleConflictItem]) -> List[AIScheduleConflictItem]:
        merged: List[AIScheduleConflictItem] = []
        seen = set()
        for group in conflict_groups:
            for item in group or []:
                conflict = AIScheduleConflictItem.model_validate(item)
                key = (
                    conflict.conflict_type,
                    conflict.course_key or "",
                    conflict.session_id or "",
                    conflict.message,
                )
                if key in seen:
                    continue
                seen.add(key)
                merged.append(conflict)
        return merged

    def _build_immutable_session_map(self, training: Training) -> Dict[str, Dict[str, dict]]:
        immutable_map: Dict[str, Dict[str, dict]] = {}
        for course in training.courses or []:
            course_key = course.course_key or f"course-{course.id}"
            for schedule in course.schedules or []:
                session_id = str(schedule.get("session_id") or "")
                if not session_id:
                    continue
                if any(schedule.get(field) for field in self.LIFECYCLE_FIELDS) or (schedule.get("status") or "pending") in self.IMMUTABLE_STATUSES:
                    immutable_map.setdefault(course_key, {})[session_id] = deepcopy(schedule)
        return immutable_map

    def _build_occupied_index(
        self,
        training: Training,
        plan_courses: List[dict],
        constraint_payload: AIScheduleTaskConstraintPayload,
    ) -> Dict[str, List[dict]]:
        occupied: Dict[str, List[dict]] = {}
        for course in plan_courses:
            for schedule in course.get("schedules") or []:
                schedule_date = self._parse_date(schedule.get("date"))
                start_time, end_time = self._parse_time_range(schedule.get("time_range"))
                if not schedule_date or not start_time or not end_time:
                    continue
                self._append_occupied(
                    occupied,
                    schedule_date,
                    self._time_to_minutes(start_time),
                    self._time_to_minutes(end_time),
                    {"course_key": course.get("course_key")},
                )
        for date_key, blocks in self._build_exam_blocks(training, constraint_payload).items():
            occupied.setdefault(date_key, []).extend(blocks)
        for slot in (constraint_payload.instructor_unavailable_slots or []):
            self._append_unavailable_slot(occupied, slot)
        for slot in (constraint_payload.location_unavailable_slots or []):
            self._append_unavailable_slot(occupied, slot)
        return occupied

    def _build_exam_blocks(
        self,
        training: Training,
        constraint_payload: AIScheduleTaskConstraintPayload,
    ) -> Dict[str, List[dict]]:
        result: Dict[str, List[dict]] = {}
        for exam in training.exam_sessions or []:
            if not isinstance(exam, Exam) or not exam.start_time:
                continue
            start_time = exam.start_time
            end_time = exam.end_time or (start_time + timedelta(hours=2))
            date_key = start_time.date().isoformat()
            if constraint_payload.avoid_exam_days:
                result.setdefault(date_key, []).append({"start": 0, "end": 24 * 60})
                continue
            result.setdefault(date_key, []).append({
                "start": self._time_to_minutes(start_time.time()),
                "end": self._time_to_minutes(end_time.time()),
            })
        return result

    def _append_unavailable_slot(self, occupied: Dict[str, List[dict]], slot: Any) -> None:
        slot_date = self._parse_date(getattr(slot, "date", None) or slot.get("date"))
        start_time, end_time = self._parse_time_range(getattr(slot, "time_range", None) or slot.get("time_range"))
        if not slot_date or not start_time or not end_time:
            return
        self._append_occupied(
            occupied,
            slot_date,
            self._time_to_minutes(start_time),
            self._time_to_minutes(end_time),
            {"block_type": "manual_unavailable"},
        )

    def _resolve_planning_dates(self, training: Training, data: AIScheduleTaskCreateRequest) -> List[date]:
        start_date = training.start_date
        end_date = training.end_date
        if data.scope_type == "current_week":
            start_date = self._resolve_scope_week_start(training, data.scope_start_date)
            end_date = start_date + timedelta(days=6)
        planning_dates: List[date] = []
        current = start_date
        while current <= end_date:
            if training.start_date <= current <= training.end_date:
                planning_dates.append(current)
            current += timedelta(days=1)
        return planning_dates

    def _resolve_scope_week_start(self, training: Training, scope_start_date: Optional[date]) -> date:
        current_week_start = self._normalize_week_start(datetime.now().date())
        min_week_start = self._normalize_week_start(training.start_date)
        max_week_start = self._normalize_week_start(training.end_date)
        default_week_start = min(max(current_week_start, min_week_start), max_week_start)
        if scope_start_date is None:
            return default_week_start

        requested_week_start = self._normalize_week_start(scope_start_date)
        if requested_week_start < min_week_start or requested_week_start > max_week_start:
            raise ValueError("所选指定周不在培训周期内，请选择培训周期内最近的有效周")
        return requested_week_start

    def _normalize_week_start(self, target_date: date) -> date:
        return target_date - timedelta(days=target_date.weekday())

    def _build_plan_summary(
        self,
        training: Training,
        data: AIScheduleTaskCreateRequest,
        metrics: AISchedulePlanMetrics,
        conflicts: List[AIScheduleConflictItem],
    ) -> str:
        goal_labels = {
            "balanced": "均衡排课",
            "practice_first": "优先实战",
            "theory_first": "优先理论",
            "exam_intensive": "考前强化",
        }
        return (
            f"针对培训班“{training.name}”按“{goal_labels.get(data.goal, data.goal)}”生成，"
            f"共覆盖 {metrics.total_sessions} 个课次、{metrics.covered_days} 天、{metrics.total_hours:.1f} 课时，"
            f"当前冲突 {len(conflicts)} 项。"
        )

    def _build_explanation(
        self,
        training: Training,
        data: AIScheduleTaskCreateRequest,
        main_plan: Optional[AISchedulePlan],
        conflicts: List[dict],
    ) -> str:
        if not main_plan:
            return "未生成有效排课方案。"
        hard_conflicts = sum(1 for item in conflicts if item.get("severity") == "error")
        return (
            f"本次排课基于培训周期、现有不可改课次、考试时段与单日最大课时进行约束生成。"
            f"主方案为 {main_plan.metrics.total_sessions} 个课次、{main_plan.metrics.total_hours:.1f} 课时，"
            f"理论课 {main_plan.metrics.theory_hours:.1f} 课时，实操课 {main_plan.metrics.practice_hours:.1f} 课时。"
            f"当前硬冲突 {hard_conflicts} 项，范围为 {data.scope_type}。"
        )

    def _build_plan_score(self, metrics: AISchedulePlanMetrics, conflicts: List[AIScheduleConflictItem]) -> float:
        error_count = sum(1 for item in conflicts if item.severity == "error")
        warning_count = sum(1 for item in conflicts if item.severity == "warning")
        score = 100 - error_count * 25 - warning_count * 8 - max(metrics.instructor_load_index - 1.5, 0) * 10
        return max(0, round(score, 1))

    def _build_plan_metrics(self, courses: List[dict]) -> AISchedulePlanMetrics:
        total_sessions = 0
        total_hours = 0.0
        theory_hours = 0.0
        practice_hours = 0.0
        covered_days = set()
        instructor_day_hours: Dict[str, float] = {}

        for course in courses:
            course_type = course.get("type") or "theory"
            instructor_key = str(course.get("primary_instructor_id") or course.get("instructor") or "unknown")
            for schedule in course.get("schedules") or []:
                total_sessions += 1
                hours = self._resolve_schedule_hours(schedule)
                total_hours += hours
                if course_type == "practice":
                    practice_hours += hours
                else:
                    theory_hours += hours
                if schedule.get("date"):
                    covered_days.add(str(schedule.get("date")))
                    key = f"{instructor_key}|{schedule.get('date')}"
                    instructor_day_hours[key] = instructor_day_hours.get(key, 0) + hours

        max_instructor_hours = max(instructor_day_hours.values()) if instructor_day_hours else 0
        average_hours = (sum(instructor_day_hours.values()) / len(instructor_day_hours)) if instructor_day_hours else 0
        overload_index = round((max_instructor_hours / average_hours), 2) if average_hours else 0
        return AISchedulePlanMetrics(
            total_sessions=total_sessions,
            total_hours=round(total_hours, 1),
            theory_hours=round(theory_hours, 1),
            practice_hours=round(practice_hours, 1),
            covered_days=len(covered_days),
            instructor_load_index=overload_index,
        )

    def _resolve_expected_course_hours(self, course: Optional[TrainingCourse]) -> float:
        if not course:
            return 0.0
        declared_hours = float(getattr(course, "hours", 0) or 0)
        scheduled_hours = round(sum(self._resolve_schedule_hours(item or {}) for item in (course.schedules or [])), 1)
        return max(declared_hours, scheduled_hours)

    def _normalize_plan_courses(self, courses: List[dict]) -> List[dict]:
        for course in courses or []:
            schedules = course.get("schedules") or []
            for schedule in schedules:
                schedule["hours"] = self._resolve_schedule_hours(schedule)
            course["hours"] = round(sum(self._resolve_schedule_hours(item) for item in schedules), 1)
        return courses

    def _resolve_schedule_hours(self, schedule: dict) -> float:
        start_time, end_time = self._parse_time_range(schedule.get("time_range"))
        if start_time and end_time and end_time > start_time:
            return round((self._time_to_minutes(end_time) - self._time_to_minutes(start_time)) / 60, 1)
        return round(float(schedule.get("hours") or 0), 1)

    def _resolve_duration_minutes(self, schedule: Optional[dict], fallback_hours: float) -> int:
        if schedule:
            start_time, end_time = self._parse_time_range(schedule.get("time_range"))
            if start_time and end_time and end_time > start_time:
                return self._time_to_minutes(end_time) - self._time_to_minutes(start_time)
            hours = float(schedule.get("hours") or 0)
            if hours > 0:
                return int(round(hours * 60))
        return int(round(max(fallback_hours, 1) * 60))

    def _build_slot_range(self, start_text: str, duration_minutes: int) -> Optional[tuple[int, int, str]]:
        start_value = self._parse_clock(start_text)
        if start_value is None:
            return None
        end_value = start_value + duration_minutes
        if end_value > (21 * 60 + 30):
            return None
        return start_value, end_value, f"{self._format_clock(start_value)}~{self._format_clock(end_value)}"

    def _append_occupied(
        self,
        occupied: Dict[str, List[dict]],
        target_date: date,
        start_minutes: int,
        end_minutes: int,
        meta: dict,
    ) -> None:
        occupied.setdefault(target_date.isoformat(), []).append({
            "start": start_minutes,
            "end": end_minutes,
            **meta,
        })

    def _day_hours(self, occupied: Dict[str, List[dict]], target_date: date) -> float:
        return round(sum((item["end"] - item["start"]) / 60 for item in occupied.get(target_date.isoformat(), []) if item.get("course_key")), 1)

    def _has_overlap(
        self,
        occupied: Dict[str, List[dict]],
        target_date: date,
        start_minutes: int,
        end_minutes: int,
    ) -> bool:
        for item in occupied.get(target_date.isoformat(), []):
            if self._interval_overlap(start_minutes, end_minutes, item["start"], item["end"]):
                return True
        return False

    def _interval_overlap(self, left_start: int, left_end: int, right_start: int, right_end: int) -> bool:
        return max(left_start, right_start) < min(left_end, right_end)

    def _sort_schedules(self, schedules: List[dict]) -> List[dict]:
        return sorted(
            schedules,
            key=lambda item: (
                str(item.get("date") or ""),
                str(item.get("time_range") or ""),
                str(item.get("session_id") or ""),
            ),
        )

    def _schedule_identity(self, schedule: dict) -> str:
        session_id = str(schedule.get("session_id") or "")
        if session_id:
            return session_id
        return (
            f"{schedule.get('date') or ''}|{schedule.get('time_range') or ''}|"
            f"{schedule.get('location') or ''}|{schedule.get('hours') or 0}"
        )

    def _split_hours(self, hours: float) -> List[float]:
        remaining = max(hours, 0)
        if remaining <= 0:
            return [3]
        result: List[float] = []
        while remaining > 3:
            result.append(3)
            remaining -= 3
        result.append(round(max(remaining, 1), 1))
        return result

    def _parse_date(self, value: Any) -> Optional[date]:
        if isinstance(value, date):
            return value
        if not value:
            return None
        try:
            return datetime.strptime(str(value), "%Y-%m-%d").date()
        except ValueError:
            return None

    def _parse_time_range(self, value: Any) -> tuple[Optional[time], Optional[time]]:
        if not value or "~" not in str(value):
            return None, None
        start_text, end_text = [item.strip() for item in str(value).split("~", 1)]
        try:
            return datetime.strptime(start_text, "%H:%M").time(), datetime.strptime(end_text, "%H:%M").time()
        except ValueError:
            return None, None

    def _parse_clock(self, value: str) -> Optional[int]:
        try:
            parsed = datetime.strptime(value, "%H:%M").time()
        except ValueError:
            return None
        return self._time_to_minutes(parsed)

    def _time_to_minutes(self, value: time) -> int:
        return value.hour * 60 + value.minute

    def _format_clock(self, minutes: int) -> str:
        return f"{minutes // 60:02d}:{minutes % 60:02d}"
