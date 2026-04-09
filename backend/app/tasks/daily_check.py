"""
每日例行检查任务
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from celery_app import celery_app
from app.database import engine
from app.models.user import User
from app.models.notice import Notice
from logger import logger


@celery_app.task(name="app.tasks.daily_check.run_daily_checks")
def run_daily_checks():
    """每日例行检查任务"""
    logger.info("开始执行每日例行检查...")
    check_instructor_hire_expiry()
    logger.info("每日例行检查完成")


def check_instructor_hire_expiry():
    """检查教官聘任到期（到期前3个月提醒）"""
    try:
        with Session(engine) as db:
            today = date.today()
            deadline = today + timedelta(days=90)

            # 查询聘任结束日期在今天到90天内的教官
            users = db.query(User).filter(
                User.instructor_hire_end.isnot(None),
                User.instructor_hire_end >= today,
                User.instructor_hire_end <= deadline,
            ).all()

            created_count = 0
            for user in users:
                # 检查是否已发送过提醒（避免重复）
                existing = db.query(Notice).filter(
                    Notice.reminder_type == "hire_expiry_warning",
                    Notice.target_user_id == user.id,
                ).first()
                if existing:
                    continue

                # 创建提醒通知
                days_left = (user.instructor_hire_end - today).days
                notice = Notice(
                    title="聘任即将到期提醒",
                    content=f"您的教官聘任将于 {user.instructor_hire_end} 到期，剩余 {days_left} 天，请及时办理续聘手续。",
                    type="reminder",
                    reminder_type="hire_expiry_warning",
                    target_user_id=user.id,
                )
                db.add(notice)
                created_count += 1

            if created_count > 0:
                db.commit()
                logger.info(f"聘任到期提醒：已创建 {created_count} 条通知")
            else:
                logger.info("聘任到期提醒：无需创建新通知")

    except Exception as e:
        logger.error(f"检查教官聘任到期失败: {e}")
        raise
