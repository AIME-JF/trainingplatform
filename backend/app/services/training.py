"""
培训管理服务
"""
from typing import Optional, List
from datetime import datetime, date
import uuid
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Training, TrainingCourse, Enrollment, CheckinRecord, ScheduleItem, Certificate
)
from app.schemas.training import (
    TrainingCreate, TrainingUpdate, TrainingResponse, TrainingListResponse,
    TrainingCourseResponse, EnrollmentCreate, EnrollmentResponse,
    CheckinCreate, CheckinResponse, ScheduleItemResponse
)
from app.schemas import PaginatedResponse
from logger import logger


class TrainingService:
    """培训服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_trainings(
        self,
        page: int = 1,
        size: int = 10,
        status: Optional[str] = None,
        type: Optional[str] = None,
        search: Optional[str] = None
    ) -> PaginatedResponse[TrainingListResponse]:
        """获取培训列表"""
        query = self.db.query(Training).options(
            joinedload(Training.instructor),
            joinedload(Training.enrollments)
        )

        if type:
            query = query.filter(Training.type == type)
        if search:
            query = query.filter(Training.name.contains(search))

        trainings = query.order_by(Training.created_at.desc()).all()

        items: List[TrainingListResponse] = []
        for t in trainings:
            dynamic_status = self._resolve_training_status(t)
            if status and dynamic_status != status:
                continue

            student_ids = [e.user_id for e in (t.enrollments or []) if e.status == 'approved']
            enrolled = len(student_ids)

            items.append(TrainingListResponse(
                id=t.id,
                name=t.name,
                type=t.type,
                status=dynamic_status,
                progress_percent=self._calculate_progress_percent(t, dynamic_status),
                start_date=t.start_date,
                end_date=t.end_date,
                location=t.location,
                instructor_id=t.instructor_id,
                instructor_name=t.instructor.nickname if t.instructor else None,
                capacity=t.capacity,
                enrolled_count=enrolled,
                student_ids=student_ids,
                description=t.description,
                subjects=t.subjects,
                created_at=t.created_at
            ))

        total = len(items)
        if size == -1:
            paged_items = items
        else:
            skip = (page - 1) * size
            paged_items = items[skip: skip + size]

        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=paged_items
        )

    def create_training(self, data: TrainingCreate, user_id: int) -> TrainingResponse:
        """创建培训班"""
        training = Training(
            name=data.name, type=data.type, status=data.status,
            start_date=data.start_date, end_date=data.end_date,
            location=data.location,
            instructor_id=data.instructor_id or user_id,
            capacity=data.capacity, description=data.description,
            subjects=data.subjects
        )
        self.db.add(training)
        self.db.flush()

        if data.courses:
            for c in data.courses:
                tc = TrainingCourse(
                    training_id=training.id,
                    name=c.name,
                    instructor=c.instructor,
                    hours=c.hours,
                    type=c.type,
                    schedules=[item.model_dump() for item in (c.schedules or [])]
                )
                self.db.add(tc)

        self.db.commit()
        self.db.refresh(training)
        logger.info(f"创建培训班: {training.name}")
        return self._to_response(training)

    def get_training_by_id(self, training_id: int) -> Optional[TrainingResponse]:
        """获取培训详情"""
        training = self.db.query(Training).options(
            joinedload(Training.instructor),
            joinedload(Training.courses),
            joinedload(Training.enrollments)
        ).filter(Training.id == training_id).first()

        if not training:
            return None
        return self._to_response(training)

    def update_training(self, training_id: int, data: TrainingUpdate) -> Optional[TrainingResponse]:
        """更新培训班"""
        training = self.db.query(Training).filter(Training.id == training_id).first()
        if not training:
            return None

        update_data = data.model_dump(exclude_unset=True)
        courses = update_data.pop('courses', None)
        student_ids = update_data.pop('student_ids', None)

        for field, value in update_data.items():
            setattr(training, field, value)

        if courses is not None:
            self.db.query(TrainingCourse).filter(
                TrainingCourse.training_id == training_id
            ).delete(synchronize_session=False)
            for c in courses:
                self.db.add(TrainingCourse(
                    training_id=training.id,
                    name=c['name'],
                    instructor=c.get('instructor'),
                    hours=c.get('hours') or 0,
                    type=c.get('type') or 'theory',
                    schedules=c.get('schedules') or []
                ))

        if student_ids is not None:
            wanted_ids = {int(uid) for uid in student_ids}
            enrollments = self.db.query(Enrollment).filter(
                Enrollment.training_id == training_id
            ).all()

            existing_user_ids = {e.user_id for e in enrollments}

            for enrollment in enrollments:
                if enrollment.user_id in wanted_ids:
                    enrollment.status = 'approved'
                elif enrollment.status == 'approved':
                    enrollment.status = 'rejected'

            add_ids = wanted_ids - existing_user_ids
            for uid in add_ids:
                self.db.add(Enrollment(
                    training_id=training_id,
                    user_id=uid,
                    status='approved',
                    note='详情页配置学员'
                ))

        self.db.commit()
        self.db.refresh(training)
        logger.info(f"更新培训班: {training.name}")
        return self._to_response(training)

    def delete_training(self, training_id: int) -> bool:
        """删除培训班"""
        training = self.db.query(Training).filter(Training.id == training_id).first()
        if not training:
            return False

        # 先解除证书对培训班的外键引用，避免删除失败
        self.db.query(Certificate).filter(
            Certificate.training_id == training_id
        ).update({Certificate.training_id: None}, synchronize_session=False)

        self.db.delete(training)
        self.db.commit()
        logger.info(f"删除培训班: {training_id}")
        return True

    def get_training_students(
        self, training_id: int, page: int = 1, size: int = 10
    ) -> PaginatedResponse[EnrollmentResponse]:
        """获取培训学员列表"""
        query = self.db.query(Enrollment).options(
            joinedload(Enrollment.user)
        ).filter(
            Enrollment.training_id == training_id,
            Enrollment.status == 'approved'
        )

        total = query.count()

        if size == -1:
            records = query.all()
        else:
            skip = (page - 1) * size
            records = query.offset(skip).limit(size).all()

        items = [self._enrollment_to_response(r) for r in records]
        return PaginatedResponse(
            page=page, size=size if size != -1 else total,
            total=total, items=items
        )

    def get_schedule(self, training_id: int) -> List[ScheduleItemResponse]:
        """获取周计划"""
        items = self.db.query(ScheduleItem).filter(
            ScheduleItem.training_id == training_id
        ).order_by(ScheduleItem.day, ScheduleItem.time_start).all()
        return [ScheduleItemResponse.model_validate(i) for i in items]

    def enroll(self, training_id: int, user_id: int, data: EnrollmentCreate) -> EnrollmentResponse:
        """学员报名"""
        existing = self.db.query(Enrollment).filter(
            Enrollment.training_id == training_id,
            Enrollment.user_id == user_id
        ).first()
        if existing:
            raise ValueError("已报名该培训班")

        enrollment = Enrollment(
            training_id=training_id, user_id=user_id,
            status='pending', note=data.note
        )
        self.db.add(enrollment)
        self.db.commit()
        self.db.refresh(enrollment)
        logger.info(f"用户{user_id}报名培训{training_id}")
        return self._enrollment_to_response(enrollment)

    def get_enrollments(
        self, training_id: int, page: int = 1, size: int = 10
    ) -> PaginatedResponse[EnrollmentResponse]:
        """获取报名列表"""
        query = self.db.query(Enrollment).options(
            joinedload(Enrollment.user)
        ).filter(Enrollment.training_id == training_id)

        total = query.count()
        query = query.order_by(Enrollment.enroll_time.desc())

        if size == -1:
            records = query.all()
        else:
            skip = (page - 1) * size
            records = query.offset(skip).limit(size).all()

        items = [self._enrollment_to_response(r) for r in records]
        return PaginatedResponse(
            page=page, size=size if size != -1 else total,
            total=total, items=items
        )

    def approve_enrollment(self, training_id: int, enrollment_id: int) -> EnrollmentResponse:
        """审批通过"""
        enrollment = self.db.query(Enrollment).filter(
            Enrollment.id == enrollment_id,
            Enrollment.training_id == training_id
        ).first()
        if not enrollment:
            raise ValueError("报名记录不存在")

        enrollment.status = 'approved'
        self.db.commit()
        self.db.refresh(enrollment)
        logger.info(f"审批通过: 报名{enrollment_id}")
        return self._enrollment_to_response(enrollment)

    def reject_enrollment(self, training_id: int, enrollment_id: int, note: Optional[str] = None) -> EnrollmentResponse:
        """审批拒绝"""
        enrollment = self.db.query(Enrollment).filter(
            Enrollment.id == enrollment_id,
            Enrollment.training_id == training_id
        ).first()
        if not enrollment:
            raise ValueError("报名记录不存在")

        enrollment.status = 'rejected'
        if note:
            enrollment.note = note
        self.db.commit()
        self.db.refresh(enrollment)
        logger.info(f"审批拒绝: 报名{enrollment_id}")
        return self._enrollment_to_response(enrollment)

    def get_checkin_records(
        self, training_id: int, date_filter: Optional[date] = None
    ) -> List[CheckinResponse]:
        """获取签到记录"""
        query = self.db.query(CheckinRecord).options(
            joinedload(CheckinRecord.user)
        ).filter(CheckinRecord.training_id == training_id)

        if date_filter:
            query = query.filter(CheckinRecord.date == date_filter)

        records = query.order_by(CheckinRecord.date.desc(), CheckinRecord.time).all()
        items = []
        for r in records:
            items.append(CheckinResponse(
                id=r.id,
                training_id=r.training_id,
                user_id=r.user_id,
                user_name=r.user.username if r.user else None,
                user_nickname=r.user.nickname if r.user else None,
                date=r.date,
                time=r.time,
                status=r.status,
                session_key=r.session_key
            ))
        return items

    def checkin(self, training_id: int, user_id: int, data: CheckinCreate) -> CheckinResponse:
        """签到"""
        now = datetime.now()
        checkin_date = data.date or now.date()
        checkin_time = data.time or now.strftime("%H:%M")
        session_key = data.session_key or 'start'
        target_user_id = data.user_id or user_id

        existing = self.db.query(CheckinRecord).filter(
            CheckinRecord.training_id == training_id,
            CheckinRecord.user_id == target_user_id,
            CheckinRecord.date == checkin_date,
            CheckinRecord.session_key == session_key
        ).first()

        if existing:
            existing.time = checkin_time
            existing.status = 'on_time'
            record = existing
        else:
            record = CheckinRecord(
                training_id=training_id,
                user_id=target_user_id,
                date=checkin_date,
                time=checkin_time,
                status='on_time',
                session_key=session_key
            )
            self.db.add(record)

        self.db.commit()
        self.db.refresh(record)
        logger.info(f"用户{target_user_id}签到培训{training_id} 场次={session_key}")
        return CheckinResponse(
            id=record.id,
            training_id=record.training_id,
            user_id=record.user_id,
            date=record.date,
            time=record.time,
            status=record.status,
            session_key=record.session_key
        )

    def generate_checkin_qr(self, training_id: int) -> dict:
        """生成签到二维码"""
        token = str(uuid.uuid4())
        return {
            "training_id": training_id,
            "token": token,
            "url": f"/mobile/checkin/{token}",
            "expire_at": datetime.now().isoformat()
        }

    def _to_response(self, training: Training) -> TrainingResponse:
        """转换为响应"""
        enrollments = self.db.query(Enrollment).filter(
            Enrollment.training_id == training.id
        ).all()
        student_ids = [e.user_id for e in enrollments if e.status == 'approved']
        enrolled = len(student_ids)

        if not hasattr(training, 'courses'):
            training = self.db.query(Training).options(
                joinedload(Training.courses),
                joinedload(Training.instructor)
            ).filter(Training.id == training.id).first()

        courses = []
        if training and training.courses:
            courses = [TrainingCourseResponse.model_validate(c) for c in training.courses]

        dynamic_status = self._resolve_training_status(training)

        return TrainingResponse(
            id=training.id,
            name=training.name,
            type=training.type,
            status=dynamic_status,
            progress_percent=self._calculate_progress_percent(training, dynamic_status),
            start_date=training.start_date,
            end_date=training.end_date,
            location=training.location,
            instructor_id=training.instructor_id,
            instructor_name=training.instructor.nickname if training.instructor else None,
            capacity=training.capacity,
            enrolled_count=enrolled,
            student_ids=student_ids,
            description=training.description,
            subjects=training.subjects,
            courses=courses,
            created_at=training.created_at,
            updated_at=training.updated_at
        )

    def _enrollment_to_response(self, enrollment: Enrollment) -> EnrollmentResponse:
        """转换报名为响应"""
        user = enrollment.user if hasattr(enrollment, 'user') and enrollment.user else None
        departments = [d.name for d in user.departments] if user and user.departments else []
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
            enroll_time=enrollment.enroll_time
        )

    def _resolve_training_status(self, training: Training) -> str:
        today = date.today()
        if training.start_date and today < training.start_date:
            return 'upcoming'
        if training.end_date and today > training.end_date:
            return 'ended'
        if training.start_date and training.end_date and training.start_date <= today <= training.end_date:
            return 'active'
        return training.status or 'upcoming'

    def _calculate_progress_percent(self, training: Training, resolved_status: Optional[str] = None) -> int:
        status = resolved_status or self._resolve_training_status(training)
        if status == 'upcoming':
            return 0
        if status == 'ended':
            return 100

        if not training.start_date or not training.end_date:
            return 0

        total_days = (training.end_date - training.start_date).days + 1
        if total_days <= 0:
            return 0

        elapsed_days = (date.today() - training.start_date).days + 1
        percent = int(elapsed_days * 100 / total_days)
        if percent < 0:
            return 0
        if percent > 100:
            return 100
        return percent
