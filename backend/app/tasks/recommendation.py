"""
推荐预计算任务（可选启用）
"""
from typing import List

from app.database import SessionLocal
from app.models import User, Resource
from app.services.recommendation import RecommendationService


def refresh_recommendation_scores_for_user(user_id: int):
    """刷新单用户推荐分(占位实现，便于后续接入 Celery beat)"""
    db = SessionLocal()
    try:
        service = RecommendationService(db)
        feed = service.get_recommendation_feed(user_id=user_id, page=1, size=500)
        rows = []
        for item in feed.get('items', []):
            rows.append({
                'resource_id': item['resource_id'],
                'score': item['score'],
                'police_type_score': 0,
                'department_score': 0,
                'interest_score': 0,
                'freshness_score': 0,
                'popularity_score': 0,
            })
        service.upsert_precomputed_scores(user_id=user_id, score_rows=rows)
    finally:
        db.close()


def refresh_recommendation_scores_for_all_users(limit: int = 1000):
    """刷新全部用户推荐分(占位实现)"""
    db = SessionLocal()
    try:
        user_ids = [u.id for u in db.query(User.id).limit(limit).all()]
    finally:
        db.close()

    for uid in user_ids:
        refresh_recommendation_scores_for_user(uid)
