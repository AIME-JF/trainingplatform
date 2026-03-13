"""
自动数据库迁移模块。

在应用启动时自动检查并执行 Alembic 迁移，并在启动前校验关键表结构
是否与当前代码兼容，避免出现“数据库版本已是 head，但字段并未真正落库”
的假升级状态。
"""
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from app.database import engine
from config import settings
from logger import logger


CRITICAL_SCHEMA_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "exam_papers": (
        "id",
        "title",
        "duration",
        "total_score",
        "passing_score",
        "type",
        "created_by",
    ),
    "exam_paper_questions": (
        "paper_id",
        "question_id",
        "sort_order",
        "question_type",
        "content",
        "options",
        "answer",
        "explanation",
        "score",
        "knowledge_point",
    ),
    "admission_exams": (
        "id",
        "paper_id",
        "title",
        "duration",
        "total_score",
        "passing_score",
        "status",
        "type",
        "scope",
        "max_attempts",
        "start_time",
        "end_time",
        "published_at",
        "created_by",
    ),
    "admission_exam_records": (
        "id",
        "admission_exam_id",
        "paper_id",
        "user_id",
        "attempt_no",
        "status",
        "wrong_question_details",
        "submitted_at",
    ),
    "exams": (
        "paper_id",
        "purpose",
        "training_id",
        "max_attempts",
        "allow_makeup",
        "published_at",
    ),
    "exam_questions": (
        "question_type",
        "content",
        "options",
        "answer",
        "explanation",
        "score",
        "knowledge_point",
    ),
    "exam_records": (
        "paper_id",
        "attempt_no",
        "status",
        "wrong_question_details",
        "submitted_at",
    ),
    "trainings": (
        "publish_status",
        "class_code",
        "published_by",
        "locked_by",
        "admission_exam_id",
        "enrollment_start_at",
        "enrollment_end_at",
        "published_at",
        "locked_at",
    ),
    "training_courses": (
        "primary_instructor_id",
        "assistant_instructor_ids",
    ),
    "enrollments": (
        "contact_phone",
        "need_accommodation",
        "group_name",
        "cadre_role",
        "profile_snapshot",
        "approved_at",
        "reviewed_at",
        "reviewed_by",
        "archived_at",
    ),
    "checkin_records": (
        "checkin_method",
        "checkout_time",
        "checkout_status",
        "checkout_method",
        "evaluation_score",
        "evaluation_comment",
        "evaluation_submitted_at",
        "absence_reason",
    ),
    "training_histories": (
        "id",
        "training_id",
        "user_id",
        "training_name",
        "training_type",
        "status",
        "attendance_rate",
        "completed_sessions",
        "total_sessions",
        "evaluation_score",
        "passed_exam_count",
        "summary",
    ),
}


