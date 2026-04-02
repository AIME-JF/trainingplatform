"""
题库管理服务
"""
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload, selectinload

from app.models import KnowledgePoint, PoliceType, Question, QuestionFolder, User
from app.schemas import PaginatedResponse
from app.schemas.exam import QuestionCreate, QuestionUpdate, QuestionResponse, QuestionBatchCreate, QuestionFolderCreate, QuestionFolderUpdate
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

    def _get_descendant_folder_ids(self, parent_id: int) -> List[int]:
        """递归获取所有子文件夹ID"""
        result = []
        children = self.db.query(QuestionFolder.id).filter(QuestionFolder.parent_id == parent_id).all()
        for child_id, in children:
            result.append(child_id)
            result.extend(self._get_descendant_folder_ids(child_id))
        return result

    def get_questions(
        self,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        type: Optional[str] = None,
        difficulty: Optional[int] = None,
        knowledge_point: Optional[str] = None,
        knowledge_point_id: Optional[int] = None,
        folder_id: Optional[int] = None,
        recursive: bool = False,
        current_user_id: Optional[int] = None,
    ) -> PaginatedResponse[QuestionResponse]:
        """获取题目列表"""
        query = self.db.query(Question).options(*self._question_load_options())

        if search or knowledge_point or knowledge_point_id is not None:
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
        if knowledge_point_id is not None:
            query = query.filter(KnowledgePoint.id == knowledge_point_id)

        # 文件夹筛选，支持递归
        if folder_id is not None:
            if recursive:
                # 递归：获取所有子文件夹ID
                folder_ids = self._get_descendant_folder_ids(folder_id)
                folder_ids.append(folder_id)
                query = query.filter(Question.folder_id.in_(folder_ids))
            else:
                query = query.filter(Question.folder_id == folder_id)

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

    # ============== 文件夹管理 ==============

    def _build_folder_response(self, folder: QuestionFolder, question_count: int = 0, paper_count: int = 0) -> dict:
        creator_name = None
        if folder.created_by:
            user = self.db.query(User).filter(User.id == folder.created_by).first()
            if user:
                creator_name = user.name or user.username

        if question_count > 0 or paper_count > 0:
            status = "使用中"
        else:
            status = "未使用"

        return {
            "id": folder.id,
            "name": folder.name,
            "category": folder.category or "默认分类",
            "parent_id": folder.parent_id,
            "sort_order": folder.sort_order,
            "question_count": question_count,
            "paper_count": paper_count,
            "exercise_count": 0,
            "status": status,
            "created_by": folder.created_by,
            "created_by_name": creator_name,
            "created_at": folder.created_at,
            "updated_at": folder.updated_at,
            "children": [],
        }

    def get_question_folders(self) -> List:
        """获取试题文件夹树"""
        folders = self.db.query(QuestionFolder).order_by(QuestionFolder.sort_order, QuestionFolder.id).all()

        creator_ids = {f.created_by for f in folders if f.created_by}
        creators = {u.id: u for u in self.db.query(User).filter(User.id.in_(creator_ids)).all()} if creator_ids else {}

        folder_ids = [f.id for f in folders]
        question_counts = {}
        if folder_ids:
            from sqlalchemy import func as sa_func
            counts = self.db.query(Question.folder_id, sa_func.count(Question.id)).filter(
                Question.folder_id.in_(folder_ids)
            ).group_by(Question.folder_id).all()
            question_counts = {row[0]: row[1] for row in counts}

        # 预构建文件夹ID到子文件夹ID列表的映射
        folder_children_map = {}
        for folder in folders:
            if folder.parent_id:
                if folder.parent_id not in folder_children_map:
                    folder_children_map[folder.parent_id] = []
                folder_children_map[folder.parent_id].append(folder.id)

        # 递归计算每个文件夹的题目总数（包括子文件夹）
        def get_recursive_question_count(folder_id):
            count = question_counts.get(folder_id, 0)
            children_ids = folder_children_map.get(folder_id, [])
            for child_id in children_ids:
                count += get_recursive_question_count(child_id)
            return count

        # 计算每个文件夹的递归题目总数
        recursive_question_counts = {fid: get_recursive_question_count(fid) for fid in folder_ids}

        paper_counts = {}
        if folder_ids:
            from sqlalchemy import func as sa_func
            from app.models.exam import ExamPaperQuestion
            try:
                counts = self.db.query(
                    Question.folder_id,
                    sa_func.count(sa_func.distinct(ExamPaperQuestion.paper_id))
                ).join(
                    ExamPaperQuestion, ExamPaperQuestion.question_id == Question.id
                ).filter(
                    Question.folder_id.in_(folder_ids)
                ).group_by(Question.folder_id).all()
                paper_counts = {row[0]: row[1] for row in counts}
            except Exception as e:
                logger.error(f"paper_counts query error: {e}")
                paper_counts = {}

        folder_responses = []
        for folder in folders:
            q_count = recursive_question_counts.get(folder.id, 0)
            p_count = paper_counts.get(folder.id, 0)
            creator = creators.get(folder.created_by)
            creator_name = creator.nickname if creator and creator.nickname else (creator.username if creator else None)

            if q_count > 0 or p_count > 0:
                status = "使用中"
            else:
                status = "未使用"

            folder_responses.append({
                "id": folder.id,
                "name": folder.name,
                "category": folder.category or "默认分类",
                "parent_id": folder.parent_id,
                "sort_order": folder.sort_order,
                "question_count": q_count,
                "paper_count": p_count,
                "exercise_count": 0,
                "status": status,
                "created_by": folder.created_by,
                "created_by_name": creator_name,
                "created_at": folder.created_at,
                "updated_at": folder.updated_at,
                "children": [],
            })
        return self._build_folder_tree(folder_responses)

    def _build_folder_tree(self, folders: List) -> List:
        """构建文件夹树"""
        folder_map = {f["id"]: f for f in folders}
        root_folders = []
        for folder in folders:
            if folder["parent_id"] and folder["parent_id"] in folder_map:
                folder_map[folder["parent_id"]]["children"].append(folder)
            else:
                root_folders.append(folder)
        return root_folders

    def create_question_folder(self, data: QuestionFolderCreate, user_id: int):
        if data.parent_id:
            parent = self.db.query(QuestionFolder).filter(QuestionFolder.id == data.parent_id).first()
            if not parent:
                raise ValueError("父文件夹不存在")
        folder = QuestionFolder(
            name=data.name,
            category=data.category,
            parent_id=data.parent_id,
            sort_order=data.sort_order,
            created_by=user_id,
        )
        self.db.add(folder)
        self.db.commit()
        return self._build_folder_response(folder)

    def update_question_folder(self, folder_id: int, data: QuestionFolderUpdate):
        folder = self.db.query(QuestionFolder).filter(QuestionFolder.id == folder_id).first()
        if not folder:
            raise ValueError("文件夹不存在")
        if data.name is not None:
            folder.name = data.name
        if data.category is not None:
            folder.category = data.category
        if data.parent_id is not None:
            if data.parent_id == folder_id:
                raise ValueError("不能将文件夹设置为自己的子文件夹")
            parent = self.db.query(QuestionFolder).filter(QuestionFolder.id == data.parent_id).first()
            if not parent:
                raise ValueError("父文件夹不存在")
            folder.parent_id = data.parent_id
        if data.sort_order is not None:
            folder.sort_order = data.sort_order
        self.db.commit()

        q_count = self.db.query(Question).filter(Question.folder_id == folder_id).count()
        return self._build_folder_response(folder, question_count=q_count)

    def delete_question_folder(self, folder_id: int) -> None:
        """删除文件夹"""
        folder = self.db.query(QuestionFolder).filter(QuestionFolder.id == folder_id).first()
        if not folder:
            raise ValueError("文件夹不存在")
        children = self.db.query(QuestionFolder).filter(QuestionFolder.parent_id == folder_id).count()
        if children > 0:
            raise ValueError("请先删除子文件夹")
        question_count = self.db.query(Question).filter(Question.folder_id == folder_id).count()
        if question_count > 0:
            raise ValueError("请先将文件夹内的试题移出后再删除")
        self.db.delete(folder)
        self.db.commit()

    def move_question_to_folder(self, question_id: int, folder_id: Optional[int]) -> QuestionResponse:
        """移动试题到文件夹"""
        question = self._get_question_entity(question_id)
        if not question:
            raise ValueError("试题不存在")
        if folder_id is not None:
            folder = self.db.query(QuestionFolder).filter(QuestionFolder.id == folder_id).first()
            if not folder:
                raise ValueError("目标文件夹不存在")
        question.folder_id = folder_id
        self.db.commit()
        return self._get_question_response(question.id)

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
            folder_id=data.folder_id,
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
            folder_id=question.folder_id,
            folder_name=question.folder.name if question.folder else None,
            score=question.score or 1,
            created_by=question.created_by,
            created_at=question.created_at,
            updated_at=question.updated_at,
        )
