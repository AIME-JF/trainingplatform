#!/usr/bin/env python3
"""
数据库迁移管理脚本

该脚本提供了便捷的数据库迁移管理功能，包括：
- 自动生成迁移文件
- 应用迁移
- 查看迁移历史
- 回滚迁移等

使用方法：
    python migrate.py --help
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from logger import logger


def run_command(cmd: list, description: str = ""):
    """运行命令并处理输出"""
    try:
        logger.info(f"执行命令: {' '.join(cmd)}")
        if description:
            logger.info(f"操作描述: {description}")
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=project_root,
            encoding='utf-8',
            errors='ignore'  # 忽略编码错误
        )
        
        if result.stdout:
            print(result.stdout)
            
        if result.stderr:
            print(f"警告/错误信息: {result.stderr}")
            
        if result.returncode != 0:
            logger.error(f"命令执行失败，退出码: {result.returncode}")
            sys.exit(1)
        else:
            logger.info("命令执行成功")
            
    except Exception as e:
        logger.error(f"执行命令时发生错误: {e}")
        sys.exit(1)


def generate_migration(message: str, autogenerate: bool = True):
    """生成新的迁移文件"""
    cmd = ["alembic", "revision"]
    
    if autogenerate:
        cmd.append("--autogenerate")
        
    cmd.extend(["-m", message])
    
    description = f"生成{'自动' if autogenerate else '手动'}迁移文件: {message}"
    run_command(cmd, description)


def upgrade_database(revision: str = "head"):
    """升级数据库到指定版本"""
    cmd = ["alembic", "upgrade", revision]
    description = f"升级数据库到版本: {revision}"
    run_command(cmd, description)


def downgrade_database(revision: str):
    """降级数据库到指定版本"""
    cmd = ["alembic", "downgrade", revision]
    description = f"降级数据库到版本: {revision}"
    run_command(cmd, description)


def show_current_revision():
    """显示当前数据库版本"""
    cmd = ["alembic", "current"]
    description = "显示当前数据库版本"
    run_command(cmd, description)


def show_migration_history():
    """显示迁移历史"""
    cmd = ["alembic", "history", "--verbose"]
    description = "显示迁移历史"
    run_command(cmd, description)


def show_migration_heads():
    """显示迁移分支头"""
    cmd = ["alembic", "heads"]
    description = "显示迁移分支头"
    run_command(cmd, description)


def stamp_database(revision: str):
    """标记数据库版本（不执行迁移，仅限结构已完全一致时使用）"""
    cmd = ["alembic", "stamp", revision]
    description = f"标记数据库版本为: {revision}（仅在已确认数据库结构与该版本完全一致时使用）"
    run_command(cmd, description)


def init_database():
    """初始化数据库（创建表并插入初始数据）"""
    try:
        logger.info("开始初始化数据库...")
        
        # 首先生成初始迁移文件
        logger.info("生成初始迁移文件...")
        generate_migration("初始化数据库表结构", autogenerate=True)
        
        # 应用迁移
        logger.info("应用数据库迁移...")
        upgrade_database()
        
        # 执行数据初始化
        logger.info("插入初始数据...")
        from init_data import main as init_data_main
        init_data_main()
        
        logger.info("数据库初始化完成！")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        sys.exit(1)


def check_migration_status():
    """检查迁移状态"""
    logger.info("检查迁移状态...")
    show_current_revision()
    show_migration_heads()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="数据库迁移管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python migrate.py init                    # 初始化数据库（首次部署）
  python migrate.py generate "添加新字段"     # 生成自动迁移文件
  python migrate.py generate "手动迁移" --no-auto  # 生成手动迁移文件
  python migrate.py upgrade                 # 升级到最新版本
  python migrate.py upgrade +1              # 升级一个版本
  python migrate.py downgrade -1            # 回滚一个版本
  python migrate.py current                 # 显示当前版本
  python migrate.py history                 # 显示迁移历史
  python migrate.py status                  # 检查迁移状态
  python migrate.py stamp head              # 仅在已确认库结构与最新版本完全一致时才使用
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # init命令 - 初始化数据库
    init_parser = subparsers.add_parser("init", help="初始化数据库（首次部署使用）")
    
    # generate命令 - 生成迁移文件
    generate_parser = subparsers.add_parser("generate", help="生成迁移文件")
    generate_parser.add_argument("message", help="迁移描述信息")
    generate_parser.add_argument("--no-auto", action="store_true", help="不使用自动生成，创建空的迁移文件")
    
    # upgrade命令 - 升级数据库
    upgrade_parser = subparsers.add_parser("upgrade", help="升级数据库")
    upgrade_parser.add_argument("revision", nargs="?", default="head", help="目标版本（默认为最新版本）")
    
    # downgrade命令 - 降级数据库
    downgrade_parser = subparsers.add_parser("downgrade", help="降级数据库")
    downgrade_parser.add_argument("revision", help="目标版本")
    
    # current命令 - 显示当前版本
    current_parser = subparsers.add_parser("current", help="显示当前数据库版本")
    
    # history命令 - 显示迁移历史
    history_parser = subparsers.add_parser("history", help="显示迁移历史")
    
    # status命令 - 检查迁移状态
    status_parser = subparsers.add_parser("status", help="检查迁移状态")
    
    # stamp命令 - 标记数据库版本
    stamp_parser = subparsers.add_parser("stamp", help="标记数据库版本（不执行迁移）")
    stamp_parser.add_argument("revision", help="目标版本")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 检查是否在项目根目录
    if not os.path.exists("alembic.ini"):
        logger.error("未找到alembic.ini文件，请确保在项目根目录下运行此脚本")
        sys.exit(1)
    
    # 执行对应的命令
    try:
        if args.command == "init":
            init_database()
        elif args.command == "generate":
            generate_migration(args.message, autogenerate=not args.no_auto)
        elif args.command == "upgrade":
            upgrade_database(args.revision)
        elif args.command == "downgrade":
            downgrade_database(args.revision)
        elif args.command == "current":
            show_current_revision()
        elif args.command == "history":
            show_migration_history()
        elif args.command == "status":
            check_migration_status()
        elif args.command == "stamp":
            stamp_database(args.revision)
    except KeyboardInterrupt:
        logger.info("操作被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"执行命令时发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
