"""
题库管理服务
"""
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload, selectinload

from app.models import KnowledgePoint, PoliceType, Question
from app.schemas import PaginatedResponse
from app.schemas.exam import QuestionCreate, QuestionUpdate, QuestionResponse, QuestionBatchCreate
from app.schemas.knowledge_point import KnowledgePointSimpleResponse
from app.utils.authz import can_view_question_with_context
from app.utils.data_scope import build_data_scope_context, can_assign_scoped_values
from logger import logger
from .knowledge_point import KnowledgePointService


def deduplicate_questions(questions: List[Question]) -> List[Question]:
    """按题目 ID 保序去重，避免 PostgreSQL 对 JSON 列做 DISTINCT 比较。"""
    deduplicated: List[Question] = []
    seen_ids: set[int] = set()
    for question in questions:
        if question.id in seen_ids:
            continue
        seen_ids.add(question.id)
        deduplicated.append(question)
    return deduplicated


class QuestionService:
    """题库服务"""

    def __init__(self, db: Session):
        self.db = db
        self.knowledge_point_service = KnowledgePointService(db)

    def get_questions(
        self,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        type: Optional[str] = None,
        difficulty: Optional[int] = None,
        knowledge_point: Optional[str] = None,
        current_user_id: Optional[int] = None,
    ) -> PaginatedResponse[QuestionResponse]:
        """获取题目列表"""
        query = self.db.query(Question).options(*self._question_load_options())

        if search or knowledge_point:
            query = query.outerjoin(Question.knowledge_points)
        if search:
            query = query.filter(
                or_(
                    Question.content.contains(search),
                    KnowledgePoint.name.contains(search),
                )
            )
        if type:
            query = query.filter(Question.type == type)
        if difficulty:
            query = query.filter(Question.difficulty == difficulty)
        if knowledge_point:
            query = query.filter(KnowledgePoint.name.contains(knowledge_point))

        query = query.order_by(Question.created_at.desc(), Question.id.desc())
        questions = deduplicate_questions(query.all())
        scope_context = build_data_scope_context(self.db, current_user_id) if current_user_id else None
        if scope_context:
            questions = [
                question
                for question in questions
                if can_view_question_with_context(scope_context, question)
            ]
        total = len(questions)

        if size != -1:
            skip = (page - 1) * size
            questions = questions[skip: skip + size]

        items = [self._to_response(q) for q in questions]

        return PaginatedResponse(
            page=page, size=size if size != -1 else total,
            total=total, items=items
        )

    def create_question(self, data: QuestionCreate, user_id: int) -> QuestionResponse:
        """创建题目"""
        question = self._create_question_entity(data, user_id)
        self.db.commit()
        logger.info(f"创建题目: {question.id}")
        return self._get_question_response(question.id)

    def update_question(
        self,
        question_id: int,
        data: QuestionUpdate,
        user_id: Optional[int] = None,
    ) -> Optional[QuestionResponse]:
        """更新题目"""
        question = self._get_question_entity(question_id)
        if not question:
            return None

        update_data = data.model_dump(exclude_unset=True)
        knowledge_point_names = update_data.pop("knowledge_point_names", None)
        if "police_type_id" in update_data:
            if user_id is not None:
                self._ensure_actor_can_assign_question_scope(user_id, update_data["police_type_id"])
            self._ensure_police_type(update_data["police_type_id"])
        for field, value in update_data.items():
            setattr(question, field, value)
        if knowledge_point_names is not None:
            self._replace_question_knowledge_points(question, knowledge_point_names, user_id)

        self.db.commit()
        logger.info(f"更新题目: {question.id}")
        return self._get_question_response(question.id)

    def delete_question(self, question_id: int) -> bool:
        """删除题目"""
        question = self.db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return False
        self.db.delete(question)
        self.db.commit()
        logger.info(f"删除题目: {question_id}")
        return True

    def batch_create(self, data: QuestionBatchCreate, user_id: int) -> List[QuestionResponse]:
        """批量导入题目"""
        created_ids: List[int] = []
        scope_context = build_data_scope_context(self.db, user_id)
        for q_data in data.questions:
            if not can_assign_scoped_values(
                scope_context,
                police_type_id=q_data.police_type_id,
                dimension_mode="all",
                treat_missing_as_unrestricted=True,
            ):
                raise ValueError("超出当前角色可操作的数据范围")
            question = self._create_question_entity(q_data, user_id, check_scope=False)
            created_ids.append(question.id)

        self.db.commit()
        logger.info(f"批量导入题目: {len(created_ids)}题")
        return self._load_question_responses(created_ids)

    def _question_load_options(self) -> tuple:
        return (
            joinedload(Question.police_type),
            selectinload(Question.knowledge_points),
        )

    def _get_question_entity(self, question_id: int) -> Optional[Question]:
        return self.db.query(Question).options(*self._question_load_options()).filter(Question.id == question_id).first()

    def _get_question_response(self, question_id: int) -> QuestionResponse:
        question = self._get_question_entity(question_id)
        if not question:
            raise ValueError("题目不存在")
        return self._to_response(question)

    def _load_question_responses(self, question_ids: List[int]) -> List[QuestionResponse]:
        if not question_ids:
            return []
        questions = self.db.query(Question).options(*self._question_load_options()).filter(
            Question.id.in_(question_ids)
        ).all()
        question_map = {question.id: question for question in questions}
        return [
            self._to_response(question_map[question_id])
            for question_id in question_ids
            if question_id in question_map
        ]

    def _create_question_entity(
        self,
        data: QuestionCreate,
        user_id: int,
        check_scope: bool = True,
    ) -> Question:
        if check_scope:
            self._ensure_actor_can_assign_question_scope(user_id, data.police_type_id)
        self._ensure_police_type(data.police_type_id)

        question = Question(
            type=data.type,
            content=data.content,
            options=data.options,
            answer=data.answer,
            explanation=data.explanation,
            difficulty=data.difficulty,
            police_type_id=data.police_type_id,
            score=data.score,
            created_by=user_id,
        )
        self.db.add(question)
        self.db.flush()
        self._replace_question_knowledge_points(question, data.knowledge_point_names, user_id)
        return question

    def _replace_question_knowledge_points(
        self,
        question: Question,
        knowledge_point_names: Optional[List[str]],
        user_id: Optional[int],
    ) -> None:
        normalized_names = self.knowledge_point_service.normalize_names(knowledge_point_names or [])
        question.knowledge_points = self.knowledge_point_service.ensure_knowledge_points(normalized_names, user_id)
        self.db.flush()

    def _ensure_police_type(self, police_type_id: Optional[int]) -> Optional[PoliceType]:
        if not police_type_id:
            return None
        police_type = self.db.query(PoliceType).filter(PoliceType.id == police_type_id).first()
        if not police_type:
            raise ValueError("警种不存在")
        return police_type

    def _ensure_actor_can_assign_question_scope(self, user_id: int, police_type_id: Optional[int]) -> None:
        context = build_data_scope_context(self.db, user_id)
        if not can_assign_scoped_values(
            context,
            police_type_id=police_type_id,
            dimension_mode="all",
            treat_missing_as_unrestricted=True,
        ):
            raise ValueError("超出当前角色可操作的数据范围")

    def _to_response(self, question: Question) -> QuestionResponse:
        knowledge_points = sorted(question.knowledge_points or [], key=lambda item: (item.name or "", item.id or 0))
        return QuestionResponse(
            id=question.id,
            type=question.type,
            content=question.content,
            options=question.options,
            answer=question.answer,
            explanation=question.explanation,
            difficulty=question.difficulty or 1,
            knowledge_points=[
                KnowledgePointSimpleResponse(id=item.id, name=item.name)
                for item in knowledge_points
            ],
            knowledge_point_names=[item.name for item in knowledge_points],
            police_type_id=question.police_type_id,
            police_type_name=question.police_type.name if question.police_type else None,
            score=question.score or 1,
            created_by=question.created_by,
            created_at=question.created_at,
            updated_at=question.updated_at,
        )
