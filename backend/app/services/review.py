"""
通用审核工作流引擎

支持 resource / training / exam 等多种业务类型复用。
通过 ReviewCallbackRegistry 实现业务解耦：每种业务注册自己的回调函数，
审核引擎在提交、通过、驳回、阶段推进时触发对应回调来更新业务状态。
"""
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

from sqlalchemy.orm import Session, joinedload

from app.models import Resource, User, Role, Department
from app.models.review import (
    ReviewPolicy, ReviewPolicyStage,
    ReviewWorkflow, ReviewTask, ReviewLog,
)
from app.schemas.review import (
    ReviewPolicyCreate, ReviewPolicyUpdate,
    ReviewPolicyResponse, ReviewPolicyStageResponse,
    ReviewTaskResponse, ReviewWorkflowResponse,
)

VALID_SCOPE_TYPES = {'global', 'department', 'department_tree'}
VALID_UPLOADER_CONSTRAINTS = {'all', 'specific_role', 'specific_department'}
VALID_REVIEWER_TYPES = {'role', 'department', 'user'}
VALID_BUSINESS_TYPES = {'resource', 'training', 'exam'}
DEFAULT_REVIEW_POLICY_NAME = '系统默认审核策略'
DEFAULT_REVIEW_POLICY_PRIORITY = 9999
DEFAULT_REVIEW_ROLE_CODE = 'admin'


# ===================== 回调机制 =====================

@dataclass
class ReviewCallbacks:
    """业务审核回调"""
    on_submitted: Optional[Callable] = None       # (db, business_id) -> None  提交审核后回调
    on_approved: Optional[Callable] = None         # (db, business_id) -> None  审核通过后回调
    on_rejected: Optional[Callable] = None         # (db, business_id) -> None  审核驳回后回调
    on_stage_advanced: Optional[Callable] = None   # (db, business_id) -> None  阶段推进后回调（可选）


class ReviewCallbackRegistry:
    """审核回调注册表，每种 business_type 注册一组回调"""
    _callbacks: Dict[str, ReviewCallbacks] = {}

    @classmethod
    def register(cls, business_type: str, callbacks: ReviewCallbacks):
        cls._callbacks[business_type] = callbacks

    @classmethod
    def get(cls, business_type: str) -> Optional[ReviewCallbacks]:
        return cls._callbacks.get(business_type)


# ===================== 资源审核回调 =====================

def _resource_on_submitted(db: Session, business_id: int):
    resource = db.query(Resource).filter(Resource.id == business_id).first()
    if resource:
        resource.status = 'pending_review'


def _resource_on_approved(db: Session, business_id: int):
    resource = db.query(Resource).filter(Resource.id == business_id).first()
    if resource:
        resource.status = 'published'
        if not resource.publish_at:
            resource.publish_at = datetime.now()


def _resource_on_rejected(db: Session, business_id: int):
    resource = db.query(Resource).filter(Resource.id == business_id).first()
    if resource:
        resource.status = 'rejected'


def _resource_on_stage_advanced(db: Session, business_id: int):
    resource = db.query(Resource).filter(Resource.id == business_id).first()
    if resource:
        resource.status = 'reviewing'


ReviewCallbackRegistry.register('resource', ReviewCallbacks(
    on_submitted=_resource_on_submitted,
    on_approved=_resource_on_approved,
    on_rejected=_resource_on_rejected,
    on_stage_advanced=_resource_on_stage_advanced,
))


# ===================== 审核服务 =====================

