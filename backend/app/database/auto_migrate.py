"""
自动数据库迁移模块

在应用启动时自动检查并执行数据库迁移
"""
import os
import sys
from pathlib import Path
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text

from logger import logger
from config import settings
from app.database import engine


class AutoMigrate:
    """自动迁移类"""
    
    def __init__(self):
        """初始化自动迁移"""
        # 获取项目根目录
        self.project_root = Path(__file__).parent.parent.parent
        self.alembic_cfg_path = self.project_root / "alembic.ini"
        
        # 检查Alembic配置文件是否存在
        if not self.alembic_cfg_path.exists():
            logger.warning("未找到alembic.ini配置文件，跳过自动迁移")
            self.enabled = False
            return
        
        # 创建Alembic配置对象
        self.alembic_cfg = Config(str(self.alembic_cfg_path))
        self.alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        
        # 获取脚本目录
        try:
            self.script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            self.enabled = True
            logger.info("自动迁移模块初始化成功")
        except Exception as e:
            logger.error(f"自动迁移模块初始化失败: {e}")
            self.enabled = False
    
    def get_current_revision(self) -> str:
        """获取当前数据库版本"""
        try:
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                current_rev = context.get_current_revision()
                return current_rev or "无版本"
        except Exception as e:
            logger.error(f"获取当前数据库版本失败: {e}")
            return "未知"
    
    def get_head_revision(self) -> str:
        """获取最新迁移版本"""
        try:
            head_rev = self.script_dir.get_current_head()
            return head_rev or "无版本"
        except Exception as e:
            logger.error(f"获取最新迁移版本失败: {e}")
            return "未知"
    
    def is_migration_needed(self) -> bool:
        """检查是否需要迁移"""
        if not self.enabled:
            return False
        
        current_rev = self.get_current_revision()
        head_rev = self.get_head_revision()
        
        logger.info(f"当前数据库版本: {current_rev}")
        logger.info(f"最新迁移版本: {head_rev}")
        
        # 如果版本不同，需要迁移
        return current_rev != head_rev
    
    def create_alembic_version_table(self):
        """创建Alembic版本表（如果不存在）"""
        try:
            with engine.connect() as connection:
                # 检查alembic_version表是否存在
                result = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'alembic_version'
                    );
                """))
                
                table_exists = result.scalar()
                
                if not table_exists:
                    logger.info("创建Alembic版本表...")
                    connection.execute(text("""
                        CREATE TABLE alembic_version (
                            version_num VARCHAR(32) NOT NULL, 
                            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                        );
                    """))
                    connection.commit()
                    logger.info("Alembic版本表创建成功")
                    return True
                else:
                    logger.debug("Alembic版本表已存在")
                    return False
                    
        except Exception as e:
            logger.error(f"创建Alembic版本表失败: {e}")
            return False
    
    def run_migration(self) -> bool:
        """执行数据库迁移"""
        if not self.enabled:
            logger.warning("自动迁移未启用，跳过迁移")
            return False
        
        try:
            logger.info("开始执行数据库迁移...")
            
            # 确保版本表存在
            self.create_alembic_version_table()
            
            # 获取当前版本
            current_rev = self.get_current_revision()
            
            # 如果数据库为空（无版本），先标记为最新版本
            if current_rev == "无版本":
                logger.info("数据库未初始化，检查是否已有表结构...")
                
                # 检查是否已有表（通过检查用户表）
                with engine.connect() as connection:
                    result = connection.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'users'
                        );
                    """))
                    
                    has_tables = result.scalar()
                    
                    if has_tables:
                        # 如果已有表结构，标记为最新版本
                        head_rev = self.get_head_revision()
                        if head_rev != "无版本":
                            logger.info(f"检测到已有表结构，标记数据库版本为: {head_rev}")
                            command.stamp(self.alembic_cfg, head_rev)
                            return True
                        else:
                            logger.warning("未找到迁移文件，无法标记版本")
                            return False
                    else:
                        logger.info("数据库为空，将执行完整迁移")
            
            # 执行迁移到最新版本
            command.upgrade(self.alembic_cfg, "head")
            
            # 验证迁移结果
            new_rev = self.get_current_revision()
            logger.info(f"迁移完成，当前数据库版本: {new_rev}")
            
            return True
            
        except Exception as e:
            logger.error(f"执行数据库迁移失败: {e}")
            return False
    
    def auto_migrate(self) -> bool:
        """自动迁移主函数"""
        if not self.enabled:
            logger.info("自动迁移未启用")
            return False
        
        try:
            logger.info("检查数据库迁移状态...")
            
            # 检查是否需要迁移
            if self.is_migration_needed():
                logger.info("检测到数据库需要迁移")
                return self.run_migration()
            else:
                logger.info("数据库已是最新版本，无需迁移")
                return True
                
        except Exception as e:
            logger.error(f"自动迁移检查失败: {e}")
            return False


# 创建全局自动迁移实例
auto_migrate = AutoMigrate()


def run_auto_migration() -> bool:
    """运行自动迁移（供外部调用）"""
    return auto_migrate.auto_migrate()


def is_auto_migration_enabled() -> bool:
    """检查自动迁移是否启用"""
    return auto_migrate.enabled


def get_migration_status() -> dict:
    """获取迁移状态信息"""
    if not auto_migrate.enabled:
        return {
            "enabled": False,
            "current_revision": "未知",
            "head_revision": "未知",
            "migration_needed": False
        }
    
    return {
        "enabled": True,
        "current_revision": auto_migrate.get_current_revision(),
        "head_revision": auto_migrate.get_head_revision(),
        "migration_needed": auto_migrate.is_migration_needed()
    }
