"""
初始化数据脚本
"""
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.database import engine, init_db
from app.models import User, Role, Permission, Department, PoliceType
from app.models.permission import PermissionGroup
from app.models.training_type import TrainingType
from app.models.dict_instructor_specialty import DictInstructorSpecialty
from app.models.dict_teaching_direction import DictTeachingDirection
from app.models.evaluation import EvaluationTemplate, EvaluationDimension
from app.models.system import SystemMeta
from app.services.auth import auth_service
from app.services.system import SystemConfigService
from app.utils.permission_group import infer_permission_group
from logger import logger


def init_permission_groups():
    """初始化权限组（每次运行都同步，补充缺失的组）"""
    groups_data = [
        {"group_key": "SYSTEM", "group_name": "系统基础", "description": "系统基础权限", "sort_order": 0},
        {"group_key": "AUTH", "group_name": "认证鉴权", "description": "登录、密码、Token 相关", "sort_order": 1},
        {"group_key": "USER_MANAGEMENT", "group_name": "用户管理", "description": "用户增删改查、导入导出", "sort_order": 2},
        {"group_key": "ROLE_MANAGEMENT", "group_name": "角色管理", "description": "角色与权限分配", "sort_order": 3},
        {"group_key": "PERMISSION_MANAGEMENT", "group_name": "权限管理", "description": "权限维护与同步", "sort_order": 4},
        {"group_key": "DEPARTMENT_MANAGEMENT", "group_name": "部门管理", "description": "部门树与部门权限", "sort_order": 5},
        {"group_key": "POLICE_TYPE_MANAGEMENT", "group_name": "警种管理", "description": "警种维护", "sort_order": 6},
        {"group_key": "COURSE_MANAGEMENT", "group_name": "课程管理", "description": "课程资源与学习进度", "sort_order": 10},
        {"group_key": "EXAM_MANAGEMENT", "group_name": "考试管理", "description": "考试、成绩与试卷", "sort_order": 11},
        {"group_key": "QUESTION_BANK", "group_name": "题库管理", "description": "题目与知识点维护", "sort_order": 12},
        {"group_key": "TRAINING_MANAGEMENT", "group_name": "培训管理", "description": "培训班、签到、报名", "sort_order": 13},
        {"group_key": "CERTIFICATE_MANAGEMENT", "group_name": "证书管理", "description": "结业证书签发", "sort_order": 14},
        {"group_key": "RESOURCE_REVIEW", "group_name": "资源与审核", "description": "资源库、审核工作流", "sort_order": 15},
        {"group_key": "AI", "group_name": "AI 智能任务", "description": "智能出题、组卷、排课等", "sort_order": 20},
        {"group_key": "PROFILE", "group_name": "个人中心", "description": "个人信息与学习统计", "sort_order": 30},
        {"group_key": "DASHBOARD", "group_name": "工作台", "description": "工作台数据", "sort_order": 31},
        {"group_key": "REPORT", "group_name": "数据看板", "description": "KPI、趋势、排名等", "sort_order": 32},
        {"group_key": "TALENT", "group_name": "人才库", "description": "人才列表与统计", "sort_order": 33},
    ]
    try:
        with Session(engine) as db:
            existing_keys = {g.group_key for g in db.query(PermissionGroup).all()}
            added = []
            for gd in groups_data:
                if gd["group_key"] not in existing_keys:
                    db.add(PermissionGroup(**gd, is_active=True))
                    added.append(gd["group_key"])
            if added:
                db.commit()
                logger.info(f"权限组补充完成: {', '.join(added)}")
            else:
                logger.info("权限组已是最新，无需补充")
    except Exception as e:
        logger.error(f"初始化权限组失败: {e}")
        raise


def sync_permission_group_ids():
    """同步权限的 group_id 外键（根据 group 字段匹配权限组）"""
    try:
        with Session(engine) as db:
            group_map = {g.group_key: g.id for g in db.query(PermissionGroup).all()}
            if not group_map:
                return
            updated = 0
            for perm in db.query(Permission).filter(Permission.group_id.is_(None)).all():
                gid = group_map.get(perm.group)
                if gid:
                    perm.group_id = gid
                    updated += 1
            if updated:
                db.commit()
                logger.info(f"已为 {updated} 个权限关联权限组")
    except Exception as e:
        logger.error(f"同步权限组关联失败: {e}")
        raise


