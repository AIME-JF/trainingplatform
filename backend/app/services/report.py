"""
数据看板服务
"""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models import User, Course, Exam, Training, ExamRecord, Department, PoliceType
from app.models.department import user_departments
from app.models.police_type import user_police_types
from app.schemas.report import KpiResponse, TrendItem, PoliceTypeDistribution, CityRanking
from logger import logger


class ReportService:
    """数据看板服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_kpi(self) -> KpiResponse:
        """获取KPI数据"""
        total_students = self.db.query(User).filter(User.is_active == True).count()
        total_courses = self.db.query(Course).count()
        total_exams = self.db.query(Exam).count()
        total_trainings = self.db.query(Training).count()

        avg_score_result = self.db.query(func.avg(ExamRecord.score)).scalar()
        avg_score = round(float(avg_score_result), 1) if avg_score_result else 0

        total_records = self.db.query(ExamRecord).count()
        pass_records = self.db.query(ExamRecord).filter(ExamRecord.result == 'pass').count()
        pass_rate = round(pass_records / total_records * 100, 1) if total_records > 0 else 0

        active_trainings = self.db.query(Training).filter(Training.status == 'active').count()

        return KpiResponse(
            total_students=total_students,
            total_courses=total_courses,
            total_exams=total_exams,
            total_trainings=total_trainings,
            avg_score=avg_score,
            pass_rate=pass_rate,
            active_trainings=active_trainings
        )

    def get_trend(self) -> List[TrendItem]:
        """获取月度趋势"""
        results = self.db.query(
            extract('month', ExamRecord.end_time).label('month'),
            func.count(func.distinct(ExamRecord.user_id)).label('students'),
            func.count(ExamRecord.id).label('exams'),
            func.avg(ExamRecord.score).label('avg_score')
        ).filter(
            ExamRecord.end_time.isnot(None)
        ).group_by(
            extract('month', ExamRecord.end_time)
        ).order_by('month').all()

        items = []
        for r in results:
            items.append(TrendItem(
                month=f"{int(r.month)}月",
                students=r.students or 0,
                exams=r.exams or 0,
                avg_score=round(float(r.avg_score), 1) if r.avg_score else 0
            ))
        return items

    def get_police_type_distribution(self) -> List[PoliceTypeDistribution]:
        """获取警种分布（通过关联表统计）"""
        results = self.db.query(
            PoliceType.name,
            func.count(user_police_types.c.user_id).label('count')
        ).join(
            user_police_types, PoliceType.id == user_police_types.c.police_type_id
        ).join(
            User, User.id == user_police_types.c.user_id
        ).filter(
            User.is_active == True,
            PoliceType.is_active == True
        ).group_by(PoliceType.name).all()

        return [
            PoliceTypeDistribution(name=r.name, value=r.count)
            for r in results
        ]

    def get_city_ranking(self) -> List[CityRanking]:
        """获取城市/单位排名（通过关联表统计）"""
        results = self.db.query(
            Department.name,
            func.avg(User.avg_score).label('score'),
            func.count(user_departments.c.user_id).label('students')
        ).join(
            user_departments, Department.id == user_departments.c.department_id
        ).join(
            User, User.id == user_departments.c.user_id
        ).filter(
            User.is_active == True,
            Department.is_active == True
        ).group_by(Department.name).order_by(func.avg(User.avg_score).desc()).limit(20).all()

        return [
            CityRanking(
                city=r.name,
                score=round(float(r.score), 1) if r.score else 0,
                students=r.students
            )
            for r in results
        ]