class AutoMigrate:
    """自动迁移类。"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.alembic_cfg_path = self.project_root / "alembic.ini"

        if not self.alembic_cfg_path.exists():
            logger.warning("未找到 alembic.ini 配置文件，跳过自动迁移")
            self.enabled = False
            return

        self.alembic_cfg = Config(str(self.alembic_cfg_path))
        self.alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

        try:
            self.script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            self.enabled = True
            logger.info("自动迁移模块初始化成功")
        except Exception as exc:
            logger.error(f"自动迁移模块初始化失败: {exc}")
            self.enabled = False

    def get_current_revision(self) -> str:
        """获取当前数据库版本。"""
        try:
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                current_rev = context.get_current_revision()
                return current_rev or "无版本"
        except Exception as exc:
            logger.error(f"获取当前数据库版本失败: {exc}")
            return "未知"

    def get_head_revision(self) -> str:
        """获取最新迁移版本。"""
        try:
            head_rev = self.script_dir.get_current_head()
            return head_rev or "无版本"
        except Exception as exc:
            logger.error(f"获取最新迁移版本失败: {exc}")
            return "未知"

    def is_migration_needed(self) -> bool:
        """检查是否需要迁移。"""
        if not self.enabled:
            return False

        current_rev = self.get_current_revision()
        head_rev = self.get_head_revision()

        logger.info(f"当前数据库版本: {current_rev}")
        logger.info(f"最新迁移版本: {head_rev}")
        return current_rev != head_rev

    def create_alembic_version_table(self) -> bool:
        """创建 Alembic 版本表（如果不存在）。"""
        try:
            with engine.connect() as connection:
                result = connection.execute(
                    text(
                        """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public'
                              AND table_name = 'alembic_version'
                        );
                        """
                    )
                )
                table_exists = result.scalar()

                if table_exists:
                    logger.debug("Alembic 版本表已存在")
                    return False

                logger.info("创建 Alembic 版本表...")
                connection.execute(
                    text(
                        """
                        CREATE TABLE alembic_version (
                            version_num VARCHAR(32) NOT NULL,
                            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                        );
                        """
                    )
                )
                connection.commit()
                logger.info("Alembic 版本表创建成功")
                return True
        except Exception as exc:
            logger.error(f"创建 Alembic 版本表失败: {exc}")
            return False

    def get_application_tables(self) -> list[str]:
        """获取当前业务表列表。"""
        try:
            with engine.connect() as connection:
                result = connection.execute(
                    text(
                        """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_type = 'BASE TABLE'
                          AND table_name <> 'alembic_version'
                        ORDER BY table_name;
                        """
                    )
                )
                return [row[0] for row in result]
        except Exception as exc:
            logger.error(f"获取业务表列表失败: {exc}")
            return []

    def get_schema_drift_issues(self) -> list[str]:
        """检查关键表结构是否与当前代码兼容。"""
        try:
            with engine.connect() as connection:
                inspector = inspect(connection)
                issues: list[str] = []

                for table_name, required_columns in CRITICAL_SCHEMA_REQUIREMENTS.items():
                    if not inspector.has_table(table_name):
                        issues.append(f"缺少关键表 `{table_name}`")
                        continue

                    existing_columns = {
                        column["name"] for column in inspector.get_columns(table_name)
                    }
                    missing_columns = [
                        column_name
                        for column_name in required_columns
                        if column_name not in existing_columns
                    ]
                    if missing_columns:
                        issues.append(
                            f"表 `{table_name}` 缺少字段: {', '.join(missing_columns)}"
                        )

                return issues
        except Exception as exc:
            logger.error(f"检查数据库结构兼容性失败: {exc}")
            return [f"无法检查数据库结构: {exc}"]

    def run_migration(self) -> bool:
        """执行数据库迁移。"""
        if not self.enabled:
            logger.warning("自动迁移未启用，跳过迁移")
            return False

        try:
            logger.info("开始执行数据库迁移...")
            self.create_alembic_version_table()

            current_rev = self.get_current_revision()
            if current_rev == "无版本":
                existing_tables = self.get_application_tables()
                if existing_tables:
                    table_names = ", ".join(existing_tables[:12])
                    if len(existing_tables) > 12:
                        table_names += ", ..."
                    logger.error(
                        "检测到数据库已存在业务表，但没有 Alembic 版本记录；"
                        f"拒绝自动 stamp head。现有表: {table_names}",
                    )
                    logger.error(
                        "请备份数据库后手动执行 `python migrate.py upgrade`。"
                        "如果数据库曾被错误标记为 head，请先拉取兼容修复迁移后再升级。"
                    )
                    return False

                logger.info("数据库为空，将执行完整迁移")

            command.upgrade(self.alembic_cfg, "head")

            new_rev = self.get_current_revision()
            logger.info(f"迁移完成，当前数据库版本: {new_rev}")

            issues = self.get_schema_drift_issues()
            if issues:
                logger.error("迁移完成后仍检测到关键结构缺失：")
                for issue in issues:
                    logger.error(f" - {issue}")
                return False

            return True
        except Exception as exc:
            logger.error(f"执行数据库迁移失败: {exc}")
            return False

    def auto_migrate(self) -> bool:
        """自动迁移主函数。"""
        if not self.enabled:
            logger.info("自动迁移未启用")
            return False

        try:
            logger.info("检查数据库迁移状态...")
            current_rev = self.get_current_revision()
            head_rev = self.get_head_revision()

            logger.info(f"当前数据库版本: {current_rev}")
            logger.info(f"最新迁移版本: {head_rev}")

            if current_rev != head_rev:
                logger.info("检测到数据库需要迁移")
                return self.run_migration()

            issues = self.get_schema_drift_issues()
            if issues:
                logger.error("数据库版本已是最新，但关键结构缺失：")
                for issue in issues:
                    logger.error(f" - {issue}")
                return False

            logger.info("数据库已是最新版本，无需迁移")
            return True
        except Exception as exc:
            logger.error(f"自动迁移检查失败: {exc}")
            return False


auto_migrate = AutoMigrate()


def run_auto_migration() -> bool:
    """运行自动迁移（供外部调用）。"""
    return auto_migrate.auto_migrate()


def is_auto_migration_enabled() -> bool:
    """检查自动迁移是否启用。"""
    return auto_migrate.enabled


def get_schema_compatibility_issues() -> list[str]:
    """返回当前数据库与代码之间的关键结构差异。"""
    return auto_migrate.get_schema_drift_issues()


def ensure_schema_compatibility() -> None:
    """在应用启动前校验关键结构，发现漂移就直接阻断启动。"""
    issues = get_schema_compatibility_issues()
    if not issues:
        return

    current_revision = auto_migrate.get_current_revision()
    head_revision = auto_migrate.get_head_revision()
    detail_lines = "\n".join(f"- {issue}" for issue in issues)
    raise RuntimeError(
        "数据库结构与当前代码不兼容。\n"
        f"当前版本: {current_revision}\n"
        f"最新版本: {head_revision}\n"
        "请先执行 `python migrate.py upgrade`，再重新启动服务。\n"
        f"{detail_lines}"
    )


def get_migration_status() -> dict:
    """获取迁移状态信息。"""
    if not auto_migrate.enabled:
        return {
            "enabled": False,
            "current_revision": "未知",
            "head_revision": "未知",
            "migration_needed": False,
            "schema_compatible": False,
            "schema_issues": ["自动迁移未启用"],
        }

    schema_issues = auto_migrate.get_schema_drift_issues()
    return {
        "enabled": True,
        "current_revision": auto_migrate.get_current_revision(),
        "head_revision": auto_migrate.get_head_revision(),
        "migration_needed": auto_migrate.is_migration_needed(),
        "schema_compatible": not schema_issues,
        "schema_issues": schema_issues,
    }