def init_permissions():
    """初始化权限数据"""
    try:
        with Session(engine) as db:
            existing_count = db.query(Permission).count()
            if existing_count > 0:
                logger.info("权限数据已存在，跳过初始化")
                return

            permissions_data = [
                # 认证相关权限
                {"path": "/api/v1/auth/me", "code": "GET_CURRENT_USER", "description": "获取当前用户信息"},
                {"path": "/api/v1/auth/change-password", "code": "CHANGE_PASSWORD", "description": "修改密码"},

                # 用户管理权限
                {"path": "/api/v1/users/create", "code": "CREATE_USER", "description": "创建用户"},
                {"path": "/api/v1/users/{user_id}/detail", "code": "GET_USER", "description": "获取用户详情"},
                {"path": "/api/v1/users/list", "code": "GET_USERS", "description": "获取用户列表"},
                {"path": "/api/v1/users/{user_id}/update", "code": "UPDATE_USER", "description": "更新用户"},
                {"path": "/api/v1/users/{user_id}/delete", "code": "DELETE_USER", "description": "删除用户"},
                {"path": "/api/v1/users/{user_id}/roles", "code": "UPDATE_USER_ROLES", "description": "更新用户角色"},
                {"path": "/api/v1/users/{user_id}/departments", "code": "UPDATE_USER_DEPARTMENTS", "description": "更新用户部门"},
                {"path": "/api/v1/users/import/template", "code": "DOWNLOAD_USER_IMPORT_TEMPLATE", "description": "下载用户导入模板"},
                {"path": "/api/v1/users/export", "code": "EXPORT_USERS", "description": "导出用户"},
                {"path": "/api/v1/users/import", "code": "IMPORT_USERS", "description": "导入用户"},

                # 角色管理权限
                {"path": "/api/v1/roles", "code": "CREATE_ROLE", "description": "创建角色"},
                {"path": "/api/v1/roles/{role_id}/detail", "code": "GET_ROLE", "description": "获取角色详情"},
                {"path": "/api/v1/roles/list", "code": "GET_ROLES", "description": "获取角色列表"},
                {"path": "/api/v1/roles/{role_id}/update", "code": "UPDATE_ROLE", "description": "更新角色"},
                {"path": "/api/v1/roles/{role_id}/delete", "code": "DELETE_ROLE", "description": "删除角色"},
                {"path": "/api/v1/roles/{role_id}/permissions", "code": "UPDATE_ROLE_PERMISSIONS", "description": "更新角色权限"},
                {"path": "/api/v1/roles/import/template", "code": "DOWNLOAD_ROLE_IMPORT_TEMPLATE", "description": "下载角色导入模板"},
                {"path": "/api/v1/roles/export", "code": "EXPORT_ROLES", "description": "导出角色"},
                {"path": "/api/v1/roles/import", "code": "IMPORT_ROLES", "description": "导入角色"},

                # 权限管理权限
                {"path": "/api/v1/permissions", "code": "CREATE_PERMISSION", "description": "创建权限"},
                {"path": "/api/v1/permissions/{permission_id}/detail", "code": "GET_PERMISSION", "description": "获取权限详情"},
                {"path": "/api/v1/permissions/list", "code": "GET_PERMISSIONS", "description": "获取权限列表"},
                {"path": "/api/v1/permissions/{permission_id}/update", "code": "UPDATE_PERMISSION", "description": "更新权限"},
                {"path": "/api/v1/permissions/{permission_id}/delete", "code": "DELETE_PERMISSION", "description": "删除权限"},
                {"path": "/api/v1/permissions/sync", "code": "SYNC_PERMISSIONS", "description": "同步权限"},

                # 部门管理权限
                {"path": "/api/v1/departments", "code": "CREATE_DEPARTMENT", "description": "创建部门"},
                {"path": "/api/v1/departments/{department_id}/detail", "code": "GET_DEPARTMENT", "description": "获取部门详情"},
                {"path": "/api/v1/departments/list", "code": "GET_DEPARTMENTS", "description": "获取部门列表"},
                {"path": "/api/v1/departments/tree", "code": "GET_DEPARTMENT_TREE", "description": "获取部门树形结构"},
                {"path": "/api/v1/departments/{department_id}/update", "code": "UPDATE_DEPARTMENT", "description": "更新部门"},
                {"path": "/api/v1/departments/{department_id}", "code": "DELETE_DEPARTMENT", "description": "删除部门"},
                {"path": "/api/v1/departments/{department_id}/permissions", "code": "UPDATE_DEPARTMENT_PERMISSIONS", "description": "更新部门权限"},
                {"path": "/api/v1/departments/import/template", "code": "DOWNLOAD_DEPARTMENT_IMPORT_TEMPLATE", "description": "下载部门导入模板"},
                {"path": "/api/v1/departments/export", "code": "EXPORT_DEPARTMENTS", "description": "导出部门"},
                {"path": "/api/v1/departments/import", "code": "IMPORT_DEPARTMENTS", "description": "导入部门"},

                # 系统权限
                {"path": "/", "code": "ROOT", "description": "根路径访问"},
                {"path": "/health", "code": "HEALTH_CHECK", "description": "健康检查"},

                # ====== 警务培训平台业务权限 ======

                # 课程管理
                {"path": "/api/v1/courses", "code": "GET_COURSES", "description": "获取课程列表"},
                {"path": "/api/v1/courses/create", "code": "CREATE_COURSE", "description": "创建课程"},
                {"path": "/api/v1/courses/{id}", "code": "GET_COURSE_DETAIL", "description": "获取课程详情"},
                {"path": "/api/v1/courses/{id}/update", "code": "UPDATE_COURSE", "description": "更新课程"},
                {"path": "/api/v1/courses/progress", "code": "GET_COURSE_PROGRESS", "description": "获取学习进度"},
                {"path": "/api/v1/courses/{id}/chapters/{chapter_id}/progress", "code": "UPDATE_CHAPTER_PROGRESS", "description": "更新章节进度"},

                # 考试管理
                {"path": "/api/v1/exams", "code": "GET_EXAMS", "description": "获取考试列表"},
                {"path": "/api/v1/exams/create", "code": "CREATE_EXAM", "description": "创建考试"},
                {"path": "/api/v1/exams/{id}", "code": "GET_EXAM_DETAIL", "description": "获取考试详情"},
                {"path": "/api/v1/exams/{id}/submit", "code": "SUBMIT_EXAM", "description": "提交考试"},
                {"path": "/api/v1/exams/{id}/result", "code": "GET_EXAM_RESULT", "description": "获取考试结果"},
                {"path": "/api/v1/exams/{id}/scores", "code": "GET_EXAM_SCORES", "description": "获取成绩管理"},

                # 题库管理
                {"path": "/api/v1/questions", "code": "GET_QUESTIONS", "description": "获取题目列表"},
                {"path": "/api/v1/questions/create", "code": "CREATE_QUESTION", "description": "创建题目"},
                {"path": "/api/v1/questions/{id}/update", "code": "UPDATE_QUESTION", "description": "更新题目"},
                {"path": "/api/v1/questions/{id}/delete", "code": "DELETE_QUESTION", "description": "删除题目"},
                {"path": "/api/v1/questions/batch", "code": "BATCH_CREATE_QUESTIONS", "description": "批量导入题目"},
                {"path": "/api/v1/knowledge-points", "code": "GET_KNOWLEDGE_POINTS", "description": "获取知识点列表"},
                {"path": "/api/v1/knowledge-points/create", "code": "CREATE_KNOWLEDGE_POINT", "description": "创建知识点"},
                {"path": "/api/v1/knowledge-points/{id}/update", "code": "UPDATE_KNOWLEDGE_POINT", "description": "更新知识点"},
                {"path": "/api/v1/knowledge-points/{id}/delete", "code": "DELETE_KNOWLEDGE_POINT", "description": "删除知识点"},

                # 培训管理
                {"path": "/api/v1/trainings", "code": "GET_TRAININGS", "description": "获取培训列表"},
                {"path": "/api/v1/trainings/create", "code": "CREATE_TRAINING", "description": "创建培训班"},
                {"path": "/api/v1/trainings/{id}", "code": "GET_TRAINING_DETAIL", "description": "获取培训详情"},
                {"path": "/api/v1/trainings/{id}/update", "code": "UPDATE_TRAINING", "description": "更新培训班"},
                {"path": "/api/v1/trainings/{id}/manage", "code": "MANAGE_TRAINING", "description": "管理端更新培训班"},
                {"path": "/api/v1/trainings/{id}/delete", "code": "DELETE_TRAINING", "description": "删除培训班"},
                {"path": "/api/v1/trainings/{id}/students", "code": "GET_TRAINING_STUDENTS", "description": "获取培训学员"},
                {"path": "/api/v1/trainings/{id}/schedule", "code": "GET_TRAINING_SCHEDULE", "description": "获取训练计划"},
                {"path": "/api/v1/trainings/{id}/enroll", "code": "ENROLL_TRAINING", "description": "培训报名"},
                {"path": "/api/v1/trainings/{id}/enrollments", "code": "GET_ENROLLMENTS", "description": "获取报名列表"},
                {"path": "/api/v1/trainings/{id}/enrollments/{eid}/approve", "code": "APPROVE_ENROLLMENT", "description": "审批通过"},
                {"path": "/api/v1/trainings/{id}/enrollments/{eid}/reject", "code": "REJECT_ENROLLMENT", "description": "审批拒绝"},
                {"path": "/api/v1/trainings/{id}/courses", "code": "GET_TRAINING_COURSES", "description": "获取培训课程列表"},
                {"path": "/api/v1/trainings/{id}/checkin/records", "code": "GET_CHECKIN_RECORDS", "description": "获取签到记录"},
                {"path": "/api/v1/trainings/{id}/checkin", "code": "CHECKIN", "description": "签到"},
                {"path": "/api/v1/trainings/{id}/checkin/qr", "code": "GET_CHECKIN_QR", "description": "生成签到二维码"},

                # 证书管理
                {"path": "/api/v1/certificates", "code": "GET_CERTIFICATES", "description": "获取证书列表"},
                {"path": "/api/v1/certificates/create", "code": "CREATE_CERTIFICATE", "description": "签发证书"},

                # 个人中心
                {"path": "/api/v1/profile", "code": "GET_PROFILE", "description": "获取个人信息"},
                {"path": "/api/v1/profile/update", "code": "UPDATE_PROFILE", "description": "更新个人信息"},
                {"path": "/api/v1/profile/study-stats", "code": "GET_STUDY_STATS", "description": "获取学习统计"},
                {"path": "/api/v1/profile/exam-history", "code": "GET_EXAM_HISTORY", "description": "获取考试历史"},

                # 数据看板
                {"path": "/api/v1/report/kpi", "code": "GET_REPORT_KPI", "description": "获取KPI数据"},
                {"path": "/api/v1/report/trend", "code": "GET_REPORT_TREND", "description": "获取月度趋势"},
                {"path": "/api/v1/report/police-type-distribution", "code": "GET_POLICE_TYPE_DIST", "description": "获取警种分布"},
                {"path": "/api/v1/report/city-ranking", "code": "GET_CITY_RANKING", "description": "获取城市排名"},

                # AI任务
                {"path": "/api/v1/ai/question-tasks", "code": "GET_AI_QUESTION_TASKS", "description": "获取 AI 智能出题任务"},
                {"path": "/api/v1/ai/question-tasks", "code": "CREATE_AI_QUESTION_TASK", "description": "创建 AI 智能出题任务"},
                {"path": "/api/v1/ai/question-tasks/{task_id}/result", "code": "UPDATE_AI_QUESTION_TASK", "description": "更新 AI 智能出题任务"},
                {"path": "/api/v1/ai/question-tasks/{task_id}/confirm", "code": "CONFIRM_AI_QUESTION_TASK", "description": "确认 AI 智能出题任务"},
                {"path": "/api/v1/ai/paper-assembly-tasks", "code": "GET_AI_PAPER_ASSEMBLY_TASKS", "description": "获取 AI 自动组卷任务"},
                {"path": "/api/v1/ai/paper-assembly-tasks", "code": "CREATE_AI_PAPER_ASSEMBLY_TASK", "description": "创建 AI 自动组卷任务"},
                {"path": "/api/v1/ai/paper-assembly-tasks/{task_id}/result", "code": "UPDATE_AI_PAPER_ASSEMBLY_TASK", "description": "更新 AI 自动组卷任务"},
                {"path": "/api/v1/ai/paper-assembly-tasks/{task_id}/confirm", "code": "CONFIRM_AI_PAPER_ASSEMBLY_TASK", "description": "确认 AI 自动组卷任务"},
                {"path": "/api/v1/ai/paper-generation-tasks", "code": "GET_AI_PAPER_GENERATION_TASKS", "description": "获取 AI 自动生成试卷任务"},
                {"path": "/api/v1/ai/paper-generation-tasks", "code": "CREATE_AI_PAPER_GENERATION_TASK", "description": "创建 AI 自动生成试卷任务"},
                {"path": "/api/v1/ai/paper-generation-tasks/{task_id}/result", "code": "UPDATE_AI_PAPER_GENERATION_TASK", "description": "更新 AI 自动生成试卷任务"},
                {"path": "/api/v1/ai/paper-generation-tasks/{task_id}/confirm", "code": "CONFIRM_AI_PAPER_GENERATION_TASK", "description": "确认 AI 自动生成试卷任务"},

                # 人才库
                {"path": "/api/v1/talent", "code": "GET_TALENTS", "description": "获取人才列表"},
                {"path": "/api/v1/talent/stats", "code": "GET_TALENT_STATS", "description": "获取人才统计"},

                # 工作台
                {"path": "/api/v1/dashboard", "code": "GET_DASHBOARD", "description": "获取工作台数据"},

                # 资源库与审核推荐
                {"path": "/api/v1/resources", "code": "CREATE_RESOURCE", "description": "创建资源"},
                {"path": "/api/v1/resources/{id}", "code": "UPDATE_RESOURCE", "description": "更新资源"},
                {"path": "/api/v1/resources/list", "code": "VIEW_RESOURCE_ALL", "description": "全局查看资源"},
                {"path": "/api/v1/resources/list/department", "code": "VIEW_RESOURCE_DEPARTMENT", "description": "按部门查看资源"},
                {"path": "/api/v1/resources/{id}/visibility", "code": "MANAGE_RESOURCE_VISIBILITY", "description": "管理资源可见域"},
                {"path": "/api/v1/resources/{id}/submit", "code": "SUBMIT_RESOURCE_REVIEW", "description": "提交资源审核"},
                {"path": "/api/v1/ai/teaching-resource-generation-tasks", "code": "USE_TEACHING_RESOURCE_GENERATION", "description": "使用教学资源生成功能"},
                {"path": "/api/v1/reviews/tasks", "code": "REVIEW_RESOURCE_STAGE1", "description": "资源一级审核"},
                {"path": "/api/v1/reviews/tasks", "code": "REVIEW_RESOURCE_STAGE2", "description": "资源二级审核"},
                {"path": "/api/v1/review-policies", "code": "MANAGE_REVIEW_POLICY", "description": "管理审核策略"},

                # 警种管理
                {"path": "/api/v1/police-types", "code": "GET_POLICE_TYPES", "description": "获取警种列表"},
                {"path": "/api/v1/police-types/create", "code": "CREATE_POLICE_TYPE", "description": "创建警种"},
                {"path": "/api/v1/police-types/{id}", "code": "GET_POLICE_TYPE_DETAIL", "description": "获取警种详情"},
                {"path": "/api/v1/police-types/{id}/update", "code": "UPDATE_POLICE_TYPE", "description": "更新警种"},
                {"path": "/api/v1/police-types/{id}/delete", "code": "DELETE_POLICE_TYPE", "description": "删除警种"},
                {"path": "/api/v1/users/{user_id}/police-types", "code": "UPDATE_USER_POLICE_TYPES", "description": "更新用户警种"},
            ]

            for perm_data in permissions_data:
                permission = Permission(
                    path=perm_data["path"],
                    code=perm_data["code"],
                    group=(perm_data.get("group") or "").strip() or infer_permission_group(perm_data["path"]),
                    description=perm_data["description"],
                    is_active=True
                )
                db.add(permission)

            db.commit()
            logger.info(f"权限数据初始化完成，共创建 {len(permissions_data)} 个权限")

    except Exception as e:
        logger.error(f"初始化权限数据失败: {e}")
        raise


