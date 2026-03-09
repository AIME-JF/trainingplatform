"""
资源审核工作流服务
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models import Resource, User, Role, Department
from app.models.review import (
    ReviewPolicy, ReviewPolicyStage,
    ResourceReviewWorkflow, ResourceReviewTask, ResourceReviewLog
)
from app.schemas.review import (
    ReviewPolicyCreate, ReviewPolicyUpdate,
    ReviewPolicyResponse, ReviewPolicyStageResponse,
    ReviewTaskResponse, ReviewWorkflowResponse
)


class ReviewService:
    """审核服务"""

    def __init__(self, db: Session):
        self.db = db

    # ===== policy =====
    def list_policies(self) -> List[ReviewPolicyResponse]:
        policies = self.db.query(ReviewPolicy).options(
            joinedload(ReviewPolicy.stages)
        ).order_by(ReviewPolicy.priority.asc(), ReviewPolicy.id.asc()).all()

        return [self._to_policy_response(p) for p in policies]

    def create_policy(self, data: ReviewPolicyCreate) -> ReviewPolicyResponse:
        policy = ReviewPolicy(
            name=data.name,
            enabled=data.enabled,
            scope_type=data.scope_type,
            scope_department_id=data.scope_department_id,
            uploader_constraint=data.uploader_constraint,
            constraint_ref_id=data.constraint_ref_id,
            priority=data.priority,
        )
        self.db.add(policy)
        self.db.flush()

        for s in sorted(data.stages, key=lambda x: x.stage_order):
            self.db.add(ReviewPolicyStage(
                policy_id=policy.id,
                stage_order=s.stage_order,
                reviewer_type=s.reviewer_type,
                reviewer_ref_id=s.reviewer_ref_id,
                min_approvals=s.min_approvals,
                allow_self_review=s.allow_self_review,
            ))

        self.db.commit()
        self.db.refresh(policy)
        policy = self.db.query(ReviewPolicy).options(joinedload(ReviewPolicy.stages)).filter(ReviewPolicy.id == policy.id).first()
        return self._to_policy_response(policy)

    def update_policy(self, policy_id: int, data: ReviewPolicyUpdate) -> Optional[ReviewPolicyResponse]:
        policy = self.db.query(ReviewPolicy).options(joinedload(ReviewPolicy.stages)).filter(ReviewPolicy.id == policy_id).first()
        if not policy:
            return None

        update_data = data.model_dump(exclude_unset=True)
        stages = update_data.pop('stages', None)

        for k, v in update_data.items():
            setattr(policy, k, v)

        if stages is not None:
            self.db.query(ReviewPolicyStage).filter(ReviewPolicyStage.policy_id == policy.id).delete()
            for s in sorted(stages, key=lambda x: x.stage_order):
                payload = s.model_dump() if hasattr(s, 'model_dump') else dict(s)
                self.db.add(ReviewPolicyStage(
                    policy_id=policy.id,
                    stage_order=payload['stage_order'],
                    reviewer_type=payload['reviewer_type'],
                    reviewer_ref_id=payload['reviewer_ref_id'],
                    min_approvals=payload.get('min_approvals', 1),
                    allow_self_review=payload.get('allow_self_review', False),
                ))

        self.db.commit()
        policy = self.db.query(ReviewPolicy).options(joinedload(ReviewPolicy.stages)).filter(ReviewPolicy.id == policy_id).first()
        return self._to_policy_response(policy)

    # ===== workflow =====
    def submit_resource(self, resource_id: int, submitter_user_id: int) -> ReviewWorkflowResponse:
        resource = self.db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise ValueError('资源不存在')

        if resource.uploader_id != submitter_user_id:
            raise PermissionError('仅上传者可提交审核')

        policy = self._match_policy(resource)
        if not policy:
            raise ValueError('未匹配到可用审核策略')

        workflow = ResourceReviewWorkflow(
            resource_id=resource.id,
            policy_id=policy.id,
            current_stage=1,
            status='pending',
        )
        self.db.add(workflow)
        self.db.flush()

        self._create_stage_tasks(workflow.id, resource.id, policy, stage_order=1, uploader_id=resource.uploader_id)

        resource.status = 'pending_review'
        self._write_log(resource.id, workflow.id, submitter_user_id, 'submit', {'policy_id': policy.id})

        self.db.commit()
        return self.get_workflow(resource.id)

    def list_my_tasks(self, user_id: int, status: str = 'pending') -> List[ReviewTaskResponse]:
        query = self.db.query(ResourceReviewTask).options(
            joinedload(ResourceReviewTask.assignee)
        ).filter(ResourceReviewTask.assignee_user_id == user_id)

        if status:
            query = query.filter(ResourceReviewTask.status == status)

        tasks = query.order_by(ResourceReviewTask.created_at.desc()).all()
        return [self._to_task_response(t) for t in tasks]

    def approve_task(self, task_id: int, actor_id: int, comment: Optional[str] = None) -> ReviewWorkflowResponse:
        task = self.db.query(ResourceReviewTask).filter(ResourceReviewTask.id == task_id).first()
        if not task:
            raise ValueError('审核任务不存在')
        if task.assignee_user_id != actor_id:
            raise PermissionError('无权限处理该任务')
        if task.status != 'pending':
            raise ValueError('任务已处理')

        task.status = 'approved'
        task.comment = comment
        task.reviewed_at = datetime.now()

        workflow = self.db.query(ResourceReviewWorkflow).filter(ResourceReviewWorkflow.id == task.workflow_id).first()
        resource = self.db.query(Resource).filter(Resource.id == task.resource_id).first()
        policy = self.db.query(ReviewPolicy).options(joinedload(ReviewPolicy.stages)).filter(ReviewPolicy.id == workflow.policy_id).first()

        self._write_log(resource.id, workflow.id, actor_id, 'approve', {'task_id': task.id, 'comment': comment})

        self._advance_if_stage_passed(workflow, resource, policy)

        self.db.commit()
        return self.get_workflow(resource.id)

    def reject_task(self, task_id: int, actor_id: int, comment: Optional[str] = None) -> ReviewWorkflowResponse:
        task = self.db.query(ResourceReviewTask).filter(ResourceReviewTask.id == task_id).first()
        if not task:
            raise ValueError('审核任务不存在')
        if task.assignee_user_id != actor_id:
            raise PermissionError('无权限处理该任务')
        if task.status != 'pending':
            raise ValueError('任务已处理')

        task.status = 'rejected'
        task.comment = comment
        task.reviewed_at = datetime.now()

        workflow = self.db.query(ResourceReviewWorkflow).filter(ResourceReviewWorkflow.id == task.workflow_id).first()
        resource = self.db.query(Resource).filter(Resource.id == task.resource_id).first()

        workflow.status = 'rejected'
        workflow.finished_at = datetime.now()
        resource.status = 'rejected'

        self._write_log(resource.id, workflow.id, actor_id, 'reject', {'task_id': task.id, 'comment': comment})

        self.db.commit()
        return self.get_workflow(resource.id)

    def get_workflow(self, resource_id: int) -> Optional[ReviewWorkflowResponse]:
        workflow = self.db.query(ResourceReviewWorkflow).options(
            joinedload(ResourceReviewWorkflow.tasks).joinedload(ResourceReviewTask.assignee)
        ).filter(ResourceReviewWorkflow.resource_id == resource_id).order_by(ResourceReviewWorkflow.id.desc()).first()

        if not workflow:
            return None

        tasks = [self._to_task_response(t) for t in sorted(workflow.tasks, key=lambda x: (x.stage_order, x.id))]
        return ReviewWorkflowResponse(
            id=workflow.id,
            resource_id=workflow.resource_id,
            policy_id=workflow.policy_id,
            current_stage=workflow.current_stage,
            status=workflow.status,
            started_at=workflow.started_at,
            finished_at=workflow.finished_at,
            tasks=tasks,
        )

    # ===== internal =====
    def _match_policy(self, resource: Resource) -> Optional[ReviewPolicy]:
        query = self.db.query(ReviewPolicy).options(joinedload(ReviewPolicy.stages)).filter(ReviewPolicy.enabled == True).order_by(ReviewPolicy.priority.asc(), ReviewPolicy.id.asc())
        policies = query.all()
        for p in policies:
            if p.scope_type == 'global':
                return p
            if p.scope_type in ('department', 'department_tree'):
                if p.scope_department_id and p.scope_department_id == resource.owner_department_id:
                    return p
        return None

    def _resolve_reviewer_user_ids(self, stage: ReviewPolicyStage, uploader_id: int) -> List[int]:
        query = self.db.query(User).filter(User.is_active == True)

        if stage.reviewer_type == 'user':
            user = query.filter(User.id == stage.reviewer_ref_id).first()
            if not user:
                return []
            if not stage.allow_self_review and user.id == uploader_id:
                return []
            return [user.id]

        if stage.reviewer_type == 'role':
            users = query.join(User.roles).filter(Role.id == stage.reviewer_ref_id).all()
            ids = [u.id for u in users if stage.allow_self_review or u.id != uploader_id]
            return sorted(set(ids))

        if stage.reviewer_type == 'department':
            users = query.join(User.departments).filter(Department.id == stage.reviewer_ref_id).all()
            ids = [u.id for u in users if stage.allow_self_review or u.id != uploader_id]
            return sorted(set(ids))

        return []

    def _create_stage_tasks(self, workflow_id: int, resource_id: int, policy: ReviewPolicy, stage_order: int, uploader_id: int):
        stage = next((s for s in (policy.stages or []) if s.stage_order == stage_order), None)
        if not stage:
            return

        assignees = self._resolve_reviewer_user_ids(stage, uploader_id=uploader_id)
        for uid in assignees:
            self.db.add(ResourceReviewTask(
                workflow_id=workflow_id,
                resource_id=resource_id,
                stage_order=stage_order,
                assignee_user_id=uid,
                status='pending',
            ))

    def _advance_if_stage_passed(self, workflow: ResourceReviewWorkflow, resource: Resource, policy: ReviewPolicy):
        current_stage = workflow.current_stage
        stage_cfg = next((s for s in (policy.stages or []) if s.stage_order == current_stage), None)
        if not stage_cfg:
            return

        approved_count = self.db.query(ResourceReviewTask).filter(
            ResourceReviewTask.workflow_id == workflow.id,
            ResourceReviewTask.stage_order == current_stage,
            ResourceReviewTask.status == 'approved',
        ).count()

        if approved_count < stage_cfg.min_approvals:
            workflow.status = 'reviewing'
            resource.status = 'reviewing'
            return

        next_stage = current_stage + 1
        next_stage_cfg = next((s for s in (policy.stages or []) if s.stage_order == next_stage), None)

        if not next_stage_cfg:
            workflow.status = 'approved'
            workflow.finished_at = datetime.now()
            resource.status = 'published'
            if not resource.publish_at:
                resource.publish_at = datetime.now()
            return

        workflow.current_stage = next_stage
        workflow.status = 'reviewing'
        resource.status = 'reviewing'
        self._create_stage_tasks(workflow.id, resource.id, policy, next_stage, uploader_id=resource.uploader_id)

    def _write_log(self, resource_id: int, workflow_id: int, actor_id: int, action: str, detail: Optional[dict] = None):
        self.db.add(ResourceReviewLog(
            resource_id=resource_id,
            workflow_id=workflow_id,
            actor_id=actor_id,
            action=action,
            detail_json=detail,
        ))

    def _to_task_response(self, task: ResourceReviewTask) -> ReviewTaskResponse:
        resource = self.db.query(Resource).filter(Resource.id == task.resource_id).first()
        return ReviewTaskResponse(
            id=task.id,
            workflow_id=task.workflow_id,
            resource_id=task.resource_id,
            resource_title=resource.title if resource else None,
            stage_order=task.stage_order,
            assignee_user_id=task.assignee_user_id,
            assignee_name=task.assignee.nickname if task.assignee else None,
            status=task.status,
            comment=task.comment,
            reviewed_at=task.reviewed_at,
            created_at=task.created_at,
        )

    def _to_policy_response(self, policy: ReviewPolicy) -> ReviewPolicyResponse:
        stages = [
            ReviewPolicyStageResponse(
                id=s.id,
                stage_order=s.stage_order,
                reviewer_type=s.reviewer_type,
                reviewer_ref_id=s.reviewer_ref_id,
                min_approvals=s.min_approvals,
                allow_self_review=s.allow_self_review,
            )
            for s in sorted((policy.stages or []), key=lambda x: x.stage_order)
        ]
        return ReviewPolicyResponse(
            id=policy.id,
            name=policy.name,
            enabled=policy.enabled,
            scope_type=policy.scope_type,
            scope_department_id=policy.scope_department_id,
            uploader_constraint=policy.uploader_constraint,
            constraint_ref_id=policy.constraint_ref_id,
            priority=policy.priority,
            stages=stages,
        )
