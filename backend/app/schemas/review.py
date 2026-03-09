"""
资源审核工作流相关数据模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ReviewPolicyStageCreate(BaseModel):
    stage_order: int = Field(..., ge=1)
    reviewer_type: str = Field(..., description='role/department/user')
    reviewer_ref_id: int = Field(..., description='审核对象ID')
    min_approvals: int = Field(1, ge=1)
    allow_self_review: bool = False


class ReviewPolicyCreate(BaseModel):
    name: str = Field(..., max_length=100)
    enabled: bool = True
    scope_type: str = Field('global', description='global/department/department_tree')
    scope_department_id: Optional[int] = None
    uploader_constraint: str = Field('all', description='all/specific_role/specific_department')
    constraint_ref_id: Optional[int] = None
    priority: int = Field(100)
    stages: List[ReviewPolicyStageCreate] = Field(default_factory=list)


class ReviewPolicyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    enabled: Optional[bool] = None
    scope_type: Optional[str] = None
    scope_department_id: Optional[int] = None
    uploader_constraint: Optional[str] = None
    constraint_ref_id: Optional[int] = None
    priority: Optional[int] = None
    stages: Optional[List[ReviewPolicyStageCreate]] = None


class ReviewTaskActionRequest(BaseModel):
    comment: Optional[str] = Field(None, description='审核意见')


class ReviewTaskResponse(BaseModel):
    id: int
    workflow_id: int
    resource_id: int
    resource_title: Optional[str] = None
    stage_order: int
    assignee_user_id: int
    assignee_name: Optional[str] = None
    status: str
    comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewWorkflowResponse(BaseModel):
    id: int
    resource_id: int
    policy_id: int
    current_stage: int
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    tasks: List[ReviewTaskResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ReviewPolicyStageResponse(BaseModel):
    id: int
    stage_order: int
    reviewer_type: str
    reviewer_ref_id: int
    min_approvals: int
    allow_self_review: bool

    model_config = ConfigDict(from_attributes=True)


class ReviewPolicyResponse(BaseModel):
    id: int
    name: str
    enabled: bool
    scope_type: str
    scope_department_id: Optional[int] = None
    uploader_constraint: str
    constraint_ref_id: Optional[int] = None
    priority: int
    stages: List[ReviewPolicyStageResponse] = []

    model_config = ConfigDict(from_attributes=True)
