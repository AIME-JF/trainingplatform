"""
智慧排课智能体服务
"""
from copy import deepcopy
from datetime import date, datetime, time, timedelta
import math
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
from app.services.training_schedule_rule import TrainingScheduleRuleService
from app.utils.authz import can_manage_training


class ScheduleAgentService:
    """基于规则的排课建议服务"""

    SLOT_STARTS = ["09:00", "14:00", "19:00"]
    DEFAULT_SESSION_HOURS = 3.0
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
        rule_config = self._resolve_rule_config(training, data)

        template_courses, units, base_conflicts = self._prepare_plan_materials(training, data, rule_config)
        plans: List[AISchedulePlan] = []
        plan_conflict_map: Dict[str, List[AIScheduleConflictItem]] = {}
        for plan_index in range(3):
            plan_courses = deepcopy(template_courses)
            conflicts = [AIScheduleConflictItem.model_validate(item) for item in base_conflicts]
            conflicts.extend(self._assign_units_to_courses(training, plan_courses, units, data, plan_index, rule_config))
            metrics = self._build_plan_metrics(plan_courses, rule_config)
            title = "主方案" if plan_index == 0 else f"备选方案{'AB'[plan_index - 1]}"
            plan_id = f"plan-{plan_index + 1}"
            plan_conflict_map[plan_id] = conflicts
            plans.append(
                AISchedulePlan(
                    plan_id=plan_id,
                    title=title,
                    summary=self._build_plan_summary(training, data, metrics, conflicts, rule_config),
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
            self._normalize_plan_courses(main_plan_payload.get("courses") or [], rule_config)
            main_plan_payload["metrics"] = self._build_plan_metrics(main_plan_payload.get("courses") or [], rule_config).model_dump(mode="json")
            merged_conflicts = self._merge_conflicts(
                plan_conflict_map.get(main_plan.plan_id) or [],
                self._validate_plan_courses(
                    training,
                    main_plan_payload.get("courses") or [],
                    data.constraint_payload,
                    data.overwrite_existing_schedule,
                    data.planning_mode,
                    rule_config,
                ),
            )
            main_plan_payload["summary"] = self._build_plan_summary(
                training,
                data,
                AISchedulePlanMetrics.model_validate(main_plan_payload.get("metrics") or {}),
                merged_conflicts,
                rule_config,
            )
            main_plan_payload["score"] = self._build_plan_score(
                AISchedulePlanMetrics.model_validate(main_plan_payload.get("metrics") or {}),
                merged_conflicts,
            )
            main_plan = AISchedulePlan.model_validate(main_plan_payload)
            conflicts = [item.model_dump(mode="json") for item in merged_conflicts]
        explanation = self._build_explanation(training, data, main_plan, conflicts, rule_config)

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
        rule_config = self._resolve_rule_config(training, request_payload)
        main_plan_payload = data.main_plan.model_dump(mode="json")
        self._normalize_plan_courses(main_plan_payload.get("courses") or [], rule_config)
        conflicts = self._validate_plan_courses(
            training,
            main_plan_payload.get("courses") or [],
            request_payload.constraint_payload,
            request_payload.overwrite_existing_schedule,
            request_payload.planning_mode,
            rule_config,
        )
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
        rule_config = self._resolve_rule_config(training, request_payload)
        main_plan_payload = deepcopy(main_plan_payload)
        self._normalize_plan_courses(main_plan_payload.get("courses") or [], rule_config)
        main_plan = AISchedulePlan.model_validate(main_plan_payload)
        conflicts = self._validate_plan_courses(
            training,
            main_plan_payload.get("courses") or [],
            request_payload.constraint_payload,
            request_payload.overwrite_existing_schedule,
            request_payload.planning_mode,
            rule_config,
        )
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
        rule_config: dict[str, Any],
    ) -> tuple[List[dict], List[dict], List[dict]]:
        normalized_courses = self.course_change_service.snapshot_course_entities(training.courses or [])
        original_course_map = {
            (course.course_key or f"course-{course.id}"): course
            for course in (training.courses or [])
        }

        template_courses: List[dict] = []
        units: List[dict] = []
        planning_date_list = self._resolve_planning_dates(training, data)
        planning_dates = {item.isoformat() for item in planning_date_list}
        fixed_course_keys = set(data.constraint_payload.fixed_course_keys or [])
        planning_mode = self._resolve_planning_mode(data.planning_mode)
        if planning_mode == "by_hours":
            self._ensure_by_hours_courses_ready(normalized_courses, data.scope_type)

        for course_data in normalized_courses:
            course_key = course_data.get("course_key") or f"course-{uuid4()}"
            original_course = original_course_map.get(course_key)
            template_course = deepcopy(course_data)
            template_course["schedules"] = []
            raw_schedule_map = self._build_raw_schedule_map(original_course)
            existing_schedules = course_data.get("schedules") or []
            existing_scheduled_hours = 0.0

            for schedule in existing_schedules:
                existing_scheduled_hours += self._resolve_schedule_hours(schedule, rule_config)
                raw_schedule = raw_schedule_map.get(self._schedule_identity(schedule), schedule)
                if self._is_schedule_locked(course_key, raw_schedule, data, planning_dates, fixed_course_keys):
                    template_course["schedules"].append(deepcopy(schedule))
                    continue
                units.append(self._build_plan_unit(template_course, schedule, rule_config=rule_config))

            if not existing_schedules and self._should_schedule_empty_course(data.scope_type):
                units.extend(
                    self._build_empty_course_units(
                        template_course,
                        planning_date_list,
                        planning_mode,
                        rule_config,
                        training,
                        data.constraint_payload,
                    ),
                )
            elif existing_schedules and not data.overwrite_existing_schedule:
                units.extend(
                    self._build_remaining_course_units(
                        template_course,
                        existing_scheduled_hours,
                        planning_date_list,
                        planning_mode,
                        rule_config,
                    )
                )

            template_courses.append(template_course)

        return template_courses, self._sort_units(units, data.goal), []

    def _should_schedule_empty_course(self, scope_type: str) -> bool:
        return scope_type in {"all", "current_week", "unscheduled"}

    def _build_empty_course_units(
        self,
        course: dict,
        planning_dates: List[date],
        planning_mode: str,
        rule_config: dict[str, Any],
        training: Training,
        constraint_payload: AIScheduleTaskConstraintPayload,
    ) -> List[dict]:
        effective_mode = self._resolve_course_generation_mode(course, planning_mode)
        declared_hours = self._normalize_course_hours(course.get("hours"))
        if effective_mode == "by_hours":
            return [
                self._build_plan_unit(course, None, rule_config=rule_config, fallback_hours=hours)
                for hours in self._split_hours(declared_hours, rule_config)
            ]

        target_dates = self._resolve_fill_target_dates(planning_dates, effective_mode)
        target_dates = self._filter_fill_target_dates_by_availability(
            course,
            target_dates,
            training,
            constraint_payload,
            rule_config,
        )
        default_fill_units = self._resolve_default_fill_units(rule_config)
        return [
            self._build_plan_unit(
                course,
                None,
                fallback_hours=default_fill_units,
                candidate_dates=[target_date],
                rule_config=rule_config,
            )
            for target_date in target_dates
        ]

    def _build_remaining_course_units(
        self,
        course: dict,
        existing_scheduled_hours: float,
        planning_dates: List[date],
        planning_mode: str,
        rule_config: dict[str, Any],
    ) -> List[dict]:
        effective_mode = self._resolve_course_generation_mode(course, planning_mode)
        declared_hours = self._normalize_course_hours(course.get("hours"))
        remaining_hours = round(max(declared_hours - existing_scheduled_hours, 0), 1)
        if remaining_hours <= 0 or effective_mode != "by_hours":
            return []
        return [
            self._build_plan_unit(course, None, rule_config=rule_config, fallback_hours=hours)
            for hours in self._split_hours(remaining_hours, rule_config)
        ]

    def _ensure_by_hours_courses_ready(self, courses: List[dict], scope_type: str) -> None:
        if not self._should_schedule_empty_course(scope_type):
            return
        missing_hours_courses = [
            f"“{course.get('name') or '未命名课程'}”"
            for course in (courses or [])
            if not (course.get("schedules") or [])
            and self._normalize_course_hours(course.get("hours")) <= 0
        ]
        if not missing_hours_courses:
            return
        preview = "、".join(missing_hours_courses[:3])
        suffix = f" 等 {len(missing_hours_courses)} 门课程" if len(missing_hours_courses) > 3 else ""
        raise ValueError(f"当前排课方式为“按课时排”，以下课程未设置计划课时：{preview}{suffix}。请先补充计划课时或改用排满模式")

    def _resolve_course_generation_mode(self, course: dict, planning_mode: str) -> str:
        mode = self._resolve_planning_mode(planning_mode)
        if mode != "auto":
            return mode
        return "by_hours" if self._normalize_course_hours(course.get("hours")) > 0 else "fill_workdays"

    def _resolve_fill_target_dates(self, planning_dates: List[date], planning_mode: str) -> List[date]:
        if planning_mode == "fill_all_days":
            return list(planning_dates)
        return [item for item in planning_dates if self._is_workday(item)] or list(planning_dates)

    def _filter_fill_target_dates_by_availability(
        self,
        course: dict,
        target_dates: List[date],
        training: Training,
        constraint_payload: AIScheduleTaskConstraintPayload,
        rule_config: dict[str, Any],
    ) -> List[date]:
        if not target_dates:
            return []

        slot_candidates = self._build_slot_candidates(
            rule_config,
            self._resolve_default_fill_units(rule_config),
            0,
        )
        if not slot_candidates:
            return list(target_dates)

        occupied: Dict[str, List[dict]] = {}
        for date_key, blocks in self._build_exam_blocks(training, constraint_payload).items():
            occupied.setdefault(date_key, []).extend(blocks)
        for slot in (constraint_payload.blocked_time_slots or []):
            self._append_unavailable_slot(occupied, slot, scope="global")
        for slot in (constraint_payload.instructor_unavailable_slots or []):
            self._append_unavailable_slot(occupied, slot, scope="instructor")
        for slot in (constraint_payload.location_unavailable_slots or []):
            self._append_unavailable_slot(occupied, slot, scope="location")

        unit_context = {
            "course_type": course.get("type") or "theory",
            "instructor": course.get("instructor"),
            "location": course.get("location"),
        }
        available_dates: List[date] = []
        for target_date in target_dates:
            if any(
                not self._has_overlap(occupied, target_date, start_minutes, end_minutes, unit_context)
                for start_minutes, end_minutes, _ in slot_candidates
            ):
                available_dates.append(target_date)

        return available_dates or list(target_dates)

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
        if not data.overwrite_existing_schedule:
            return True
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
        candidate_dates: Optional[List[date]] = None,
        rule_config: Optional[dict[str, Any]] = None,
    ) -> dict:
        minutes = self._resolve_duration_minutes(
            schedule,
            fallback_hours or float(course.get("hours") or 0) or self._resolve_default_fill_units(rule_config or {}),
            rule_config,
        )
        unit_count = self._resolve_schedule_hours(schedule or {"hours": fallback_hours}, rule_config)
        return {
            "course_key": course.get("course_key"),
            "course_name": course.get("name"),
            "course_type": course.get("type") or "theory",
            "instructor": course.get("instructor"),
            "location": (schedule or {}).get("location") or course.get("location"),
            "primary_instructor_id": course.get("primary_instructor_id"),
            "session_id": (schedule or {}).get("session_id") or f"ai-session-{uuid4()}",
            "hours": unit_count,
            "minutes": minutes,
            "candidate_dates": [item.isoformat() for item in (candidate_dates or [])],
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
        rule_config: dict[str, Any],
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
        course_map = {item.get("course_key"): item for item in plan_courses}
        occupied = self._build_occupied_index(training, plan_courses, data.constraint_payload, rule_config)
        conflicts: List[AIScheduleConflictItem] = []

        for unit in units:
            placed = False
            preferred_dates = self._resolve_exam_focus_dates_for_unit(training, unit, data.constraint_payload, date_sequence)
            for target_date in self._resolve_unit_candidate_dates(unit, date_sequence, preferred_dates):
                if self._day_hours(occupied, target_date) + unit["hours"] > data.constraint_payload.daily_max_hours + 1e-6:
                    continue
                slot_candidates = self._build_slot_candidates(rule_config, unit["hours"], plan_index)
                slot_candidates = self._apply_course_type_time_preferences(
                    slot_candidates,
                    target_date,
                    unit,
                    data.constraint_payload,
                )
                for start_minutes, end_minutes, time_range in slot_candidates:
                    if self._has_overlap(occupied, target_date, start_minutes, end_minutes, unit):
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
                    self._append_occupied(occupied, target_date, start_minutes, end_minutes, {"course_key": unit.get("course_key"), "unit_count": unit["hours"]})
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
            course["hours"] = self._normalize_course_hours(course.get("hours"))
        return conflicts

    def _validate_plan_courses(
        self,
        training: Training,
        courses: List[dict],
        constraint_payload: AIScheduleTaskConstraintPayload,
        overwrite_existing_schedule: bool,
        planning_mode: str = "auto",
        rule_config: Optional[dict[str, Any]] = None,
    ) -> List[AIScheduleConflictItem]:
        conflicts: List[AIScheduleConflictItem] = []
        immutable_sessions = self._build_immutable_session_map(training)
        occupied: Dict[str, List[dict]] = {}
        exam_blocks = self._build_exam_blocks(training, constraint_payload)
        global_daily_hours: Dict[str, float] = {}
        effective_planning_mode = self._resolve_planning_mode(planning_mode)
        course_map = {item.get("course_key"): item for item in courses}
        original_course_map = {
            (course.course_key or f"course-{course.id}"): course
            for course in (training.courses or [])
        }
        for slot in (constraint_payload.blocked_time_slots or []):
            self._append_unavailable_slot(occupied, slot, scope="global")
        for slot in (constraint_payload.instructor_unavailable_slots or []):
            self._append_unavailable_slot(occupied, slot, scope="instructor")
        for slot in (constraint_payload.location_unavailable_slots or []):
            self._append_unavailable_slot(occupied, slot, scope="location")

        if not overwrite_existing_schedule:
            conflicts.extend(self._validate_existing_schedules_preserved(training, course_map))

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
                schedule_hours = self._resolve_schedule_hours(schedule, rule_config)
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

                preference_violation = self._build_course_type_preference_conflict(
                    schedule_date,
                    start_minutes,
                    end_minutes,
                    course.get("type") or "theory",
                    course_key,
                    schedule.get("session_id"),
                    constraint_payload,
                )
                if preference_violation:
                    conflicts.append(preference_violation)

                if self._has_overlap(
                    occupied,
                    schedule_date,
                    start_minutes,
                    end_minutes,
                    {
                        "course_type": course.get("type") or "theory",
                        "instructor": course.get("instructor"),
                        "location": schedule.get("location") or course.get("location"),
                    },
                ):
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

            if self._should_validate_course_hours(effective_planning_mode):
                original_course = original_course_map.get(course_key)
                expected_hours = self._resolve_expected_course_hours(original_course, rule_config)
                if expected_hours > 0 and expected_hours > planned_total_hours + 1e-6:
                    conflicts.append(
                        AIScheduleConflictItem(
                            severity="error",
                            conflict_type="course_hours_insufficient",
                            course_key=course_key,
                            message=f"课程“{course.get('name') or '未命名课程'}”当前仅排入 {planned_total_hours:.1f} / {expected_hours:.1f} 课时",
                            suggestion="请补齐缺失课次后再保存或确认",
                        )
                    )
                elif expected_hours > 0 and planned_total_hours > expected_hours + 1e-6:
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

    def _validate_existing_schedules_preserved(
        self,
        training: Training,
        planned_course_map: Dict[str, dict],
    ) -> List[AIScheduleConflictItem]:
        conflicts: List[AIScheduleConflictItem] = []
        for course in training.courses or []:
            course_key = course.course_key or f"course-{course.id}"
            planned_course = planned_course_map.get(course_key) or {}
            planned_schedule_map = {
                self._schedule_identity(item): item
                for item in (planned_course.get("schedules") or [])
            }
            for schedule in course.schedules or []:
                identity = self._schedule_identity(schedule)
                planned_schedule = planned_schedule_map.get(identity)
                if not planned_schedule:
                    conflicts.append(
                        AIScheduleConflictItem(
                            severity="error",
                            conflict_type="existing_session_removed",
                            course_key=course_key,
                            session_id=schedule.get("session_id"),
                            message=f"课程“{course.name or '未命名课程'}”的已有课次被删除或替换",
                            suggestion="关闭覆盖当前课表时，必须保留现有课次",
                        )
                    )
                    continue
                if (
                    str(planned_schedule.get("date")) != str(schedule.get("date"))
                    or str(planned_schedule.get("time_range")) != str(schedule.get("time_range"))
                    or str(planned_schedule.get("location") or "") != str(schedule.get("location") or "")
                ):
                    conflicts.append(
                        AIScheduleConflictItem(
                            severity="error",
                            conflict_type="existing_session_changed",
                            course_key=course_key,
                            session_id=schedule.get("session_id"),
                            message=f"课程“{course.name or '未命名课程'}”的已有课次被改动",
                            suggestion="关闭覆盖当前课表时，已有课次只能保留，不能直接改动",
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
        rule_config: Optional[dict[str, Any]] = None,
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
                    {"course_key": course.get("course_key"), "unit_count": self._resolve_schedule_hours(schedule, rule_config)},
                )
        for date_key, blocks in self._build_exam_blocks(training, constraint_payload).items():
            occupied.setdefault(date_key, []).extend(blocks)
        for slot in (constraint_payload.blocked_time_slots or []):
            self._append_unavailable_slot(occupied, slot, scope="global")
        for slot in (constraint_payload.instructor_unavailable_slots or []):
            self._append_unavailable_slot(occupied, slot, scope="instructor")
        for slot in (constraint_payload.location_unavailable_slots or []):
            self._append_unavailable_slot(occupied, slot, scope="location")
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

    def _append_unavailable_slot(self, occupied: Dict[str, List[dict]], slot: Any, scope: str = "global") -> None:
        slot_date = self._parse_date(getattr(slot, "date", None) or slot.get("date"))
        start_time, end_time = self._parse_time_range(getattr(slot, "time_range", None) or slot.get("time_range"))
        if not slot_date or not start_time or not end_time:
            return
        self._append_occupied(
            occupied,
            slot_date,
            self._time_to_minutes(start_time),
            self._time_to_minutes(end_time),
            {
                "block_type": f"{scope}_unavailable",
                "label": getattr(slot, "label", None) or slot.get("label"),
            },
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
        rule_config: dict[str, Any],
    ) -> str:
        goal_labels = {
            "balanced": "均衡排课",
            "practice_first": "优先实战",
            "theory_first": "优先理论",
            "exam_intensive": "考前强化",
        }
        planning_mode_label = self.PLANNING_MODE_LABELS.get(
            self._resolve_planning_mode(data.planning_mode),
            self.PLANNING_MODE_LABELS["auto"],
        )
        return (
            f"针对培训班“{training.name}”按“{goal_labels.get(data.goal, data.goal)}”生成，"
            f"排课方式为“{planning_mode_label}”，"
            f"采用 {rule_config.get('lesson_unit_minutes')} 分钟/课时、课间 {rule_config.get('break_minutes')} 分钟规则，"
            f"共覆盖 {metrics.total_sessions} 个课次、{metrics.covered_days} 天、{metrics.total_hours:.1f} 课时，"
            f"当前冲突 {len(conflicts)} 项。"
        )

    def _build_explanation(
        self,
        training: Training,
        data: AIScheduleTaskCreateRequest,
        main_plan: Optional[AISchedulePlan],
        conflicts: List[dict],
        rule_config: dict[str, Any],
    ) -> str:
        if not main_plan:
            return "未生成有效排课方案。"
        hard_conflicts = sum(1 for item in conflicts if item.get("severity") == "error")
        planning_mode_label = self.PLANNING_MODE_LABELS.get(
            self._resolve_planning_mode(data.planning_mode),
            self.PLANNING_MODE_LABELS["auto"],
        )
        return (
            f"本次排课基于培训周期、现有不可改课次、考试时段与单日最大课时进行约束生成。"
            f"当前排课方式为“{planning_mode_label}”，单课时 {rule_config.get('lesson_unit_minutes')} 分钟，"
            f"课间休息 {rule_config.get('break_minutes')} 分钟，单节最多 {rule_config.get('max_units_per_session')} 课时。"
            f"主方案为 {main_plan.metrics.total_sessions} 个课次、{main_plan.metrics.total_hours:.1f} 课时，"
            f"理论课 {main_plan.metrics.theory_hours:.1f} 课时，实操课 {main_plan.metrics.practice_hours:.1f} 课时。"
            f"当前硬冲突 {hard_conflicts} 项，范围为 {data.scope_type}。"
        )

    def _build_plan_score(self, metrics: AISchedulePlanMetrics, conflicts: List[AIScheduleConflictItem]) -> float:
        error_count = sum(1 for item in conflicts if item.severity == "error")
        warning_count = sum(1 for item in conflicts if item.severity == "warning")
        score = 100 - error_count * 25 - warning_count * 8 - max(metrics.instructor_load_index - 1.5, 0) * 10
        return max(0, round(score, 1))

    def _build_plan_metrics(self, courses: List[dict], rule_config: Optional[dict[str, Any]] = None) -> AISchedulePlanMetrics:
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
                hours = self._resolve_schedule_hours(schedule, rule_config)
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

    def _resolve_expected_course_hours(self, course: Optional[TrainingCourse], rule_config: Optional[dict[str, Any]] = None) -> float:
        if not course:
            return 0.0
        declared_hours = self._normalize_course_hours(getattr(course, "hours", 0))
        if declared_hours <= 0:
            return 0.0
        scheduled_hours = round(sum(self._resolve_schedule_hours(item or {}, rule_config) for item in (course.schedules or [])), 1)
        return max(declared_hours, scheduled_hours)

    def _normalize_plan_courses(self, courses: List[dict], rule_config: Optional[dict[str, Any]] = None) -> List[dict]:
        for course in courses or []:
            schedules = course.get("schedules") or []
            for schedule in schedules:
                schedule["hours"] = self._resolve_schedule_hours(schedule, rule_config)
            course["hours"] = self._normalize_course_hours(course.get("hours"))
        return courses

    def _resolve_schedule_hours(self, schedule: dict, rule_config: Optional[dict[str, Any]] = None) -> float:
        try:
            declared_units = float(schedule.get("hours") or 0)
        except (TypeError, ValueError):
            declared_units = 0.0
        if declared_units > 0:
            return round(declared_units, 1)
        start_time, end_time = self._parse_time_range(schedule.get("time_range"))
        if start_time and end_time and end_time > start_time:
            diff_minutes = self._time_to_minutes(end_time) - self._time_to_minutes(start_time)
            return self._minutes_to_units(diff_minutes, rule_config)
        return 0.0

    def _resolve_duration_minutes(
        self,
        schedule: Optional[dict],
        fallback_hours: float,
        rule_config: Optional[dict[str, Any]] = None,
    ) -> int:
        if schedule:
            start_time, end_time = self._parse_time_range(schedule.get("time_range"))
            if start_time and end_time and end_time > start_time:
                return self._time_to_minutes(end_time) - self._time_to_minutes(start_time)
            hours = self._resolve_schedule_hours(schedule, rule_config)
            if hours > 0:
                return self._units_to_minutes(hours, rule_config)
        return self._units_to_minutes(max(fallback_hours, 1), rule_config)

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
        return round(sum(float(item.get("unit_count") or 0) for item in occupied.get(target_date.isoformat(), []) if item.get("course_key")), 1)

    def _has_overlap(
        self,
        occupied: Dict[str, List[dict]],
        target_date: date,
        start_minutes: int,
        end_minutes: int,
        unit_context: Optional[dict[str, Any]] = None,
    ) -> bool:
        for item in occupied.get(target_date.isoformat(), []):
            if not self._interval_overlap(start_minutes, end_minutes, item["start"], item["end"]):
                continue
            if not self._occupied_item_applies_to_unit(item, unit_context or {}):
                continue
            return True
        return False

    def _occupied_item_applies_to_unit(self, item: dict, unit_context: dict[str, Any]) -> bool:
        block_type = str(item.get("block_type") or "")
        if block_type == "instructor_unavailable":
            label = str(item.get("label") or "").strip().lower()
            instructor = str(unit_context.get("instructor") or "").strip().lower()
            return not label or (instructor and label == instructor)
        if block_type == "location_unavailable":
            label = str(item.get("label") or "").strip().lower()
            location = str(unit_context.get("location") or "").strip().lower()
            return not label or (location and label == location)
        return True

    def _apply_course_type_time_preferences(
        self,
        slot_candidates: List[tuple[int, int, str]],
        target_date: date,
        unit: dict,
        constraint_payload: AIScheduleTaskConstraintPayload,
    ) -> List[tuple[int, int, str]]:
        preferences = [
            item
            for item in (constraint_payload.course_type_time_preferences or [])
            if self._preference_matches_unit(item, target_date, unit)
        ]
        if not preferences:
            return slot_candidates

        strict_windows = [
            (self._parse_clock(item.start_time), self._parse_clock(item.end_time))
            for item in preferences
            if item.priority == "only"
        ]
        strict_windows = [(start, end) for start, end in strict_windows if start is not None and end is not None]
        if strict_windows:
            return [
                candidate
                for candidate in slot_candidates
                if any(candidate[0] >= start and candidate[1] <= end for start, end in strict_windows)
            ]

        preferred_windows = [
            (self._parse_clock(item.start_time), self._parse_clock(item.end_time))
            for item in preferences
        ]
        preferred_windows = [(start, end) for start, end in preferred_windows if start is not None and end is not None]
        preferred_slots = [
            candidate
            for candidate in slot_candidates
            if any(candidate[0] >= start and candidate[1] <= end for start, end in preferred_windows)
        ]
        if not preferred_slots:
            return slot_candidates
        preferred_keys = {(start, end, time_range) for start, end, time_range in preferred_slots}
        fallback_slots = [candidate for candidate in slot_candidates if candidate not in preferred_keys]
        return preferred_slots + fallback_slots

    def _preference_matches_unit(self, preference: Any, target_date: date, unit: dict) -> bool:
        course_type = getattr(preference, "course_type", None)
        weekdays = list(getattr(preference, "weekdays", None) or [])
        return (
            course_type == (unit.get("course_type") or "theory")
            and (not weekdays or target_date.isoweekday() in weekdays)
        )

    def _build_course_type_preference_conflict(
        self,
        schedule_date: date,
        start_minutes: int,
        end_minutes: int,
        course_type: str,
        course_key: Optional[str],
        session_id: Optional[str],
        constraint_payload: AIScheduleTaskConstraintPayload,
    ) -> Optional[AIScheduleConflictItem]:
        matched_preferences = [
            item
            for item in (constraint_payload.course_type_time_preferences or [])
            if item.course_type == course_type and (not item.weekdays or schedule_date.isoweekday() in item.weekdays)
        ]
        if not matched_preferences:
            return None

        strict_preferences = [item for item in matched_preferences if item.priority == "only"]
        if strict_preferences:
            if any(
                self._slot_within_window(start_minutes, end_minutes, item.start_time, item.end_time)
                for item in strict_preferences
            ):
                return None
            return AIScheduleConflictItem(
                severity="error",
                conflict_type="course_type_time_preference_violation",
                course_key=course_key,
                session_id=session_id,
                message=f"{self.COURSE_TYPE_LABELS.get(course_type, course_type)}未落在允许时段内",
                suggestion="请调整课次时间，或修改该课程类型的时段限制",
            )

        if any(
            self._slot_within_window(start_minutes, end_minutes, item.start_time, item.end_time)
            for item in matched_preferences
        ):
            return None
        return AIScheduleConflictItem(
            severity="warning",
            conflict_type="course_type_time_preference_miss",
            course_key=course_key,
            session_id=session_id,
            message=f"{self.COURSE_TYPE_LABELS.get(course_type, course_type)}未命中偏好时段",
            suggestion="如条件允许，建议调整到偏好时间段",
        )

    def _resolve_exam_focus_dates_for_unit(
        self,
        training: Training,
        unit: dict,
        constraint_payload: AIScheduleTaskConstraintPayload,
        default_dates: List[date],
    ) -> List[date]:
        focus = constraint_payload.exam_week_focus
        if not focus or not self._unit_matches_exam_focus(unit, focus):
            return []
        focus_dates: List[date] = []
        for exam in training.exam_sessions or []:
            if not isinstance(exam, Exam) or not exam.start_time:
                continue
            exam_date = exam.start_time.date()
            window_start = exam_date - timedelta(days=max(int(focus.days_before_exam or 7), 1))
            focus_dates.extend(
                item
                for item in default_dates
                if window_start <= item < exam_date
            )
        return list(dict.fromkeys(focus_dates))

    def _unit_matches_exam_focus(self, unit: dict, focus: Any) -> bool:
        course_type = getattr(focus, "course_type", None)
        if course_type and course_type != (unit.get("course_type") or "theory"):
            return False
        keywords = [str(item).strip() for item in (getattr(focus, "course_keywords", None) or []) if str(item).strip()]
        if not keywords:
            return True
        course_name = str(unit.get("course_name") or "")
        return any(keyword in course_name for keyword in keywords)

    def _slot_within_window(self, start_minutes: int, end_minutes: int, start_time: str, end_time: str) -> bool:
        window_start = self._parse_clock(start_time)
        window_end = self._parse_clock(end_time)
        if window_start is None or window_end is None:
            return False
        return start_minutes >= window_start and end_minutes <= window_end

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

    def _split_hours(self, hours: float, rule_config: Optional[dict[str, Any]] = None) -> List[float]:
        remaining = max(hours, 0)
        if remaining <= 0:
            return [float(self._resolve_default_fill_units(rule_config or {}))]
        max_units_per_session = max(1, int((rule_config or {}).get("max_units_per_session") or 3))
        rounded_total = round(remaining)
        if abs(remaining - rounded_total) <= 1e-6:
            session_count = max(1, math.ceil(rounded_total / max_units_per_session))
            base = rounded_total // session_count
            remainder = rounded_total % session_count
            return [
                float(base + (1 if index < remainder else 0))
                for index in range(session_count)
                if base + (1 if index < remainder else 0) > 0
            ]
        result: List[float] = []
        while remaining > max_units_per_session:
            result.append(float(max_units_per_session))
            remaining -= max_units_per_session
        result.append(round(max(remaining, 1), 1))
        return result

    def _resolve_unit_candidate_dates(
        self,
        unit: dict,
        default_dates: List[date],
        preferred_dates: Optional[List[date]] = None,
    ) -> List[date]:
        candidate_date_values = {
            str(item).strip()
            for item in (unit.get("candidate_dates") or [])
            if str(item).strip()
        }
        candidate_dates = default_dates
        if not candidate_date_values:
            candidate_dates = default_dates
        else:
            candidate_dates = [item for item in default_dates if item.isoformat() in candidate_date_values]
        if not preferred_dates:
            return candidate_dates
        preferred_keys = {item.isoformat() for item in preferred_dates}
        prioritized = [item for item in candidate_dates if item.isoformat() in preferred_keys]
        fallback = [item for item in candidate_dates if item.isoformat() not in preferred_keys]
        return prioritized + fallback

    @staticmethod
    def _is_workday(target_date: date) -> bool:
        return target_date.weekday() < 5

    @staticmethod
    def _resolve_planning_mode(value: Any) -> str:
        mode = str(value or "auto").strip()
        if mode in {"fill_all_days", "fill_workdays", "by_hours", "auto"}:
            return mode
        return "auto"

    @staticmethod
    def _should_validate_course_hours(planning_mode: str) -> bool:
        return planning_mode in {"auto", "by_hours"}

    @staticmethod
    def _normalize_course_hours(value: Any) -> float:
        try:
            return round(max(float(value or 0), 0), 1)
        except (TypeError, ValueError):
            return 0.0

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

    def _resolve_rule_config(self, training: Training, data: AIScheduleTaskCreateRequest) -> dict[str, Any]:
        override = data.schedule_rule_override.model_dump(mode="json") if data.schedule_rule_override else None
        return TrainingScheduleRuleService.resolve_effective_rule_config(training.schedule_rule_config, override)

    def _units_to_minutes(self, hours: float, rule_config: Optional[dict[str, Any]] = None) -> int:
        if not rule_config:
            return int(round(max(hours, 1) * 60))
        lesson_unit_minutes = max(int(rule_config.get("lesson_unit_minutes") or 40), 1)
        break_minutes = max(int(rule_config.get("break_minutes") or 0), 0)
        if hours <= 0:
            return lesson_unit_minutes
        if abs(hours - round(hours)) <= 1e-6:
            unit_count = int(round(hours))
            return lesson_unit_minutes * unit_count + break_minutes * max(unit_count - 1, 0)
        return int(round(hours * lesson_unit_minutes + break_minutes * max(hours - 1, 0)))

    def _minutes_to_units(self, duration_minutes: int, rule_config: Optional[dict[str, Any]] = None) -> float:
        if duration_minutes <= 0:
            return 0.0
        if not rule_config:
            return round(duration_minutes / 60, 1)
        lesson_unit_minutes = max(int(rule_config.get("lesson_unit_minutes") or 40), 1)
        break_minutes = max(int(rule_config.get("break_minutes") or 0), 0)
        if duration_minutes <= lesson_unit_minutes or break_minutes <= 0:
            return round(duration_minutes / lesson_unit_minutes, 1)
        exact_units = (duration_minutes + break_minutes) / (lesson_unit_minutes + break_minutes)
        rounded_units = round(exact_units)
        if abs(exact_units - rounded_units) <= 0.05:
            return float(rounded_units)
        return round(exact_units, 1)

    def _resolve_default_fill_units(self, rule_config: dict[str, Any]) -> int:
        max_units_per_session = max(1, int(rule_config.get("max_units_per_session") or 3))
        daily_max_units = max(1, int(rule_config.get("daily_max_units") or max_units_per_session))
        window_capacity = max(self._compute_window_capacity_units(item, rule_config) for item in (rule_config.get("teaching_windows") or [{}]))
        return max(1, min(max_units_per_session, daily_max_units, window_capacity))

    def _compute_window_capacity_units(self, window: dict[str, Any], rule_config: dict[str, Any]) -> int:
        start_minutes = self._parse_clock(window.get("start_time") or "")
        end_minutes = self._parse_clock(window.get("end_time") or "")
        if start_minutes is None or end_minutes is None or end_minutes <= start_minutes:
            return 1
        lesson_unit_minutes = max(int(rule_config.get("lesson_unit_minutes") or 40), 1)
        break_minutes = max(int(rule_config.get("break_minutes") or 0), 0)
        step = lesson_unit_minutes + break_minutes
        total_minutes = end_minutes - start_minutes
        if total_minutes < lesson_unit_minutes:
            return 1
        return max(1, 1 + max(total_minutes - lesson_unit_minutes, 0) // max(step, 1))

    def _build_slot_candidates(
        self,
        rule_config: dict[str, Any],
        unit_count: float,
        plan_index: int,
    ) -> List[tuple[int, int, str]]:
        duration_minutes = self._units_to_minutes(unit_count, rule_config)
        windows = list(rule_config.get("teaching_windows") or [])
        if not windows:
            windows = [{"start_time": item, "end_time": self._format_clock((self._parse_clock(item) or 0) + duration_minutes)} for item in self.SLOT_STARTS]
        windows = windows[plan_index:] + windows[:plan_index]
        lesson_unit_minutes = max(int(rule_config.get("lesson_unit_minutes") or 40), 1)
        break_minutes = max(int(rule_config.get("break_minutes") or 0), 0)
        step = max(lesson_unit_minutes + break_minutes, 1)
        slots: List[tuple[int, int, str]] = []
        for window in windows:
            start_minutes = self._parse_clock(window.get("start_time") or "")
            end_minutes = self._parse_clock(window.get("end_time") or "")
            if start_minutes is None or end_minutes is None or end_minutes <= start_minutes:
                continue
            latest_start = end_minutes - duration_minutes
            if latest_start < start_minutes:
                continue
            candidate_starts = list(range(start_minutes, latest_start + 1, step))
            if candidate_starts:
                rotate_offset = plan_index % len(candidate_starts)
                candidate_starts = candidate_starts[rotate_offset:] + candidate_starts[:rotate_offset]
            for candidate_start in candidate_starts:
                candidate_end = candidate_start + duration_minutes
                slots.append(
                    (
                        candidate_start,
                        candidate_end,
                        f"{self._format_clock(candidate_start)}~{self._format_clock(candidate_end)}",
                    )
                )
        return slots
