"""
授权相关工具
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Question, Role, Training, TrainingBase, TrainingCourse, User
from app.utils.data_scope import (
    DataScopeContext,
    build_data_scope_context,
    can_access_scoped_object,
    can_access_user_target,
)


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


def can_view_training_with_context(context: DataScopeContext, training: Optional[Training]) -> bool:
    if not training:
        return False
    if context.is_admin:
        return True
    # 已审批学员始终可见自己加入的培训班
    for enrollment in (training.enrollments or []):
        if enrollment.user_id == context.user_id and enrollment.status == "approved":
            return True
    # 创建人或班主任始终可见
    owner_ids = {uid for uid in [training.created_by, training.instructor_id] if uid is not None}
    if context.user_id in owner_ids:
        return True
    # 班内课程的授课教官（主讲/助教）始终可见
    for course in (training.courses or []):
        if course.primary_instructor_id == context.user_id:
            return True
        if context.user_id in (course.assistant_instructor_ids or []):
            return True
    # 根据培训班的可见范围配置判断
    scope = getattr(training, "visibility_scope", None) or "all"
    scope_dept_ids = set(getattr(training, "visibility_department_ids", None) or [])
    if scope == "all":
        return can_access_scoped_object(
            context,
            department_id=training.department_id,
            police_type_id=training.police_type_id,
            owner_user_ids=[training.created_by, training.instructor_id],
            dimension_mode="all",
            treat_missing_as_unrestricted=True,
        )
    if not scope_dept_ids:
        return False
    if scope == "department":
        return bool(context.department_ids & scope_dept_ids)
    if scope == "department_and_sub":
        return bool(context.department_ids & scope_dept_ids) or bool(context.department_with_sub_ids & scope_dept_ids)
    return False


def is_training_related_user(training: Optional[Training], user_id: int) -> bool:
    """判断用户是否与培训班有直接关系（已审批学员、班主任、创建人、课程教官），
    有关系的用户可查看班级全部详情且忽略数据范围限制。"""
    if not training or not user_id:
        return False
    # 创建人或班主任
    if training.created_by == user_id or training.instructor_id == user_id:
        return True
    # 已审批学员
    for enrollment in (training.enrollments or []):
        if enrollment.user_id == user_id and enrollment.status == "approved":
            return True
    # 课程主讲/助教教官
    for course in (training.courses or []):
        if course.primary_instructor_id == user_id:
            return True
        if user_id in (course.assistant_instructor_ids or []):
            return True
    return False


def can_view_training(db: Session, training: Optional[Training], user_id: int) -> bool:
    if not training:
        return False
    context = build_data_scope_context(db, user_id)
    return can_view_training_with_context(context, training)


def can_manage_training(db: Session, training: Optional[Training], user_id: int) -> bool:
    if not can_view_training(db, training, user_id):
        return False
    return is_admin_user(db, user_id) or is_training_director(training, user_id)


def can_update_training(db: Session, training: Optional[Training], user_id: int) -> bool:
    if not can_view_training(db, training, user_id):
        return False
    return (
        is_training_director(training, user_id)
    )


def can_view_training_base(db: Session, training_base: Optional[TrainingBase], user_id: int) -> bool:
    if not training_base:
        return False
    context = build_data_scope_context(db, user_id)
    return can_view_training_base_with_context(context, training_base)


def can_view_training_base_with_context(context: DataScopeContext, training_base: Optional[TrainingBase]) -> bool:
    if not training_base:
        return False
    return can_access_scoped_object(
        context,
        department_id=training_base.department_id,
        owner_user_ids=[training_base.created_by],
        dimension_mode="all",
        treat_missing_as_unrestricted=True,
    )


def can_manage_training_base(db: Session, training_base: Optional[TrainingBase], user_id: int) -> bool:
    return can_view_training_base(db, training_base, user_id)


def can_view_question(db: Session, question: Optional[Question], user_id: int) -> bool:
    if not question:
        return False
    context = build_data_scope_context(db, user_id)
    return can_view_question_with_context(context, question)


def can_view_question_with_context(context: DataScopeContext, question: Optional[Question]) -> bool:
    if not question:
        return False
    return can_access_scoped_object(
        context,
        police_type_id=question.police_type_id,
        owner_user_ids=[question.created_by],
        dimension_mode="all",
        treat_missing_as_unrestricted=True,
    )


def can_manage_question(db: Session, question: Optional[Question], user_id: int) -> bool:
    if not question:
        return False
    if is_admin_user(db, user_id):
        return True

    if getattr(question, "folder", None) and question.folder.created_by is not None:
        return question.folder.created_by == user_id

    return question.created_by == user_id


def can_access_user_record(db: Session, target_user: Optional[User], user_id: int) -> bool:
    if not target_user:
        return False
    context = build_data_scope_context(db, user_id)
    return can_access_user_record_with_context(context, target_user)


def can_access_user_record_with_context(context: DataScopeContext, target_user: Optional[User]) -> bool:
    if not target_user:
        return False
    return can_access_user_target(context, target_user)
