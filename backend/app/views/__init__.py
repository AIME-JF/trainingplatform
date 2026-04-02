"""
视图导出
"""

from .ai import router as ai_router
from .auth import router as auth_router
from .certificate import router as certificate_router
from .course import router as course_router
from .dashboard import router as dashboard_router
from .department import router as department_router
from .exam import router as exam_router
from .knowledge_point import router as knowledge_point_router
from .media import router as media_router
from .notice import router as notice_router
from .permission import router as permission_router
from .police_type import router as police_type_router
from .practice import router as practice_router
from .profile import router as profile_router
from .question import router as question_router
from .recommendation import router as recommendation_router
from .report import router as report_router
from .resource import router as resource_router
from .review import router as review_router
from .role import router as role_router
from .system import router as system_router
from .talent import router as talent_router
from .training import router as training_router
from .training_base import router as training_base_router
from .training_type import router as training_type_router
from .user import router as user_router


all_routers = [
    auth_router,
    dashboard_router,
    course_router,
    exam_router,
    knowledge_point_router,
    question_router,
    training_router,
    training_base_router,
    training_type_router,
    certificate_router,
    profile_router,
    report_router,
    ai_router,
    talent_router,
    police_type_router,
    practice_router,
    media_router,
    user_router,
    notice_router,
    role_router,
    system_router,
    department_router,
    permission_router,
    resource_router,
    review_router,
    recommendation_router,
]


__all__ = [
    "all_routers",
    "auth_router",
    "dashboard_router",
    "course_router",
    "exam_router",
    "knowledge_point_router",
    "question_router",
    "training_router",
    "training_base_router",
    "training_type_router",
    "certificate_router",
    "profile_router",
    "report_router",
    "ai_router",
    "talent_router",
    "police_type_router",
    "practice_router",
    "media_router",
    "user_router",
    "notice_router",
    "role_router",
    "system_router",
    "department_router",
    "permission_router",
    "resource_router",
    "review_router",
    "recommendation_router",
]