def init_departments():
    """初始化部门数据"""
    try:
        with Session(engine) as db:
            existing_count = db.query(Department).count()
            if existing_count > 0:
                logger.info("部门数据已存在，跳过初始化")
                return

            root_dept = Department(
                name="总部",
                code="ROOT",
                parent_id=None,
                inherit_sub_permissions=True,
                description="总部",
                is_active=True
            )
            db.add(root_dept)
            db.flush()

            db.commit()
            logger.info("部门数据初始化完成")

    except Exception as e:
        logger.error(f"初始化部门数据失败: {e}")
        raise


def init_police_types():
    """初始化警种数据"""
    try:
        with Session(engine) as db:
            existing_count = db.query(PoliceType).count()
            if existing_count > 0:
                logger.info("警种数据已存在，跳过初始化")
                return

            police_types_data = [
                {"name": "管理", "code": "MANAGEMENT", "description": "管理警种"},
                {"name": "刑侦", "code": "CRIMINAL_INVESTIGATION", "description": "刑事侦查"},
                {"name": "治安", "code": "PUBLIC_SECURITY", "description": "治安管理"},
                {"name": "交通", "code": "TRAFFIC", "description": "交通管理"},
                {"name": "网安", "code": "CYBER_SECURITY", "description": "网络安全"},
                {"name": "特警", "code": "SWAT", "description": "特种警察"},
                {"name": "禁毒", "code": "ANTI_NARCOTICS", "description": "禁毒"},
                {"name": "经侦", "code": "ECONOMIC_CRIME", "description": "经济犯罪侦查"},
            ]

            for pt_data in police_types_data:
                pt = PoliceType(
                    name=pt_data["name"],
                    code=pt_data["code"],
                    description=pt_data["description"],
                    is_active=True
                )
                db.add(pt)

            db.commit()
            logger.info(f"警种数据初始化完成，共创建 {len(police_types_data)} 个警种")

    except Exception as e:
        logger.error(f"初始化警种数据失败: {e}")
        raise