class ReviewService:
    """通用审核引擎"""

    def __init__(self, db: Session):
        self.db = db

    # ===== 策略管理 =====
    def list_policies(self, business_type: Optional[str] = None) -> List[ReviewPolicyResponse]:
        query = self.db.query(ReviewPolicy).options(
            joinedload(ReviewPolicy.stages)
        )
        if business_type:
            query = query.filter(ReviewPolicy.business_type == business_type)
        policies = query.order_by(ReviewPolicy.priority.asc(), ReviewPolicy.id.asc()).all()
        return [self._to_policy_response(p) for p in policies]

    def create_policy(self, data: ReviewPolicyCreate) -> ReviewPolicyResponse:
        payload = self._normalize_policy_payload(data.model_dump(mode='python'))
        self._ensure_policy_name_available(payload['name'], business_type=payload['business_type'])
        policy = ReviewPolicy(
            name=payload['name'],
            business_type=payload['business_type'],
            enabled=payload['enabled'],
            scope_type=payload['scope_type'],
            scope_department_id=payload['scope_department_id'],
            uploader_constraint=payload['uploader_constraint'],
            constraint_ref_id=payload['constraint_ref_id'],
            priority=payload['priority'],
        )
        self.db.add(policy)
        self.db.flush()

        for s in payload['stages']:
            self.db.add(ReviewPolicyStage(
                policy_id=policy.id,
                stage_order=s['stage_order'],
                reviewer_type=s['reviewer_type'],
                reviewer_ref_id=s['reviewer_ref_id'],
                min_approvals=s['min_approvals'],
                allow_self_review=s['allow_self_review'],
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
        business_type = update_data.get('business_type', policy.business_type)
        merged_payload = {
            'name': update_data.get('name', policy.name),
            'business_type': business_type,
            'enabled': update_data.get('enabled', policy.enabled),
            'scope_type': update_data.get('scope_type', policy.scope_type),
            'scope_department_id': update_data.get('scope_department_id', policy.scope_department_id),
            'uploader_constraint': update_data.get('uploader_constraint', policy.uploader_constraint),
            'constraint_ref_id': update_data.get('constraint_ref_id', policy.constraint_ref_id),
            'priority': update_data.get('priority', policy.priority),
            'stages': update_data.get('stages', self._serialize_policy_stages(policy.stages or [])),
        }
        normalized_payload = self._normalize_policy_payload(merged_payload)
        self._ensure_policy_name_available(
            normalized_payload['name'],
            business_type=normalized_payload['business_type'],
            excluding_policy_id=policy.id,
        )

        policy.name = normalized_payload['name']
        policy.business_type = normalized_payload['business_type']
        policy.enabled = normalized_payload['enabled']
        policy.scope_type = normalized_payload['scope_type']
        policy.scope_department_id = normalized_payload['scope_department_id']
        policy.uploader_constraint = normalized_payload['uploader_constraint']
        policy.constraint_ref_id = normalized_payload['constraint_ref_id']
        policy.priority = normalized_payload['priority']

        self.db.query(ReviewPolicyStage).filter(ReviewPolicyStage.policy_id == policy.id).delete()
        for stage_payload in normalized_payload['stages']:
            self.db.add(ReviewPolicyStage(
                policy_id=policy.id,
                stage_order=stage_payload['stage_order'],
                reviewer_type=stage_payload['reviewer_type'],
                reviewer_ref_id=stage_payload['reviewer_ref_id'],
                min_approvals=stage_payload['min_approvals'],
                allow_self_review=stage_payload['allow_self_review'],
            ))

        self.db.commit()
        policy = self.db.query(ReviewPolicy).options(joinedload(ReviewPolicy.stages)).filter(ReviewPolicy.id == policy_id).first()
        return self._to_policy_response(policy)

    # ===== 通用工作流 =====
    def submit_for_review(
        self,
        business_type: str,
        business_id: int,
        submitter_user_id: int,
        scope_context: Optional[Dict[str, Any]] = None,
    ) -> ReviewWorkflowResponse:
        """
        通用提交审核入口。

        参数：
            business_type: 业务类型（resource / training / exam）
            business_id: 业务对象 ID
            submitter_user_id: 提交人用户 ID
            scope_context: 策略匹配上下文字典，包含 department_id / uploader_user_id 等
        """
        if business_type not in VALID_BUSINESS_TYPES:
            raise ValueError(f'不支持的业务类型: {business_type}')

        scope_context = scope_context or {}

        # 检查是否已有进行中的审核
        active_workflow = self.db.query(ReviewWorkflow.id).filter(
            ReviewWorkflow.business_type == business_type,
            ReviewWorkflow.business_id == business_id,
            ReviewWorkflow.status.in_(['pending', 'reviewing']),
        ).first()
        if active_workflow:
            raise ValueError('该对象已有进行中的审核流程')

        # 匹配策略
        policy = self._match_policy_by_context(business_type, scope_context)
        if not policy:
            if self._has_enabled_custom_policies(business_type):
                raise ValueError('未匹配到可用审核策略')
            policy = self._ensure_default_policy(business_type)

        # 创建工作流
        workflow = ReviewWorkflow(
            business_type=business_type,
            business_id=business_id,
            policy_id=policy.id,
            current_stage=1,
            status='pending',
        )
        self.db.add(workflow)
        self.db.flush()

        uploader_id = scope_context.get('uploader_user_id') or submitter_user_id
        assignee_count = self._create_stage_tasks(
            workflow.id, business_type, business_id, policy, stage_order=1, uploader_id=uploader_id
        )
        if assignee_count < 1:
            if policy.name == DEFAULT_REVIEW_POLICY_NAME:
                raise ValueError('默认审核策略未找到可用管理员审核人，请先检查管理员账号状态')
            raise ValueError('命中的审核策略第 1 级未找到可用审核人，请先检查策略配置')

        # 触发回调：提交审核
        callbacks = ReviewCallbackRegistry.get(business_type)
        if callbacks and callbacks.on_submitted:
            callbacks.on_submitted(self.db, business_id)

        # 如果是资源类型，设置 review_policy_id
        if business_type == 'resource':
            resource = self.db.query(Resource).filter(Resource.id == business_id).first()
            if resource:
                resource.review_policy_id = policy.id

        self._write_log(business_type, business_id, workflow.id, submitter_user_id, 'submit', {'policy_id': policy.id})
        self.db.commit()
        return self.get_workflow(business_type, business_id)

    def submit_resource(self, resource_id: int, submitter_user_id: int) -> ReviewWorkflowResponse:
        """
        资源审核提交（兼容旧接口）。
        内部调用通用 submit_for_review。
        """
        resource = self.db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise ValueError('资源不存在')
        if resource.uploader_id != submitter_user_id:
            raise PermissionError('仅上传者可提交审核')
        if resource.status not in {'draft', 'rejected'}:
            raise ValueError('当前资源状态不允许提交审核')

        scope_context = {
            'department_id': resource.owner_department_id,
            'uploader_user_id': resource.uploader_id,
        }
        return self.submit_for_review('resource', resource_id, submitter_user_id, scope_context)

    def list_my_tasks(self, user_id: int, status: str = 'pending', business_type: Optional[str] = None) -> List[ReviewTaskResponse]:
        query = self.db.query(ReviewTask).options(
            joinedload(ReviewTask.assignee)
        ).filter(ReviewTask.assignee_user_id == user_id)

        if status:
            query = query.filter(ReviewTask.status == status)
        if business_type:
            query = query.filter(ReviewTask.business_type == business_type)

        tasks = query.order_by(ReviewTask.created_at.desc()).all()
        return [self._to_task_response(t) for t in tasks]

    def approve_task(self, task_id: int, actor_id: int, comment: Optional[str] = None) -> ReviewWorkflowResponse:
        task = self.db.query(ReviewTask).filter(ReviewTask.id == task_id).first()
        if not task:
            raise ValueError('审核任务不存在')
        if task.assignee_user_id != actor_id:
            raise PermissionError('无权限处理该任务')
        if task.status != 'pending':
            raise ValueError('任务已处理')

        task.status = 'approved'
        task.comment = comment
        task.reviewed_at = datetime.now()

        workflow = self.db.query(ReviewWorkflow).filter(ReviewWorkflow.id == task.workflow_id).first()
        policy = self.db.query(ReviewPolicy).options(joinedload(ReviewPolicy.stages)).filter(ReviewPolicy.id == workflow.policy_id).first()

        self._write_log(
            workflow.business_type, workflow.business_id, workflow.id,
            actor_id, 'approve', {'task_id': task.id, 'comment': comment}
        )

        self._advance_if_stage_passed(workflow, policy)

        self.db.commit()
        return self.get_workflow(workflow.business_type, workflow.business_id)

    def reject_task(self, task_id: int, actor_id: int, comment: Optional[str] = None) -> ReviewWorkflowResponse:
        task = self.db.query(ReviewTask).filter(ReviewTask.id == task_id).first()
        if not task:
            raise ValueError('审核任务不存在')
        if task.assignee_user_id != actor_id:
            raise PermissionError('无权限处理该任务')
        if task.status != 'pending':
            raise ValueError('任务已处理')

        task.status = 'rejected'
        task.comment = comment
        task.reviewed_at = datetime.now()

        workflow = self.db.query(ReviewWorkflow).filter(ReviewWorkflow.id == task.workflow_id).first()

        workflow.status = 'rejected'
        workflow.finished_at = datetime.now()
        self._skip_pending_tasks(workflow.id)

        # 触发回调：审核驳回
        callbacks = ReviewCallbackRegistry.get(workflow.business_type)
        if callbacks and callbacks.on_rejected:
            callbacks.on_rejected(self.db, workflow.business_id)

        self._write_log(
            workflow.business_type, workflow.business_id, workflow.id,
            actor_id, 'reject', {'task_id': task.id, 'comment': comment}
        )

        self.db.commit()
        return self.get_workflow(workflow.business_type, workflow.business_id)

    def get_workflow(self, business_type: str, business_id: int) -> Optional[ReviewWorkflowResponse]:
        """获取业务对象最新的审核工作流"""
        workflow = self.db.query(ReviewWorkflow).options(
            joinedload(ReviewWorkflow.tasks).joinedload(ReviewTask.assignee)
        ).filter(
            ReviewWorkflow.business_type == business_type,
            ReviewWorkflow.business_id == business_id,
        ).order_by(ReviewWorkflow.id.desc()).first()

        if not workflow:
            return None

        tasks = [self._to_task_response(t) for t in sorted(workflow.tasks, key=lambda x: (x.stage_order, x.id))]

        return ReviewWorkflowResponse(
            id=workflow.id,
            business_type=workflow.business_type,
            business_id=workflow.business_id,
            resource_id=workflow.business_id if workflow.business_type == 'resource' else None,
            policy_id=workflow.policy_id,
            current_stage=workflow.current_stage,
            status=workflow.status,
            started_at=workflow.started_at,
            finished_at=workflow.finished_at,
            tasks=tasks,
        )

    # ===== 内部方法 =====
    def _match_policy_by_context(
        self, business_type: str, scope_context: Dict[str, Any], include_default: bool = False
    ) -> Optional[ReviewPolicy]:
        """通过 scope_context 字典匹配策略（替代直接依赖 Resource 对象）"""
        query = self.db.query(ReviewPolicy).options(joinedload(ReviewPolicy.stages)).filter(
            ReviewPolicy.enabled == True,
            ReviewPolicy.business_type == business_type,
        )
        if not include_default:
            query = query.filter(ReviewPolicy.name != DEFAULT_REVIEW_POLICY_NAME)
        query = query.order_by(ReviewPolicy.priority.asc(), ReviewPolicy.id.asc())
        policies = query.all()

        uploader_user_id = scope_context.get('uploader_user_id')
        uploader = self._load_user_with_relations(uploader_user_id)
        department_id = scope_context.get('department_id')

        for p in policies:
            if not self._policy_matches_scope_context(p, department_id):
                continue
            if not self._policy_matches_uploader(p, uploader):
                continue
            return p
        return None

    def _policy_matches_scope_context(self, policy: ReviewPolicy, department_id: Optional[int]) -> bool:
        """使用 department_id 匹配策略作用域（不依赖 Resource 对象）"""
        if policy.scope_type == 'global':
            return True
        if not policy.scope_department_id or not department_id:
            return False
        if policy.scope_type == 'department':
            return int(policy.scope_department_id) == int(department_id)
        if policy.scope_type == 'department_tree':
            return int(department_id) in self._get_department_subtree_ids(int(policy.scope_department_id))
        return False

    def _has_enabled_custom_policies(self, business_type: str) -> bool:
        return self.db.query(ReviewPolicy.id).filter(
            ReviewPolicy.enabled == True,
            ReviewPolicy.business_type == business_type,
            ReviewPolicy.name != DEFAULT_REVIEW_POLICY_NAME,
        ).first() is not None

    def _ensure_default_policy(self, business_type: str = 'resource') -> ReviewPolicy:
        admin_role = self._get_default_review_role()
        if not admin_role:
            raise ValueError('当前没有启用审核规则，且未找到可用管理员账号，无法启用默认审核策略')

        policy = self.db.query(ReviewPolicy).options(
            joinedload(ReviewPolicy.stages)
        ).filter(
            ReviewPolicy.name == DEFAULT_REVIEW_POLICY_NAME,
            ReviewPolicy.business_type == business_type,
        ).first()

        if not policy:
            policy = ReviewPolicy(
                name=DEFAULT_REVIEW_POLICY_NAME,
                business_type=business_type,
                enabled=True,
                scope_type='global',
                scope_department_id=None,
                uploader_constraint='all',
                constraint_ref_id=None,
                priority=DEFAULT_REVIEW_POLICY_PRIORITY,
            )
            self.db.add(policy)
            self.db.flush()
        else:
            policy.enabled = True
            policy.scope_type = 'global'
            policy.scope_department_id = None
            policy.uploader_constraint = 'all'
            policy.constraint_ref_id = None
            policy.priority = DEFAULT_REVIEW_POLICY_PRIORITY
            self.db.query(ReviewPolicyStage).filter(
                ReviewPolicyStage.policy_id == policy.id
            ).delete()

        self.db.add(ReviewPolicyStage(
            policy_id=policy.id,
            stage_order=1,
            reviewer_type='role',
            reviewer_ref_id=admin_role.id,
            min_approvals=1,
            allow_self_review=False,
        ))
        self.db.flush()
        self.db.expire(policy, ['stages'])

        return self.db.query(ReviewPolicy).options(
            joinedload(ReviewPolicy.stages)
        ).filter(ReviewPolicy.id == policy.id).first()

    def _get_default_review_role(self) -> Optional[Role]:
        role = self.db.query(Role).filter(
            Role.code == DEFAULT_REVIEW_ROLE_CODE,
            Role.is_active == True,
        ).first()
        if not role:
            return None

        has_active_user = self.db.query(User.id).join(User.roles).filter(
            Role.id == role.id,
            User.is_active == True,
        ).first()
        if not has_active_user:
            return None
        return role

    def _policy_matches_uploader(self, policy: ReviewPolicy, uploader: Optional[User]) -> bool:
        if policy.uploader_constraint == 'all':
            return True
        if not uploader or not policy.constraint_ref_id:
            return False
        if policy.uploader_constraint == 'specific_role':
            return any(int(role.id) == int(policy.constraint_ref_id) for role in (uploader.roles or []))
        if policy.uploader_constraint == 'specific_department':
            return any(int(department.id) == int(policy.constraint_ref_id) for department in (uploader.departments or []))
        return False

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

    def _create_stage_tasks(
        self, workflow_id: int, business_type: str, business_id: int,
        policy: ReviewPolicy, stage_order: int, uploader_id: int,
    ):
        stage = next((s for s in (policy.stages or []) if s.stage_order == stage_order), None)
        if not stage:
            return 0

        assignees = self._resolve_reviewer_user_ids(stage, uploader_id=uploader_id)
        for uid in assignees:
            self.db.add(ReviewTask(
                workflow_id=workflow_id,
                business_type=business_type,
                business_id=business_id,
                stage_order=stage_order,
                assignee_user_id=uid,
                status='pending',
            ))
        return len(assignees)

    def _advance_if_stage_passed(self, workflow: ReviewWorkflow, policy: ReviewPolicy):
        """阶段推进判定——通过回调更新业务状态，不直接操作业务表"""
        current_stage = workflow.current_stage
        stage_cfg = next((s for s in (policy.stages or []) if s.stage_order == current_stage), None)
        if not stage_cfg:
            return

        approved_count = self.db.query(ReviewTask).filter(
            ReviewTask.workflow_id == workflow.id,
            ReviewTask.stage_order == current_stage,
            ReviewTask.status == 'approved',
        ).count()

        callbacks = ReviewCallbackRegistry.get(workflow.business_type)

        if approved_count < stage_cfg.min_approvals:
            workflow.status = 'reviewing'
            # 触发回调：阶段推进（审核中）
            if callbacks and callbacks.on_stage_advanced:
                callbacks.on_stage_advanced(self.db, workflow.business_id)
            return

        self._skip_pending_tasks(workflow.id, stage_order=current_stage)
        next_stage = current_stage + 1
        next_stage_cfg = next((s for s in (policy.stages or []) if s.stage_order == next_stage), None)

        if not next_stage_cfg:
            # 所有阶段通过
            workflow.status = 'approved'
            workflow.finished_at = datetime.now()
            if callbacks and callbacks.on_approved:
                callbacks.on_approved(self.db, workflow.business_id)
            return

        # 推进到下一阶段
        workflow.current_stage = next_stage
        workflow.status = 'reviewing'
        if callbacks and callbacks.on_stage_advanced:
            callbacks.on_stage_advanced(self.db, workflow.business_id)

        # 获取 uploader_id 用于自审判断
        uploader_id = 0
        if workflow.business_type == 'resource':
            resource = self.db.query(Resource).filter(Resource.id == workflow.business_id).first()
            if resource:
                uploader_id = resource.uploader_id
        else:
            # 对于其他业务类型，从提交日志中取提交人
            submit_log = self.db.query(ReviewLog).filter(
                ReviewLog.workflow_id == workflow.id,
                ReviewLog.action == 'submit',
            ).first()
            if submit_log:
                uploader_id = submit_log.actor_id

        assignee_count = self._create_stage_tasks(
            workflow.id, workflow.business_type, workflow.business_id,
            policy, next_stage, uploader_id=uploader_id,
        )
        if assignee_count < 1:
            raise ValueError(f'审核策略第 {next_stage} 级未找到可用审核人，请检查策略配置')

    def _write_log(
        self, business_type: str, business_id: int, workflow_id: int,
        actor_id: int, action: str, detail: Optional[dict] = None,
    ):
        self.db.add(ReviewLog(
            business_type=business_type,
            business_id=business_id,
            workflow_id=workflow_id,
            actor_id=actor_id,
            action=action,
            detail_json=detail,
        ))

    def _to_task_response(self, task: ReviewTask) -> ReviewTaskResponse:
        # 兼容资源类型：返回 resource_id 和 resource_title
        resource_id = None
        resource_title = None
        if task.business_type == 'resource':
            resource_id = task.business_id
            resource = self.db.query(Resource).filter(Resource.id == task.business_id).first()
            resource_title = resource.title if resource else None

        return ReviewTaskResponse(
            id=task.id,
            workflow_id=task.workflow_id,
            business_type=task.business_type,
            business_id=task.business_id,
            resource_id=resource_id,
            resource_title=resource_title,
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
            business_type=policy.business_type,
            enabled=policy.enabled,
            scope_type=policy.scope_type,
            scope_department_id=policy.scope_department_id,
            uploader_constraint=policy.uploader_constraint,
            constraint_ref_id=policy.constraint_ref_id,
            priority=policy.priority,
            stages=stages,
        )

    def _normalize_policy_payload(self, payload: dict) -> dict:
        name = str(payload.get('name') or '').strip()
        if not name:
            raise ValueError('策略名称不能为空')

        business_type = str(payload.get('business_type') or 'resource').strip() or 'resource'
        if business_type not in VALID_BUSINESS_TYPES:
            raise ValueError(f'不支持的业务类型: {business_type}')

        scope_type = str(payload.get('scope_type') or 'global').strip() or 'global'
        if scope_type not in VALID_SCOPE_TYPES:
            raise ValueError('作用域类型不合法')
        scope_department_id = self._normalize_optional_int(payload.get('scope_department_id'))
        if scope_type != 'global':
            if not scope_department_id:
                raise ValueError('选择部门作用域后，必须指定作用部门')
            self._ensure_department_exists(scope_department_id, '作用部门不存在')
        else:
            scope_department_id = None

        uploader_constraint = str(payload.get('uploader_constraint') or 'all').strip() or 'all'
        if uploader_constraint not in VALID_UPLOADER_CONSTRAINTS:
            raise ValueError('上传者约束类型不合法')
        constraint_ref_id = self._normalize_optional_int(payload.get('constraint_ref_id'))
        if uploader_constraint == 'specific_role':
            if not constraint_ref_id:
                raise ValueError('按角色限制上传者时，必须指定角色')
            self._ensure_role_exists(constraint_ref_id, '上传者约束角色不存在')
        elif uploader_constraint == 'specific_department':
            if not constraint_ref_id:
                raise ValueError('按部门限制上传者时，必须指定部门')
            self._ensure_department_exists(constraint_ref_id, '上传者约束部门不存在')
        else:
            constraint_ref_id = None

        stages = self._normalize_policy_stages(payload.get('stages') or [])
        priority = int(payload.get('priority') or 100)

        return {
            'name': name,
            'business_type': business_type,
            'enabled': bool(payload.get('enabled', True)),
            'scope_type': scope_type,
            'scope_department_id': scope_department_id,
            'uploader_constraint': uploader_constraint,
            'constraint_ref_id': constraint_ref_id,
            'priority': priority,
            'stages': stages,
        }

    def _normalize_policy_stages(self, raw_stages: List[dict]) -> List[dict]:
        if not raw_stages:
            raise ValueError('请至少配置一个审核阶段')

        normalized_stages = []
        seen_orders = set()
        for index, raw_stage in enumerate(raw_stages, start=1):
            stage_payload = raw_stage.model_dump(mode='python') if hasattr(raw_stage, 'model_dump') else dict(raw_stage)
            stage_order = int(stage_payload.get('stage_order') or 0)
            if stage_order < 1:
                raise ValueError(f'第 {index} 个审核阶段的顺序必须大于 0')
            if stage_order in seen_orders:
                raise ValueError('审核阶段顺序不能重复')
            seen_orders.add(stage_order)

            reviewer_type = str(stage_payload.get('reviewer_type') or '').strip()
            if reviewer_type not in VALID_REVIEWER_TYPES:
                raise ValueError(f'第 {index} 个审核阶段的审核人类型不合法')

            reviewer_ref_id = self._normalize_optional_int(stage_payload.get('reviewer_ref_id'))
            if not reviewer_ref_id:
                raise ValueError(f'第 {index} 个审核阶段缺少审核对象')

            min_approvals = int(stage_payload.get('min_approvals') or 1)
            if min_approvals < 1:
                raise ValueError(f'第 {index} 个审核阶段的最小通过数必须大于 0')

            self._ensure_reviewer_reference_exists(reviewer_type, reviewer_ref_id, index)
            self._validate_stage_approval_capacity(reviewer_type, reviewer_ref_id, min_approvals, index)

            if reviewer_type == 'user' and min_approvals > 1:
                raise ValueError(f'第 {index} 个审核阶段按用户审核时，最小通过数不能超过 1')

            normalized_stages.append({
                'stage_order': stage_order,
                'reviewer_type': reviewer_type,
                'reviewer_ref_id': reviewer_ref_id,
                'min_approvals': min_approvals,
                'allow_self_review': bool(stage_payload.get('allow_self_review', False)),
            })

        normalized_stages.sort(key=lambda item: item['stage_order'])
        expected_orders = list(range(1, len(normalized_stages) + 1))
        actual_orders = [item['stage_order'] for item in normalized_stages]
        if actual_orders != expected_orders:
            raise ValueError('审核阶段顺序必须从 1 开始并连续递增')
        return normalized_stages

    def _serialize_policy_stages(self, stages: List[ReviewPolicyStage]) -> List[dict]:
        return [
            {
                'stage_order': stage.stage_order,
                'reviewer_type': stage.reviewer_type,
                'reviewer_ref_id': stage.reviewer_ref_id,
                'min_approvals': stage.min_approvals,
                'allow_self_review': stage.allow_self_review,
            }
            for stage in sorted(stages, key=lambda item: item.stage_order)
        ]

    def _ensure_reviewer_reference_exists(self, reviewer_type: str, reviewer_ref_id: int, stage_index: int) -> None:
        if reviewer_type == 'user':
            self._ensure_user_exists(reviewer_ref_id, f'第 {stage_index} 个审核阶段指定的用户不存在')
            return
        if reviewer_type == 'role':
            self._ensure_role_exists(reviewer_ref_id, f'第 {stage_index} 个审核阶段指定的角色不存在')
            return
        if reviewer_type == 'department':
            self._ensure_department_exists(reviewer_ref_id, f'第 {stage_index} 个审核阶段指定的部门不存在')

    def _validate_stage_approval_capacity(self, reviewer_type: str, reviewer_ref_id: int, min_approvals: int, stage_index: int) -> None:
        available_count = self._count_stage_reviewer_candidates(reviewer_type, reviewer_ref_id)
        if available_count < 1:
            raise ValueError(f'第 {stage_index} 个审核阶段没有可分配的有效审核人')
        if min_approvals > available_count:
            raise ValueError(f'第 {stage_index} 个审核阶段的最小通过数不能超过可分配审核人数')

    def _count_stage_reviewer_candidates(self, reviewer_type: str, reviewer_ref_id: int) -> int:
        if reviewer_type == 'user':
            return 1

        query = self.db.query(User.id).filter(User.is_active == True)
        if reviewer_type == 'role':
            return query.join(User.roles).filter(Role.id == reviewer_ref_id).distinct().count()
        if reviewer_type == 'department':
            return query.join(User.departments).filter(Department.id == reviewer_ref_id).distinct().count()
        return 0

    def _load_user_with_relations(self, user_id: Optional[int]) -> Optional[User]:
        if not user_id:
            return None
        return self.db.query(User).options(
            joinedload(User.roles),
            joinedload(User.departments),
        ).filter(User.id == user_id).first()

    def _get_department_subtree_ids(self, root_department_id: int) -> set[int]:
        departments = self.db.query(Department.id, Department.parent_id).all()
        children_map = {}
        for department_id, parent_id in departments:
            children_map.setdefault(parent_id, []).append(department_id)

        result = set()
        queue = [root_department_id]
        while queue:
            current_id = queue.pop(0)
            if current_id in result:
                continue
            result.add(current_id)
            queue.extend(children_map.get(current_id, []))
        return result

    def _skip_pending_tasks(self, workflow_id: int, stage_order: Optional[int] = None) -> None:
        query = self.db.query(ReviewTask).filter(
            ReviewTask.workflow_id == workflow_id,
            ReviewTask.status == 'pending',
        )
        if stage_order is not None:
            query = query.filter(ReviewTask.stage_order == stage_order)
        for task in query.all():
            task.status = 'skipped'
            task.reviewed_at = datetime.now()

    def _ensure_department_exists(self, department_id: int, error_message: str) -> None:
        exists = self.db.query(Department.id).filter(Department.id == department_id).first()
        if not exists:
            raise ValueError(error_message)

    def _ensure_policy_name_available(
        self, name: str, business_type: str = 'resource', excluding_policy_id: Optional[int] = None
    ) -> None:
        query = self.db.query(ReviewPolicy.id).filter(
            ReviewPolicy.name == name,
            ReviewPolicy.business_type == business_type,
        )
        if excluding_policy_id:
            query = query.filter(ReviewPolicy.id != excluding_policy_id)
        if query.first():
            raise ValueError('策略名称已存在，请更换后再保存')

    def _ensure_role_exists(self, role_id: int, error_message: str) -> None:
        exists = self.db.query(Role.id).filter(Role.id == role_id).first()
        if not exists:
            raise ValueError(error_message)

    def _ensure_user_exists(self, user_id: int, error_message: str) -> None:
        exists = self.db.query(User.id).filter(User.id == user_id, User.is_active == True).first()
        if not exists:
            raise ValueError(error_message)

    @staticmethod
    def _normalize_optional_int(value: Optional[int]) -> Optional[int]:
        if value is None or value == '':
            return None
        try:
            normalized = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError('配置项 ID 必须是整数') from exc
        return normalized if normalized > 0 else None
