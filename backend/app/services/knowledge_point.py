"""
知识点管理服务
"""
from typing import Iterable, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import KnowledgePoint, question_knowledge_point_relations
from app.schemas import (
    KnowledgePointCreate,
    KnowledgePointResponse,
    KnowledgePointUpdate,
    PaginatedResponse,
)


class KnowledgePointService:
    """知识点服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_knowledge_points(
        self,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> PaginatedResponse[KnowledgePointResponse]:
        """获取知识点列表"""
        base_query = self.db.query(KnowledgePoint)
        if search:
            base_query = base_query.filter(KnowledgePoint.name.contains(search))
        if is_active is not None:
            base_query = base_query.filter(KnowledgePoint.is_active == is_active)

        total = base_query.count()
        query = self._base_list_query(search, is_active)
        if size != -1:
            query = query.offset((page - 1) * size).limit(size)

        items = [
            self._to_response(knowledge_point, question_count)
            for knowledge_point, question_count in query.all()
        ]
        return PaginatedResponse(
            page=page,
            size=size if size != -1 else total,
            total=total,
            items=items,
        )

    def create_knowledge_point(self, data: KnowledgePointCreate, user_id: int) -> KnowledgePointResponse:
        """创建知识点"""
        normalized_name = self._normalize_name(data.name)
        if self._get_by_name(normalized_name):
            raise ValueError("知识点名称已存在")

        knowledge_point = KnowledgePoint(
            name=normalized_name,
            description=self._normalize_description(data.description),
            is_active=bool(data.is_active),
            created_by=user_id,
        )
        self.db.add(knowledge_point)
        self.db.commit()
        self.db.refresh(knowledge_point)
        return self._to_response(knowledge_point, 0)

    def update_knowledge_point(self, knowledge_point_id: int, data: KnowledgePointUpdate) -> Optional[KnowledgePointResponse]:
        """更新知识点"""
        knowledge_point = self.db.query(KnowledgePoint).filter(KnowledgePoint.id == knowledge_point_id).first()
        if not knowledge_point:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if "name" in update_data:
            normalized_name = self._normalize_name(update_data["name"])
            existed = self._get_by_name(normalized_name)
            if existed and existed.id != knowledge_point_id:
                raise ValueError("知识点名称已存在")
            knowledge_point.name = normalized_name
        if "description" in update_data:
            knowledge_point.description = self._normalize_description(update_data["description"])
        if "is_active" in update_data:
            knowledge_point.is_active = bool(update_data["is_active"])

        self.db.commit()
        self.db.refresh(knowledge_point)
        question_count = self._get_question_count(knowledge_point.id)
        return self._to_response(knowledge_point, question_count)

    def delete_knowledge_point(self, knowledge_point_id: int) -> bool:
        """删除知识点"""
        knowledge_point = self.db.query(KnowledgePoint).filter(KnowledgePoint.id == knowledge_point_id).first()
        if not knowledge_point:
            return False
        if self._get_question_count(knowledge_point_id) > 0:
            raise ValueError("知识点已被题目引用，不能删除")

        self.db.delete(knowledge_point)
        self.db.commit()
        return True

    def ensure_knowledge_points(
        self,
        names: Iterable[str],
        user_id: Optional[int] = None,
    ) -> List[KnowledgePoint]:
        """按名称获取或创建知识点"""
        normalized_names = self.normalize_names(names)
        if not normalized_names:
            return []

        existing_items = self.db.query(KnowledgePoint).filter(
            KnowledgePoint.name.in_(normalized_names)
        ).all()
        existing_map = {item.name: item for item in existing_items}

        results: List[KnowledgePoint] = []
        for name in normalized_names:
            knowledge_point = existing_map.get(name)
            if not knowledge_point:
                knowledge_point = KnowledgePoint(
                    name=name,
                    is_active=True,
                    created_by=user_id,
                )
                self.db.add(knowledge_point)
                self.db.flush()
                existing_map[name] = knowledge_point
            elif not knowledge_point.is_active:
                knowledge_point.is_active = True
            results.append(knowledge_point)
        return results

    @staticmethod
    def normalize_names(names: Iterable[str]) -> List[str]:
        """标准化知识点名称列表"""
        normalized: List[str] = []
        seen = set()
        for raw_name in names or []:
            name = str(raw_name or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            normalized.append(name[:100])
        return normalized

    def _base_list_query(self, search: Optional[str], is_active: Optional[bool]):
        query = self.db.query(
            KnowledgePoint,
            func.count(question_knowledge_point_relations.c.question_id).label("question_count"),
        ).outerjoin(
            question_knowledge_point_relations,
            question_knowledge_point_relations.c.knowledge_point_id == KnowledgePoint.id,
        )
        if search:
            query = query.filter(KnowledgePoint.name.contains(search))
        if is_active is not None:
            query = query.filter(KnowledgePoint.is_active == is_active)
        return query.group_by(
            KnowledgePoint.id,
            KnowledgePoint.name,
            KnowledgePoint.description,
            KnowledgePoint.is_active,
            KnowledgePoint.created_by,
            KnowledgePoint.created_at,
            KnowledgePoint.updated_at,
        ).order_by(KnowledgePoint.name.asc(), KnowledgePoint.id.asc())

    def _get_by_name(self, name: str) -> Optional[KnowledgePoint]:
        return self.db.query(KnowledgePoint).filter(KnowledgePoint.name == name).first()

    def _get_question_count(self, knowledge_point_id: int) -> int:
        return self.db.query(question_knowledge_point_relations.c.question_id).filter(
            question_knowledge_point_relations.c.knowledge_point_id == knowledge_point_id
        ).count()

    def _normalize_name(self, name: str) -> str:
        normalized_name = str(name or "").strip()
        if not normalized_name:
            raise ValueError("请填写知识点名称")
        return normalized_name[:100]

    @staticmethod
    def _normalize_description(description: Optional[str]) -> Optional[str]:
        return str(description or "").strip() or None

    @staticmethod
    def _to_response(knowledge_point: KnowledgePoint, question_count: int) -> KnowledgePointResponse:
        return KnowledgePointResponse(
            id=knowledge_point.id,
            name=knowledge_point.name,
            description=knowledge_point.description,
            is_active=bool(knowledge_point.is_active),
            question_count=int(question_count or 0),
            created_by=knowledge_point.created_by,
            created_at=knowledge_point.created_at,
            updated_at=knowledge_point.updated_at,
        )