def init_roles():
    """初始化角色数据"""
    try:
        with Session(engine) as db:
            existing_count = db.query(Role).count()
            all_permissions = db.query(Permission).all()
            perm_map = {str(p.code): p for p in all_permissions}

            # 角色权限定义
            role_perm_defs = {
                "admin": {
                    "name": "管理员",
                    "description": "系统管理员，拥有所有权限",
                    "data_scopes": ["all"],
                    "perm_codes": None,  # None = 全部权限
                },
                "instructor": {
                    "name": "教官",
                    "description": "教官，负责教学和培训管理",
                    "data_scopes": ["department_and_sub", "police_type", "self"],
                    "perm_codes": [
                        "GET_CURRENT_USER", "CHANGE_PASSWORD", "ROOT", "HEALTH_CHECK",
                        "GET_DASHBOARD",
                        "GET_COURSES", "GET_COURSE_DETAIL",
                        "GET_EXAMS", "CREATE_EXAM", "GET_EXAM_DETAIL", "GET_EXAM_SCORES",
                        "GET_QUESTIONS", "CREATE_QUESTION", "UPDATE_QUESTION", "DELETE_QUESTION", "BATCH_CREATE_QUESTIONS",
                        "GET_KNOWLEDGE_POINTS", "CREATE_KNOWLEDGE_POINT", "UPDATE_KNOWLEDGE_POINT", "DELETE_KNOWLEDGE_POINT",
                        "GET_TRAININGS", "CREATE_TRAINING", "GET_TRAINING_DETAIL", "UPDATE_TRAINING",
                        "GET_TRAINING_STUDENTS", "GET_TRAINING_COURSES", "GET_TRAINING_SCHEDULE",
                        "GET_ENROLLMENTS", "APPROVE_ENROLLMENT", "REJECT_ENROLLMENT",
                        "GET_CHECKIN_RECORDS", "GET_CHECKIN_QR",
                        "GET_CERTIFICATES", "CREATE_CERTIFICATE",
                        "GET_PROFILE", "UPDATE_PROFILE", "GET_STUDY_STATS", "GET_EXAM_HISTORY",
                        "GET_AI_QUESTION_TASKS", "CREATE_AI_QUESTION_TASK", "UPDATE_AI_QUESTION_TASK", "CONFIRM_AI_QUESTION_TASK",
                        "GET_AI_PAPER_ASSEMBLY_TASKS", "CREATE_AI_PAPER_ASSEMBLY_TASK", "UPDATE_AI_PAPER_ASSEMBLY_TASK", "CONFIRM_AI_PAPER_ASSEMBLY_TASK",
                        "GET_AI_PAPER_GENERATION_TASKS", "CREATE_AI_PAPER_GENERATION_TASK", "UPDATE_AI_PAPER_GENERATION_TASK", "CONFIRM_AI_PAPER_GENERATION_TASK",
                        "CREATE_RESOURCE", "UPDATE_RESOURCE", "VIEW_RESOURCE_DEPARTMENT",
                        "USE_TEACHING_RESOURCE_GENERATION",
                        "MANAGE_RESOURCE_VISIBILITY", "SUBMIT_RESOURCE_REVIEW",
                        "REVIEW_RESOURCE_STAGE1", "REVIEW_RESOURCE_STAGE2",
                    ],
                },
                "student": {
                    "name": "学员",
                    "description": "学员，参与学习和考试",
                    "data_scopes": ["department", "police_type", "self"],
                    "perm_codes": [
                        "GET_CURRENT_USER", "CHANGE_PASSWORD", "ROOT", "HEALTH_CHECK",
                        "GET_DASHBOARD",
                        "GET_COURSES", "GET_COURSE_DETAIL", "GET_COURSE_PROGRESS", "UPDATE_CHAPTER_PROGRESS",
                        "GET_EXAMS", "GET_EXAM_DETAIL", "SUBMIT_EXAM", "GET_EXAM_RESULT",
                        "GET_TRAININGS", "GET_TRAINING_DETAIL", "ENROLL_TRAINING",
                        "GET_TRAINING_COURSES", "GET_TRAINING_SCHEDULE",
                        "CHECKIN", "GET_CHECKIN_RECORDS",
                        "GET_CERTIFICATES",
                        "GET_PROFILE", "UPDATE_PROFILE", "GET_STUDY_STATS", "GET_EXAM_HISTORY",
                    ],
                },
            }

            if existing_count > 0:
                # 角色已存在，补充缺失的权限（不替换现有权限）
                for role_code, role_def in role_perm_defs.items():
                    role = db.query(Role).filter(Role.code == role_code).first()
                    if not role:
                        continue
                    if role_def["perm_codes"] is None:
                        # 管理员：确保拥有全部权限
                        target_perms = all_permissions
                    else:
                        target_perms = [perm_map[c] for c in role_def["perm_codes"] if c in perm_map]
                    existing_perm_ids = {p.id for p in role.permissions}
                    added = []
                    for perm in target_perms:
                        if perm.id not in existing_perm_ids:
                            role.permissions.append(perm)
                            added.append(perm.code)
                    if added:
                        logger.info(f"角色 {role_code} 补充权限: {', '.join(added)}")
                db.commit()
                logger.info("角色权限同步完成")
                return

            # 首次初始化：创建角色
            for role_code, role_def in role_perm_defs.items():
                role = Role(
                    code=role_code, name=role_def["name"],
                    description=role_def["description"], is_active=True,
                    data_scopes=role_def["data_scopes"],
                )
                if role_def["perm_codes"] is None:
                    role.permissions = all_permissions
                else:
                    role.permissions = [perm_map[c] for c in role_def["perm_codes"] if c in perm_map]
                db.add(role)

            db.commit()
            logger.info("角色数据初始化完成")

    except Exception as e:
        logger.error(f"初始化角色数据失败: {e}")
        raise


