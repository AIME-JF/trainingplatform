"""
授权相关工具
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Role, Training, TrainingCourse, User


def has_role(db: Session, user_id: int, role_code: str) -> bool:
    if not role_code:
        return False
    row = db.query(User.id).join(User.roles).filter(
        User.id == user_id,
        User.is_active == True,
        Role.code == role_code,
    ).first()
    return row is not None


def is_admin_user(db: Session, user_id: int) -> bool:
    return has_role(db, user_id, "admin")


def is_instructor_user(db: Session, user_id: int) -> bool:
    return has_role(db, user_id, "instructor")


def is_training_director(training: Optional[Training], user_id: int) -> bool:
    return bool(training and training.instructor_id and training.instructor_id == user_id)


def is_course_primary_instructor(course: Optional[TrainingCourse], user_id: int) -> bool:
    return bool(course and course.primary_instructor_id and course.primary_instructor_id == user_id)


def is_course_assistant_instructor(course: Optional[TrainingCourse], user_id: int) -> bool:
    if not course:
        return False
    assistant_ids = course.assistant_instructor_ids or []
    return user_id in assistant_ids


def can_operate_training_course(
    db: Session,
    training: Optional[Training],
    course: Optional[TrainingCourse],
    user_id: int,
) -> bool:
    if is_admin_user(db, user_id):
        return True
    if is_training_director(training, user_id):
        return True
    return is_course_primary_instructor(course, user_id) or is_course_assistant_instructor(course, user_id)


def can_manage_training(db: Session, training: Optional[Training], user_id: int) -> bool:
    return is_admin_user(db, user_id) or is_training_director(training, user_id)
