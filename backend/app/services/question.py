"""
题库管理服务
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Question
from app.schemas.exam import QuestionCreate, QuestionUpdate, QuestionResponse, QuestionBatchCreate
from app.schemas import PaginatedResponse
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
        knowledge_point: Optional[str] = None
    ) -> PaginatedResponse[QuestionResponse]:
        """获取题目列表"""
        query = self.db.query(Question)

        if search:
            query = query.filter(Question.content.contains(search))
        if type:
            query = query.filter(Question.type == type)
        if difficulty:
            query = query.filter(Question.difficulty == difficulty)
        if knowledge_point:
            query = query.filter(Question.knowledge_point.contains(knowledge_point))

        query = query.order_by(Question.created_at.desc())
        total = query.count()

        if size == -1:
            questions = query.all()
        else:
            skip = (page - 1) * size
            questions = query.offset(skip).limit(size).all()

        items = [QuestionResponse.model_validate(q) for q in questions]

        return PaginatedResponse(
            page=page, size=size if size != -1 else total,
            total=total, items=items
        )

    def create_question(self, data: QuestionCreate, user_id: int) -> QuestionResponse:
        """创建题目"""
        question = Question(
            type=data.type, content=data.content,
            options=data.options, answer=data.answer,
            explanation=data.explanation, difficulty=data.difficulty,
            knowledge_point=data.knowledge_point, score=data.score,
            created_by=user_id
        )
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        logger.info(f"创建题目: {question.id}")
        return QuestionResponse.model_validate(question)

    def update_question(self, question_id: int, data: QuestionUpdate) -> Optional[QuestionResponse]:
        """更新题目"""
        question = self.db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(question, field, value)

        self.db.commit()
        self.db.refresh(question)
        logger.info(f"更新题目: {question.id}")
        return QuestionResponse.model_validate(question)

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
        for q_data in data.questions:
            question = Question(
                type=q_data.type, content=q_data.content,
                options=q_data.options, answer=q_data.answer,
                explanation=q_data.explanation, difficulty=q_data.difficulty,
                knowledge_point=q_data.knowledge_point, score=q_data.score,
                created_by=user_id
            )
            self.db.add(question)
            self.db.flush()
            results.append(QuestionResponse.model_validate(question))

        self.db.commit()
        logger.info(f"批量导入题目: {len(results)}题")
        return results
