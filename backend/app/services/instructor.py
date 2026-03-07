"""
教官管理服务
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload

import re
import uuid
from app.models import InstructorProfile, User, Role
from app.schemas.instructor import (
    InstructorProfileCreate, InstructorProfileUpdate, InstructorResponse
)
from app.schemas import PaginatedResponse
from app.services.auth import auth_service
from logger import logger


class InstructorService:
    """教官服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_instructors(
        self,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        specialty: Optional[str] = None
    ) -> PaginatedResponse[InstructorResponse]:
        """获取教官列表"""
        query = self.db.query(InstructorProfile).options(
            joinedload(InstructorProfile.user)
        )

        if search:
            query = query.join(User).filter(
                User.nickname.contains(search) | User.username.contains(search)
            )
        if specialty:
            query = query.filter(InstructorProfile.specialties.contains([specialty]))

        total = query.count()

        if size == -1:
            profiles = query.all()
        else:
            skip = (page - 1) * size
            profiles = query.offset(skip).limit(size).all()

        items = [self._to_response(p) for p in profiles]

        return PaginatedResponse(
            page=page, size=size if size != -1 else total,
            total=total, items=items
        )

    def get_instructor_by_id(self, instructor_id: int) -> Optional[InstructorResponse]:
        """获取教官详情"""
        profile = self.db.query(InstructorProfile).options(
            joinedload(InstructorProfile.user)
        ).filter(InstructorProfile.id == instructor_id).first()

        if not profile:
            return None
        return self._to_response(profile)

    def create_instructor(self, data: InstructorProfileCreate) -> InstructorResponse:
        """新增教官，若未传 user_id 则自动创建用户"""
        user_id = data.user_id

        if not user_id:
            if not data.name:
                raise ValueError("请提供 user_id 或 name")
            # 自动创建教官用户
            username = f"instructor_{uuid.uuid4().hex[:8]}"
            user = User(
                username=username,
                password_hash=auth_service.get_password_hash("teach2025"),
                nickname=data.name,
                is_active=True,
            )
            instructor_role = self.db.query(Role).filter(Role.code == "instructor").first()
            if instructor_role:
                user.roles = [instructor_role]
            self.db.add(user)
            self.db.flush()
            user_id = user.id
            logger.info(f"自动创建教官用户: {username} (id={user_id})")

        existing = self.db.query(InstructorProfile).filter(
            InstructorProfile.user_id == user_id
        ).first()
        if existing:
            raise ValueError("该用户已有教官档案")

        level_map = {"高级教官": "expert", "中级教官": "senior", "初级教官": "standard"}

        profile = InstructorProfile(
            user_id=user_id, title=data.title,
            level=level_map.get(data.title, data.level),
            specialties=data.specialties, qualification=data.qualification,
            certificates=data.certificates, intro=data.intro
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        logger.info(f"创建教官档案: user_id={user_id}")
        return self._to_response(profile)

    def update_instructor(self, instructor_id: int, data: InstructorProfileUpdate) -> Optional[InstructorResponse]:
        """更新教官档案"""
        profile = self.db.query(InstructorProfile).filter(
            InstructorProfile.id == instructor_id
        ).first()
        if not profile:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)

        self.db.commit()
        self.db.refresh(profile)
        logger.info(f"更新教官档案: {instructor_id}")
        return self._to_response(profile)

    def _to_response(self, profile: InstructorProfile) -> InstructorResponse:
        """转换为响应"""
        user = profile.user
        return InstructorResponse(
            id=profile.id, user_id=profile.user_id,
            name=user.username if user else None,
            nickname=user.nickname if user else None,
            police_id=user.police_id if user else None,
            avatar=user.avatar if user else None,
            title=profile.title, level=profile.level,
            specialties=profile.specialties,
            qualification=profile.qualification,
            certificates=profile.certificates,
            intro=profile.intro, rating=profile.rating,
            course_count=profile.course_count,
            student_count=profile.student_count,
            review_count=profile.review_count
        )
