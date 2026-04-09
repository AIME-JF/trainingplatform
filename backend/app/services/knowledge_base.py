"""
知识库管理服务
"""
from typing import Optional

from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase, KnowledgeDocument


class KnowledgeBaseService:
    def __init__(self, db: Session):
        self.db = db

    # ==================== 知识库 CRUD ====================

    def list_knowledge_bases(
        self, page: int, size: int, visibility: Optional[str], user_role: str
    ) -> dict:
        query = self.db.query(KnowledgeBase)
        if user_role not in ("admin",):
            query = query.filter(
                (KnowledgeBase.visibility == "all")
                | ((KnowledgeBase.visibility == "instructor") & (user_role == "instructor"))
            )
        if visibility:
            query = query.filter(KnowledgeBase.visibility == visibility)
        total = query.count()
        items = query.order_by(KnowledgeBase.created_at.desc()).offset((page - 1) * size).limit(size).all()
        return {
            "total": total,
            "items": [self._to_kb_dict(kb) for kb in items],
            "page": page,
            "size": size,
        }

    def get_knowledge_base(self, kb_id: int) -> Optional[dict]:
        kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            return None
        return self._to_kb_dict(kb)

    def create_knowledge_base(self, name: str, description: Optional[str], visibility: str, user_id: int) -> dict:
        kb = KnowledgeBase(
            name=name,
            description=description,
            visibility=visibility,
            created_by=user_id,
        )
        self.db.add(kb)
        self.db.flush()
        return self._to_kb_dict(kb)

    def update_knowledge_base(self, kb_id: int, name: Optional[str], description: Optional[str], visibility: Optional[str]) -> Optional[dict]:
        kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            return None
        if name is not None:
            kb.name = name
        if description is not None:
            kb.description = description
        if visibility is not None:
            kb.visibility = visibility
        self.db.flush()
        return self._to_kb_dict(kb)

    def delete_knowledge_base(self, kb_id: int) -> bool:
        kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            return False
        self.db.delete(kb)
        self.db.flush()
        return True

    # ==================== 文档 CRUD ====================

    def list_documents(self, kb_id: int, page: int, size: int, search: Optional[str]) -> dict:
        query = self.db.query(KnowledgeDocument).filter(KnowledgeDocument.knowledge_base_id == kb_id)
        if search:
            query = query.filter(KnowledgeDocument.title.ilike(f"%{search}%"))
        total = query.count()
        items = query.order_by(KnowledgeDocument.created_at.desc()).offset((page - 1) * size).limit(size).all()
        return {
            "total": total,
            "items": [self._to_doc_dict(doc) for doc in items],
            "page": page,
            "size": size,
        }

    def create_document(self, kb_id: int, title: str, content: str, source_type: str, user_id: int) -> dict:
        doc = KnowledgeDocument(
            knowledge_base_id=kb_id,
            title=title,
            content=content,
            source_type=source_type,
            created_by=user_id,
        )
        self.db.add(doc)
        self.db.flush()
        # 更新知识库文档计数
        self._update_document_count(kb_id)
        return self._to_doc_dict(doc)

    def update_document(self, doc_id: int, title: Optional[str], content: Optional[str]) -> Optional[dict]:
        doc = self.db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            return None
        if title is not None:
            doc.title = title
        if content is not None:
            doc.content = content
        self.db.flush()
        return self._to_doc_dict(doc)

    def delete_document(self, doc_id: int) -> bool:
        doc = self.db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if not doc:
            return False
        kb_id = doc.knowledge_base_id
        self.db.delete(doc)
        self.db.flush()
        self._update_document_count(kb_id)
        return True

    def search_documents(self, kb_id: int, query_text: str, limit: int = 5) -> list[dict]:
        """文本检索：从知识库中搜索相关文档片段"""
        docs = (
            self.db.query(KnowledgeDocument)
            .filter(
                KnowledgeDocument.knowledge_base_id == kb_id,
                KnowledgeDocument.content.ilike(f"%{query_text}%"),
            )
            .limit(limit)
            .all()
        )
        if not docs:
            # 降级：按关键词分词搜索
            keywords = [w.strip() for w in query_text.split() if len(w.strip()) >= 2]
            if keywords:
                conditions = [KnowledgeDocument.content.ilike(f"%{kw}%") for kw in keywords[:3]]
                from sqlalchemy import or_
                docs = (
                    self.db.query(KnowledgeDocument)
                    .filter(
                        KnowledgeDocument.knowledge_base_id == kb_id,
                        or_(*conditions),
                    )
                    .limit(limit)
                    .all()
                )
        return [self._to_doc_dict(doc) for doc in docs]

    # ==================== helpers ====================

    def _update_document_count(self, kb_id: int):
        count = self.db.query(sa_func.count(KnowledgeDocument.id)).filter(
            KnowledgeDocument.knowledge_base_id == kb_id
        ).scalar()
        self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).update({"document_count": count or 0})

    @staticmethod
    def _to_kb_dict(kb: KnowledgeBase) -> dict:
        return {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "visibility": kb.visibility,
            "documentCount": kb.document_count,
            "usageCount": kb.usage_count,
            "createdBy": kb.created_by,
            "createdAt": str(kb.created_at) if kb.created_at else None,
            "updatedAt": str(kb.updated_at) if kb.updated_at else None,
        }

    @staticmethod
    def _to_doc_dict(doc: KnowledgeDocument) -> dict:
        return {
            "id": doc.id,
            "knowledgeBaseId": doc.knowledge_base_id,
            "title": doc.title,
            "content": doc.content,
            "sourceType": doc.source_type,
            "createdBy": doc.created_by,
            "createdAt": str(doc.created_at) if doc.created_at else None,
            "updatedAt": str(doc.updated_at) if doc.updated_at else None,
        }