def init_users():
    """初始化用户数据"""
    try:
        with Session(engine) as db:
            existing_count = db.query(User).count()
            if existing_count > 0:
                logger.info("用户数据已存在，跳过初始化")
                return

            admin_role = db.query(Role).filter(Role.code == "admin").first()
            instructor_role = db.query(Role).filter(Role.code == "instructor").first()
            student_role = db.query(Role).filter(Role.code == "student").first()
            root_dept = db.query(Department).filter(Department.code == "ROOT").first()

            if not admin_role or not instructor_role or not student_role:
                logger.error("角色数据不存在，请先初始化角色数据")
                return
            if not root_dept:
                logger.error("部门数据不存在，请先初始化部门数据")
                return

            # 获取警种
            pt_management = db.query(PoliceType).filter(PoliceType.code == "MANAGEMENT").first()
            pt_criminal = db.query(PoliceType).filter(PoliceType.code == "CRIMINAL_INVESTIGATION").first()
            pt_security = db.query(PoliceType).filter(PoliceType.code == "PUBLIC_SECURITY").first()

            # 管理员
            admin_user = User(
                username="admin",
                password_hash=auth_service.get_password_hash("police2025"),
                nickname="系统管理员",
                email="admin@gxpolice.gov.cn",
                phone="13800000001",
                police_id="GX-ADM-001",
                is_active=True
            )
            admin_user.roles = [admin_role]
            admin_user.departments = [root_dept]
            if pt_management:
                admin_user.police_types = [pt_management]
            db.add(admin_user)

            # 教官
            instructor_user = User(
                username="instructor",
                password_hash=auth_service.get_password_hash("teach2025"),
                nickname="张教官",
                email="instructor@gxpolice.gov.cn",
                phone="13800000002",
                police_id="GX-INS-001",
                join_date=date(2010, 7, 1),
                instructor_title="高级教官",
                instructor_level="expert",
                instructor_specialties=["刑事侦查", "反诈骗", "网络安全"],
                instructor_qualification=["公安部认证教官", "广西优秀教官"],
                instructor_certificates=[
                    {"name": "公安部高级教官证书", "issuer": "公安部", "year": 2020},
                    {"name": "广西优秀教官", "issuer": "广西公安厅", "year": 2022}
                ],
                instructor_intro="从事公安教育训练工作15年，主讲刑事侦查和反诈骗课程。",
                instructor_rating=4.8,
                instructor_course_count=12,
                instructor_student_count=560,
                instructor_review_count=230,
                is_active=True
            )
            instructor_user.roles = [instructor_role]
            instructor_user.departments = [root_dept]
            if pt_criminal:
                instructor_user.police_types = [pt_criminal]
            db.add(instructor_user)

            # 学员
            student_user = User(
                username="student",
                password_hash=auth_service.get_password_hash("learn2025"),
                nickname="李学员",
                email="student@gxpolice.gov.cn",
                phone="13800000003",
                police_id="GX-STU-001",
                join_date=date(2020, 9, 1),
                level="中级",
                study_hours=120.5,
                exam_count=8,
                avg_score=82.5,
                is_active=True
            )
            student_user.roles = [student_role]
            student_user.departments = [root_dept]
            if pt_security:
                student_user.police_types = [pt_security]
            db.add(student_user)

            db.commit()
            logger.info("用户数据初始化完成")

    except Exception as e:
        logger.error(f"初始化用户数据失败: {e}")
        raise


