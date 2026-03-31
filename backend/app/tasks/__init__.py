"""后台任务导出"""

from .ai_paper_assembly import generate_ai_paper_assembly_task, schedule_paper_assembly_task
from .ai_question import generate_ai_question_task, schedule_question_task
from .teaching_resource_generation import (
    generate_teaching_resource_generation_task,
    schedule_teaching_resource_generation_task,
)
from .ai_schedule import generate_ai_schedule_task, schedule_ai_schedule_task
from .recommendation import (
    refresh_recommendation_scores_for_user,
    refresh_recommendation_scores_for_all_users,
)

__all__ = [
    "generate_ai_paper_assembly_task",
    "schedule_paper_assembly_task",
    "generate_ai_question_task",
    "schedule_question_task",
    "generate_teaching_resource_generation_task",
    "schedule_teaching_resource_generation_task",
    "generate_ai_schedule_task",
    "schedule_ai_schedule_task",
    'refresh_recommendation_scores_for_user',
    'refresh_recommendation_scores_for_all_users',
]
