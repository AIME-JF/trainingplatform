"""后台任务导出"""

from .ai_paper_assembly import generate_ai_paper_assembly_task, schedule_paper_assembly_task
from .ai_paper_generation import generate_ai_paper_generation_task, schedule_ai_paper_generation_task
from .ai_question import generate_ai_question_task, schedule_question_task
from .ai_training_report import generate_ai_training_report_task, schedule_training_report_task
from .teaching_resource_generation import (
    generate_teaching_resource_generation_task,
    schedule_teaching_resource_generation_task,
)
from .ai_schedule import generate_ai_schedule_task, schedule_ai_schedule_task
from .schedule_file_parse import (
    generate_schedule_file_parse_task,
    schedule_schedule_file_parse_task,
)
from .recommendation import (
    refresh_recommendation_scores_for_user,
    refresh_recommendation_scores_for_all_users,
)

__all__ = [
    "generate_ai_paper_assembly_task",
    "schedule_paper_assembly_task",
    "generate_ai_paper_generation_task",
    "schedule_ai_paper_generation_task",
    "generate_ai_question_task",
    "schedule_question_task",
    "generate_ai_training_report_task",
    "schedule_training_report_task",
    "generate_teaching_resource_generation_task",
    "schedule_teaching_resource_generation_task",
    "generate_ai_schedule_task",
    "schedule_ai_schedule_task",
    "generate_schedule_file_parse_task",
    "schedule_schedule_file_parse_task",
    'refresh_recommendation_scores_for_user',
    'refresh_recommendation_scores_for_all_users',
]
