"""
授权相关工具
"""
from sqlalchemy.orm import Session

from app.models import User, Role


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

