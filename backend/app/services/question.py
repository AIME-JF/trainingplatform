"""
题库管理服务
"""
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.models import PoliceType, Question
from app.schemas.exam import QuestionCreate, QuestionUpdate, QuestionResponse, QuestionBatchCreate
from app.schemas import PaginatedResponse
from app.utils.authz import can_view_question_with_context
from app.utils.data_scope import build_data_scope_context, can_assign_scoped_values
from logger import logger


class QuestionService:
    """题库服务"""

    def __init__(self, db: Session):
        self.db = db

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
        query = self.db.query(Question).options(joinedload(Question.police_type))

        if search:
            query = query.filter(Question.content.contains(search))
        if type:
            query = query.filter(Question.type == type)
        if difficulty:
            query = query.filter(Question.difficulty == difficulty)
        if knowledge_point:
            query = query.filter(Question.knowledge_point.contains(knowledge_point))

        query = query.order_by(Question.created_at.desc())
        questions = query.all()
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
        self._ensure_actor_can_assign_question_scope(user_id, data.police_type_id)
        question = Question(
            type=data.type, content=data.content,
            options=data.options, answer=data.answer,
            explanation=data.explanation, difficulty=data.difficulty,
            knowledge_point=data.knowledge_point, police_type_id=data.police_type_id, score=data.score,
            created_by=user_id
        )
        self._ensure_police_type(data.police_type_id)
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        logger.info(f"创建题目: {question.id}")
        return self._to_response(question)

    def update_question(
        self,
        question_id: int,
        data: QuestionUpdate,
        user_id: Optional[int] = None,
    ) -> Optional[QuestionResponse]:
        """更新题目"""
        question = self.db.query(Question).options(joinedload(Question.police_type)).filter(Question.id == question_id).first()
        if not question:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if "police_type_id" in update_data:
            if user_id is not None:
                self._ensure_actor_can_assign_question_scope(user_id, update_data["police_type_id"])
            self._ensure_police_type(update_data["police_type_id"])
        for field, value in update_data.items():
            setattr(question, field, value)

        self.db.commit()
        self.db.refresh(question)
        logger.info(f"更新题目: {question.id}")
        return self._to_response(question)

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
        results = []
        scope_context = build_data_scope_context(self.db, user_id)
        for q_data in data.questions:
            if not can_assign_scoped_values(
                scope_context,
                police_type_id=q_data.police_type_id,
                dimension_mode="all",
                treat_missing_as_unrestricted=True,
            ):
                raise ValueError("超出当前角色可操作的数据范围")
            question = Question(
                type=q_data.type, content=q_data.content,
                options=q_data.options, answer=q_data.answer,
                explanation=q_data.explanation, difficulty=q_data.difficulty,
                knowledge_point=q_data.knowledge_point, police_type_id=q_data.police_type_id, score=q_data.score,
                created_by=user_id
            )
            self._ensure_police_type(q_data.police_type_id)
            self.db.add(question)
            self.db.flush()
            results.append(self._to_response(question))

        self.db.commit()
        logger.info(f"批量导入题目: {len(results)}题")
        return results

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
        return QuestionResponse(
            id=question.id,
            type=question.type,
            content=question.content,
            options=question.options,
            answer=question.answer,
            explanation=question.explanation,
            difficulty=question.difficulty or 1,
            knowledge_point=question.knowledge_point,
            police_type_id=question.police_type_id,
            police_type_name=question.police_type.name if question.police_type else None,
            score=question.score or 1,
            created_by=question.created_by,
            created_at=question.created_at,
            updated_at=question.updated_at,
        )
