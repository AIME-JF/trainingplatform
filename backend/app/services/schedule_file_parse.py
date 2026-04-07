"""
智能解析课表文件 - 编排服务
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.agents.schedule_file_class_info_agent import ScheduleFileClassInfoAgent
from app.agents.schedule_file_course_parse_agent import ScheduleFileCourseParseAgent
from app.models import AITask, Role, TrainingBase, User
from app.schemas.schedule_file_parse import (
    ScheduleFileCourse,
    ScheduleFileClassInfo,
    ScheduleFileHeadteacher,
    ScheduleFileInstructor,
    ScheduleFileParseTaskDetailResponse,
    ScheduleFileParseTaskUpdateRequest,
    ScheduleFileTrainingConfig,
)
from app.schemas.response import PaginatedResponse
from app.schemas.ai import AITaskSummaryResponse
from app.services.document_parser import DocumentParserService
from logger import logger

TASK_TYPE = "schedule_file_parse"
DEFAULT_PASSWORD = "Police@123456"


class ScheduleFileParseService:
    """智能解析课表文件任务编排"""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # 列表
    # ------------------------------------------------------------------
    def list_tasks(
        self,
        page: int,
        size: int,
        status_value: str | None,
        current_user_id: int,
    ) -> PaginatedResponse:
        query = self.db.query(AITask).filter(
            AITask.task_type == TASK_TYPE,
            AITask.created_by == current_user_id,
        )
        if status_value:
            query = query.filter(AITask.status == status_value)
        query = query.order_by(desc(AITask.created_at), desc(AITask.id))

        total = query.count()
        if size == -1:
            items = query.all()
        else:
            items = query.offset((page - 1) * size).limit(size).all()

        return PaginatedResponse(
            total=total,
            page=page,
            size=size if size != -1 else total,
            items=[self._to_task_summary(t) for t in items],
        )

    # ------------------------------------------------------------------
    # 创建
    # ------------------------------------------------------------------
    def create_task(
        self,
        file_content: bytes,
        file_name: str,
        task_name: str | None,
        current_user_id: int,
    ) -> ScheduleFileParseTaskDetailResponse:
        # 1. 提取纯文本
        parser = DocumentParserService()
        raw_text = parser.parse(file_content, file_name)
        if not raw_text or raw_text.startswith("["):
            raise ValueError("无法从文件中提取有效文本内容")

        # 2. 创建任务
        auto_name = task_name or f"解析课表：{file_name}"
        task = AITask(
            task_name=auto_name[:200],
            task_type=TASK_TYPE,
            status="pending",
            request_payload={
                "file_name": file_name,
                "raw_text": raw_text[:60000],
            },
            result_payload={
                "task_stage": "parsing",
            },
            created_by=current_user_id,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        # 3. 调度异步任务
        from app.tasks.schedule_file_parse import schedule_schedule_file_parse_task
        schedule_schedule_file_parse_task(preferred_task_id=task.id, db=self.db)

        return self.get_task_detail(task.id, current_user_id)

    # ------------------------------------------------------------------
    # 执行（Celery 调用）
    # ------------------------------------------------------------------
    def execute_task(self, task_id: int) -> None:
        task = self.db.query(AITask).filter(AITask.id == task_id).first()
        if not task:
            raise ValueError("任务不存在")
        if task.status in ("completed", "confirmed", "failed"):
            return

        task.status = "processing"
        task.started_at = datetime.now(timezone.utc)
        self.db.commit()

        try:
            raw_text = (task.request_payload or {}).get("raw_text", "")
            if not raw_text:
                raise ValueError("任务缺少原始文本")

            # Agent A: 提取班级信息
            class_info_agent = ScheduleFileClassInfoAgent()
            class_info_raw = class_info_agent.extract(raw_text)

            # Agent B: 解析课程
            course_agent = ScheduleFileCourseParseAgent()
            course_result = course_agent.extract(raw_text)

            courses_raw = course_result.get("courses", [])
            parse_error = course_result.get("error")

            # 如果课表完全无法提取
            if not courses_raw and parse_error:
                task.status = "failed"
                task.error_message = parse_error
                task.completed_at = datetime.now(timezone.utc)
                result = dict(task.result_payload or {})
                result["task_stage"] = "parsing"
                result["parse_success"] = False
                result["parse_error"] = parse_error
                task.result_payload = result
                self.db.commit()
                return

            # 匹配班主任
            class_info = self._resolve_class_info(class_info_raw)
            # 匹配教官
            courses = self._resolve_courses(courses_raw)

            result = dict(task.result_payload or {})
            result["task_stage"] = "class_info_confirmation"
            result["parse_success"] = True
            result["parse_error"] = parse_error
            result["class_info"] = class_info
            result["courses"] = courses
            task.result_payload = result
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
            self.db.commit()

        except Exception as exc:
            logger.opt(exception=True).error("智能解析课表任务 {} 执行异常: {}", task_id, exc)
            try:
                self.db.rollback()
                task.status = "failed"
                task.error_message = str(exc)[:2000]
                task.completed_at = datetime.now(timezone.utc)
                result = dict(task.result_payload or {})
                result["parse_success"] = False
                result["parse_error"] = str(exc)[:2000]
                task.result_payload = result
                self.db.commit()
            except Exception as db_exc:
                logger.error("更新任务 {} 失败状态时出错: {}", task_id, db_exc)
                raise exc  # 让 Celery 重试或调用 _mark_task_failed

    # ------------------------------------------------------------------
    # 详情
    # ------------------------------------------------------------------
    def get_task_detail(self, task_id: int, current_user_id: int) -> ScheduleFileParseTaskDetailResponse:
        task = self.db.query(AITask).filter(AITask.id == task_id).first()
        if not task:
            raise ValueError("任务不存在")
        if task.created_by != current_user_id:
            raise ValueError("无权访问此任务")
        return self._build_detail_response(task)

    # ------------------------------------------------------------------
    # 更新（步骤 2-4）
    # ------------------------------------------------------------------
    def update_task(
        self,
        task_id: int,
        data: ScheduleFileParseTaskUpdateRequest,
        current_user_id: int,
    ) -> ScheduleFileParseTaskDetailResponse:
        task = self.db.query(AITask).filter(AITask.id == task_id).first()
        if not task:
            raise ValueError("任务不存在")
        if task.created_by != current_user_id:
            raise ValueError("无权操作此任务")
        if task.status not in ("completed",):
            raise ValueError("当前任务状态不支持更新")

        result = dict(task.result_payload or {})

        if data.task_name:
            task.task_name = data.task_name[:200]

        if data.confirmed_class_info is not None:
            result["confirmed_class_info"] = data.confirmed_class_info.model_dump()
            # 步骤 2 → 步骤 3
            if result.get("task_stage") == "class_info_confirmation":
                result["task_stage"] = "course_confirmation"

        if data.confirmed_courses is not None:
            result["confirmed_courses"] = [c.model_dump() for c in data.confirmed_courses]
            # 步骤 3 → 步骤 4
            if result.get("task_stage") == "course_confirmation":
                result["task_stage"] = "training_config"

        if data.training_config is not None:
            result["training_config"] = data.training_config.model_dump()
            # 步骤 4 → 步骤 5
            if result.get("task_stage") == "training_config":
                result["task_stage"] = "preview"

        # 允许前端直接指定阶段（回退场景）
        if data.current_stage is not None:
            result["task_stage"] = data.current_stage

        task.result_payload = result
        self.db.commit()
        self.db.refresh(task)
        return self._build_detail_response(task)

    # ------------------------------------------------------------------
    # 确认（步骤 6 - 创建培训班）
    # ------------------------------------------------------------------
    def confirm_task(self, task_id: int, current_user_id: int) -> ScheduleFileParseTaskDetailResponse:
        task = self.db.query(AITask).filter(AITask.id == task_id).first()
        if not task:
            raise ValueError("任务不存在")
        if task.created_by != current_user_id:
            raise ValueError("无权操作此任务")
        if task.status != "completed":
            raise ValueError("当前任务状态不支持确认")

        result = dict(task.result_payload or {})
        stage = result.get("task_stage")
        if stage not in ("training_config", "preview"):
            raise ValueError("请先完成所有步骤后再确认")

        confirmed_class = result.get("confirmed_class_info") or result.get("class_info")
        confirmed_courses = result.get("confirmed_courses") or result.get("courses")
        training_config = result.get("training_config") or {}

        if not confirmed_class:
            raise ValueError("缺少班级信息")

        # 构建培训班创建数据
        from app.schemas.training import TrainingCreate, TrainingCourseCreate
        from app.services.training import TrainingService

        class_info = ScheduleFileClassInfo(**confirmed_class) if isinstance(confirmed_class, dict) else confirmed_class
        config = ScheduleFileTrainingConfig(**training_config) if isinstance(training_config, dict) else training_config

        # 自动创建需要的教官账号
        created_instructors = self._auto_create_instructors(confirmed_class, confirmed_courses or [])

        # 重新解析教官 ID（创建后已有 ID）
        instructor_id = self._resolve_headteacher_as_instructor(class_info)

        # 构建课程列表
        courses_payload = self._build_courses_payload(confirmed_courses or [])

        training_data = TrainingCreate(
            name=class_info.name or "未命名培训班",
            type=config.type if config else "basic",
            start_date=class_info.start_date,
            end_date=class_info.end_date,
            location=class_info.location,
            training_base_id=class_info.training_base_id,
            capacity=class_info.capacity or 30,
            instructor_id=instructor_id,
            department_id=config.department_id if config else None,
            police_type_id=config.police_type_id if config else None,
            visibility_scope=config.visibility_scope if config else "all",
            visibility_department_ids=config.visibility_department_ids if config else None,
            description=config.description if config else None,
            enrollment_requires_approval=config.enrollment_requires_approval if config else True,
            admission_exam_id=config.admission_exam_id if config else None,
            enrollment_start_at=config.enrollment_start_at if config else None,
            enrollment_end_at=config.enrollment_end_at if config else None,
            class_code=config.class_code if config else None,
            courses=courses_payload,
        )

        training_service = TrainingService(self.db)
        training_response = training_service.create_training(training_data, current_user_id)

        result["confirmed_training_id"] = training_response.id
        result["task_stage"] = "confirmed"
        result["created_instructors"] = created_instructors
        task.result_payload = result
        task.status = "confirmed"
        task.confirmed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(task)
        return self._build_detail_response(task)

    # ------------------------------------------------------------------
    # 标记失败
    # ------------------------------------------------------------------
    def mark_task_failed(self, task_id: int, error_message: str) -> None:
        try:
            self.db.rollback()
        except Exception:
            pass
        task = self.db.query(AITask).filter(AITask.id == task_id).first()
        if not task:
            return
        task.status = "failed"
        task.error_message = error_message[:2000]
        task.completed_at = datetime.now(timezone.utc)
        self.db.commit()

    # ==================================================================
    # 私有方法
    # ==================================================================

    def _resolve_class_info(self, raw: dict) -> dict:
        """匹配班主任到用户表、地点到培训基地"""
        headteachers = []
        for ht in (raw.get("headteachers") or []):
            name = ht.get("name", "")
            user = self._find_user_by_name(name)
            headteachers.append({
                "name": name,
                "role_label": ht.get("role_label", "班主任"),
                "user_id": user.id if user else None,
                "auto_create": user is None,
            })

        location = raw.get("location")
        training_base_id = None
        location_source = "manual"
        if location:
            base = self._fuzzy_match_training_base(location)
            if base:
                training_base_id = base.id
                location_source = "base"
                location = base.location or location

        return {
            "name": raw.get("name"),
            "start_date": raw.get("start_date"),
            "end_date": raw.get("end_date"),
            "capacity": raw.get("capacity"),
            "location": location,
            "location_source": location_source,
            "training_base_id": training_base_id,
            "headteachers": headteachers,
        }

    def _resolve_courses(self, courses_raw: list) -> list:
        """匹配课程中的教官到用户表"""
        courses = []
        for c in courses_raw:
            primary = {"name": None, "user_id": None, "auto_create": False}
            pname = c.get("primary_instructor_name")
            if pname:
                user = self._find_user_by_name(pname)
                primary = {"name": pname, "user_id": user.id if user else None, "auto_create": user is None}

            assistants = []
            for aname in (c.get("assistant_instructor_names") or []):
                if aname:
                    user = self._find_user_by_name(aname)
                    assistants.append({"name": aname, "user_id": user.id if user else None, "auto_create": user is None})

            courses.append({
                "name": c.get("name"),
                "type": c.get("type", "theory"),
                "location": c.get("location"),
                "primary_instructor": primary,
                "assistant_instructors": assistants,
                "sessions": c.get("sessions", []),
            })
        return courses

    def _find_user_by_name(self, name: str) -> User | None:
        if not name:
            return None
        return self.db.query(User).filter(
            (User.nickname == name) | (User.username == name)
        ).first()

    def _fuzzy_match_training_base(self, location: str) -> TrainingBase | None:
        if not location:
            return None
        return self.db.query(TrainingBase).filter(
            TrainingBase.name.ilike(f"%{location}%")
        ).first()

    def _auto_create_instructors(self, class_info: Any, courses: list) -> list[str]:
        """自动创建不存在的教官账号，返回已创建的姓名列表"""
        from app.services.auth import AuthService
        auth_service = AuthService()
        instructor_role = self.db.query(Role).filter(Role.code == "instructor").first()

        names_to_create: set[str] = set()

        # 收集班主任
        headteachers = []
        if isinstance(class_info, dict):
            headteachers = class_info.get("headteachers", [])
        elif hasattr(class_info, "headteachers"):
            headteachers = [ht.model_dump() if hasattr(ht, "model_dump") else ht for ht in class_info.headteachers]
        for ht in headteachers:
            if isinstance(ht, dict) and ht.get("auto_create") and ht.get("name"):
                names_to_create.add(ht["name"])

        # 收集教官
        for c in courses:
            if isinstance(c, dict):
                pi = c.get("primary_instructor") or {}
                if isinstance(pi, dict) and pi.get("auto_create") and pi.get("name"):
                    names_to_create.add(pi["name"])
                for ai in (c.get("assistant_instructors") or []):
                    if isinstance(ai, dict) and ai.get("auto_create") and ai.get("name"):
                        names_to_create.add(ai["name"])

        created = []
        for name in names_to_create:
            existing = self._find_user_by_name(name)
            if existing:
                continue
            username = self._build_unique_username(name)
            new_user = User(
                username=username,
                password_hash=auth_service.get_password_hash(DEFAULT_PASSWORD),
                nickname=name,
                is_active=True,
            )
            if instructor_role:
                new_user.roles = [instructor_role]
            self.db.add(new_user)
            self.db.flush()
            created.append(name)

        return created

    def _build_unique_username(self, seed: str) -> str:
        base = re.sub(r"[^a-zA-Z0-9_]+", "", str(seed or "").strip())
        if not base:
            base = "user"
        base = base[:40]
        if len(base) < 3:
            base = f"{base}usr"
        candidate = base
        index = 1
        while self.db.query(User.id).filter(User.username == candidate).first():
            suffix = f"_{index}"
            candidate = f"{base[:50 - len(suffix)]}{suffix}"
            index += 1
        return candidate

    def _resolve_headteacher_as_instructor(self, class_info: ScheduleFileClassInfo) -> int | None:
        """取第一个班主任作为培训班的 instructor_id"""
        for ht in (class_info.headteachers or []):
            if ht.user_id:
                return ht.user_id
            user = self._find_user_by_name(ht.name)
            if user:
                return user.id
        return None

    def _build_courses_payload(self, courses: list) -> list:
        """构建 TrainingCourseCreate 列表"""
        from app.schemas.training import TrainingCourseCreate, TrainingScheduleItem
        result = []
        for c in courses:
            if isinstance(c, dict):
                c_obj = ScheduleFileCourse(**c)
            else:
                c_obj = c

            primary_id = None
            instructor_name = None
            if c_obj.primary_instructor and c_obj.primary_instructor.name:
                instructor_name = c_obj.primary_instructor.name
                if c_obj.primary_instructor.user_id:
                    primary_id = c_obj.primary_instructor.user_id
                else:
                    user = self._find_user_by_name(c_obj.primary_instructor.name)
                    if user:
                        primary_id = user.id

            assistant_ids = []
            for ai in (c_obj.assistant_instructors or []):
                if ai.user_id:
                    assistant_ids.append(ai.user_id)
                elif ai.name:
                    user = self._find_user_by_name(ai.name)
                    if user:
                        assistant_ids.append(user.id)

            schedules = []
            for s in (c_obj.sessions or []):
                session_id = str(uuid.uuid4())
                time_range = f"{s.time_start}~{s.time_end}"
                # 计算课时
                try:
                    h1, m1 = map(int, s.time_start.split(":"))
                    h2, m2 = map(int, s.time_end.split(":"))
                    hours = round((h2 * 60 + m2 - h1 * 60 - m1) / 60, 2)
                except Exception:
                    hours = 0
                schedules.append(TrainingScheduleItem(
                    session_id=session_id,
                    date=s.date,
                    time_range=time_range,
                    hours=max(hours, 0),
                    location=s.location or c_obj.location,
                    status="pending",
                ))

            total_hours = sum(sc.hours for sc in schedules)

            result.append(TrainingCourseCreate(
                course_key=str(uuid.uuid4()),
                name=c_obj.name,
                location=c_obj.location,
                instructor=instructor_name,
                primary_instructor_id=primary_id,
                assistant_instructor_ids=assistant_ids,
                hours=round(total_hours, 2),
                type=c_obj.type,
                schedules=schedules,
            ))
        return result

    # ------------------------------------------------------------------
    # 响应构建
    # ------------------------------------------------------------------
    def _to_task_summary(self, task: AITask) -> AITaskSummaryResponse:
        rp = task.result_payload or {}
        req = task.request_payload or {}
        courses = rp.get("courses") or rp.get("confirmed_courses") or []
        return AITaskSummaryResponse(
            id=task.id,
            task_name=task.task_name,
            task_type=task.task_type,
            status=task.status,
            task_stage=rp.get("task_stage"),
            item_count=len(courses),
            summary_text=req.get("file_name"),
            created_by=task.created_by,
            can_delete=task.status in ("pending", "failed"),
            created_at=task.created_at,
            completed_at=task.completed_at,
            confirmed_at=task.confirmed_at,
            updated_at=task.updated_at,
        )

    def _build_detail_response(self, task: AITask) -> ScheduleFileParseTaskDetailResponse:
        rp = task.result_payload or {}
        req = task.request_payload or {}
        return ScheduleFileParseTaskDetailResponse(
            id=task.id,
            task_name=task.task_name,
            task_type=task.task_type,
            status=task.status,
            task_stage=rp.get("task_stage"),
            created_by=task.created_by,
            created_at=task.created_at,
            completed_at=task.completed_at,
            confirmed_at=task.confirmed_at,
            updated_at=task.updated_at,
            can_delete=task.status in ("pending", "failed"),
            error_message=task.error_message,
            file_name=req.get("file_name"),
            class_info=rp.get("class_info"),
            courses=rp.get("courses") or [],
            parse_success=rp.get("parse_success", False),
            parse_error=rp.get("parse_error"),
            confirmed_class_info=rp.get("confirmed_class_info"),
            confirmed_courses=rp.get("confirmed_courses"),
            training_config=rp.get("training_config"),
            confirmed_training_id=rp.get("confirmed_training_id"),
        )
