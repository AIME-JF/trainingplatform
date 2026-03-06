"""
数据看板服务
"""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models import User, Course, Exam, Training, ExamRecord
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
        """获取警种分布"""
        results = self.db.query(
            User.police_type,
            func.count(User.id).label('count')
        ).filter(
            User.police_type.isnot(None),
            User.is_active == True
        ).group_by(User.police_type).all()

        return [
            PoliceTypeDistribution(name=r.police_type or "未知", value=r.count)
            for r in results
        ]

    def get_city_ranking(self) -> List[CityRanking]:
        """获取城市/单位排名"""
        results = self.db.query(
            User.unit,
            func.avg(User.avg_score).label('score'),
            func.count(User.id).label('students')
        ).filter(
            User.unit.isnot(None),
            User.is_active == True
        ).group_by(User.unit).order_by(func.avg(User.avg_score).desc()).limit(20).all()

        return [
            CityRanking(
                city=r.unit or "未知",
                score=round(float(r.score), 1) if r.score else 0,
                students=r.students
            )
            for r in results
        ]
