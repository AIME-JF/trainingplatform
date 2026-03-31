"""
Permission group helpers.
"""
from typing import Optional, Tuple


SYSTEM_PERMISSION_GROUP = "SYSTEM"

# Order matters: first matched prefix wins.
_PATH_GROUP_RULES: Tuple[Tuple[str, str], ...] = (
    ("/api/v1/auth", "AUTH"),
    ("/api/v1/users", "USER_MANAGEMENT"),
    ("/api/v1/roles", "ROLE_MANAGEMENT"),
    ("/api/v1/permissions", "PERMISSION_MANAGEMENT"),
    ("/api/v1/departments", "DEPARTMENT_MANAGEMENT"),
    ("/api/v1/police-types", "POLICE_TYPE_MANAGEMENT"),
    ("/api/v1/knowledge-points", "QUESTION_BANK"),
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


def infer_permission_group(path: Optional[str]) -> str:
    """Infer permission group from api path."""
    if not path:
        return SYSTEM_PERMISSION_GROUP

    normalized_path = path.strip()
    if normalized_path in {"/", "/health"}:
        return SYSTEM_PERMISSION_GROUP

    for prefix, group in _PATH_GROUP_RULES:
        if normalized_path.startswith(prefix):
            return group

    return SYSTEM_PERMISSION_GROUP

