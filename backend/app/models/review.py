"""
资源审核工作流相关数据库模型
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON,
    UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ReviewPolicy(Base):
    """审核策略"""
    __tablename__ = 'review_policies'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, comment='策略名称')
    enabled = Column(Boolean, default=True, comment='是否启用')
    scope_type = Column(String(30), nullable=False, default='global', comment='作用域: global/department/department_tree')
    scope_department_id = Column(Integer, ForeignKey('departments.id'), nullable=True, comment='作用部门ID')
    uploader_constraint = Column(String(30), nullable=False, default='all', comment='上传者约束: all/specific_role/specific_department')
    constraint_ref_id = Column(Integer, nullable=True, comment='约束对象ID')
    priority = Column(Integer, default=100, index=True, comment='优先级(小优先)')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment='更新时间')

    stages = relationship('ReviewPolicyStage', back_populates='policy', cascade='all, delete-orphan')


class ReviewPolicyStage(Base):
    """审核策略节点"""
    __tablename__ = 'review_policy_stages'

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey('review_policies.id', ondelete='CASCADE'), nullable=False, index=True)
    stage_order = Column(Integer, nullable=False, comment='阶段顺序')
    reviewer_type = Column(String(30), nullable=False, comment='审核人类型: role/department/user')
    reviewer_ref_id = Column(Integer, nullable=False, comment='审核对象ID')
    min_approvals = Column(Integer, default=1, comment='最小通过数')
    allow_self_review = Column(Boolean, default=False, comment='允许自审')

    __table_args__ = (
        UniqueConstraint('policy_id', 'stage_order', name='uq_review_policy_stage_order'),
    )

    policy = relationship('ReviewPolicy', back_populates='stages')


class ResourceReviewWorkflow(Base):
    """资源审核流程实例"""
    __tablename__ = 'resource_review_workflows'

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey('resources.id', ondelete='CASCADE'), nullable=False, index=True)
    policy_id = Column(Integer, ForeignKey('review_policies.id'), nullable=False, index=True)
    current_stage = Column(Integer, default=1, comment='当前阶段')
    status = Column(String(30), nullable=False, default='pending', index=True, comment='状态: pending/reviewing/approved/rejected/cancelled')
    started_at = Column(DateTime(timezone=True), server_default=func.now(), comment='发起时间')
    finished_at = Column(DateTime(timezone=True), nullable=True, comment='结束时间')

    __table_args__ = (
        Index('ix_workflow_resource_status', 'resource_id', 'status'),
    )

    tasks = relationship('ResourceReviewTask', back_populates='workflow', cascade='all, delete-orphan')


class ResourceReviewTask(Base):
    """资源审核任务"""
    __tablename__ = 'resource_review_tasks'

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey('resource_review_workflows.id', ondelete='CASCADE'), nullable=False, index=True)
    resource_id = Column(Integer, ForeignKey('resources.id', ondelete='CASCADE'), nullable=False, index=True)
    stage_order = Column(Integer, nullable=False, comment='阶段顺序')
    assignee_user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True, comment='审核人ID')
    status = Column(String(30), nullable=False, default='pending', index=True, comment='状态: pending/approved/rejected/skipped')
    comment = Column(Text, nullable=True, comment='审核意见')
    reviewed_at = Column(DateTime(timezone=True), nullable=True, comment='审核时间')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')

    __table_args__ = (
        Index('ix_review_task_assignee_status', 'assignee_user_id', 'status'),
    )

    workflow = relationship('ResourceReviewWorkflow', back_populates='tasks')
    assignee = relationship('User', foreign_keys=[assignee_user_id])


class ResourceReviewLog(Base):
    """资源审核日志"""
    __tablename__ = 'resource_review_logs'

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey('resources.id', ondelete='CASCADE'), nullable=False, index=True)
    workflow_id = Column(Integer, ForeignKey('resource_review_workflows.id', ondelete='CASCADE'), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    action = Column(String(30), nullable=False, comment='动作: submit/approve/reject/revoke/reassign')
    detail_json = Column(JSON, nullable=True, comment='日志详情')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
