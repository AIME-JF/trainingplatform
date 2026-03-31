"""
培训管理服务
"""
import json
import uuid
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.attributes import flag_modified

from app.database import get_redis
from app.models import (
    AdmissionExam,
    AdmissionExamRecord,
    Certificate,
    CheckinRecord,
    Department,
    Enrollment,
    Exam,
    ExamPaper,
    ExamRecord,
    Notice,
    PoliceType,
    Role,
    ScheduleItem,
    Training,
    TrainingBase,
    TrainingCourseChangeLog,
    TrainingCourse,
    TrainingHistory,
    User,
)
from app.models.resource import Resource, ResourceTagRelation, TrainingResourceRef
from app.schemas import PaginatedResponse
from app.schemas.resource import ResourceListItemResponse, TrainingResourceBindRequest
from app.schemas.training import (
    CheckinCreate,
    CheckinResponse,
    TrainingCheckinQrResponse,
    CheckoutCreate,
    EnrollmentCreate,
    EnrollmentResponse,
    ScheduleItemResponse,
    TrainingAttendanceSummaryResponse,
    TrainingCourseResponse,
    TrainingCourseChangeLogResponse,
    TrainingCreate,
    TrainingCurrentSessionResponse,
    TrainingEvaluationCreate,
    TrainingExamSummary,
    TrainingHistoryResponse,
    TrainingListResponse,
    TrainingStatsResponse,
    TrainingResponse,
    TrainingScheduleRuleConfig,
    TrainingSessionActionPermissions,
    TrainingSkipCourseRequest,
    TrainingUpdate,
    TrainingWorkflowStepResponse,
)
from app.schemas.notice import NoticeResponse
from app.services.batch_import import BatchImportService
from app.services.system_exchange import SystemExchangeService
from app.services.training_course_change import TrainingCourseChangeService
from app.services.training_schedule_rule import TrainingScheduleRuleService
from app.utils.authz import (
    can_manage_training,
    can_update_training,
    can_operate_training_course,
    can_view_training,
    can_view_training_with_context,
)
from app.utils.data_scope import build_data_scope_context, can_assign_scoped_values
from logger import logger

_UNSET = object()


