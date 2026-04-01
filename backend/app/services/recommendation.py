"""
资源推荐服务
"""
from typing import List, Optional, Dict, Set
from datetime import datetime

from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Resource, ResourceLike
from app.models.recommendation import ResourceBehaviorEvent, ResourceRecommendScore
from app.services.resource import ResourceService


PASSIVE_EVENT_TYPES = {'impression', 'click', 'play', 'complete', 'favorite'}


class RecommendationService:
    """推荐服务"""

    def __init__(self, db: Session):
        self.db = db
        self.resource_service = ResourceService(db)

    def record_event(
        self,
        resource_id: int,
        user_id: int,
        user_permissions: List[str],
        event_type: str,
        watch_seconds: int = 0,
        context_json: Optional[dict] = None,
    ) -> ResourceBehaviorEvent:
        resource = self.resource_service.get_viewable_resource_entity(resource_id, user_id, user_permissions)
        if not resource:
            raise ValueError('资源不存在或无访问权限')

        normalized_event_type = str(event_type or '').strip()
        if normalized_event_type not in PASSIVE_EVENT_TYPES:
            raise ValueError('不支持的事件类型')

        event = self._append_event(
            resource_id=resource_id,
            user_id=user_id,
            event_type=normalized_event_type,
            watch_seconds=watch_seconds,
            context_json=context_json,
        )

        if normalized_event_type in {'click', 'play', 'complete'}:
            resource.view_count = (resource.view_count or 0) + 1
        if normalized_event_type == 'favorite':
            resource.favorite_count = (resource.favorite_count or 0) + 1

        self.db.commit()
        self.db.refresh(event)
        return event

    def like_resource(self, resource_id: int, user_id: int, user_permissions: List[str]) -> Dict[str, int | bool]:
        resource = self.resource_service.get_viewable_resource_entity(resource_id, user_id, user_permissions)
        if not resource:
            raise ValueError('资源不存在或无访问权限')

        existing_like = self.db.query(ResourceLike).filter(
            ResourceLike.resource_id == resource_id,
            ResourceLike.user_id == user_id,
        ).first()

        if not existing_like:
            self.db.add(ResourceLike(resource_id=resource_id, user_id=user_id))
            resource.like_count = int(resource.like_count or 0) + 1
            self._append_event(resource_id=resource_id, user_id=user_id, event_type='like')

        self.db.commit()
        return {
            'resource_id': resource_id,
            'liked': True,
            'like_count': int(resource.like_count or 0),
        }

    def unlike_resource(self, resource_id: int, user_id: int, user_permissions: List[str]) -> Dict[str, int | bool]:
        resource = self.resource_service.get_viewable_resource_entity(resource_id, user_id, user_permissions)
        if not resource:
            raise ValueError('资源不存在或无访问权限')

        existing_like = self.db.query(ResourceLike).filter(
            ResourceLike.resource_id == resource_id,
            ResourceLike.user_id == user_id,
        ).first()

        if existing_like:
            self.db.delete(existing_like)
            resource.like_count = max(int(resource.like_count or 0) - 1, 0)
            self._append_event(resource_id=resource_id, user_id=user_id, event_type='unlike')

        self.db.commit()
        return {
            'resource_id': resource_id,
            'liked': False,
            'like_count': int(resource.like_count or 0),
        }

    def share_resource(self, resource_id: int, user_id: int, user_permissions: List[str]) -> Dict[str, int]:
        resource = self.resource_service.get_viewable_resource_entity(resource_id, user_id, user_permissions)
        if not resource:
            raise ValueError('资源不存在或无访问权限')

        resource.share_count = int(resource.share_count or 0) + 1
        self._append_event(resource_id=resource_id, user_id=user_id, event_type='share')
        self.db.commit()
        return {
            'resource_id': resource_id,
            'share_count': int(resource.share_count or 0),
        }

    def get_recommendation_feed(self, user_id: int, page: int = 1, size: int = 10) -> Dict:
        user_ctx = self._get_user_context(user_id)
        # 优先使用预计算分
        pre_scores = self.db.query(ResourceRecommendScore).filter(
            ResourceRecommendScore.user_id == user_id
        ).order_by(ResourceRecommendScore.score.desc()).all()

        if pre_scores:
            resource_ids = [int(item.resource_id) for item in pre_scores if item.resource_id]
            resource_map = {
                item.id: item
                for item in self.db.query(Resource).options(
                    selectinload(Resource.visibility_scopes),
                ).filter(
                    Resource.id.in_(resource_ids),
                    Resource.status == 'published',
                ).all()
            }
            filtered_scores = [
                score
                for score in pre_scores
                if resource_map.get(int(score.resource_id))
                and self.resource_service.can_user_access_published_resource(
                    resource_map[int(score.resource_id)],
                    user_id,
                    user_ctx,
                )
            ]

            total = len(filtered_scores)
            start = (page - 1) * size
            selected = filtered_scores[start:start + size]
            return {
                'items': [
                    {
                        'resource_id': s.resource_id,
                        'score': float(s.score),
                    }
                    for s in selected
                ],
                'page': page,
                'size': size,
                'total': total,
            }

        # 无缓存则实时规则排序
        resources = self.db.query(Resource).options(
            joinedload(Resource.owner_department),
            selectinload(Resource.visibility_scopes),
            selectinload(Resource.tag_relations),
        ).filter(Resource.status == 'published').all()

        interest_weights = self._get_interest_weights(user_id)

        scored = []
        now = datetime.now()
        for r in resources:
            if not self.resource_service.can_user_access_published_resource(r, user_id, user_ctx):
                continue
            police_type_score = self._calc_police_type_score(r, user_ctx['police_type_ids'])
            department_score = self._calc_department_score(r, user_ctx['department_ids'])
            interest_score = self._calc_interest_score(r, interest_weights)
            freshness_score = self._calc_freshness_score(r, now)
            popularity_score = self._calc_popularity_score(r)

            score = (
                0.30 * police_type_score
                + 0.25 * department_score
                + 0.20 * interest_score
                + 0.15 * freshness_score
                + 0.10 * popularity_score
            )
            scored.append((r.id, float(score)))

        scored.sort(key=lambda x: x[1], reverse=True)
        total = len(scored)
        start = (page - 1) * size
        selected = scored[start:start + size]

        return {
            'items': [
                {
                    'resource_id': rid,
                    'score': score,
                }
                for rid, score in selected
            ],
            'page': page,
            'size': size,
            'total': total,
        }

    def upsert_precomputed_scores(self, user_id: int, score_rows: List[dict]):
        for row in score_rows:
            existing = self.db.query(ResourceRecommendScore).filter(
                ResourceRecommendScore.user_id == user_id,
                ResourceRecommendScore.resource_id == row['resource_id'],
            ).first()

            if not existing:
                existing = ResourceRecommendScore(
                    user_id=user_id,
                    resource_id=row['resource_id'],
                )
                self.db.add(existing)

            existing.score = float(row.get('score', 0))
            existing.police_type_score = float(row.get('police_type_score', 0))
            existing.department_score = float(row.get('department_score', 0))
            existing.interest_score = float(row.get('interest_score', 0))
            existing.freshness_score = float(row.get('freshness_score', 0))
            existing.popularity_score = float(row.get('popularity_score', 0))

        self.db.commit()

    def _get_user_context(self, user_id: int) -> Dict[str, Set[int]]:
        from app.models import User

        user = self.db.query(User).options(
            selectinload(User.departments),
            selectinload(User.police_types),
            selectinload(User.roles),
        ).filter(User.id == user_id).first()

        if not user:
            return {'department_ids': set(), 'police_type_ids': set(), 'role_ids': set()}

        return {
            'department_ids': {d.id for d in (user.departments or [])},
            'police_type_ids': {p.id for p in (user.police_types or [])},
            'role_ids': {r.id for r in (user.roles or [])},
        }

    def _get_interest_weights(self, user_id: int) -> Dict[int, float]:
        rows = self.db.query(ResourceBehaviorEvent.resource_id, ResourceBehaviorEvent.event_type).filter(
            ResourceBehaviorEvent.user_id == user_id
        ).all()

        weight_by_event = {
            'impression': 0.2,
            'click': 0.8,
            'play': 1.0,
            'complete': 1.5,
            'like': 2.0,
            'favorite': 2.5,
        }

        resource_weight = {}
        for resource_id, event_type in rows:
            resource_weight[resource_id] = resource_weight.get(resource_id, 0) + weight_by_event.get(event_type, 0.1)

        # 聚合到标签
        tag_weight = {}
        if not resource_weight:
            return tag_weight

        resources = self.db.query(Resource).options(selectinload(Resource.tag_relations)).filter(Resource.id.in_(list(resource_weight.keys()))).all()
        for r in resources:
            rw = resource_weight.get(r.id, 0)
            for rel in (r.tag_relations or []):
                tag_weight[rel.tag_id] = tag_weight.get(rel.tag_id, 0) + rw

        return tag_weight

    def _calc_police_type_score(self, resource: Resource, user_police_type_ids: Set[int]) -> float:
        if not user_police_type_ids:
            return 0.2
        if resource.visibility_type == 'police_type':
            scopes = [s.scope_id for s in (resource.visibility_scopes or []) if s.scope_type == 'police_type']
            if set(scopes).intersection(user_police_type_ids):
                return 1.0
            return 0.1
        return 0.5

    def _calc_department_score(self, resource: Resource, user_department_ids: Set[int]) -> float:
        if not user_department_ids:
            return 0.2
        if resource.owner_department_id and resource.owner_department_id in user_department_ids:
            return 1.0
        if resource.visibility_type == 'department':
            scopes = [s.scope_id for s in (resource.visibility_scopes or []) if s.scope_type == 'department']
            if set(scopes).intersection(user_department_ids):
                return 0.9
        return 0.3

    def _calc_interest_score(self, resource: Resource, tag_weights: Dict[int, float]) -> float:
        if not tag_weights:
            return 0.3
        score = 0.0
        for rel in (resource.tag_relations or []):
            score += tag_weights.get(rel.tag_id, 0)
        return min(1.0, score / 10.0)

    def _calc_freshness_score(self, resource: Resource, now: datetime) -> float:
        base_time = resource.publish_at or resource.created_at
        if not base_time:
            return 0.2
        delta_days = max(0, (now - base_time.replace(tzinfo=None) if getattr(base_time, 'tzinfo', None) else now - base_time).days)
        if delta_days <= 3:
            return 1.0
        if delta_days <= 7:
            return 0.8
        if delta_days <= 30:
            return 0.5
        return 0.2

    def _calc_popularity_score(self, resource: Resource) -> float:
        views = resource.view_count or 0
        likes = resource.like_count or 0
        favorites = resource.favorite_count or 0
        raw = views * 0.01 + likes * 0.2 + favorites * 0.3
        return min(1.0, raw / 20.0)

    def _append_event(
        self,
        resource_id: int,
        user_id: int,
        event_type: str,
        watch_seconds: int = 0,
        context_json: Optional[dict] = None,
    ) -> ResourceBehaviorEvent:
        event = ResourceBehaviorEvent(
            user_id=user_id,
            resource_id=resource_id,
            event_type=event_type,
            watch_seconds=watch_seconds,
            context_json=context_json,
        )
        self.db.add(event)
        return event
