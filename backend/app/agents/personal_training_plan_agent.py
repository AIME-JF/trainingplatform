"""
个性化训练方案智能体服务
"""
from typing import List

from sqlalchemy.orm import Session, selectinload

from app.models import AITask, PersonalTrainingPlanSnapshot, Resource, ResourceTagRelation
from app.schemas import (
    AIPersonalTrainingAction,
    AIPersonalTrainingPlan,
    AIPersonalTrainingPortrait,
    AIPersonalTrainingResourceRecommendation,
    AIPersonalTrainingTaskCreateRequest,
    AIPersonalTrainingTaskUpdateRequest,
)
from app.services.recommendation import RecommendationService
from app.services.training_portrait_aggregator import TrainingPortraitAggregator


class PersonalTrainingPlanAgentService:
    """基于画像的个训方案生成与确认服务"""

    def __init__(self, db: Session):
        self.db = db
        self.recommendation_service = RecommendationService(db)
        self.portrait_aggregator = TrainingPortraitAggregator(db)

    def build_task_result(self, data: AIPersonalTrainingTaskCreateRequest, current_user_id: int) -> dict:
        portrait = self.portrait_aggregator.build_portrait(data.training_id, data.target_user_id, current_user_id)
        plan = self._build_plan(data, portrait)
        return {
            "portrait": portrait.model_dump(mode="json"),
            "plan": plan.model_dump(mode="json"),
        }

    def validate_task_update(
        self,
        task: AITask,
        data: AIPersonalTrainingTaskUpdateRequest,
        current_user_id: int,
    ) -> AIPersonalTrainingTaskUpdateRequest:
        request_payload = AIPersonalTrainingTaskCreateRequest.model_validate(task.request_payload or {})
        portrait = self.portrait_aggregator.build_portrait(
            request_payload.training_id,
            request_payload.target_user_id,
            current_user_id,
        )
        if data.portrait.user_id != request_payload.target_user_id:
            raise ValueError("画像学员与任务目标学员不一致")
        if data.portrait.training_id != request_payload.training_id:
            raise ValueError("画像培训班与任务不一致")
        if data.plan.cycle_days != request_payload.plan_cycle_days:
            raise ValueError("方案周期与任务配置不一致")
        return data.model_copy(update={"portrait": portrait})

    def confirm_task(self, task: AITask, current_user_id: int) -> PersonalTrainingPlanSnapshot:
        request_payload = AIPersonalTrainingTaskCreateRequest.model_validate(task.request_payload or {})
        result_payload = task.result_payload or {}
        portrait_payload = result_payload.get("portrait")
        plan_payload = result_payload.get("plan")
        if not portrait_payload or not plan_payload:
            raise ValueError("任务结果中没有可确认的个训方案")

        portrait = AIPersonalTrainingPortrait.model_validate(portrait_payload)
        plan = AIPersonalTrainingPlan.model_validate(plan_payload)
        self.portrait_aggregator.build_portrait(request_payload.training_id, request_payload.target_user_id, current_user_id)

        latest = self.db.query(PersonalTrainingPlanSnapshot.version_no).filter(
            PersonalTrainingPlanSnapshot.training_id == request_payload.training_id,
            PersonalTrainingPlanSnapshot.user_id == request_payload.target_user_id,
        ).order_by(PersonalTrainingPlanSnapshot.version_no.desc()).first()
        version_no = (latest[0] if latest else 0) + 1

        snapshot = PersonalTrainingPlanSnapshot(
            ai_task_id=task.id,
            training_id=request_payload.training_id,
            user_id=request_payload.target_user_id,
            version_no=version_no,
            task_name=task.task_name,
            request_payload=request_payload.model_dump(mode="json"),
            portrait_payload=portrait.model_dump(mode="json"),
            plan_payload=plan.model_dump(mode="json"),
            summary=plan.summary,
            created_by=task.created_by,
            confirmed_by=current_user_id,
        )
        self.db.add(snapshot)
        self.db.flush()
        return snapshot

    def _build_plan(
        self,
        data: AIPersonalTrainingTaskCreateRequest,
        portrait: AIPersonalTrainingPortrait,
    ) -> AIPersonalTrainingPlan:
        focus_codes = {item.code for item in portrait.tags}
        objectives = self._build_objectives(data, focus_codes)
        actions = self._build_actions(data, focus_codes)
        resources = self._build_resource_recommendations(portrait.user_id, portrait.preferred_resource_tags, focus_codes)
        coach_tips = self._build_coach_tips(focus_codes)
        student_tips = self._build_student_tips(focus_codes)

        tag_labels = "、".join(item.label for item in portrait.tags[:3])
        return AIPersonalTrainingPlan(
            title=f"{portrait.user_name}个性化训练方案",
            cycle_days=data.plan_cycle_days,
            weekly_sessions=data.weekly_sessions,
            objectives=objectives,
            actions=actions,
            resource_recommendations=resources,
            coach_tips=coach_tips,
            student_tips=student_tips,
            summary=f"围绕“{data.plan_goal}”，结合画像标签 {tag_labels or '稳定提升'} 制定 {data.plan_cycle_days} 天方案。",
        )

    def _build_objectives(self, data: AIPersonalTrainingTaskCreateRequest, focus_codes: set[str]) -> List[str]:
        objectives = [data.plan_goal]
        if "theory_weak" in focus_codes:
            objectives.append("稳住理论基础题型，提升错题回顾效率")
        if "practice_weak" in focus_codes:
            objectives.append("通过实战复盘和动作拆解补齐实操短板")
        if "attendance_risk" in focus_codes:
            objectives.append("提高训练到场率和按计划执行率")
        if "exam_boost" in focus_codes:
            objectives.append("围绕结训考试进行考前强化")
        if len(objectives) == 1:
            objectives.append("维持当前训练节奏，围绕重点课程做精细提升")
        return objectives[:4]

    def _build_actions(self, data: AIPersonalTrainingTaskCreateRequest, focus_codes: set[str]) -> List[AIPersonalTrainingAction]:
        actions: List[AIPersonalTrainingAction] = []
        if data.focus_mode in {"auto", "theory"} or "theory_weak" in focus_codes:
            actions.append(AIPersonalTrainingAction(
                title="理论专项巩固",
                description="围绕近期考试错题和高频知识点进行分组训练。",
                frequency=f"每周 {max(1, data.weekly_sessions // 2)} 次",
                duration_minutes=45,
                emphasis="先做错题回顾，再做同类变式训练",
                execution_tips="每次训练后记录 3 个仍不稳固的知识点",
            ))
        if data.focus_mode in {"auto", "practice"} or "practice_weak" in focus_codes:
            actions.append(AIPersonalTrainingAction(
                title="实操动作复盘",
                description="结合班级训练项目做标准动作拆解和场景复盘。",
                frequency=f"每周 {max(1, data.weekly_sessions // 2)} 次",
                duration_minutes=60,
                emphasis="以一次完整流程演练为主，复盘关键动作",
                execution_tips="建议与教官确认 1 个重点动作进行针对性纠偏",
            ))
        if "attendance_risk" in focus_codes:
            actions.append(AIPersonalTrainingAction(
                title="训练打卡纠偏",
                description="建立个人训练清单，按周完成签到与复盘。",
                frequency="每日 1 次",
                duration_minutes=15,
                emphasis="先恢复稳定执行，再追加强化内容",
                execution_tips="每周末回看未完成项，及时补课",
            ))
        if "exam_boost" in focus_codes or data.focus_mode == "exam":
            actions.append(AIPersonalTrainingAction(
                title="考前冲刺",
                description="针对结训考试进行限时训练和错题再练。",
                frequency="每周 2 次",
                duration_minutes=50,
                emphasis="模拟限时，压缩答题犹豫时间",
                execution_tips="建议在正式考试前完成 2 轮整卷模拟",
            ))
        if not actions:
            actions.append(AIPersonalTrainingAction(
                title="稳态提升训练",
                description="保持节奏，围绕当前课程重点进行巩固。",
                frequency=f"每周 {data.weekly_sessions} 次",
                duration_minutes=45,
                emphasis="保持稳定训练频率",
                execution_tips="每次训练后简短记录本次收获和疑点",
            ))
        return actions[:4]

    def _build_resource_recommendations(
        self,
        user_id: int,
        preferred_tags: List[str],
        focus_codes: set[str],
    ) -> List[AIPersonalTrainingResourceRecommendation]:
        feed = self.recommendation_service.get_recommendation_feed(user_id, page=1, size=5)
        rows = feed.get("items") or []
        resource_ids = [int(item.get("resource_id")) for item in rows if item.get("resource_id")]
        if not resource_ids:
            return []

        score_map = {int(item["resource_id"]): float(item.get("score") or 0) for item in rows}
        resources = self.db.query(Resource).options(
            selectinload(Resource.tag_relations).joinedload(ResourceTagRelation.tag),
        ).filter(Resource.id.in_(resource_ids)).all()

        recommendations: List[AIPersonalTrainingResourceRecommendation] = []
        for resource in resources:
            tag_names = [relation.tag.name for relation in (resource.tag_relations or []) if relation.tag and relation.tag.name]
            reason = "结合近期学习行为与推荐分排序"
            if preferred_tags and set(tag_names).intersection(preferred_tags):
                reason = f"匹配你的资源偏好标签：{'、'.join(sorted(set(tag_names).intersection(preferred_tags))[:2])}"
            elif "theory_weak" in focus_codes:
                reason = "建议优先用于理论短板补齐"
            elif "practice_weak" in focus_codes:
                reason = "建议用于实操动作复盘"
            recommendations.append(AIPersonalTrainingResourceRecommendation(
                resource_id=resource.id,
                title=resource.title,
                score=round(score_map.get(resource.id, 0), 2),
                reason=reason,
                tag_names=tag_names[:5],
            ))
        return sorted(recommendations, key=lambda item: item.score, reverse=True)

    def _build_coach_tips(self, focus_codes: set[str]) -> List[str]:
        tips = []
        if "attendance_risk" in focus_codes:
            tips.append("优先盯执行节奏，先把缺课补齐，再追加强化内容。")
        if "practice_weak" in focus_codes:
            tips.append("建议在周训练中安排一次针对性动作点评，避免泛化训练。")
        if "theory_weak" in focus_codes:
            tips.append("理论训练建议采用错题簿 + 小测快反馈方式。")
        if not tips:
            tips.append("当前状态相对稳定，可按训练计划做滚动优化。")
        return tips[:3]

    def _build_student_tips(self, focus_codes: set[str]) -> List[str]:
        tips = []
        if "progress_lag" in focus_codes:
            tips.append("先补齐落后的学习进度，再做额外强化，避免越练越散。")
        if "exam_boost" in focus_codes:
            tips.append("考前阶段尽量固定复习时段，减少临时突击。")
        tips.append("每次训练后用 5 分钟记录疑点，下一次优先处理。")
        return tips[:3]
