"""
视图导出
"""
from .auth import router as auth_router
from .dashboard import router as dashboard_router
from .course import router as course_router
from .exam import router as exam_router
from .question import router as question_router
from .training import router as training_router
from .certificate import router as certificate_router
from .profile import router as profile_router
from .report import router as report_router
from .ai import router as ai_router
from .talent import router as talent_router
from .police_type import router as police_type_router
from .media import router as media_router
from .user import router as user_router, roles_router, departments_router
from .notice import router as notice_router

all_routers = [
    auth_router,
    dashboard_router,
    course_router,
    exam_router,
    question_router,
    training_router,
    certificate_router,
    profile_router,
    report_router,
    ai_router,
    talent_router,
    police_type_router,
    media_router,
    user_router,
    notice_router,
    roles_router,
    departments_router,
]

__all__ = [
    "all_routers",
    "auth_router", "dashboard_router", "course_router", "exam_router",
    "question_router", "training_router",
    "certificate_router", "profile_router", "report_router",
    "ai_router", "talent_router", "police_type_router",
    "media_router", "user_router", "notice_router", "roles_router", "departments_router",
]
