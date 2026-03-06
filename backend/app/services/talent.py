"""
人才库服务
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import User, Department
from app.models.department import user_departments
from app.schemas.talent import TalentResponse, TalentStatsResponse
from app.schemas import PaginatedResponse
from logger import logger


class TalentService:
    """人才库服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_talents(
        self,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        tier: Optional[str] = None,
        department_id: Optional[int] = None
    ) -> PaginatedResponse[TalentResponse]:
        """获取人才列表"""
        query = self.db.query(User).options(
            joinedload(User.departments),
            joinedload(User.police_types)
        ).filter(User.is_active == True)

        if search:
            query = query.filter(
                User.nickname.contains(search) | User.username.contains(search) |
                User.police_id.contains(search)
            )
        if department_id:
            query = query.join(User.departments).filter(Department.id == department_id)

        if tier == 'gold':
            query = query.filter(User.avg_score >= 90)
        elif tier == 'silver':
            query = query.filter(User.avg_score >= 80, User.avg_score < 90)
        elif tier == 'bronze':
            query = query.filter(User.avg_score >= 60, User.avg_score < 80)

        query = query.order_by(User.avg_score.desc())
        total = query.count()

        if size == -1:
            users = query.all()
        else:
            skip = (page - 1) * size
            users = query.offset(skip).limit(size).all()

        items = [self._to_response(u) for u in users]

        return PaginatedResponse(
            page=page, size=size if size != -1 else total,
            total=total, items=items
        )

    def get_stats(self) -> TalentStatsResponse:
        """获取统计概览"""
        total = self.db.query(User).filter(User.is_active == True).count()

        avg_score_result = self.db.query(func.avg(User.avg_score)).filter(
            User.is_active == True
        ).scalar()
        avg_score = round(float(avg_score_result), 1) if avg_score_result else 0

        avg_hours_result = self.db.query(func.avg(User.study_hours)).filter(
            User.is_active == True
        ).scalar()
        avg_hours = round(float(avg_hours_result), 1) if avg_hours_result else 0

        # 等级分布
        gold = self.db.query(User).filter(User.is_active == True, User.avg_score >= 90).count()
        silver = self.db.query(User).filter(User.is_active == True, User.avg_score >= 80, User.avg_score < 90).count()
        bronze = self.db.query(User).filter(User.is_active == True, User.avg_score >= 60, User.avg_score < 80).count()

        tier_distribution = [
            {"name": "金牌", "value": gold},
            {"name": "银牌", "value": silver},
            {"name": "铜牌", "value": bronze}
        ]

        # 单位（部门）分布：通过关联表统计
        dept_results = self.db.query(
            Department.name, func.count(user_departments.c.user_id).label('count')
        ).join(
            user_departments, Department.id == user_departments.c.department_id
        ).join(
            User, User.id == user_departments.c.user_id
        ).filter(
            User.is_active == True
        ).group_by(Department.name).order_by(func.count(user_departments.c.user_id).desc()).limit(10).all()

        department_distribution = [{"name": r.name, "value": r.count} for r in dept_results]

        return TalentStatsResponse(
            total=total,
            tier_distribution=tier_distribution,
            department_distribution=department_distribution,
            avg_score=avg_score,
            avg_study_hours=avg_hours
        )

    def _to_response(self, user: User) -> TalentResponse:
        """转换为响应"""
        score = user.avg_score or 0
        if score >= 90:
            tier = "gold"
        elif score >= 80:
            tier = "silver"
        elif score >= 60:
            tier = "bronze"
        else:
            tier = None

        departments = [d.name for d in user.departments] if user.departments else []
        police_types = [pt.name for pt in user.police_types] if user.police_types else []

        return TalentResponse(
            id=user.id, username=user.username,
            nickname=user.nickname, police_id=user.police_id,
            departments=departments, police_types=police_types,
            avatar=user.avatar, level=user.level,
            study_hours=user.study_hours or 0,
            exam_count=user.exam_count or 0,
            avg_score=user.avg_score or 0,
            tier=tier
        )