class TrainingService:
    """培训服务"""

    CHECKIN_QR_PREFIX = "training:checkin:qr:"
    CHECKIN_QR_TTL_SECONDS = 15 * 60
    SESSION_PENDING = "pending"
    SESSION_CHECKIN_OPEN = "checkin_open"
    SESSION_CHECKIN_CLOSED = "checkin_closed"
    SESSION_CHECKOUT_OPEN = "checkout_open"
    SESSION_COMPLETED = "completed"
    SESSION_SKIPPED = "skipped"
    SESSION_MISSED = "missed"
    SESSION_STATUS_LABELS = {
        SESSION_PENDING: "未开始",
        SESSION_CHECKIN_OPEN: "签到中",
        SESSION_CHECKIN_CLOSED: "课程进行中",
        SESSION_CHECKOUT_OPEN: "签退中",
        SESSION_COMPLETED: "已完成",
        SESSION_SKIPPED: "已跳过",
        SESSION_MISSED: "缺勤",
    }
    WORKFLOW_STEP_DRAFT = "draft"
    WORKFLOW_STEP_PUBLISHED = "published"
    WORKFLOW_STEP_LOCKED = "locked"
    WORKFLOW_STEP_RUNNING = "running"
    WORKFLOW_STEP_COMPLETED = "completed"
    WORKFLOW_SKIP_STEP_ORDER = [WORKFLOW_STEP_PUBLISHED, WORKFLOW_STEP_LOCKED]
    WORKFLOW_STEP_LABELS = {
        WORKFLOW_STEP_DRAFT: "草稿",
        WORKFLOW_STEP_PUBLISHED: "发布招生",
        WORKFLOW_STEP_LOCKED: "锁定名单",
        WORKFLOW_STEP_RUNNING: "开班进行中",
        WORKFLOW_STEP_COMPLETED: "结班归档",
    }
    TRAINING_STATUS_VALUES = {"upcoming", "active", "ended"}

    def __init__(self, db: Session):
        self.db = db
        self.course_change_service = TrainingCourseChangeService(db)

    @staticmethod
    def _is_aware_datetime(value: Optional[datetime]) -> bool:
        return bool(value and value.tzinfo and value.tzinfo.utcoffset(value) is not None)

    @classmethod
    def _current_time(cls, *references: Optional[datetime]) -> datetime:
        for reference in references:
            if cls._is_aware_datetime(reference):
                return datetime.now(reference.tzinfo)
        return datetime.now()

    @classmethod
    def _normalize_datetime(cls, value: Optional[datetime], reference_tzinfo: Any) -> Optional[datetime]:
        if value is None:
            return None
        if cls._is_aware_datetime(value) or reference_tzinfo is None:
            return value
        return value.replace(tzinfo=reference_tzinfo)

    def get_trainings(
        self,
        page: int = 1,
        size: int = 10,
        status: Optional[str] = None,
        training_type: Optional[str] = None,
        search: Optional[str] = None,
        current_user_id: Optional[int] = None,
    ) -> PaginatedResponse[TrainingListResponse]:
        """获取培训列表"""
        trainings = self._collect_visible_trainings(
            status=status,
            training_type=training_type,
            search=search,
            current_user_id=current_user_id,
        )
        items = [self._to_list_response(training, current_user_id) for training in trainings]

        total = len(items)
        if size != -1:
            skip = (page - 1) * size
            items = items[skip: skip + size]

        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=items,
        )

    def get_training_stats(self, current_user_id: Optional[int] = None) -> TrainingStatsResponse:
        """获取培训班统计"""
        trainings = self._collect_visible_trainings(current_user_id=current_user_id)
        return TrainingStatsResponse(
            total=len(trainings),
            published=sum(1 for item in trainings if (item.publish_status or "draft") == "published"),
            active=sum(1 for item in trainings if (item.status or "upcoming") == "active"),
            locked=sum(1 for item in trainings if item.locked_at is not None),
        )

    def _collect_visible_trainings(
        self,
        status: Optional[str] = None,
        training_type: Optional[str] = None,
        search: Optional[str] = None,
        current_user_id: Optional[int] = None,
    ) -> List[Training]:
        status_filters = self._normalize_training_status_filters(status)
        query = self.db.query(Training).options(
            joinedload(Training.department),
            joinedload(Training.instructor),
            joinedload(Training.enrollments),
            joinedload(Training.admission_exam),
            joinedload(Training.police_type),
            joinedload(Training.training_base),
        )

        if training_type:
            query = query.filter(Training.type == training_type)
        if search:
            query = query.filter(Training.name.contains(search))

        trainings = query.order_by(Training.created_at.desc()).all()
        visible_trainings: List[Training] = []
        changed = False
        scope_context = build_data_scope_context(self.db, current_user_id) if current_user_id else None
        for training in trainings:
            if self.course_change_service.ensure_course_keys(training.courses or []):
                changed = True
            if self._refresh_schedule_states(training):
                changed = True
            if status_filters and (training.status or "upcoming") not in status_filters:
                continue
            if scope_context and not can_view_training_with_context(scope_context, training):
                continue
            visible_trainings.append(training)

        if changed:
            self.db.commit()

        return visible_trainings

    def _normalize_training_status_filters(self, status: Optional[str]) -> List[str]:
        if not status:
            return []
        normalized: List[str] = []
        for item in str(status).split(","):
            value = item.strip()
            if not value or value in normalized:
                continue
            if value not in self.TRAINING_STATUS_VALUES:
                continue
            normalized.append(value)
        return normalized

    def create_training(self, data: TrainingCreate, user_id: int) -> TrainingResponse:
        """创建培训班"""
        training = Training(
            name=data.name,
            type=data.type,
            status=data.status,
            publish_status=data.publish_status or "draft",
            start_date=data.start_date,
            end_date=data.end_date,
            class_code=data.class_code,
            instructor_id=data.instructor_id or user_id,
            created_by=user_id,
            capacity=data.capacity,
            description=data.description,
            subjects=data.subjects,
            enrollment_requires_approval=bool(data.enrollment_requires_approval),
            enrollment_start_at=data.enrollment_start_at,
            enrollment_end_at=data.enrollment_end_at,
            schedule_rule_config=TrainingScheduleRuleService.normalize_rule_config(
                data.schedule_rule_config.model_dump(mode="json") if data.schedule_rule_config else None
            ),
            published_at=self._current_time(data.enrollment_start_at, data.enrollment_end_at)
            if data.publish_status == "published" else None,
            published_by=user_id if data.publish_status == "published" else None,
        )
        self._apply_training_domain_fields(
            training,
            location=data.location,
            department_id=data.department_id,
            police_type_id=data.police_type_id,
            training_base_id=data.training_base_id,
        )
        training.visibility_scope = data.visibility_scope or "all"
        training.visibility_department_ids = data.visibility_department_ids if data.visibility_scope != "all" else None
        self._ensure_actor_can_assign_training_scope(user_id, training.department_id, training.police_type_id)
        self.db.add(training)
        self.db.flush()

        if data.admission_exam_id:
            self._bind_admission_exam(training, data.admission_exam_id)

        self._replace_courses(training.id, data.courses or [])
        self.db.commit()
        self.db.refresh(training)

        logger.info("创建培训班: %s", training.name)
        detail = self.get_training_by_id(training.id, user_id)
        if not detail:
            raise ValueError("创建培训班后读取详情失败")
        return detail

    def get_training_by_id(self, training_id: int, current_user_id: Optional[int] = None) -> Optional[TrainingResponse]:
        """获取培训详情"""
        training = self.db.query(Training).options(
            joinedload(Training.department),
            joinedload(Training.instructor),
            joinedload(Training.police_type),
            joinedload(Training.training_base),
            joinedload(Training.courses).joinedload(TrainingCourse.primary_instructor),
            joinedload(Training.enrollments).joinedload(Enrollment.user).joinedload(User.departments),
            joinedload(Training.admission_exam),
            joinedload(Training.exam_sessions).joinedload(Exam.paper).joinedload(ExamPaper.paper_questions),
        ).filter(Training.id == training_id).first()
        if not training:
            return None
        if current_user_id and not can_view_training(self.db, training, current_user_id):
            return None
        changed = self.course_change_service.ensure_course_keys(training.courses or [])
        if self._refresh_schedule_states(training):
            changed = True
        if changed:
            self.db.commit()
        return self._to_response(training, current_user_id)

    def update_training(
        self,
        training_id: int,
        data: TrainingUpdate,
        actor_id: Optional[int] = None,
    ) -> Optional[TrainingResponse]:
        """更新培训班"""
        training = self.db.query(Training).options(
            joinedload(Training.enrollments),
            joinedload(Training.courses),
            joinedload(Training.training_base),
        ).filter(Training.id == training_id).first()
        if not training:
            return None
        self.course_change_service.ensure_course_keys(training.courses or [])

        update_data = data.model_dump(exclude_unset=True)
        courses = update_data.pop("courses", None)
        student_ids = update_data.pop("student_ids", None)
        roster_assignments = update_data.pop("roster_assignments", None)
        should_refresh_histories = any(
            key in update_data
            for key in ("status", "start_date", "end_date", "name", "type")
        )
        admission_exam_id = None
        if "admission_exam_id" in update_data:
            admission_exam_id = update_data.pop("admission_exam_id")
        schedule_rule_config = _UNSET
        if "schedule_rule_config" in update_data:
            schedule_rule_config = update_data.pop("schedule_rule_config")

        if student_ids is not None and training.locked_at:
            raise ValueError("班次名单已锁定，不能再调整学员名单")

        if any(
            key in update_data
            for key in ("location", "department_id", "police_type_id", "training_base_id")
        ):
            self._apply_training_domain_fields(
                training,
                location=update_data.pop("location", _UNSET),
                department_id=update_data.pop("department_id", _UNSET),
                police_type_id=update_data.pop("police_type_id", _UNSET),
                training_base_id=update_data.pop("training_base_id", _UNSET),
            )
            if actor_id:
                self._ensure_actor_can_assign_training_scope(actor_id, training.department_id, training.police_type_id)

        for field, value in update_data.items():
            setattr(training, field, value)

        if (training.visibility_scope or "all") == "all":
            training.visibility_department_ids = None

        if schedule_rule_config is not _UNSET:
            training.schedule_rule_config = TrainingScheduleRuleService.normalize_rule_config(
                schedule_rule_config
            )

        if admission_exam_id is not None:
            training.admission_exam_id = None
            if admission_exam_id:
                self._bind_admission_exam(training, admission_exam_id)

        if courses is not None:
            self._assert_training_course_editable(training, "修改课程安排")
            before_courses = self.course_change_service.snapshot_course_entities(training.courses or [])
            after_courses = self.course_change_service.snapshot_course_payloads(courses or [])
            self._validate_schedule_mutation_window(training, before_courses, after_courses)
            self._replace_courses(training.id, courses)
            self.db.flush()
            after_courses = self._load_training_courses(training.id)
            if training.status == "active":
                self.course_change_service.record_changes(
                    training.id,
                    before_courses,
                    after_courses,
                    actor_id,
                    "detail_update",
                )
            should_refresh_histories = True

        changed_user_ids: List[int] = []
        if student_ids is not None:
            changed_user_ids.extend(self._sync_student_ids(training, student_ids))
            should_refresh_histories = True

        if roster_assignments is not None:
            changed_user_ids.extend(self._apply_roster_assignments(training_id, roster_assignments))
            should_refresh_histories = True

        if changed_user_ids:
            self._refresh_training_histories(training_id, list(set(changed_user_ids)))
        elif should_refresh_histories:
            self._refresh_training_histories(training_id)

        self.db.commit()
        self.db.refresh(training)

        logger.info("更新培训班: %s", training.name)
        return self.get_training_by_id(training_id, actor_id)

    def delete_training(self, training_id: int) -> bool:
        """删除培训班"""
        training = self.db.query(Training).filter(Training.id == training_id).first()
        if not training:
            return False

        self.db.query(Certificate).filter(
            Certificate.training_id == training_id
        ).update({Certificate.training_id: None}, synchronize_session=False)
        self.db.delete(training)
        self.db.commit()

        logger.info("删除培训班: %s", training_id)
        return True

    def publish_training(
        self,
        training_id: int,
        user_id: int,
        skip_steps: Optional[List[str]] = None,
    ) -> Optional[TrainingResponse]:
        """发布培训班"""
        training = self.db.query(Training).filter(Training.id == training_id).first()
        if not training:
            return None
        self._normalize_workflow_skip_steps(skip_steps)
        self._assert_training_can_publish(training)
        self._mark_training_published(training, user_id)
        self.db.commit()
        return self.get_training_by_id(training_id, user_id)

    def lock_training(
        self,
        training_id: int,
        user_id: int,
        skip_steps: Optional[List[str]] = None,
    ) -> Optional[TrainingResponse]:
        """锁定培训班名单"""
        training = self.db.query(Training).options(
            joinedload(Training.enrollments),
        ).filter(Training.id == training_id).first()
        if not training:
            return None

        normalized_skip_steps = self._normalize_workflow_skip_steps(skip_steps)
        self._assert_training_can_lock(training, normalized_skip_steps)
        if training.publish_status != "published":
            self._mark_training_published(training, user_id)
        self._mark_training_locked(training, user_id)
        self._refresh_training_histories(training_id)
        self.db.commit()
        return self.get_training_by_id(training_id, user_id)

    def start_training(
        self,
        training_id: int,
        actor_id: Optional[int] = None,
        skip_steps: Optional[List[str]] = None,
    ) -> Optional[TrainingResponse]:
        """手动开班"""
        training = self.db.query(Training).options(
            joinedload(Training.enrollments),
        ).filter(Training.id == training_id).first()
        if not training:
            return None
        normalized_skip_steps = self._normalize_workflow_skip_steps(skip_steps)
        self._assert_training_can_start(training, normalized_skip_steps)
        action_user_id = actor_id or training.instructor_id or training.created_by
        if training.publish_status != "published":
            if action_user_id is None:
                raise ValueError("缺少流程操作人，无法自动发布培训班")
            self._mark_training_published(training, action_user_id)
        if not training.locked_at:
            if action_user_id is None:
                raise ValueError("缺少流程操作人，无法自动锁定培训班名单")
            self._mark_training_locked(training, action_user_id)
        training.status = "active"
        self._refresh_training_histories(training_id)
        self.db.commit()
        logger.info("手动开班: %s", training_id)
        return self.get_training_by_id(training_id, actor_id)

    def end_training(self, training_id: int, actor_id: Optional[int] = None) -> Optional[TrainingResponse]:
        """手动结班"""
        training = self.db.query(Training).options(
            joinedload(Training.courses),
            joinedload(Training.enrollments),
        ).filter(Training.id == training_id).first()
        if not training:
            return None
        if training.status != "active":
            raise ValueError("仅开班进行中的培训班可结班")

        training.status = "ended"
        for session in self._build_session_catalog(training):
            self._sync_absent_records(training, session["session_key"], session["date"])

        self._refresh_training_histories(training_id)
        self.db.commit()
        logger.info("手动结班: %s", training_id)
        return self.get_training_by_id(training_id, actor_id)

    def _normalize_workflow_skip_steps(self, skip_steps: Optional[List[str]]) -> List[str]:
        normalized: List[str] = []
        for item in skip_steps or []:
            value = str(item or "").strip()
            if not value:
                continue
            if value not in self.WORKFLOW_SKIP_STEP_ORDER:
                raise ValueError(f"不支持跳过的流程节点: {value}")
            if value not in normalized:
                normalized.append(value)
        return normalized

    def _assert_training_can_publish(self, training: Training) -> None:
        if training.status == "ended":
            raise ValueError("已结班的培训班不能发布")
        if training.status == "active":
            raise ValueError("开班进行中的培训班不能重新发布")
        if training.publish_status == "published":
            raise ValueError("当前培训班已发布")

    def _assert_training_can_lock(self, training: Training, skip_steps: List[str]) -> None:
        if training.status == "ended":
            raise ValueError("已结班的培训班不能锁定名单")
        if training.status == "active":
            raise ValueError("开班进行中的培训班不能重新锁定名单")
        if training.locked_at:
            raise ValueError("当前培训班已锁定名单")
        missing_steps = self._get_missing_workflow_steps(training, "lock")
        self._ensure_workflow_skip_confirmed(missing_steps, skip_steps)

    def _assert_training_can_start(self, training: Training, skip_steps: List[str]) -> None:
        if training.status == "ended":
            raise ValueError("已结班的培训班不能再次开班")
        if training.status == "active":
            raise ValueError("当前培训班已开班")
        missing_steps = self._get_missing_workflow_steps(training, "start")
        self._ensure_workflow_skip_confirmed(missing_steps, skip_steps)

    def _get_missing_workflow_steps(self, training: Training, action: str) -> List[str]:
        missing_steps: List[str] = []
        if action in {"lock", "start"} and training.publish_status != "published":
            missing_steps.append(self.WORKFLOW_STEP_PUBLISHED)
        if action == "start" and not training.locked_at:
            missing_steps.append(self.WORKFLOW_STEP_LOCKED)
        return missing_steps

    def _ensure_workflow_skip_confirmed(self, missing_steps: List[str], skip_steps: List[str]) -> None:
        if not missing_steps:
            return
        if all(step in skip_steps for step in missing_steps):
            return
        labels = "、".join(self.WORKFLOW_STEP_LABELS[step] for step in missing_steps)
        suffix = "该环节" if len(missing_steps) == 1 else "这些环节"
        raise ValueError(f"当前培训班尚未完成“{labels}”环节，如需继续请先确认跳过{suffix}")

    def _mark_training_published(self, training: Training, user_id: int) -> None:
        if training.publish_status == "published":
            return
        training.publish_status = "published"
        training.published_at = self._current_time(
            training.enrollment_start_at,
            training.enrollment_end_at,
            training.published_at,
            training.locked_at,
        )
        training.published_by = user_id

    def _mark_training_locked(self, training: Training, user_id: int) -> None:
        if training.locked_at:
            return
        now = self._current_time(
            training.enrollment_start_at,
            training.enrollment_end_at,
            training.published_at,
            training.locked_at,
        )
        training.locked_at = now
        training.locked_by = user_id
        for enrollment in training.enrollments or []:
            if enrollment.status == "pending":
                enrollment.status = "rejected"
                enrollment.note = enrollment.note or "班次名单已锁定"
                enrollment.reviewed_at = now
                enrollment.reviewed_by = user_id

    def import_training_students(self, training_id: int, file_bytes: bytes) -> dict:
        importer = BatchImportService(self.db)
        return importer.import_training_students(training_id, file_bytes)

    def build_training_student_import_template(self) -> bytes:
        return SystemExchangeService(self.db).build_training_student_template()

    def build_training_course_import_template(self) -> bytes:
        return SystemExchangeService(self.db).build_training_course_template()

    def build_training_session_import_template(self) -> bytes:
        return SystemExchangeService(self.db).build_training_session_template()

    def build_training_instructor_import_template(self) -> bytes:
        return SystemExchangeService(self.db).build_training_instructor_template()

    def build_training_schedule_import_template(self) -> bytes:
        return self.build_training_session_import_template()

    def import_training_courses(
        self,
        training_id: int,
        file_bytes: bytes,
        actor_id: Optional[int] = None,
    ) -> dict:
        return self._run_training_course_import(
            training_id,
            file_bytes,
            actor_id,
            action_text="导入课程",
            change_source="import_course",
            importer_action=lambda importer: importer.import_training_courses(
                training_id,
                file_bytes,
                commit=False,
            ),
        )

    def import_training_instructors(self, training_id: int, file_bytes: bytes) -> dict:
        importer = BatchImportService(self.db)
        return importer.import_training_instructors(training_id, file_bytes)

    def import_training_sessions(
        self,
        training_id: int,
        file_bytes: bytes,
        actor_id: Optional[int] = None,
    ) -> dict:
        return self._run_training_course_import(
            training_id,
            file_bytes,
            actor_id,
            action_text="导入课次",
            change_source="import_session",
            importer_action=lambda importer: importer.import_training_sessions(
                training_id,
                file_bytes,
                commit=False,
            ),
        )

    def import_training_schedule(
        self,
        training_id: int,
        file_bytes: bytes,
        replace_existing: bool = True,
        actor_id: Optional[int] = None,
    ) -> dict:
        summary = self.import_training_sessions(
            training_id,
            file_bytes,
            actor_id=actor_id,
        )
        summary["replace_existing"] = False
        return summary

    def _run_training_course_import(
        self,
        training_id: int,
        file_bytes: bytes,
        actor_id: Optional[int],
        *,
        action_text: str,
        change_source: str,
        importer_action,
    ) -> dict:
        training = self.db.query(Training).options(
            joinedload(Training.courses),
        ).filter(Training.id == training_id).first()
        if not training:
            raise ValueError("培训班不存在")
        self.course_change_service.ensure_course_keys(training.courses or [])
        self._assert_training_course_editable(training, action_text)
        before_courses = self.course_change_service.snapshot_course_entities(training.courses or [])
        importer = BatchImportService(self.db)
        summary = importer_action(importer)
        self.db.flush()
        after_courses = self._load_training_courses(training_id)
        try:
            self._validate_schedule_mutation_window(
                training,
                before_courses,
                self.course_change_service.snapshot_course_entities(after_courses),
            )
        except ValueError:
            self.db.rollback()
            raise
        if training.status == "active":
            self.course_change_service.record_changes(
                training_id,
                before_courses,
                after_courses,
                actor_id,
                change_source,
            )
        self.db.commit()
        return summary

    def get_training_students(self, training_id: int, page: int = 1, size: int = 10) -> PaginatedResponse[EnrollmentResponse]:
        """获取培训学员列表"""
        query = self.db.query(Enrollment).options(
            joinedload(Enrollment.user).joinedload(User.departments),
        ).filter(
            Enrollment.training_id == training_id,
            Enrollment.status == "approved",
        ).order_by(Enrollment.approved_at.desc(), Enrollment.enroll_time.desc())

        total = query.count()
        if size == -1:
            records = query.all()
        else:
            skip = (page - 1) * size
            records = query.offset(skip).limit(size).all()

        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=[self._enrollment_to_response(record) for record in records],
        )

    def get_schedule(self, training_id: int) -> List[ScheduleItemResponse]:
        """获取周计划"""
        items = self.db.query(ScheduleItem).filter(
            ScheduleItem.training_id == training_id
        ).order_by(ScheduleItem.day, ScheduleItem.time_start).all()
        return [ScheduleItemResponse.model_validate(item) for item in items]

    def enroll(self, training_id: int, user_id: int, data: EnrollmentCreate) -> EnrollmentResponse:
        """学员报名"""
        training = self.db.query(Training).options(
            joinedload(Training.admission_exam),
        ).filter(Training.id == training_id).first()
        if not training:
            raise ValueError("培训班不存在")
        if training.publish_status != "published":
            raise ValueError("当前培训班未开放报名")
        if training.locked_at:
            raise ValueError("当前培训班名单已锁定")

        now = self._current_time(
            training.enrollment_start_at,
            training.enrollment_end_at,
            training.published_at,
            training.locked_at,
        )
        enrollment_start_at = self._normalize_datetime(training.enrollment_start_at, now.tzinfo)
        enrollment_end_at = self._normalize_datetime(training.enrollment_end_at, now.tzinfo)
        if enrollment_start_at and now < enrollment_start_at:
            raise ValueError("报名尚未开始")
        if enrollment_end_at and now > enrollment_end_at:
            raise ValueError("报名已截止")

        existing = self.db.query(Enrollment).filter(
            Enrollment.training_id == training_id,
            Enrollment.user_id == user_id,
        ).first()
        if existing:
            raise ValueError("已报名该培训班")

        if training.admission_exam_id:
            passed = self.db.query(AdmissionExamRecord.id).filter(
                AdmissionExamRecord.admission_exam_id == training.admission_exam_id,
                AdmissionExamRecord.user_id == user_id,
                AdmissionExamRecord.result == "pass",
                AdmissionExamRecord.status == "submitted",
            ).first()
            if not passed:
                raise ValueError("该培训班要求先通过准入考试")

        user = self.db.query(User).options(joinedload(User.departments)).filter(User.id == user_id).first()
        requires_approval = bool(training.enrollment_requires_approval if training.enrollment_requires_approval is not None else True)
        if not requires_approval:
            approved_count = sum(1 for item in (training.enrollments or []) if item.status == "approved")
            if training.capacity and training.capacity > 0 and approved_count >= training.capacity:
                raise ValueError("培训班名额已满")
        enrollment = Enrollment(
            training_id=training_id,
            user_id=user_id,
            status="pending" if requires_approval else "approved",
            note=data.note,
            contact_phone=data.phone,
            need_accommodation=bool(data.need_accommodation),
            profile_snapshot=self._build_profile_snapshot(user),
            approved_at=None if requires_approval else now,
            reviewed_at=None if requires_approval else now,
            reviewed_by=None if requires_approval else user_id,
        )
        self.db.add(enrollment)
        if not requires_approval:
            self._refresh_training_histories(training_id, [user_id])
        self.db.commit()
        self.db.refresh(enrollment)

        logger.info("用户%s报名培训%s", user_id, training_id)
        return self._enrollment_to_response(enrollment)

    def get_enrollments(
        self,
        training_id: int,
        page: int = 1,
        size: int = 10,
        user_id: Optional[int] = None,
    ) -> PaginatedResponse[EnrollmentResponse]:
        """获取报名列表"""
        query = self.db.query(Enrollment).options(
            joinedload(Enrollment.user).joinedload(User.departments),
        ).filter(Enrollment.training_id == training_id).order_by(Enrollment.enroll_time.desc())
        if user_id is not None:
            query = query.filter(Enrollment.user_id == user_id)

        total = query.count()
        if size == -1:
            records = query.all()
        else:
            skip = (page - 1) * size
            records = query.offset(skip).limit(size).all()

        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=[self._enrollment_to_response(record) for record in records],
        )

    def approve_enrollment(self, training_id: int, enrollment_id: int, reviewer_id: Optional[int] = None) -> EnrollmentResponse:
        """审批通过"""
        training = self.db.query(Training).options(joinedload(Training.enrollments)).filter(Training.id == training_id).first()
        if not training:
            raise ValueError("培训班不存在")
        if training.locked_at:
            raise ValueError("名单已锁定，不能再调整")

        approved_count = sum(1 for item in training.enrollments or [] if item.status == "approved")
        if training.capacity and training.capacity > 0 and approved_count >= training.capacity:
            raise ValueError("培训班名额已满")

        enrollment = self.db.query(Enrollment).filter(
            Enrollment.id == enrollment_id,
            Enrollment.training_id == training_id,
        ).first()
        if not enrollment:
            raise ValueError("报名记录不存在")

        now = self._current_time(enrollment.enroll_time, enrollment.approved_at, enrollment.reviewed_at)
        enrollment.status = "approved"
        enrollment.approved_at = now
        enrollment.reviewed_at = now
        enrollment.reviewed_by = reviewer_id
        self._refresh_training_histories(training_id, [enrollment.user_id])
        self.db.commit()
        self.db.refresh(enrollment)

        logger.info("审批通过报名: %s", enrollment_id)
        return self._enrollment_to_response(enrollment)

    def reject_enrollment(
        self,
        training_id: int,
        enrollment_id: int,
        note: Optional[str] = None,
        reviewer_id: Optional[int] = None,
    ) -> EnrollmentResponse:
        """审批拒绝"""
        enrollment = self.db.query(Enrollment).filter(
            Enrollment.id == enrollment_id,
            Enrollment.training_id == training_id,
        ).first()
        if not enrollment:
            raise ValueError("报名记录不存在")

        enrollment.status = "rejected"
        enrollment.note = note or enrollment.note
        enrollment.reviewed_at = self._current_time(enrollment.enroll_time, enrollment.approved_at, enrollment.reviewed_at)
        enrollment.reviewed_by = reviewer_id
        self._refresh_training_histories(training_id, [enrollment.user_id])
        self.db.commit()
        self.db.refresh(enrollment)

        logger.info("审批拒绝报名: %s", enrollment_id)
        return self._enrollment_to_response(enrollment)

    def update_roster_assignments(self, training_id: int, assignments: List[dict]) -> List[EnrollmentResponse]:
        """更新学员编组和班干部信息"""
        user_ids = self._apply_roster_assignments(training_id, assignments)
        self._refresh_training_histories(training_id, list(set(user_ids)))
        self.db.commit()

        rows = self.db.query(Enrollment).options(
            joinedload(Enrollment.user).joinedload(User.departments),
        ).filter(
            Enrollment.training_id == training_id,
            Enrollment.status == "approved",
        ).order_by(Enrollment.group_name.asc().nulls_last(), Enrollment.user_id.asc()).all()
        return [self._enrollment_to_response(row) for row in rows]

    def get_checkin_records(
        self,
        training_id: int,
        date_filter: Optional[date] = None,
        session_key: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> List[CheckinResponse]:
        """获取签到记录"""
        training = self.db.query(Training).options(
            joinedload(Training.courses),
            joinedload(Training.enrollments),
        ).filter(Training.id == training_id).first()
        if not training:
            return []

        if session_key:
            self._sync_absent_records(training, session_key, date_filter)

        query = self.db.query(CheckinRecord).options(
            joinedload(CheckinRecord.user),
        ).filter(CheckinRecord.training_id == training_id)
        if user_id is not None:
            query = query.filter(CheckinRecord.user_id == user_id)
        if date_filter:
            query = query.filter(CheckinRecord.date == date_filter)
        if session_key:
            query = query.filter(CheckinRecord.session_key == session_key)

        records = query.order_by(CheckinRecord.date.desc(), CheckinRecord.time.asc().nulls_last()).all()
        return [self._checkin_to_response(record) for record in records]

    def checkin(self, training_id: int, user_id: int, data: CheckinCreate) -> CheckinResponse:
        """签到"""
        training = self.db.query(Training).options(
            joinedload(Training.courses),
        ).filter(Training.id == training_id).first()
        if not training:
            raise ValueError("培训班不存在")

        target_user_id = data.user_id or user_id
        self._ensure_training_member(training_id, target_user_id)

        now = datetime.now()
        session_key = data.session_key or "start"
        session = self._find_schedule_session(training, session_key)
        if not session:
            raise ValueError("课次不存在")
        if (session["schedule"].get("status") or self.SESSION_PENDING) != self.SESSION_CHECKIN_OPEN:
            raise ValueError("当前课次未处于签到状态")
        checkin_date = data.date or self._resolve_session_date(training, session_key, now.date())
        checkin_time = data.time or now.strftime("%H:%M")
        status = data.status or self._resolve_checkin_status(training, session_key, checkin_date, checkin_time)

        record = self.db.query(CheckinRecord).filter(
            CheckinRecord.training_id == training_id,
            CheckinRecord.user_id == target_user_id,
            CheckinRecord.date == checkin_date,
            CheckinRecord.session_key == session_key,
        ).first()

        if not record:
            record = CheckinRecord(
                training_id=training_id,
                user_id=target_user_id,
                date=checkin_date,
                session_key=session_key,
            )
            self.db.add(record)

        record.time = checkin_time
        record.status = status
        record.checkin_method = "manual" if data.user_id else "qr"
        record.absence_reason = None

        self._refresh_training_histories(training_id, [target_user_id])
        self.db.commit()
        self.db.refresh(record)

        logger.info("用户%s签到培训%s，场次=%s", target_user_id, training_id, session_key)
        return self._checkin_to_response(record)

    def checkout(self, training_id: int, user_id: int, data: CheckoutCreate) -> CheckinResponse:
        """签退"""
        training = self.db.query(Training).options(joinedload(Training.courses)).filter(Training.id == training_id).first()
        if not training:
            raise ValueError("培训班不存在")

        target_user_id = data.user_id or user_id
        self._ensure_training_member(training_id, target_user_id)

        now = datetime.now()
        session_key = data.session_key or "start"
        session = self._find_schedule_session(training, session_key)
        if not session:
            raise ValueError("课次不存在")
        if (session["schedule"].get("status") or self.SESSION_PENDING) != self.SESSION_CHECKOUT_OPEN:
            raise ValueError("当前课次未处于签退状态")
        target_date = data.date or self._resolve_session_date(training, session_key, now.date())
        checkout_time = data.time or now.strftime("%H:%M")

        record = self.db.query(CheckinRecord).filter(
            CheckinRecord.training_id == training_id,
            CheckinRecord.user_id == target_user_id,
            CheckinRecord.date == target_date,
            CheckinRecord.session_key == session_key,
        ).first()
        if not record:
            record = CheckinRecord(
                training_id=training_id,
                user_id=target_user_id,
                date=target_date,
                session_key=session_key,
                status="on_time",
            )
            self.db.add(record)

        record.checkout_time = checkout_time
        record.checkout_status = "completed"
        record.checkout_method = "manual" if data.user_id else "qr"
        if record.status == "absent":
            record.status = "on_time"
            record.absence_reason = None

        self._refresh_training_histories(training_id, [target_user_id])
        self.db.commit()
        self.db.refresh(record)

        logger.info("用户%s签退培训%s，场次=%s", target_user_id, training_id, session_key)
        return self._checkin_to_response(record)

    def submit_training_evaluation(self, training_id: int, user_id: int, data: TrainingEvaluationCreate) -> CheckinResponse:
        """提交评课"""
        training = self.db.query(Training).options(joinedload(Training.courses)).filter(Training.id == training_id).first()
        if not training:
            raise ValueError("培训班不存在")

        target_user_id = data.user_id or user_id
        self._ensure_training_member(training_id, target_user_id)

        target_date = data.date or self._resolve_session_date(training, data.session_key, date.today())
        record = self.db.query(CheckinRecord).filter(
            CheckinRecord.training_id == training_id,
            CheckinRecord.user_id == target_user_id,
            CheckinRecord.date == target_date,
            CheckinRecord.session_key == data.session_key,
        ).first()
        if not record:
            record = CheckinRecord(
                training_id=training_id,
                user_id=target_user_id,
                date=target_date,
                session_key=data.session_key,
                status="on_time",
            )
            self.db.add(record)

        record.evaluation_score = data.score
        record.evaluation_comment = data.comment
        record.evaluation_submitted_at = datetime.now()

        self._refresh_training_histories(training_id, [target_user_id])
        self.db.commit()
        self.db.refresh(record)

        logger.info("用户%s提交培训%s评课，场次=%s", target_user_id, training_id, data.session_key)
        return self._checkin_to_response(record)

    def get_attendance_summary(
        self,
        training_id: int,
        session_key: str,
        date_filter: Optional[date] = None,
    ) -> TrainingAttendanceSummaryResponse:
        """获取某个签到场次的统计摘要"""
        training = self.db.query(Training).options(joinedload(Training.courses)).filter(Training.id == training_id).first()
        records = self.get_checkin_records(training_id, date_filter, session_key)
        total_students = self.db.query(Enrollment.id).filter(
            Enrollment.training_id == training_id,
            Enrollment.status == "approved",
        ).count()

        on_time_count = sum(1 for item in records if item.status == "on_time")
        late_count = sum(1 for item in records if item.status == "late")
        absent_count = sum(1 for item in records if item.status == "absent")
        checked_out_count = sum(1 for item in records if item.checkout_status == "completed")
        evaluated_count = sum(1 for item in records if item.evaluation_score is not None)
        completion_rate = int(round(((on_time_count + late_count) / total_students) * 100)) if total_students else 0

        return TrainingAttendanceSummaryResponse(
            session_key=session_key,
            total_students=total_students,
            on_time_count=on_time_count,
            late_count=late_count,
            absent_count=absent_count,
            checked_out_count=checked_out_count,
            evaluated_count=evaluated_count,
            completion_rate=completion_rate,
            session_status=self._find_schedule_session(training, session_key)["status"] if training and self._find_schedule_session(training, session_key) else None,
        )

    def start_session_checkin(self, training_id: int, session_key: str, user_id: int) -> TrainingResponse:
        training, session = self._load_training_session(training_id, session_key)
        self._assert_training_course_editable(training, "修改课次状态")
        if not self._can_operate_schedule(training, session["course"], session["schedule"], user_id, "start_checkin"):
            raise ValueError("当前用户无权开始该课次签到，或课次状态不允许")
        before_course = self._snapshot_course_entity(session["course"])
        now = datetime.now().isoformat()
        schedule = session["schedule"]
        schedule["status"] = self.SESSION_CHECKIN_OPEN
        schedule["started_at"] = schedule.get("started_at") or now
        schedule["checkin_started_at"] = now
        flag_modified(session["course"], "schedules")
        if training.status != "ended":
            if training.publish_status != "published":
                self._mark_training_published(training, user_id)
            if not training.locked_at:
                self._mark_training_locked(training, user_id)
            training.status = "active"
        self._record_course_entity_changes(training.id, before_course, session["course"], user_id, "start_checkin")
        self._refresh_training_histories(training_id)
        self.db.commit()
        detail = self.get_training_by_id(training_id, user_id)
        if not detail:
            raise ValueError("培训班不存在")
        return detail

    def end_session_checkin(self, training_id: int, session_key: str, user_id: int) -> TrainingResponse:
        training, session = self._load_training_session(training_id, session_key)
        self._assert_training_course_editable(training, "修改课次状态")
        if not self._can_operate_schedule(training, session["course"], session["schedule"], user_id, "end_checkin"):
            raise ValueError("当前用户无权结束该课次签到，或课次状态不允许")
        before_course = self._snapshot_course_entity(session["course"])
        session["schedule"]["status"] = self.SESSION_CHECKIN_CLOSED
        session["schedule"]["checkin_ended_at"] = datetime.now().isoformat()
        flag_modified(session["course"], "schedules")
        self._record_course_entity_changes(training.id, before_course, session["course"], user_id, "end_checkin")
        self.db.commit()
        detail = self.get_training_by_id(training_id, user_id)
        if not detail:
            raise ValueError("培训班不存在")
        return detail

    def start_session_checkout(self, training_id: int, session_key: str, user_id: int) -> TrainingResponse:
        training, session = self._load_training_session(training_id, session_key)
        self._assert_training_course_editable(training, "修改课次状态")
        if not self._can_operate_schedule(training, session["course"], session["schedule"], user_id, "start_checkout"):
            raise ValueError("当前用户无权开始该课次签退，或课次状态不允许")
        before_course = self._snapshot_course_entity(session["course"])
        session["schedule"]["status"] = self.SESSION_CHECKOUT_OPEN
        session["schedule"]["checkout_started_at"] = datetime.now().isoformat()
        flag_modified(session["course"], "schedules")
        self._record_course_entity_changes(training.id, before_course, session["course"], user_id, "start_checkout")
        self.db.commit()
        detail = self.get_training_by_id(training_id, user_id)
        if not detail:
            raise ValueError("培训班不存在")
        return detail

    def end_session_checkout(self, training_id: int, session_key: str, user_id: int) -> TrainingResponse:
        training, session = self._load_training_session(training_id, session_key)
        self._assert_training_course_editable(training, "修改课次状态")
        if not self._can_operate_schedule(training, session["course"], session["schedule"], user_id, "end_checkout"):
            raise ValueError("当前用户无权结束该课次签退，或课次状态不允许")
        before_course = self._snapshot_course_entity(session["course"])
        now = datetime.now().isoformat()
        schedule = session["schedule"]
        schedule["status"] = self.SESSION_COMPLETED
        schedule["checkout_ended_at"] = now
        schedule["ended_at"] = now
        flag_modified(session["course"], "schedules")
        self._record_course_entity_changes(training.id, before_course, session["course"], user_id, "end_checkout")
        self._sync_absent_records(training, session_key, session["date"])
        self._refresh_training_histories(training_id)
        self.db.commit()
        detail = self.get_training_by_id(training_id, user_id)
        if not detail:
            raise ValueError("培训班不存在")
        return detail

    def skip_session(self, training_id: int, session_key: str, user_id: int, note: Optional[str] = None) -> TrainingResponse:
        training, session = self._load_training_session(training_id, session_key)
        self._assert_training_course_editable(training, "修改课次状态")
        if not self._can_operate_schedule(training, session["course"], session["schedule"], user_id, "skip"):
            raise ValueError("当前用户无权跳过该课次，或课次状态不允许")
        before_course = self._snapshot_course_entity(session["course"])
        now = datetime.now().isoformat()
        schedule = session["schedule"]
        schedule["status"] = self.SESSION_SKIPPED
        schedule["skipped_at"] = now
        schedule["skipped_by"] = user_id
        schedule["skip_reason"] = note
        schedule["ended_at"] = now
        flag_modified(session["course"], "schedules")
        self._record_course_entity_changes(training.id, before_course, session["course"], user_id, "skip_session")
        self._refresh_training_histories(training_id)
        self.db.commit()
        detail = self.get_training_by_id(training_id, user_id)
        if not detail:
            raise ValueError("培训班不存在")
        return detail

    def generate_checkin_qr(
        self,
        training_id: int,
        session_key: str = "start",
        target_date: Optional[date] = None,
        user_id: Optional[int] = None,
    ) -> TrainingCheckinQrResponse:
        """生成签到二维码"""
        training = self.db.query(Training).options(
            joinedload(Training.courses),
        ).filter(Training.id == training_id).first()
        if not training:
            raise ValueError("培训班不存在")

        session = self._find_schedule_session(training, session_key)
        if not session:
            raise ValueError("课次不存在")
        if user_id and not can_operate_training_course(self.db, training, session["course"], user_id):
            raise ValueError("当前用户无权为该课次生成签到二维码")
        if (session["schedule"].get("status") or self.SESSION_PENDING) != self.SESSION_CHECKIN_OPEN:
            raise ValueError("当前课次未开启签到")

        token = str(uuid.uuid4())
        session_date = target_date or session["date"]
        expire_at = datetime.now() + timedelta(seconds=self.CHECKIN_QR_TTL_SECONDS)
        payload = {
            "training_id": training_id,
            "training_name": training.name,
            "session_key": session_key,
            "session_label": session["session_label"],
            "date": session_date.isoformat() if session_date else None,
            "expire_at": expire_at.isoformat(),
        }

        redis_client = self._get_redis_client()
        redis_client.setex(
            f"{self.CHECKIN_QR_PREFIX}{token}",
            self.CHECKIN_QR_TTL_SECONDS,
            json.dumps(payload, ensure_ascii=False),
        )

        return TrainingCheckinQrResponse(
            token=token,
            training_id=training_id,
            training_name=training.name,
            session_key=session_key,
            session_label=payload["session_label"],
            date=session_date,
            url=f"/mobile/checkin/{token}/{session_key}",
            expire_at=expire_at,
            expires_in_seconds=self.CHECKIN_QR_TTL_SECONDS,
        )

    def get_checkin_qr_payload(self, token: str) -> Optional[TrainingCheckinQrResponse]:
        """获取扫码签到载荷"""
        payload = self._load_checkin_qr_payload(token)
        if not payload:
            return None

        raw_date = payload.get("date")
        raw_expire_at = payload.get("expire_at")
        return TrainingCheckinQrResponse(
            token=token,
            training_id=int(payload["training_id"]),
            training_name=str(payload["training_name"]),
            session_key=str(payload["session_key"]),
            session_label=str(payload["session_label"]),
            date=date.fromisoformat(raw_date) if raw_date else None,
            url=f"/mobile/checkin/{token}/{payload['session_key']}",
            expire_at=datetime.fromisoformat(raw_expire_at) if raw_expire_at else datetime.now(),
            expires_in_seconds=max(0, self._get_redis_client().ttl(f"{self.CHECKIN_QR_PREFIX}{token}")),
        )

    def checkin_by_qr(self, token: str, user_id: int) -> CheckinResponse:
        """通过二维码签到"""
        payload = self._load_checkin_qr_payload(token)
        if not payload:
            raise ValueError("签到二维码不存在或已失效")

        raw_date = payload.get("date")
        return self.checkin(
            int(payload["training_id"]),
            user_id,
            CheckinCreate(
                session_key=str(payload["session_key"]),
                date=date.fromisoformat(raw_date) if raw_date else None,
            ),
        )

    def get_training_histories(
        self,
        training_id: int,
        user_id: Optional[int] = None,
    ) -> List[TrainingHistoryResponse]:
        """获取培训训历"""
        self._refresh_training_histories(training_id, [user_id] if user_id else None)
        self.db.commit()

        query = self.db.query(TrainingHistory).options(
            joinedload(TrainingHistory.user).joinedload(User.departments),
        ).filter(TrainingHistory.training_id == training_id)
        if user_id:
            query = query.filter(TrainingHistory.user_id == user_id)

        rows = query.order_by(TrainingHistory.archived_at.desc(), TrainingHistory.id.desc()).all()
        return [self._history_to_response(row) for row in rows]

    def get_training_course_change_logs(self, training_id: int) -> List[TrainingCourseChangeLogResponse]:
        rows = self.db.query(TrainingCourseChangeLog).options(
            joinedload(TrainingCourseChangeLog.actor),
        ).filter(
            TrainingCourseChangeLog.training_id == training_id,
        ).order_by(
            TrainingCourseChangeLog.created_at.desc(),
            TrainingCourseChangeLog.id.desc(),
        ).all()
        return [self._course_change_log_to_response(row) for row in rows]

    def get_user_training_histories(self, user_id: int) -> List[TrainingHistoryResponse]:
        """获取某个学员的训历档案"""
        rows = self.db.query(TrainingHistory).options(
            joinedload(TrainingHistory.user).joinedload(User.departments),
        ).filter(
            TrainingHistory.user_id == user_id,
        ).order_by(TrainingHistory.archived_at.desc(), TrainingHistory.id.desc()).all()
        return [self._history_to_response(row) for row in rows]

    def add_training_resource(self, training_id: int, data: TrainingResourceBindRequest) -> ResourceListItemResponse:
        training = self.db.query(Training).filter(Training.id == training_id).first()
        if not training:
            raise ValueError("培训班不存在")

        resource = self.db.query(Resource).options(
            joinedload(Resource.uploader),
            joinedload(Resource.owner_department),
            joinedload(Resource.cover_media),
            joinedload(Resource.tag_relations).joinedload(ResourceTagRelation.tag),
        ).filter(Resource.id == data.resource_id).first()
        if not resource:
            raise ValueError("资源不存在")

        ref = self.db.query(TrainingResourceRef).filter(
            TrainingResourceRef.training_id == training_id,
            TrainingResourceRef.resource_id == data.resource_id,
        ).first()
        if not ref:
            ref = TrainingResourceRef(
                training_id=training_id,
                resource_id=data.resource_id,
                usage_type=data.usage_type,
                sort_order=data.sort_order,
            )
            self.db.add(ref)
        else:
            ref.usage_type = data.usage_type
            ref.sort_order = data.sort_order

        self.db.commit()
        return self._resource_to_response(resource)

    def list_training_resources(self, training_id: int) -> List[ResourceListItemResponse]:
        refs = self.db.query(TrainingResourceRef).options(
            joinedload(TrainingResourceRef.resource).joinedload(Resource.uploader),
            joinedload(TrainingResourceRef.resource).joinedload(Resource.owner_department),
            joinedload(TrainingResourceRef.resource).joinedload(Resource.cover_media),
            joinedload(TrainingResourceRef.resource).joinedload(Resource.tag_relations).joinedload(ResourceTagRelation.tag),
        ).filter(
            TrainingResourceRef.training_id == training_id,
        ).order_by(
            TrainingResourceRef.sort_order.asc(),
            TrainingResourceRef.id.asc(),
        ).all()

        items = []
        for ref in refs:
            if ref.resource:
                items.append(self._resource_to_response(ref.resource))
        return items

    def remove_training_resource(self, training_id: int, resource_id: int) -> bool:
        ref = self.db.query(TrainingResourceRef).filter(
            TrainingResourceRef.training_id == training_id,
            TrainingResourceRef.resource_id == resource_id,
        ).first()
        if not ref:
            return False
        self.db.delete(ref)
        self.db.commit()
        return True

    def _replace_courses(self, training_id: int, courses: List[Any]) -> None:
        self.db.query(TrainingCourse).filter(
            TrainingCourse.training_id == training_id,
        ).delete(synchronize_session=False)

        for course in courses:
            payload = self._normalize_course_payload(course)
            self.db.add(TrainingCourse(
                training_id=training_id,
                course_key=payload.get("course_key"),
                name=payload["name"],
                location=payload.get("location"),
                instructor=payload.get("instructor"),
                primary_instructor_id=payload.get("primary_instructor_id"),
                assistant_instructor_ids=payload.get("assistant_instructor_ids") or [],
                hours=payload.get("hours") or 0,
                type=payload.get("type") or "theory",
                schedules=payload.get("schedules") or [],
            ))

    def _normalize_course_payload(self, course: Any) -> Dict[str, Any]:
        payload = course.model_dump() if hasattr(course, "model_dump") else dict(course)
        course_key = str(payload.get("course_key") or payload.get("courseKey") or "").strip() or str(uuid.uuid4())
        primary_instructor_id = payload.get("primary_instructor_id") or payload.get("primaryInstructorId")
        course_location = self._normalize_optional_text(payload.get("location"))
        instructor_name = (payload.get("instructor") or "").strip() or None
        if not primary_instructor_id and instructor_name:
            primary_instructor_id = self._guess_primary_instructor_id(instructor_name)
        if primary_instructor_id and not instructor_name:
            instructor_name = self._resolve_user_name(primary_instructor_id)

        assistant_instructor_ids = []
        for raw_id in (payload.get("assistant_instructor_ids") or payload.get("assistantInstructorIds") or []):
            if raw_id is None:
                continue
            assistant_instructor_ids.append(int(raw_id))

        schedules = [
            self._normalize_schedule_item(item)
            for item in (payload.get("schedules") or [])
        ]
        schedules.sort(key=lambda item: (item.get("date") or "", item.get("time_range") or ""))
        planned_hours = self._normalize_course_hours(payload.get("hours"))

        return {
            "course_key": course_key,
            "name": payload["name"],
            "location": course_location,
            "instructor": instructor_name,
            "primary_instructor_id": primary_instructor_id,
            "assistant_instructor_ids": sorted(set(assistant_instructor_ids)),
            "hours": planned_hours if planned_hours is not None else 0,
            "type": payload.get("type") or "theory",
            "schedules": schedules,
        }

    def _load_training_courses(self, training_id: int) -> List[TrainingCourse]:
        courses = self.db.query(TrainingCourse).options(
            joinedload(TrainingCourse.primary_instructor),
        ).filter(
            TrainingCourse.training_id == training_id,
        ).order_by(
            TrainingCourse.id.asc(),
        ).all()
        self.course_change_service.ensure_course_keys(courses)
        return courses

    def _snapshot_course_entity(self, course: TrainingCourse) -> Dict[str, Any]:
        self.course_change_service.ensure_course_keys([course])
        return self.course_change_service.snapshot_course_entities([course])[0]

    def _record_course_entity_changes(
        self,
        training_id: int,
        before_course: Dict[str, Any],
        after_course: TrainingCourse,
        actor_id: Optional[int],
        source: str,
    ) -> None:
        self.course_change_service.ensure_course_keys([after_course])
        self.course_change_service.record_changes(
            training_id,
            [before_course],
            [after_course],
            actor_id,
            source,
        )

    def _assert_training_course_editable(self, training: Training, action_text: str) -> None:
        if (training.status or "upcoming") == "ended":
            raise ValueError(f"已结班的培训班不能再{action_text}")

    @staticmethod
    def _normalize_optional_text(value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _normalize_course_hours(value: Any) -> Optional[float]:
        if value in (None, ""):
            return None
        try:
            return round(max(float(value), 0), 2)
        except (TypeError, ValueError):
            return None

    def _normalize_schedule_item(self, item: Any) -> Dict[str, Any]:
        raw = item.model_dump() if hasattr(item, "model_dump") else dict(item)
        raw_date = raw.get("date")
        if isinstance(raw_date, date):
            raw_date = raw_date.isoformat()
        return {
            "session_id": raw.get("session_id") or raw.get("sessionId") or str(uuid.uuid4()),
            "date": raw_date,
            "time_range": raw.get("time_range") or raw.get("timeRange") or "",
            "hours": float(raw.get("hours", 0) or 0),
            "location": self._normalize_optional_text(raw.get("location")),
            "status": raw.get("status") or self.SESSION_PENDING,
            "started_at": self._serialize_dt(raw.get("started_at") or raw.get("startedAt")),
            "checkin_started_at": self._serialize_dt(raw.get("checkin_started_at") or raw.get("checkinStartedAt")),
            "checkin_ended_at": self._serialize_dt(raw.get("checkin_ended_at") or raw.get("checkinEndedAt")),
            "checkout_started_at": self._serialize_dt(raw.get("checkout_started_at") or raw.get("checkoutStartedAt")),
            "checkout_ended_at": self._serialize_dt(raw.get("checkout_ended_at") or raw.get("checkoutEndedAt")),
            "ended_at": self._serialize_dt(raw.get("ended_at") or raw.get("endedAt")),
            "skipped_at": self._serialize_dt(raw.get("skipped_at") or raw.get("skippedAt")),
            "skipped_by": raw.get("skipped_by") or raw.get("skippedBy"),
            "skip_reason": raw.get("skip_reason") or raw.get("skipReason"),
        }

    def _serialize_dt(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def _resolve_schedule_deadline_from_item(self, schedule: Dict[str, Any]) -> Optional[datetime]:
        schedule_date = self._parse_schedule_date(schedule)
        if not schedule_date:
            return None
        _, time_end = self._parse_time_range(schedule.get("time_range"))
        if time_end:
            return datetime.combine(schedule_date, time_end)
        return datetime.combine(schedule_date, time(23, 59))

    def _get_schedule_edit_lock_reason(self, training: Training, schedule: Dict[str, Any]) -> Optional[str]:
        if (training.status or "upcoming") == "ended":
            return "training_ended"

        status = schedule.get("status") or self.SESSION_PENDING
        if status != self.SESSION_PENDING:
            return "status_locked"

        deadline = self._resolve_schedule_deadline_from_item(schedule)
        if deadline is None:
            return "invalid_time"

        now = self._current_time(deadline)
        normalized_deadline = self._normalize_datetime(deadline, now.tzinfo)
        if not normalized_deadline:
            return "invalid_time"
        if now > normalized_deadline:
            return "expired"
        return None

    def _get_schedule_status_label(self, status: Optional[str]) -> str:
        normalized_status = status or self.SESSION_PENDING
        return self.SESSION_STATUS_LABELS.get(normalized_status, normalized_status)

    def _build_schedule_edit_block_message(
        self,
        training: Training,
        course_name: str,
        schedule: Dict[str, Any],
        action: str,
    ) -> str:
        reason = self._get_schedule_edit_lock_reason(training, schedule)
        schedule_label = self._format_schedule_label(schedule)
        if reason == "training_ended":
            return f"培训班已结班，不能{action}课次：{course_name} {schedule_label}"
        if reason == "status_locked":
            status_label = self._get_schedule_status_label(schedule.get("status"))
            return f"课次已进入“{status_label}”状态，不能{action}：{course_name} {schedule_label}"
        if reason == "invalid_time":
            return f"课次时间无效，不能{action}：{course_name} {schedule_label}"
        return f"已过课次结束时间，不能{action}：{course_name} {schedule_label}"

    def _is_schedule_editable(self, training: Training, schedule: Dict[str, Any]) -> bool:
        return self._get_schedule_edit_lock_reason(training, schedule) is None

    def _is_schedule_expired(self, training: Training, schedule: Dict[str, Any]) -> bool:
        if (training.status or "upcoming") == "ended":
            return True
        deadline = self._resolve_schedule_deadline_from_item(schedule)
        if deadline is None:
            return True
        now = self._current_time(deadline)
        normalized_deadline = self._normalize_datetime(deadline, now.tzinfo)
        return not bool(normalized_deadline and now <= normalized_deadline)

    @staticmethod
    def _format_schedule_label(schedule: Dict[str, Any]) -> str:
        return f"{schedule.get('date') or '-'} {schedule.get('time_range') or '-'}"

    def _build_schedule_response_item(
        self,
        training: Training,
        course: TrainingCourse,
        item: Any,
    ) -> Dict[str, Any]:
        schedule = self._normalize_schedule_item(item)
        edit_lock_reason = self._get_schedule_edit_lock_reason(training, schedule)
        can_edit = edit_lock_reason is None
        return {
            **schedule,
            "location": schedule.get("location") or course.location,
            "is_expired": self._is_schedule_expired(training, schedule),
            "can_edit": can_edit,
            "can_delete": can_edit,
            "edit_lock_reason": edit_lock_reason,
            "edit_lock_message": None if can_edit else self._build_schedule_edit_block_message(training, course.name, schedule, "编辑"),
            "delete_lock_message": None if can_edit else self._build_schedule_edit_block_message(training, course.name, schedule, "删除"),
        }

    def _validate_schedule_mutation_window(
        self,
        training: Training,
        before_courses: List[Dict[str, Any]],
        after_courses: List[Dict[str, Any]],
    ) -> None:
        before_map = {item.get("course_key"): item for item in before_courses or [] if item.get("course_key")}
        after_map = {item.get("course_key"): item for item in after_courses or [] if item.get("course_key")}

        for after_course in after_courses or []:
            course_name = after_course.get("name") or "未命名课程"
            before_course = before_map.get(after_course.get("course_key"))
            before_schedule_ids = {
                item.get("session_id")
                for item in (before_course or {}).get("schedules", [])
                if item.get("session_id")
            }
            for after_schedule in after_course.get("schedules", []) or []:
                session_id = after_schedule.get("session_id")
                if session_id in before_schedule_ids:
                    continue
                if not self._is_schedule_editable(training, after_schedule):
                    raise ValueError(self._build_schedule_edit_block_message(training, course_name, after_schedule, "新增"))

        for before_course in before_courses or []:
            course_name = before_course.get("name") or "未命名课程"
            immutable_schedules = [
                item for item in (before_course.get("schedules") or [])
                if not self._is_schedule_editable(training, item)
            ]
            if not immutable_schedules:
                continue
            after_course = after_map.get(before_course.get("course_key"))
            if after_course is None:
                raise ValueError(self._build_schedule_edit_block_message(training, course_name, immutable_schedules[0], "删除"))

            after_schedule_map = {
                item.get("session_id"): item
                for item in (after_course.get("schedules") or [])
                if item.get("session_id")
            }
            for before_schedule in immutable_schedules:
                session_id = before_schedule.get("session_id")
                after_schedule = after_schedule_map.get(session_id)
                if after_schedule is None:
                    raise ValueError(self._build_schedule_edit_block_message(training, course_name, before_schedule, "删除"))
                if after_schedule != before_schedule:
                    raise ValueError(self._build_schedule_edit_block_message(training, course_name, before_schedule, "编辑"))

    def _guess_primary_instructor_id(self, instructor_name: str) -> Optional[int]:
        user = self.db.query(User).filter(
            (User.nickname == instructor_name) | (User.username == instructor_name)
        ).first()
        return user.id if user else None

    def _resolve_user_name(self, user_id: Optional[int]) -> Optional[str]:
        if not user_id:
            return None
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        return user.nickname or user.username

    def _sync_student_ids(self, training: Training, student_ids: List[int]) -> List[int]:
        wanted_ids = {int(user_id) for user_id in student_ids}
        existing_enrollments = list(training.enrollments or [])
        existing_user_ids = {row.user_id for row in existing_enrollments}
        changed_user_ids: List[int] = []

        for enrollment in existing_enrollments:
            if enrollment.user_id in wanted_ids:
                if enrollment.status != "approved":
                    enrollment.status = "approved"
                    enrollment.approved_at = self._current_time(
                        enrollment.enroll_time,
                        enrollment.approved_at,
                        enrollment.reviewed_at,
                    )
                    changed_user_ids.append(enrollment.user_id)
            elif enrollment.status == "approved":
                enrollment.status = "rejected"
                enrollment.note = enrollment.note or "名单调整移除"
                changed_user_ids.append(enrollment.user_id)

        for user_id in wanted_ids - existing_user_ids:
            self.db.add(Enrollment(
                training_id=training.id,
                user_id=user_id,
                status="approved",
                note="详情页配置学员",
                approved_at=self._current_time(training.published_at, training.locked_at),
            ))
            changed_user_ids.append(user_id)

        return changed_user_ids

    def _apply_roster_assignments(self, training_id: int, assignments: List[Any]) -> List[int]:
        changed_user_ids: List[int] = []
        for item in assignments:
            payload = item.model_dump() if hasattr(item, "model_dump") else dict(item)
            enrollment = self.db.query(Enrollment).filter(
                Enrollment.training_id == training_id,
                Enrollment.id == payload["enrollment_id"],
                Enrollment.status == "approved",
            ).first()
            if not enrollment:
                continue
            enrollment.group_name = payload.get("group_name") or None
            enrollment.cadre_role = payload.get("cadre_role") or None
            changed_user_ids.append(enrollment.user_id)
        return changed_user_ids

    def _bind_admission_exam(self, training: Training, exam_id: int) -> None:
        exam = self.db.query(AdmissionExam).filter(AdmissionExam.id == exam_id).first()
        if not exam:
            raise ValueError("准入考试不存在")
        training.admission_exam_id = exam_id

    def _ensure_department(self, department_id: Optional[int]) -> Optional[Department]:
        if not department_id:
            return None
        department = self.db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise ValueError("部门不存在")
        return department

    def _ensure_police_type(self, police_type_id: Optional[int]) -> Optional[PoliceType]:
        if not police_type_id:
            return None
        police_type = self.db.query(PoliceType).filter(PoliceType.id == police_type_id).first()
        if not police_type:
            raise ValueError("警种不存在")
        return police_type

    def _ensure_training_base(self, training_base_id: Optional[int]) -> Optional[TrainingBase]:
        if not training_base_id:
            return None
        training_base = self.db.query(TrainingBase).filter(TrainingBase.id == training_base_id).first()
        if not training_base:
            raise ValueError("培训基地不存在")
        return training_base

    def _apply_training_domain_fields(
        self,
        training: Training,
        *,
        location: Any = _UNSET,
        department_id: Any = _UNSET,
        police_type_id: Any = _UNSET,
        training_base_id: Any = _UNSET,
    ) -> None:
        base = training.training_base
        base_changed = training_base_id is not _UNSET
        if base_changed:
            base = self._ensure_training_base(training_base_id)
            training.training_base_id = training_base_id
            training.training_base = base

        if police_type_id is not _UNSET:
            self._ensure_police_type(police_type_id)
            training.police_type_id = police_type_id

        if location is not _UNSET:
            training.location = location or (base.location if base else None)
        elif base_changed and base and not training.location:
            training.location = base.location

        if department_id is not _UNSET:
            self._ensure_department(department_id)
            training.department_id = department_id
        elif base_changed:
            training.department_id = base.department_id if base and base.department_id else None

    def _ensure_actor_can_assign_training_scope(
        self,
        user_id: int,
        department_id: Optional[int],
        police_type_id: Optional[int],
    ) -> None:
        context = build_data_scope_context(self.db, user_id)
        if not can_assign_scoped_values(
            context,
            department_id=department_id,
            police_type_id=police_type_id,
            dimension_mode="all",
            treat_missing_as_unrestricted=True,
        ):
            raise ValueError("超出当前角色可操作的数据范围")

    def _ensure_training_member(self, training_id: int, user_id: int) -> None:
        enrollment = self.db.query(Enrollment.id).filter(
            Enrollment.training_id == training_id,
            Enrollment.user_id == user_id,
            Enrollment.status == "approved",
        ).first()
        if not enrollment:
            raise ValueError("当前用户未被录取到该培训班")

    def _build_profile_snapshot(self, user: Optional[User]) -> Dict[str, Any]:
        if not user:
            return {}
        return {
            "username": user.username,
            "nickname": user.nickname,
            "police_id": user.police_id,
            "phone": user.phone,
            "departments": [department.name for department in (user.departments or [])],
        }

    def _get_redis_client(self):
        try:
            return get_redis()
        except Exception as exc:
            logger.error("获取签到二维码缓存失败: %s", exc)
            raise ValueError("Redis 不可用，暂时无法处理扫码签到")

    def _load_checkin_qr_payload(self, token: str) -> Optional[Dict[str, Any]]:
        cache_value = self._get_redis_client().get(f"{self.CHECKIN_QR_PREFIX}{token}")
        if not cache_value:
            return None
        return json.loads(cache_value)

    def _get_session_label(self, training: Training, session_key: str) -> str:
        session = self._find_schedule_session(training, session_key)
        if session:
            return session["session_label"]
        return session_key

    def _build_session_catalog(self, training: Training) -> List[Dict[str, Any]]:
        self._refresh_schedule_states(training)
        catalog: List[Dict[str, Any]] = []
        for course in training.courses or []:
            normalized_schedules = [self._normalize_schedule_item(item) for item in (course.schedules or [])]
            if normalized_schedules != (course.schedules or []):
                course.schedules = normalized_schedules
            schedules = course.schedules or []
            for schedule in schedules:
                schedule_date = self._parse_schedule_date(schedule)
                if not schedule_date:
                    continue
                time_start, time_end = self._parse_time_range(schedule.get("time_range"))
                catalog.append({
                    "session_key": schedule["session_id"],
                    "session_id": schedule["session_id"],
                    "session_label": f"{course.name} ({schedule.get('date') or '-'} {schedule.get('time_range') or '-'})",
                    "course": course,
                    "schedule": schedule,
                    "date": schedule_date,
                    "time_start": time_start,
                    "time_end": time_end,
                    "status": schedule.get("status") or self.SESSION_PENDING,
                })
        catalog.sort(key=lambda item: (item["date"], item["time_start"] or time(0, 0), item["session_key"]))
        return catalog

    def _resolve_session_date(self, training: Training, session_key: str, fallback: date) -> date:
        session = self._find_schedule_session(training, session_key)
        if session:
            return session["date"]
        return fallback

    def _resolve_session_deadline(self, training: Training, session_key: str, target_date: date) -> datetime:
        session = self._find_schedule_session(training, session_key)
        if session:
            if session["time_end"]:
                return datetime.combine(target_date, session["time_end"])
            return datetime.combine(target_date, time(23, 59))
        return datetime.combine(target_date, time(23, 59))

    def _resolve_checkin_status(self, training: Training, session_key: str, checkin_date: date, checkin_time: str) -> str:
        try:
            actual_time = datetime.strptime(checkin_time, "%H:%M").time()
        except ValueError:
            return "on_time"

        session = self._find_schedule_session(training, session_key)
        if session and session["date"] == checkin_date and session["time_start"]:
            scheduled_dt = datetime.combine(checkin_date, session["time_start"])
            actual_dt = datetime.combine(checkin_date, actual_time)
            if actual_dt > scheduled_dt + timedelta(minutes=15):
                return "late"
        return "on_time"

    def _sync_absent_records(self, training: Training, session_key: str, target_date: Optional[date]) -> None:
        session = self._find_schedule_session(training, session_key)
        if not session:
            return
        if session["status"] == self.SESSION_SKIPPED:
            return

        session_date = target_date or session["date"]
        deadline = self._resolve_session_deadline(training, session_key, session_date)
        now = self._current_time(deadline)
        normalized_deadline = self._normalize_datetime(deadline, now.tzinfo)
        if (
            normalized_deadline
            and session["status"] not in {self.SESSION_COMPLETED, self.SESSION_MISSED}
            and now < normalized_deadline
        ):
            return

        approved_user_ids = [
            enrollment.user_id
            for enrollment in (training.enrollments or [])
            if enrollment.status == "approved"
        ]
        if not approved_user_ids:
            return

        existing_records = self.db.query(CheckinRecord).filter(
            CheckinRecord.training_id == training.id,
            CheckinRecord.date == session_date,
            CheckinRecord.session_key == session_key,
            CheckinRecord.user_id.in_(approved_user_ids),
        ).all()
        existing_map = {record.user_id: record for record in existing_records}

        inserted = False
        for user_id in approved_user_ids:
            if user_id in existing_map:
                continue
            self.db.add(CheckinRecord(
                training_id=training.id,
                user_id=user_id,
                date=session_date,
                session_key=session_key,
                status="absent",
                absence_reason="系统自动补记缺勤",
            ))
            inserted = True

        if inserted:
            self.db.flush()

    def _parse_schedule_date(self, schedule: Dict[str, Any]) -> Optional[date]:
        raw_date = schedule.get("date")
        if not raw_date:
            return None
        if isinstance(raw_date, date):
            return raw_date
        try:
            return date.fromisoformat(str(raw_date))
        except ValueError:
            return None

    def _parse_schedule_datetime(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            return None

    def _refresh_schedule_states(self, training: Training) -> bool:
        self.course_change_service.ensure_course_keys(training.courses or [])
        before_courses = self.course_change_service.snapshot_course_entities(training.courses or [])
        deadline_references: List[datetime] = []
        for course in training.courses or []:
            for item in course.schedules or []:
                schedule = self._normalize_schedule_item(item)
                schedule_date = self._parse_schedule_date(schedule)
                _, time_end = self._parse_time_range(schedule.get("time_range"))
                if schedule_date:
                    deadline_references.append(datetime.combine(schedule_date, time_end or time(23, 59)))
        now = self._current_time(*deadline_references)
        changed = False
        for course in training.courses or []:
            normalized: List[Dict[str, Any]] = []
            for item in course.schedules or []:
                schedule = self._normalize_schedule_item(item)
                session_date = self._parse_schedule_date(schedule)
                _, time_end = self._parse_time_range(schedule.get("time_range"))
                deadline = datetime.combine(session_date, time_end or time(23, 59)) if session_date else None
                normalized_deadline = self._normalize_datetime(deadline, now.tzinfo)
                if (
                    normalized_deadline
                    and now > normalized_deadline
                    and schedule.get("status") in {
                        self.SESSION_PENDING,
                        self.SESSION_CHECKIN_OPEN,
                        self.SESSION_CHECKIN_CLOSED,
                        self.SESSION_CHECKOUT_OPEN,
                    }
                ):
                    schedule["status"] = self.SESSION_MISSED
                normalized.append(schedule)
            if normalized != (course.schedules or []):
                course.schedules = normalized
                changed = True
        if changed:
            after_courses = self.course_change_service.snapshot_course_entities(training.courses or [])
            self.course_change_service.record_changes(
                training.id,
                before_courses,
                after_courses,
                None,
                "system_refresh",
            )
        return changed

    def _find_schedule_session(self, training: Training, session_key: str) -> Optional[Dict[str, Any]]:
        for item in self._build_session_catalog(training):
            if item["session_key"] == session_key:
                return item
        return None

    def _get_current_session(self, training: Training) -> Optional[Dict[str, Any]]:
        catalog = self._build_session_catalog(training)
        active_statuses = {
            self.SESSION_CHECKIN_OPEN,
            self.SESSION_CHECKIN_CLOSED,
            self.SESSION_CHECKOUT_OPEN,
        }
        for item in catalog:
            if item["status"] in active_statuses:
                return item
        for item in catalog:
            if item["status"] != self.SESSION_PENDING:
                continue
            deadline = self._resolve_session_deadline(training, item["session_key"], item["date"])
            now = self._current_time(deadline)
            normalized_deadline = self._normalize_datetime(deadline, now.tzinfo)
            if normalized_deadline and now <= normalized_deadline:
                return item
        return None

    def _build_workflow_steps(self, training: Training) -> List[TrainingWorkflowStepResponse]:
        if training.status == "ended":
            current = "completed"
        elif training.status == "active":
            current = "running"
        elif training.locked_at:
            current = "locked"
        elif training.publish_status == "published":
            current = "published"
        else:
            current = "draft"

        step_order = ["draft", "published", "locked", "running", "completed"]
        current_index = step_order.index(current)
        display_index = current_index + 1 if current_index < step_order.index("running") else current_index
        steps = []
        labels = {
            "draft": "草稿",
            "published": "发布招生",
            "locked": "锁定名单",
            "running": "开班进行中",
            "completed": "结班归档",
        }
        for index, key in enumerate(step_order):
            status = "wait"
            if index < display_index:
                status = "finish"
            elif index == display_index:
                status = "process"
            steps.append(TrainingWorkflowStepResponse(
                key=key,
                title=labels[key],
                status=status,
            ))
        return steps

    def _can_operate_schedule(
        self,
        training: Training,
        course: TrainingCourse,
        schedule: Dict[str, Any],
        user_id: int,
        action: str,
    ) -> bool:
        if not can_operate_training_course(self.db, training, course, user_id):
            return False
        session = self._find_schedule_session(training, schedule["session_id"])
        if not session:
            return False
        deadline = self._resolve_session_deadline(training, schedule["session_id"], session["date"])
        now = self._current_time(deadline)
        normalized_deadline = self._normalize_datetime(deadline, now.tzinfo)
        status = schedule.get("status") or self.SESSION_PENDING
        if action in {"start_checkin", "skip"}:
            return bool(normalized_deadline and status == self.SESSION_PENDING and now <= normalized_deadline)
        if action == "end_checkin":
            return status == self.SESSION_CHECKIN_OPEN
        if action == "start_checkout":
            return status == self.SESSION_CHECKIN_CLOSED
        if action == "end_checkout":
            return status == self.SESSION_CHECKOUT_OPEN
        return False

    def _load_training_session(self, training_id: int, session_key: str) -> tuple[Training, Dict[str, Any]]:
        training = self.db.query(Training).options(
            joinedload(Training.instructor),
            joinedload(Training.courses).joinedload(TrainingCourse.primary_instructor),
            joinedload(Training.enrollments),
        ).filter(Training.id == training_id).first()
        if not training:
            raise ValueError("培训班不存在")
        session = self._find_schedule_session(training, session_key)
        if not session:
            raise ValueError("课次不存在")
        return training, session

    def can_user_operate_session(self, training_id: int, session_key: str, user_id: int) -> bool:
        try:
            training, session = self._load_training_session(training_id, session_key)
        except ValueError:
            return False
        return can_operate_training_course(self.db, training, session["course"], user_id)

    def _refresh_training_histories(self, training_id: int, user_ids: Optional[List[int]] = None) -> None:
        training = self.db.query(Training).options(
            joinedload(Training.courses),
            joinedload(Training.enrollments),
        ).filter(Training.id == training_id).first()
        if not training:
            return

        approved_enrollments = [
            enrollment
            for enrollment in (training.enrollments or [])
            if enrollment.status == "approved" and (not user_ids or enrollment.user_id in user_ids)
        ]
        if not approved_enrollments:
            return

        session_catalog = [
            item for item in self._build_session_catalog(training)
            if item["status"] != self.SESSION_SKIPPED
        ]
        total_sessions = len(session_catalog)

        for enrollment in approved_enrollments:
            records = self.db.query(CheckinRecord).filter(
                CheckinRecord.training_id == training_id,
                CheckinRecord.user_id == enrollment.user_id,
            ).all()
            attended = sum(1 for record in records if record.status in {"on_time", "late"})
            evaluation_scores = [record.evaluation_score for record in records if record.evaluation_score is not None]
            passed_exam_count = self.db.query(ExamRecord.id).join(
                Exam, Exam.id == ExamRecord.exam_id,
            ).filter(
                Exam.training_id == training_id,
                ExamRecord.user_id == enrollment.user_id,
                ExamRecord.result == "pass",
                ExamRecord.status == "submitted",
            ).count()

            attendance_rate = round((attended / total_sessions) * 100, 1) if total_sessions else 0
            evaluation_score = round(sum(evaluation_scores) / len(evaluation_scores), 1) if evaluation_scores else 0

            history = self.db.query(TrainingHistory).filter(
                TrainingHistory.training_id == training_id,
                TrainingHistory.user_id == enrollment.user_id,
            ).first()
            if not history:
                history = TrainingHistory(
                    training_id=training_id,
                    user_id=enrollment.user_id,
                )
                self.db.add(history)

            history.training_name = training.name
            history.training_type = training.type
            history.status = training.status or "upcoming"
            history.start_date = training.start_date
            history.end_date = training.end_date
            history.attendance_rate = attendance_rate
            history.completed_sessions = attended
            history.total_sessions = total_sessions
            history.evaluation_score = evaluation_score
            history.passed_exam_count = passed_exam_count
            history.archived_at = datetime.now()
            history.summary = {
                "group_name": enrollment.group_name,
                "cadre_role": enrollment.cadre_role,
                "need_accommodation": enrollment.need_accommodation,
            }
            enrollment.archived_at = datetime.now()

    def _resolve_department_names(self, department_ids: Optional[List[int]]) -> Optional[List[str]]:
        if not department_ids:
            return None
        from app.models import Department
        rows = self.db.query(Department.id, Department.name).filter(
            Department.id.in_(department_ids)
        ).all()
        name_map = {row.id: row.name for row in rows}
        return [name_map.get(did, str(did)) for did in department_ids if did in name_map]

    def _load_user_name_map(self, user_ids: List[int]) -> Dict[int, str]:
        wanted_ids = sorted({int(user_id) for user_id in user_ids if user_id})
        if not wanted_ids:
            return {}
        rows = self.db.query(User).filter(User.id.in_(wanted_ids)).all()
        return {row.id: (row.nickname or row.username) for row in rows}

    def _build_course_response(
        self,
        training: Training,
        course: TrainingCourse,
        user_name_map: Dict[int, str],
    ) -> TrainingCourseResponse:
        assistant_ids = [int(item) for item in (course.assistant_instructor_ids or []) if item is not None]
        schedules = [self._build_schedule_response_item(training, course, item) for item in (course.schedules or [])]
        return TrainingCourseResponse(
            id=course.id,
            training_id=course.training_id,
            course_key=course.course_key,
            name=course.name,
            location=course.location,
            instructor=course.instructor,
            primary_instructor_id=course.primary_instructor_id,
            primary_instructor_name=user_name_map.get(course.primary_instructor_id),
            assistant_instructor_ids=assistant_ids,
            assistant_instructor_names=[user_name_map[item] for item in assistant_ids if item in user_name_map],
            hours=float(course.hours or 0),
            type=course.type or "theory",
            schedules=schedules,
        )

    def _build_session_action_permissions(
        self,
        training: Training,
        session: Dict[str, Any],
        current_user_id: Optional[int],
    ) -> TrainingSessionActionPermissions:
        if not current_user_id:
            return TrainingSessionActionPermissions()
        course = session["course"]
        schedule = session["schedule"]
        return TrainingSessionActionPermissions(
            can_start_checkin=self._can_operate_schedule(training, course, schedule, current_user_id, "start_checkin"),
            can_end_checkin=self._can_operate_schedule(training, course, schedule, current_user_id, "end_checkin"),
            can_start_checkout=self._can_operate_schedule(training, course, schedule, current_user_id, "start_checkout"),
            can_end_checkout=self._can_operate_schedule(training, course, schedule, current_user_id, "end_checkout"),
            can_skip=self._can_operate_schedule(training, course, schedule, current_user_id, "skip"),
        )

    def _build_current_session_response(
        self,
        training: Training,
        current_user_id: Optional[int],
    ) -> Optional[TrainingCurrentSessionResponse]:
        session = self._get_current_session(training)
        if not session:
            return None
        course = session["course"]
        user_ids = [course.primary_instructor_id, *(course.assistant_instructor_ids or [])]
        user_name_map = self._load_user_name_map([item for item in user_ids if item])
        assistant_ids = [int(item) for item in (course.assistant_instructor_ids or []) if item is not None]
        return TrainingCurrentSessionResponse(
            course_id=course.id,
            course_name=course.name,
            session_id=session["session_id"],
            session_label=session["session_label"],
            date=session["date"],
            time_range=session["schedule"].get("time_range") or "",
            status=session["status"],
            location=session["schedule"].get("location") or course.location,
            primary_instructor_id=course.primary_instructor_id,
            primary_instructor_name=user_name_map.get(course.primary_instructor_id),
            assistant_instructor_ids=assistant_ids,
            assistant_instructor_names=[user_name_map[item] for item in assistant_ids if item in user_name_map],
            action_permissions=self._build_session_action_permissions(training, session, current_user_id),
        )

    def _resolve_current_step_key(self, training: Training) -> str:
        if training.status == "ended":
            return "completed"
        if training.status == "active":
            return "running"
        if training.locked_at:
            return "locked"
        if training.publish_status == "published":
            return "published"
        return "draft"

    @staticmethod
    def _resolve_current_enrollment(training: Training, current_user_id: Optional[int]) -> Optional[Enrollment]:
        if not current_user_id:
            return None
        for enrollment in training.enrollments or []:
            if enrollment.user_id == current_user_id:
                return enrollment
        return None

    def _to_response(self, training: Training, current_user_id: Optional[int] = None) -> TrainingResponse:
        self.course_change_service.ensure_course_keys(training.courses or [])
        approved_enrollments = [item for item in (training.enrollments or []) if item.status == "approved"]
        student_ids = [item.user_id for item in approved_enrollments]
        group_names = sorted({item.group_name for item in approved_enrollments if item.group_name})
        cadre_count = sum(1 for item in approved_enrollments if item.cadre_role)
        instructor_ids = []
        for course in training.courses or []:
            if course.primary_instructor_id:
                instructor_ids.append(course.primary_instructor_id)
            instructor_ids.extend(int(item) for item in (course.assistant_instructor_ids or []) if item is not None)
        user_name_map = self._load_user_name_map(instructor_ids)
        courses = [self._build_course_response(training, item, user_name_map) for item in (training.courses or [])]

        exam_sessions = []
        for session in (training.exam_sessions or []):
            if (session.purpose or "class_assessment") == "admission":
                continue
            exam_sessions.append(TrainingExamSummary(
                id=session.id,
                title=session.title,
                purpose=session.purpose or "class_assessment",
                status=session.status or "upcoming",
                start_time=session.start_time,
                end_time=session.end_time,
                question_count=len(session.paper.paper_questions or []) if session.paper else 0,
                passing_score=session.passing_score or 60,
            ))

        user_permission_codes = self._get_user_permission_codes(current_user_id) if current_user_id else set()
        can_edit_training = bool(
            current_user_id
            and "UPDATE_TRAINING" in user_permission_codes
            and can_update_training(self.db, training, current_user_id)
        )
        can_manage_training_directly = bool(
            current_user_id
            and "MANAGE_TRAINING" in user_permission_codes
            and can_manage_training(self.db, training, current_user_id)
        )
        can_manage_all = can_edit_training or can_manage_training_directly
        current_enrollment = self._resolve_current_enrollment(training, current_user_id)
        current_enrollment_status = current_enrollment.status if current_enrollment else None
        current_step_key = self._resolve_current_step_key(training)
        students = [self._enrollment_to_response(item) for item in approved_enrollments] if can_manage_all else []
        checkin_records = self._get_detail_checkin_records(training.id, current_user_id, can_manage_all)
        notices = self._list_training_notices(training.id)
        resources = self.list_training_resources(training.id)
        schedule_rule_config = self._resolve_training_schedule_rule_config(training)

        return TrainingResponse(
            id=training.id,
            name=training.name,
            type=training.type,
            status=training.status or "upcoming",
            publish_status=training.publish_status or "draft",
            progress_percent=self._calculate_progress_percent(training),
            start_date=training.start_date,
            end_date=training.end_date,
            location=training.location,
            department_id=training.department_id,
            department_name=training.department.name if training.department else None,
            visibility_scope=training.visibility_scope or "all",
            visibility_department_ids=training.visibility_department_ids,
            visibility_department_names=self._resolve_department_names(training.visibility_department_ids),
            police_type_id=training.police_type_id,
            police_type_name=training.police_type.name if training.police_type else None,
            training_base_id=training.training_base_id,
            training_base_name=training.training_base.name if training.training_base else None,
            created_by=training.created_by,
            class_code=training.class_code,
            instructor_id=training.instructor_id,
            instructor_name=training.instructor.nickname if training.instructor else None,
            capacity=training.capacity or 0,
            enrolled_count=len(student_ids),
            student_ids=student_ids,
            students=students,
            description=training.description,
            subjects=training.subjects or [],
            enrollment_requires_approval=bool(training.enrollment_requires_approval if training.enrollment_requires_approval is not None else True),
            enrollment_start_at=training.enrollment_start_at,
            enrollment_end_at=training.enrollment_end_at,
            published_at=training.published_at,
            locked_at=training.locked_at,
            is_locked=training.locked_at is not None,
            admission_exam_id=training.admission_exam_id,
            admission_exam_title=training.admission_exam.title if training.admission_exam else None,
            group_names=group_names,
            cadre_count=cadre_count,
            schedule_rule_config=schedule_rule_config,
            courses=courses,
            exam_sessions=sorted(exam_sessions, key=lambda item: item.start_time.isoformat() if item.start_time else ""),
            checkin_records=checkin_records,
            notices=notices,
            resources=resources,
            workflow_steps=self._build_workflow_steps(training),
            current_step_key=current_step_key,
            current_session=self._build_current_session_response(training, current_user_id),
            can_manage_all=can_manage_all,
            can_manage_training=can_manage_training_directly,
            can_edit_training=can_edit_training,
            can_edit_courses=can_manage_all,
            can_view_course_change_logs=can_edit_training or can_manage_training_directly,
            can_review_enrollments=can_manage_all,
            current_enrollment_status=current_enrollment_status,
            can_enter_training=current_enrollment_status == "approved",
            created_at=training.created_at,
            updated_at=training.updated_at,
        )

    def _resolve_training_schedule_rule_config(self, training: Training) -> TrainingScheduleRuleConfig:
        return TrainingScheduleRuleConfig.model_validate(
            TrainingScheduleRuleService.resolve_effective_rule_config(training.schedule_rule_config)
        )

    def _course_change_log_to_response(self, log: TrainingCourseChangeLog) -> TrainingCourseChangeLogResponse:
        actor = log.actor if getattr(log, "actor", None) else None
        return TrainingCourseChangeLogResponse(
            id=log.id,
            training_id=log.training_id,
            course_key=log.course_key,
            session_key=log.session_key,
            actor_id=log.actor_id,
            actor_name=(actor.nickname or actor.username) if actor else None,
            target_type=log.target_type,
            action=log.action,
            source=log.source,
            batch_id=log.batch_id,
            course_name=log.course_name,
            session_label=log.session_label,
            summary=log.summary,
            before_json=log.before_json,
            after_json=log.after_json,
            created_at=log.created_at,
        )

    def _to_list_response(self, training: Training, current_user_id: Optional[int] = None) -> TrainingListResponse:
        approved_enrollments = [item for item in (training.enrollments or []) if item.status == "approved"]
        student_ids = [item.user_id for item in approved_enrollments]
        current_enrollment = self._resolve_current_enrollment(training, current_user_id)
        current_enrollment_status = current_enrollment.status if current_enrollment else None
        return TrainingListResponse(
            id=training.id,
            name=training.name,
            type=training.type,
            status=training.status or "upcoming",
            publish_status=training.publish_status or "draft",
            progress_percent=self._calculate_progress_percent(training),
            start_date=training.start_date,
            end_date=training.end_date,
            location=training.location,
            department_id=training.department_id,
            department_name=training.department.name if training.department else None,
            visibility_scope=training.visibility_scope or "all",
            visibility_department_ids=training.visibility_department_ids,
            visibility_department_names=self._resolve_department_names(training.visibility_department_ids),
            police_type_id=training.police_type_id,
            police_type_name=training.police_type.name if training.police_type else None,
            training_base_id=training.training_base_id,
            training_base_name=training.training_base.name if training.training_base else None,
            created_by=training.created_by,
            class_code=training.class_code,
            instructor_id=training.instructor_id,
            instructor_name=training.instructor.nickname if training.instructor else None,
            capacity=training.capacity or 0,
            enrolled_count=len(student_ids),
            student_ids=student_ids,
            description=training.description,
            subjects=training.subjects or [],
            enrollment_requires_approval=bool(training.enrollment_requires_approval if training.enrollment_requires_approval is not None else True),
            enrollment_start_at=training.enrollment_start_at,
            enrollment_end_at=training.enrollment_end_at,
            is_locked=training.locked_at is not None,
            admission_exam_id=training.admission_exam_id,
            admission_exam_title=training.admission_exam.title if training.admission_exam else None,
            current_step_key=self._resolve_current_step_key(training),
            current_enrollment_status=current_enrollment_status,
            can_enter_training=current_enrollment_status == "approved",
            created_at=training.created_at,
        )

    def _enrollment_to_response(self, enrollment: Enrollment) -> EnrollmentResponse:
        user = enrollment.user if getattr(enrollment, "user", None) else None
        departments = [department.name for department in (user.departments or [])] if user else []
        return EnrollmentResponse(
            id=enrollment.id,
            training_id=enrollment.training_id,
            user_id=enrollment.user_id,
            user_name=user.username if user else None,
            user_nickname=user.nickname if user else None,
            police_id=user.police_id if user else None,
            departments=departments,
            status=enrollment.status,
            note=enrollment.note,
            contact_phone=enrollment.contact_phone,
            need_accommodation=bool(enrollment.need_accommodation),
            group_name=enrollment.group_name,
            cadre_role=enrollment.cadre_role,
            approved_at=enrollment.approved_at,
            reviewed_at=enrollment.reviewed_at,
            enroll_time=enrollment.enroll_time,
        )

    def _get_user_permission_codes(self, user_id: Optional[int]) -> set[str]:
        if not user_id:
            return set()
        user = self.db.query(User).options(
            joinedload(User.roles).joinedload(Role.permissions),
        ).filter(
            User.id == user_id,
            User.is_active == True,
        ).first()
        if not user:
            return set()
        permission_codes = set()
        for role in user.roles or []:
            for permission in role.permissions or []:
                if permission.code:
                    permission_codes.add(str(permission.code))
        return permission_codes

    def _get_detail_checkin_records(
        self,
        training_id: int,
        current_user_id: Optional[int],
        can_manage_all: bool,
    ) -> List[CheckinResponse]:
        query = self.db.query(CheckinRecord).options(
            joinedload(CheckinRecord.user),
        ).filter(CheckinRecord.training_id == training_id)
        if not can_manage_all and current_user_id is not None:
            query = query.filter(CheckinRecord.user_id == current_user_id)
        records = query.order_by(CheckinRecord.date.desc(), CheckinRecord.time.asc().nulls_last()).all()
        return [self._checkin_to_response(record) for record in records]

    def _list_training_notices(self, training_id: int) -> List[NoticeResponse]:
        notices = self.db.query(Notice).options(
            joinedload(Notice.author),
        ).filter(
            Notice.type == "training",
            Notice.training_id == training_id,
        ).order_by(Notice.created_at.desc()).all()
        return [self._notice_to_response(notice) for notice in notices]

    def _checkin_to_response(self, record: CheckinRecord) -> CheckinResponse:
        user = record.user if getattr(record, "user", None) else None
        return CheckinResponse(
            id=record.id,
            training_id=record.training_id,
            user_id=record.user_id,
            user_name=user.username if user else None,
            user_nickname=user.nickname if user else None,
            date=record.date,
            time=record.time,
            status=record.status,
            session_key=record.session_key,
            checkout_time=record.checkout_time,
            checkout_status=record.checkout_status or "pending",
            evaluation_score=record.evaluation_score,
            evaluation_comment=record.evaluation_comment,
            evaluation_submitted_at=record.evaluation_submitted_at,
            absence_reason=record.absence_reason,
        )

    def _notice_to_response(self, notice: Notice) -> NoticeResponse:
        return NoticeResponse(
            id=notice.id,
            title=notice.title,
            content=notice.content,
            type=notice.type,
            training_id=notice.training_id,
            author_id=notice.author_id,
            author_name=notice.author.nickname if notice.author else None,
            created_at=notice.created_at,
            updated_at=notice.updated_at,
        )

    def _history_to_response(self, history: TrainingHistory) -> TrainingHistoryResponse:
        user = history.user if getattr(history, "user", None) else None
        departments = [department.name for department in (user.departments or [])] if user else []
        return TrainingHistoryResponse(
            id=history.id,
            training_id=history.training_id,
            user_id=history.user_id,
            user_name=user.username if user else None,
            user_nickname=user.nickname if user else None,
            police_id=user.police_id if user else None,
            departments=departments,
            training_name=history.training_name,
            training_type=history.training_type,
            status=history.status,
            start_date=history.start_date,
            end_date=history.end_date,
            attendance_rate=history.attendance_rate or 0,
            completed_sessions=history.completed_sessions or 0,
            total_sessions=history.total_sessions or 0,
            evaluation_score=history.evaluation_score or 0,
            passed_exam_count=history.passed_exam_count or 0,
            archived_at=history.archived_at,
        )

    def _calculate_progress_percent(self, training: Training) -> int:
        status = training.status or "upcoming"
        if status == "upcoming":
            return 0
        if status == "ended":
            return 100
        if not training.start_date or not training.end_date:
            return 0
        total_days = (training.end_date - training.start_date).days + 1
        if total_days <= 0:
            return 0
        elapsed_days = (date.today() - training.start_date).days + 1
        percent = int(elapsed_days * 100 / total_days)
        return max(0, min(100, percent))

    def _parse_time_range(self, time_range: Optional[str]) -> tuple[Optional[time], Optional[time]]:
        if not time_range or "~" not in time_range:
            return None, None
        start_text, end_text = [item.strip() for item in time_range.split("~", 1)]
        try:
            return (
                datetime.strptime(start_text, "%H:%M").time(),
                datetime.strptime(end_text, "%H:%M").time(),
            )
        except ValueError:
            return None, None

    def _resource_to_response(self, resource: Resource) -> ResourceListItemResponse:
        tags = [relation.tag.name for relation in (resource.tag_relations or []) if relation.tag]
        return ResourceListItemResponse(
            id=resource.id,
            title=resource.title,
            summary=resource.summary,
            content_type=resource.content_type,
            source_type=resource.source_type,
            status=resource.status,
            visibility_type=resource.visibility_type,
            uploader_id=resource.uploader_id,
            uploader_name=resource.uploader.nickname if resource.uploader else None,
            owner_department_id=resource.owner_department_id,
            owner_department_name=resource.owner_department.name if resource.owner_department else None,
            cover_media_file_id=resource.cover_media_file_id,
            cover_url=None,
            tags=tags,
            created_at=resource.created_at,
            updated_at=resource.updated_at,
        )
