"""
Runtime sync helpers for permissions and schema compatibility.
"""
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session, selectinload

from app.database import engine
from app.models import Permission, Role
from app.utils.permission_group import infer_permission_group
from logger import logger


EXTRA_PERMISSION_DEFINITIONS = [
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
]


def sync_runtime_state():
    """Apply small runtime repairs for old databases."""
    with Session(engine) as db:
        changed = False
        changed = _ensure_extra_permissions(db) or changed
        changed = _ensure_chapter_resource_column(db) or changed
        changed = _sync_admin_role_permissions(db) or changed

        if changed:
            db.commit()
            logger.info("Runtime sync applied compatibility updates")
        else:
            db.rollback()
            logger.info("Runtime sync found no pending compatibility updates")


def _ensure_extra_permissions(db: Session) -> bool:
    existing = {perm.code: perm for perm in db.query(Permission).all()}
    changed = False

    for item in EXTRA_PERMISSION_DEFINITIONS:
        expected_group = infer_permission_group(item["path"])
        permission = existing.get(item["code"])

        if permission is None:
            permission = Permission(
                path=item["path"],
                code=item["code"],
                group=expected_group,
                description=item["description"],
                is_active=True,
            )
            db.add(permission)
            existing[item["code"]] = permission
            changed = True
            continue

        if permission.path != item["path"]:
            permission.path = item["path"]
            changed = True
        if (permission.group or "").strip() != expected_group:
            permission.group = expected_group
            changed = True
        if (permission.description or "").strip() != item["description"]:
            permission.description = item["description"]
            changed = True
        if not permission.is_active:
            permission.is_active = True
            changed = True

    if changed:
        db.flush()

    return changed


def _sync_admin_role_permissions(db: Session) -> bool:
    admin_role = (
        db.query(Role)
        .options(selectinload(Role.permissions))
        .filter(Role.code == "admin")
        .first()
    )
    if admin_role is None:
        return False

    all_permissions = db.query(Permission).filter(Permission.is_active.is_(True)).all()
    current_ids = {permission.id for permission in admin_role.permissions}
    desired_ids = {permission.id for permission in all_permissions}

    if current_ids == desired_ids:
        return False

    admin_role.permissions = all_permissions
    return True


def _ensure_chapter_resource_column(db: Session) -> bool:
    bind = db.get_bind()
    inspector = inspect(bind)
    changed = False

    if not inspector.has_table("chapters"):
        return False

    columns = {column["name"] for column in inspector.get_columns("chapters")}
    if "resource_id" not in columns:
        db.execute(text("ALTER TABLE chapters ADD COLUMN resource_id INTEGER NULL"))
        changed = True

    inspector = inspect(bind)
    if inspector.has_table("resources"):
        fk_names = {fk.get("name") for fk in inspector.get_foreign_keys("chapters")}
        if "chapters_resource_id_fkey" not in fk_names:
            db.execute(
                text(
                    "ALTER TABLE chapters "
                    "ADD CONSTRAINT chapters_resource_id_fkey "
                    "FOREIGN KEY (resource_id) REFERENCES resources (id)"
                )
            )
            changed = True

    inspector = inspect(bind)
    index_names = {index["name"] for index in inspector.get_indexes("chapters")}
    if "ix_chapters_resource_id" not in index_names:
        db.execute(text("CREATE INDEX ix_chapters_resource_id ON chapters (resource_id)"))
        changed = True

    return changed
