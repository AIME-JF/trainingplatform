"""
Authentication and permission helpers.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session, selectinload

from app.models import Department, Permission, Role, User
from app.runtime_sync import EXTRA_PERMISSION_DEFINITIONS
from app.schemas import TokenData
from config import settings
from logger import logger


class AuthService:
    """Authentication service."""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.now() + (
            expires_delta or timedelta(minutes=self.access_token_expire_minutes)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str, db: Session = None) -> Optional[TokenData]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            username = payload.get("username")

            if user_id is None or username is None:
                return None

            permissions: List[str] = []
            if db is not None:
                permissions = self.get_user_permissions(db, user_id)

            return TokenData(user_id=user_id, username=username, permissions=permissions)
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            return None

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        try:
            user = (
                db.query(User)
                .options(
                    selectinload(User.roles).selectinload(Role.permissions),
                    selectinload(User.departments).selectinload(Department.permissions),
                    selectinload(User.police_types),
                )
                .filter(User.username == username)
                .first()
            )

            if not user:
                raise HTTPException(status_code=400, detail="用户不存在")
            if user.is_active is False:
                raise HTTPException(status_code=400, detail="用户已禁用")
            if not self.verify_password(password, user.password_hash):
                raise HTTPException(status_code=400, detail="密码错误")

            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User authentication failed: {e}")
            raise HTTPException(status_code=500, detail="用户认证失败")

    def get_user_permissions(self, db: Session, user_id: int) -> List[str]:
        try:
            user = (
                db.query(User)
                .options(
                    selectinload(User.roles).selectinload(Role.permissions),
                    selectinload(User.departments).selectinload(Department.permissions),
                    selectinload(User.police_types),
                )
                .filter(User.id == user_id, User.is_active == True)
                .first()
            )

            if not user:
                return []

            permissions = set()
            is_admin = False

            for role in user.roles:
                if not role.is_active:
                    continue
                if role.code == "admin":
                    is_admin = True
                for permission in role.permissions:
                    if permission.is_active:
                        permissions.add(permission.code)

            for department in user.departments:
                if department.is_active:
                    permissions.update(self._get_department_permissions(db, department.id))

            if is_admin:
                permission_rows = (
                    db.query(Permission.code)
                    .filter(Permission.is_active == True)
                    .all()
                )
                permissions.update(code for (code,) in permission_rows)
                permissions.update(item["code"] for item in EXTRA_PERMISSION_DEFINITIONS)

            return sorted(permissions)
        except Exception as e:
            logger.error(f"Failed to load user permissions: {e}")
            return []

    def _get_department_permissions(self, db: Session, department_id: int) -> set:
        department = (
            db.query(Department)
            .options(
                selectinload(Department.permissions),
                selectinload(Department.children),
            )
            .filter(Department.id == department_id)
            .first()
        )

        if not department:
            return set()

        permissions = set()
        for permission in department.permissions:
            if permission.is_active:
                permissions.add(permission.code)

        if department.inherit_sub_permissions:
            self._collect_subdepartment_permissions(db, department, permissions)

        return permissions

    def _collect_subdepartment_permissions(self, db: Session, department: Department, permissions: set):
        for child in department.children:
            if not child.is_active:
                continue

            child_with_permissions = (
                db.query(Department)
                .options(selectinload(Department.permissions))
                .filter(Department.id == child.id)
                .first()
            )

            if child_with_permissions:
                for permission in child_with_permissions.permissions:
                    if permission.is_active:
                        permissions.add(permission.code)

            self._collect_subdepartment_permissions(db, child, permissions)

    def create_user_token(self, db: Session, user: User) -> str:
        return self.create_access_token(
            data={
                "user_id": user.id,
                "username": user.username,
            }
        )

    def check_permission(self, user_permissions: List[str], required_permission: str) -> bool:
        return required_permission in user_permissions


auth_service = AuthService()
