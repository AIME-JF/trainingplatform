"""
培训管理服务
"""
from typing import Optional, List
from datetime import datetime, date
import uuid
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import (
    Training, TrainingCourse, Enrollment, CheckinRecord, ScheduleItem, User, Certificate
)
from app.schemas.training import (
    TrainingCreate, TrainingUpdate, TrainingResponse, TrainingListResponse,
    TrainingCourseResponse, EnrollmentCreate, EnrollmentResponse,
    CheckinCreate, CheckinResponse, ScheduleItemCreate, ScheduleItemResponse
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
        query = self.db.query(Training).options(joinedload(Training.instructor))

        if status:
            query = query.filter(Training.status == status)
        if type:
            query = query.filter(Training.type == type)
        if search:
            query = query.filter(Training.name.contains(search))

        query = query.order_by(Training.created_at.desc())
        total = query.count()

        if size == -1:
            trainings = query.all()
        else:
            skip = (page - 1) * size
            trainings = query.offset(skip).limit(size).all()

        items = []
        for t in trainings:
            enrolled = self.db.query(Enrollment).filter(
                Enrollment.training_id == t.id,
                Enrollment.status == 'approved'
            ).count()
            items.append(TrainingListResponse(
                id=t.id, name=t.name, type=t.type, status=t.status,
                start_date=t.start_date, end_date=t.end_date,
                location=t.location, instructor_id=t.instructor_id,
                instructor_name=t.instructor.nickname if t.instructor else None,
                capacity=t.capacity, enrolled_count=enrolled,
                description=t.description, subjects=t.subjects,
                created_at=t.created_at
            ))

        return PaginatedResponse(
            page=page, size=size if size != -1 else total,
            total=total, items=items
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
                    training_id=training.id, name=c.name,
                    instructor=c.instructor, hours=c.hours, type=c.type
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
            joinedload(Training.courses)
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
        for field, value in update_data.items():
            setattr(training, field, value)

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
                id=r.id, training_id=r.training_id,
                user_id=r.user_id,
                user_name=r.user.username if r.user else None,
                user_nickname=r.user.nickname if r.user else None,
                date=r.date, time=r.time, status=r.status
            ))
        return items

    def checkin(self, training_id: int, user_id: int, data: CheckinCreate) -> CheckinResponse:
        """签到"""
        now = datetime.now()
        checkin_date = data.date or now.date()
        checkin_time = data.time or now.strftime("%H:%M")

        record = CheckinRecord(
            training_id=training_id, user_id=user_id,
            date=checkin_date, time=checkin_time,
            status='on_time'
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        logger.info(f"用户{user_id}签到培训{training_id}")
        return CheckinResponse(
            id=record.id, training_id=record.training_id,
            user_id=record.user_id, date=record.date,
            time=record.time, status=record.status
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
        enrolled = self.db.query(Enrollment).filter(
            Enrollment.training_id == training.id,
            Enrollment.status == 'approved'
        ).count()

        courses = []
        if hasattr(training, 'courses') and training.courses:
            courses = [TrainingCourseResponse.model_validate(c) for c in training.courses]

        return TrainingResponse(
            id=training.id, name=training.name, type=training.type,
            status=training.status, start_date=training.start_date,
            end_date=training.end_date, location=training.location,
            instructor_id=training.instructor_id,
            instructor_name=training.instructor.nickname if training.instructor else None,
            capacity=training.capacity, enrolled_count=enrolled,
            description=training.description, subjects=training.subjects,
            courses=courses,
            created_at=training.created_at, updated_at=training.updated_at
        )

    def _enrollment_to_response(self, enrollment: Enrollment) -> EnrollmentResponse:
        """转换报名为响应"""
        user = enrollment.user if hasattr(enrollment, 'user') and enrollment.user else None
        return EnrollmentResponse(
            id=enrollment.id, training_id=enrollment.training_id,
            user_id=enrollment.user_id,
            user_name=user.username if user else None,
            user_nickname=user.nickname if user else None,
            police_id=user.police_id if user else None,
            unit=user.unit if user else None,
            status=enrollment.status, note=enrollment.note,
            enroll_time=enrollment.enroll_time
        )
