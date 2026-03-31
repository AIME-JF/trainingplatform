"""sync permissions and builtin roles

Revision ID: a4b5c6d7e8f9
Revises: f2a3b4c5d6e7
Create Date: 2026-03-16 09:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "a4b5c6d7e8f9"
down_revision: Union[str, None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SYSTEM_PERMISSION_GROUP = "SYSTEM"

PATH_GROUP_RULES = (
    ("/api/v1/auth", "AUTH"),
    ("/api/v1/users", "USER_MANAGEMENT"),
    ("/api/v1/roles", "ROLE_MANAGEMENT"),
    ("/api/v1/permissions", "PERMISSION_MANAGEMENT"),
    ("/api/v1/departments", "DEPARTMENT_MANAGEMENT"),
    ("/api/v1/police-types", "POLICE_TYPE_MANAGEMENT"),
    ("/api/v1/courses", "COURSE_MANAGEMENT"),
    ("/api/v1/exams", "EXAM_MANAGEMENT"),
    ("/api/v1/questions", "QUESTION_BANK"),
    ("/api/v1/trainings", "TRAINING_MANAGEMENT"),
    ("/api/v1/certificates", "CERTIFICATE_MANAGEMENT"),
    ("/api/v1/profile", "PROFILE"),
    ("/api/v1/report", "REPORT"),
    ("/api/v1/ai", "AI"),
    ("/api/v1/talent", "TALENT"),
    ("/api/v1/dashboard", "DASHBOARD"),
    ("/api/v1/resources", "RESOURCE_REVIEW"),
    ("/api/v1/reviews", "RESOURCE_REVIEW"),
    ("/api/v1/review-policies", "RESOURCE_REVIEW"),
)

EXTRA_PERMISSION_DEFINITIONS = (
    {
        "path": "/api/v1/users/import/template",
        "code": "DOWNLOAD_USER_IMPORT_TEMPLATE",
        "description": "下载用户导入模板",
    },
    {
        "path": "/api/v1/users/export",
        "code": "EXPORT_USERS",
        "description": "导出用户",
    },
    {
        "path": "/api/v1/users/import",
        "code": "IMPORT_USERS",
        "description": "导入用户",
    },
    {
        "path": "/api/v1/departments/import/template",
        "code": "DOWNLOAD_DEPARTMENT_IMPORT_TEMPLATE",
        "description": "下载部门导入模板",
    },
    {
        "path": "/api/v1/departments/export",
        "code": "EXPORT_DEPARTMENTS",
        "description": "导出部门",
    },
    {
        "path": "/api/v1/departments/import",
        "code": "IMPORT_DEPARTMENTS",
        "description": "导入部门",
    },
    {
        "path": "/api/v1/roles/import/template",
        "code": "DOWNLOAD_ROLE_IMPORT_TEMPLATE",
        "description": "下载角色导入模板",
    },
    {
        "path": "/api/v1/roles/export",
        "code": "EXPORT_ROLES",
        "description": "导出角色",
    },
    {
        "path": "/api/v1/roles/import",
        "code": "IMPORT_ROLES",
        "description": "导入角色",
    },
    {
        "path": "/api/v1/ai/question-tasks",
        "code": "GET_AI_QUESTION_TASKS",
        "description": "获取 AI 智能出题任务",
    },
    {
        "path": "/api/v1/ai/question-tasks",
        "code": "CREATE_AI_QUESTION_TASK",
        "description": "创建 AI 智能出题任务",
    },
    {
        "path": "/api/v1/ai/question-tasks/{task_id}/result",
        "code": "UPDATE_AI_QUESTION_TASK",
        "description": "更新 AI 智能出题任务",
    },
    {
        "path": "/api/v1/ai/question-tasks/{task_id}/confirm",
        "code": "CONFIRM_AI_QUESTION_TASK",
        "description": "确认 AI 智能出题任务",
    },
    {
        "path": "/api/v1/ai/paper-assembly-tasks",
        "code": "GET_AI_PAPER_ASSEMBLY_TASKS",
        "description": "获取 AI 自动组卷任务",
    },
    {
        "path": "/api/v1/ai/paper-assembly-tasks",
        "code": "CREATE_AI_PAPER_ASSEMBLY_TASK",
        "description": "创建 AI 自动组卷任务",
    },
    {
        "path": "/api/v1/ai/paper-assembly-tasks/{task_id}/result",
        "code": "UPDATE_AI_PAPER_ASSEMBLY_TASK",
        "description": "更新 AI 自动组卷任务",
    },
    {
        "path": "/api/v1/ai/paper-assembly-tasks/{task_id}/confirm",
        "code": "CONFIRM_AI_PAPER_ASSEMBLY_TASK",
        "description": "确认 AI 自动组卷任务",
    },
    {
        "path": "/api/v1/ai/paper-generation-tasks",
        "code": "GET_AI_PAPER_GENERATION_TASKS",
        "description": "获取 AI 自动生成试卷任务",
    },
    {
        "path": "/api/v1/ai/paper-generation-tasks",
        "code": "CREATE_AI_PAPER_GENERATION_TASK",
        "description": "创建 AI 自动生成试卷任务",
    },
    {
        "path": "/api/v1/ai/paper-generation-tasks/{task_id}/result",
        "code": "UPDATE_AI_PAPER_GENERATION_TASK",
        "description": "更新 AI 自动生成试卷任务",
    },
    {
        "path": "/api/v1/ai/paper-generation-tasks/{task_id}/confirm",
        "code": "CONFIRM_AI_PAPER_GENERATION_TASK",
        "description": "确认 AI 自动生成试卷任务",
    },
    {
        "path": "/api/v1/trainings/{id}/manage",
        "code": "MANAGE_TRAINING",
        "description": "管理端更新培训班",
    },
    {
        "path": "/api/v1/resources/list",
        "code": "VIEW_RESOURCE_ALL",
        "description": "全局查看资源",
    },
    {
        "path": "/api/v1/resources/list/department",
        "code": "VIEW_RESOURCE_DEPARTMENT",
        "description": "按部门查看资源",
    },
    {
        "path": "/api/v1/resources/{id}/visibility",
        "code": "MANAGE_RESOURCE_VISIBILITY",
        "description": "管理资源可见域",
    },
    {
        "path": "/api/v1/resources/{resource_id}/submit",
        "code": "SUBMIT_RESOURCE_REVIEW",
        "description": "提交资源审核",
    },
    {
        "path": "/api/v1/reviews/tasks",
        "code": "REVIEW_RESOURCE_STAGE1",
        "description": "资源一级审核",
    },
    {
        "path": "/api/v1/reviews/tasks",
        "code": "REVIEW_RESOURCE_STAGE2",
        "description": "资源二级审核",
    },
    {
        "path": "/api/v1/review-policies",
        "code": "MANAGE_REVIEW_POLICY",
        "description": "管理审核策略",
    },
)


def infer_permission_group(path: str | None) -> str:
    if not path:
        return SYSTEM_PERMISSION_GROUP

    normalized_path = path.strip()
    if normalized_path in {"/", "/health"}:
        return SYSTEM_PERMISSION_GROUP

    for prefix, group in PATH_GROUP_RULES:
        if normalized_path.startswith(prefix):
            return group

    return SYSTEM_PERMISSION_GROUP


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("permissions") or not inspector.has_table("roles"):
        return

    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.Integer()),
        sa.column("path", sa.String(length=200)),
        sa.column("code", sa.String(length=100)),
        sa.column("group", sa.String(length=100)),
        sa.column("description", sa.Text()),
        sa.column("is_active", sa.Boolean()),
    )
    roles_table = sa.table(
        "roles",
        sa.column("id", sa.Integer()),
        sa.column("code", sa.String(length=50)),
        sa.column("data_scopes", sa.JSON()),
    )
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Integer()),
        sa.column("permission_id", sa.Integer()),
    )

    permission_rows = bind.execute(
        sa.select(
            permissions_table.c.id,
            permissions_table.c.code,
            permissions_table.c.path,
            permissions_table.c.group,
            permissions_table.c.description,
            permissions_table.c.is_active,
        )
    ).fetchall()
    existing_permissions = {row.code: row for row in permission_rows}

    for item in EXTRA_PERMISSION_DEFINITIONS:
        expected_group = infer_permission_group(item["path"])
        existing = existing_permissions.get(item["code"])
        values = {
            "path": item["path"],
            "code": item["code"],
            "group": expected_group,
            "description": item["description"],
            "is_active": True,
        }

        if existing is None:
            bind.execute(sa.insert(permissions_table).values(values))
            continue

        bind.execute(
            sa.update(permissions_table)
            .where(permissions_table.c.id == existing.id)
            .values(values)
        )

    if inspector.has_table("role_permissions"):
        admin_role_id = bind.execute(
            sa.select(roles_table.c.id).where(roles_table.c.code == "admin")
        ).scalar()
        if admin_role_id is not None:
            bind.execute(
                sa.update(roles_table)
                .where(roles_table.c.id == admin_role_id)
                .values({"data_scopes": ["all"]})
            )
            bind.execute(
                sa.delete(role_permissions_table).where(
                    role_permissions_table.c.role_id == admin_role_id
                )
            )
            active_permission_ids = bind.execute(
                sa.select(permissions_table.c.id).where(
                    permissions_table.c.is_active.is_(True)
                )
            ).fetchall()
            if active_permission_ids:
                bind.execute(
                    sa.insert(role_permissions_table),
                    [
                        {
                            "role_id": admin_role_id,
                            "permission_id": permission_id,
                        }
                        for (permission_id,) in active_permission_ids
                    ],
                )

    role_columns = {column["name"] for column in inspector.get_columns("roles")}
    if "data_scopes" in role_columns:
        bind.execute(
            sa.text(
                """
                UPDATE roles
                SET data_scopes = '["all"]'::json
                WHERE code = 'admin'
                  AND COALESCE(data_scopes::jsonb, 'null'::jsonb) IS DISTINCT FROM '["all"]'::jsonb
                """
            )
        )
        bind.execute(
            sa.text(
                """
                UPDATE roles
                SET data_scopes = '["department_and_sub", "police_type", "self"]'::json
                WHERE code = 'instructor'
                  AND (
                    data_scopes IS NULL
                    OR data_scopes::jsonb = '[]'::jsonb
                    OR data_scopes::jsonb = '["all"]'::jsonb
                  )
                """
            )
        )
        bind.execute(
            sa.text(
                """
                UPDATE roles
                SET data_scopes = '["department", "police_type", "self"]'::json
                WHERE code = 'student'
                  AND (
                    data_scopes IS NULL
                    OR data_scopes::jsonb = '[]'::jsonb
                    OR data_scopes::jsonb = '["all"]'::jsonb
                  )
                """
            )
        )


def downgrade() -> None:
    # Runtime compatibility data migration is intentionally non-destructive.
    pass
