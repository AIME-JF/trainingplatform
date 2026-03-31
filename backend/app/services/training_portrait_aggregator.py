"""
个性化训练画像聚合服务
"""
from collections import Counter
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session, selectinload

from app.models import CourseProgress, Enrollment, Exam, ExamRecord, Resource, ResourceBehaviorEvent, ResourceTagRelation, Training, User
from app.schemas import (
    AIPersonalTrainingPortrait,
    AIPersonalTrainingPortraitEvidence,
    AIPersonalTrainingPortraitTag,
)
from app.services.training import TrainingService
from app.utils.authz import can_manage_training, can_view_training


class TrainingPortraitAggregator:
    """根据训历、考试、学习和资源行为生成结构化画像"""

    def __init__(self, db: Session):
        self.db = db
        self.training_service = TrainingService(db)

    def build_portrait(self, training_id: int, target_user_id: int, current_user_id: int) -> AIPersonalTrainingPortrait:
        training = self._load_training_or_raise(training_id)
        user = self._load_user_or_raise(target_user_id)
        self._ensure_access(training, target_user_id, current_user_id)

        history_items = self.training_service.get_training_histories(training_id, target_user_id)
        history = history_items[0] if history_items else None

        exam_scores = self._load_exam_scores(training_id, target_user_id)
        avg_exam_score = round(sum(exam_scores) / len(exam_scores), 1) if exam_scores else 0.0
        recent_exam_score = round(exam_scores[0], 1) if exam_scores else 0.0

        progress_rows = self.db.query(CourseProgress).filter(CourseProgress.user_id == target_user_id).all()
        study_progress = round(sum(item.progress or 0 for item in progress_rows) / len(progress_rows), 1) if progress_rows else 0.0

        preferred_tags = self._load_preferred_resource_tags(target_user_id)
        attendance_rate = round(float(getattr(history, "attendance_rate", 0) or 0), 1)
        evaluation_score = round(float(getattr(history, "evaluation_score", 0) or 0), 1)
        completed_sessions = int(getattr(history, "completed_sessions", 0) or 0)
        total_sessions = int(getattr(history, "total_sessions", 0) or 0)
        total_study_hours = round(float(user.study_hours or 0), 1)

        tags: List[AIPersonalTrainingPortraitTag] = []
        evidence: List[AIPersonalTrainingPortraitEvidence] = [
            AIPersonalTrainingPortraitEvidence(source="training_history", label="出勤率", value=f"{attendance_rate:.1f}%"),
            AIPersonalTrainingPortraitEvidence(source="training_history", label="完成课次", value=f"{completed_sessions}/{total_sessions}"),
            AIPersonalTrainingPortraitEvidence(source="training_history", label="评课均分", value=f"{evaluation_score:.1f}"),
            AIPersonalTrainingPortraitEvidence(source="exam_record", label="平均考试分", value=f"{avg_exam_score:.1f}"),
            AIPersonalTrainingPortraitEvidence(source="course_progress", label="学习进度", value=f"{study_progress:.1f}%"),
            AIPersonalTrainingPortraitEvidence(source="user_profile", label="累计学习时长", value=f"{total_study_hours:.1f}小时"),
        ]

        if attendance_rate and attendance_rate < 85:
            tags.append(AIPersonalTrainingPortraitTag(code="attendance_risk", label="出勤风险", level="high", reason="近期出勤率低于 85%"))
        if avg_exam_score and avg_exam_score < 70:
            tags.append(AIPersonalTrainingPortraitTag(code="theory_weak", label="理论薄弱", level="high", reason="平均考试分低于 70 分"))
        elif avg_exam_score and avg_exam_score < 80:
            tags.append(AIPersonalTrainingPortraitTag(code="theory_weak", label="理论薄弱", level="medium", reason="平均考试分低于 80 分"))
        if evaluation_score and evaluation_score < 80:
            tags.append(AIPersonalTrainingPortraitTag(code="practice_weak", label="实操薄弱", level="medium", reason="评课均分偏低，建议加强复盘"))
        if study_progress and study_progress < 60:
            tags.append(AIPersonalTrainingPortraitTag(code="progress_lag", label="学习进度滞后", level="high", reason="课程学习进度低于 60%"))
        elif study_progress and study_progress < 75:
            tags.append(AIPersonalTrainingPortraitTag(code="progress_lag", label="学习进度滞后", level="medium", reason="课程学习进度低于 75%"))
        if preferred_tags:
            tags.append(AIPersonalTrainingPortraitTag(code="resource_preference", label="资源偏好明确", level="low", reason=f"近期待偏好资源标签：{'、'.join(preferred_tags[:3])}"))
        if training.end_date:
            days_to_end = (training.end_date - datetime.now().date()).days
            if days_to_end <= 10 and (not avg_exam_score or avg_exam_score < 75):
                tags.append(AIPersonalTrainingPortraitTag(code="exam_boost", label="考前强化需求", level="high", reason="临近结训且考试成绩仍有提升空间"))
        if not tags:
            tags.append(AIPersonalTrainingPortraitTag(code="stable_progress", label="训练状态稳定", level="low", reason="当前出勤、进度和成绩整体稳定"))

        return AIPersonalTrainingPortrait(
            user_id=user.id,
            user_name=user.nickname or user.username,
            training_id=training.id,
            training_name=training.name,
            attendance_rate=attendance_rate,
            completed_sessions=completed_sessions,
            total_sessions=total_sessions,
            evaluation_score=evaluation_score,
            avg_exam_score=avg_exam_score,
            recent_exam_score=recent_exam_score,
            study_progress=study_progress,
            total_study_hours=total_study_hours,
            preferred_resource_tags=preferred_tags,
            tags=tags,
            evidence=evidence,
        )

    def _load_training_or_raise(self, training_id: int) -> Training:
        training = self.db.query(Training).filter(Training.id == training_id).first()
        if not training:
            raise ValueError("培训班不存在")
        return training

    def _load_user_or_raise(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("目标学员不存在")
        return user

    def _ensure_access(self, training: Training, target_user_id: int, current_user_id: int) -> None:
        if target_user_id == current_user_id:
            if can_view_training(self.db, training, current_user_id) or self._is_training_member(training.id, target_user_id):
                return
        elif can_manage_training(self.db, training, current_user_id) and self._is_training_member(training.id, target_user_id):
            return
        raise ValueError("当前用户无权查看该学员的个训画像")

    def _is_training_member(self, training_id: int, user_id: int) -> bool:
        return self.db.query(Enrollment.id).filter(
            Enrollment.training_id == training_id,
            Enrollment.user_id == user_id,
            Enrollment.status == "approved",
        ).first() is not None

    def _load_exam_scores(self, training_id: int, target_user_id: int) -> List[float]:
        rows = self.db.query(ExamRecord.score).join(Exam, Exam.id == ExamRecord.exam_id).filter(
            Exam.training_id == training_id,
            ExamRecord.user_id == target_user_id,
            ExamRecord.status == "submitted",
        ).order_by(ExamRecord.submitted_at.desc(), ExamRecord.id.desc()).all()
        return [float(score or 0) for (score,) in rows]

    def _load_preferred_resource_tags(self, user_id: int) -> List[str]:
        event_rows = self.db.query(ResourceBehaviorEvent.resource_id).filter(
            ResourceBehaviorEvent.user_id == user_id
        ).order_by(ResourceBehaviorEvent.event_time.desc()).limit(30).all()
        resource_ids = [item[0] for item in event_rows if item and item[0]]
        if not resource_ids:
            return []

        resources = self.db.query(Resource).options(
            selectinload(Resource.tag_relations).joinedload(ResourceTagRelation.tag),
        ).filter(Resource.id.in_(resource_ids)).all()

        tag_counter: Counter[str] = Counter()
        for resource in resources:
            for relation in resource.tag_relations or []:
                if relation.tag and relation.tag.name:
                    tag_counter[relation.tag.name] += 1
        return [item for item, _ in tag_counter.most_common(5)]