def init_system_configs():
    """初始化系统配置数据。"""
    try:
        with Session(engine) as db:
            service = SystemConfigService(db)
            groups = service.sync_initial_config_groups(replace_existing=False)
            logger.info(f"系统配置初始化完成，共同步 {len(groups)} 个配置组")
    except Exception as e:
        logger.error(f"初始化系统配置失败: {e}")
        raise


def is_db_initialized():
    """检查数据库是否已初始化"""
    with Session(engine) as db:
        meta = db.query(SystemMeta).filter(SystemMeta.key == "init").first()
        return meta is not None


def mark_db_initialized():
    """在种子数据全部写入成功后标记数据库已初始化"""
    with Session(engine) as db:
        meta = db.query(SystemMeta).filter(SystemMeta.key == "init").first()
        if meta:
            return

        meta = SystemMeta(key="init", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        db.add(meta)
        db.commit()


def init_dashboard_modules():
    """初始化看板模块默认配置"""
    from app.models.system import DashboardModuleConfig

    DEFAULT_MODULES = [
        {"module_key": "kpi_overview", "module_name": "核心指标概览", "category": "general", "sort_order": 1,
         "module_description": "参训总数、课程完成率、平均考核分、考试通过率",
         "visible_role_codes": ["admin", "instructor", "student"]},
        {"module_key": "training_kpi", "module_name": "培训运营指标", "category": "training", "sort_order": 2,
         "module_description": "进行中培训班、本月参训人数、培训完成率、待审核学员",
         "visible_role_codes": ["admin", "instructor"]},
        {"module_key": "completion_trend", "module_name": "完成率趋势", "category": "general", "sort_order": 3,
         "module_description": "按月统计课程完成率变化趋势",
         "visible_role_codes": ["admin", "instructor"]},
        {"module_key": "training_trend", "module_name": "培训趋势", "category": "training", "sort_order": 4,
         "module_description": "近 6 个月培训完成率变化趋势",
         "visible_role_codes": ["admin", "instructor"]},
        {"module_key": "police_type_dist", "module_name": "警种分布", "category": "general", "sort_order": 5,
         "module_description": "按警种统计学习时长分布",
         "visible_role_codes": ["admin"]},
        {"module_key": "city_attendance", "module_name": "各单位参训人数", "category": "training", "sort_order": 6,
         "module_description": "各部门本月参训人数排名",
         "visible_role_codes": ["admin"]},
        {"module_key": "city_ranking", "module_name": "各单位考核排名", "category": "general", "sort_order": 7,
         "module_description": "各部门平均考核得分排名",
         "visible_role_codes": ["admin"]},
        {"module_key": "city_completion", "module_name": "各单位完成率排名", "category": "training", "sort_order": 8,
         "module_description": "各部门培训完成率排名",
         "visible_role_codes": ["admin"]},
        {"module_key": "exam_statistics", "module_name": "考试统计", "category": "exam", "sort_order": 9,
         "module_description": "考试参加人数、及格率等统计指标及趋势分析",
         "visible_role_codes": ["admin", "instructor"]},
    ]

    with Session(engine) as db:
        for item in DEFAULT_MODULES:
            existing = db.query(DashboardModuleConfig).filter(
                DashboardModuleConfig.module_key == item["module_key"]
            ).first()
            if existing:
                continue
            record = DashboardModuleConfig(**item, is_active=True)
            db.add(record)
        db.commit()
        logger.info(f"看板模块配置初始化完成")


def init_training_types():
    """初始化培训班类型数据（在 is_db_initialized 之前执行，确保表有数据）"""
    try:
        with Session(engine) as db:
            existing_count = db.query(TrainingType).count()
            if existing_count > 0:
                logger.info("培训班类型数据已存在，跳过初始化")
                return

            training_types_data = [
                {"name": "基础训练", "code": "basic", "description": "基础警务技能训练", "sort_order": 1},
                {"name": "专项训练", "code": "special", "description": "针对特定领域的专项训练", "sort_order": 2},
                {"name": "晋升培训", "code": "promotion", "description": "晋升晋级所需的培训", "sort_order": 3},
                {"name": "线上培训", "code": "online", "description": "在线远程培训", "sort_order": 4},
            ]

            for tt_data in training_types_data:
                tt = TrainingType(
                    name=tt_data["name"],
                    code=tt_data["code"],
                    description=tt_data["description"],
                    sort_order=tt_data["sort_order"],
                    is_active=True,
                )
                db.add(tt)

            db.commit()
            logger.info(f"培训班类型数据初始化完成，共创建 {len(training_types_data)} 个类型")

    except Exception as e:
        logger.error(f"初始化培训班类型数据失败: {e}")
        raise


def init_instructor_specialties():
    """初始化教官专长方向字典"""
    try:
        with Session(engine) as db:
            if db.query(DictInstructorSpecialty).count() > 0:
                logger.info("教官专长方向数据已存在，跳过初始化")
                return

            specialties = [
                {"name": "刑事侦查", "sort_order": 1},
                {"name": "人工智能", "sort_order": 2},
                {"name": "网络安全", "sort_order": 3},
            ]

            for item in specialties:
                db.add(DictInstructorSpecialty(name=item["name"], sort_order=item["sort_order"], enabled=True))

            db.commit()
            logger.info(f"教官专长方向初始化完成，共创建 {len(specialties)} 个专长方向")

    except Exception as e:
        logger.error(f"初始化教官专长方向失败: {e}")
        raise


def init_teaching_directions():
    """初始化教学方向字典"""
    try:
        with Session(engine) as db:
            if db.query(DictTeachingDirection).count() > 0:
                logger.info("教学方向数据已存在，跳过初始化")
                return

            directions = [
                {"name": "刑事技术", "sort_order": 1},
                {"name": "交通管理", "sort_order": 2},
                {"name": "治安防控", "sort_order": 3},
            ]

            for item in directions:
                db.add(DictTeachingDirection(name=item["name"], sort_order=item["sort_order"], enabled=True))

            db.commit()
            logger.info(f"教学方向初始化完成，共创建 {len(directions)} 个教学方向")

    except Exception as e:
        logger.error(f"初始化教学方向失败: {e}")
        raise


def init_evaluation_templates():
    """初始化评价问卷模板（固定 4 种）"""
    try:
        with Session(engine) as db:
            if db.query(EvaluationTemplate).count() > 0:
                logger.info("评价模板数据已存在，跳过初始化")
                return

            templates = [
                {
                    "name": "课程评价",
                    "target_type": "course",
                    "description": "对课程内容的评价",
                    "dimensions": [
                        {"name": "实用性", "description": "内容是否贴合工作实际、能学以致用", "sort_order": 1},
                        {"name": "前沿与丰富度", "description": "知识点是否充实、与时俱进", "sort_order": 2},
                        {"name": "结构与难度", "description": "逻辑是否清晰、难易程度是否适中", "sort_order": 3},
                    ],
                },
                {
                    "name": "教官评价",
                    "target_type": "instructor",
                    "description": "对教官授课的评价",
                    "dimensions": [
                        {"name": "专业水平", "description": "专业功底与答疑能力", "sort_order": 1},
                        {"name": "授课技巧", "description": "表达是否生动、教学方法是否多样", "sort_order": 2},
                        {"name": "课堂互动", "description": "是否能调动氛围、引导学员参与", "sort_order": 3},
                    ],
                },
                {
                    "name": "培训班评价",
                    "target_type": "training",
                    "description": "对培训班软性管理的评价",
                    "dimensions": [
                        {"name": "教学安排", "description": "课程节奏与时间规划是否合理", "sort_order": 1},
                        {"name": "班级管理", "description": "纪律维护、团队建设与学习氛围", "sort_order": 2},
                        {"name": "教务服务", "description": "带班队长的组织能力", "sort_order": 3},
                    ],
                },
                {
                    "name": "培训基地评价",
                    "target_type": "training_base",
                    "description": "对培训基地硬件后勤的评价",
                    "dimensions": [
                        {"name": "教学设施", "description": "教学环境及教学设备运行情况", "sort_order": 1},
                        {"name": "食宿质量", "description": "餐饮口味/卫生，宿舍环境/设施", "sort_order": 2},
                        {"name": "后勤保障", "description": "整体环境安全及工作人员响应速度", "sort_order": 3},
                    ],
                },
            ]

            for tpl_data in templates:
                tpl = EvaluationTemplate(
                    name=tpl_data["name"],
                    target_type=tpl_data["target_type"],
                    description=tpl_data["description"],
                    enabled=True,
                )
                db.add(tpl)
                db.flush()
                for dim_data in tpl_data["dimensions"]:
                    db.add(EvaluationDimension(
                        template_id=tpl.id,
                        name=dim_data["name"],
                        description=dim_data["description"],
                        sort_order=dim_data["sort_order"],
                        weight=1.0,
                    ))

            db.commit()
            logger.info("评价模板初始化完成，共创建 4 个模板")

    except Exception as e:
        logger.error(f"初始化评价模板失败: {e}")
        raise


def main():
    """主函数"""
    try:
        logger.info("开始初始化数据库...")

        init_db()
        init_system_configs()
        init_training_types()
        init_instructor_specialties()
        init_teaching_directions()
        init_evaluation_templates()
        init_permission_groups()
        init_permissions()
        sync_permission_group_ids()
        init_roles()

        if is_db_initialized():
            logger.info("数据库已初始化，跳过种子数据初始化")
            return

        init_departments()
        init_police_types()
        init_users()
        init_dashboard_modules()
        mark_db_initialized()

        logger.info("数据库初始化完成！")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise

if __name__ == "__main__":
    main()
