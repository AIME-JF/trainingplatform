"""
系统配置路由
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers import SystemConfigController
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import DashboardModuleConfig
from app.schemas import (
    ConfigCreate,
    ConfigGroupCreate,
    ConfigGroupDetailResponse,
    ConfigGroupResponse,
    ConfigGroupUpdate,
    ConfigResponse,
    ConfigUpdate,
    DashboardModuleConfigCreate,
    DashboardModuleConfigUpdate,
    DashboardModuleConfigResponse,
    PaginatedResponse,
    StandardResponse,
    TokenData,
)
from app.utils.authz import is_admin_user

router = APIRouter(prefix="/system", tags=["system_configuration"])


def _require_admin(db: Session, user_id: int):
    if not is_admin_user(db, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可执行该操作")


@router.get(
    "/config-groups",
    response_model=StandardResponse[PaginatedResponse[ConfigGroupResponse]],
    summary="配置组列表",
)
def get_config_groups(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=-1, description="每页大小，-1 表示全部"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    data = controller.get_config_groups(page, size)
    return StandardResponse(data=data)


@router.post(
    "/config-groups",
    response_model=StandardResponse[ConfigGroupResponse],
    summary="创建配置组",
)
def create_config_group(
    data: ConfigGroupCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    result = controller.create_config_group(data)
    return StandardResponse(message="创建配置组成功", data=result)


@router.get(
    "/config-groups/{group_id}",
    response_model=StandardResponse[ConfigGroupDetailResponse],
    summary="配置组详情",
)
def get_config_group(
    group_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    result = controller.get_config_group_by_id(group_id)
    return StandardResponse(data=result)


@router.put(
    "/config-groups/{group_id}",
    response_model=StandardResponse[ConfigGroupResponse],
    summary="更新配置组",
)
def update_config_group(
    group_id: int,
    data: ConfigGroupUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    result = controller.update_config_group(group_id, data)
    return StandardResponse(message="更新配置组成功", data=result)


@router.delete(
    "/config-groups/{group_id}",
    response_model=StandardResponse,
    summary="删除配置组",
)
def delete_config_group(
    group_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    controller.delete_config_group(group_id)
    return StandardResponse(message="删除配置组成功")


@router.post(
    "/config-groups/{group_id}/reset",
    response_model=StandardResponse[ConfigGroupDetailResponse],
    summary="重置配置组",
)
def reset_config_group(
    group_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    result = controller.reset_config_group(group_id)
    return StandardResponse(message="重置配置组成功", data=result)


@router.get(
    "/configs",
    response_model=StandardResponse[PaginatedResponse[ConfigResponse]],
    summary="配置项列表",
)
def get_configs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=-1, description="每页大小，-1 表示全部"),
    group_id: Optional[int] = Query(None, description="配置组ID"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    data = controller.get_configs(page, size, group_id)
    return StandardResponse(data=data)


@router.post(
    "/configs",
    response_model=StandardResponse[ConfigResponse],
    summary="创建配置项",
)
def create_config(
    data: ConfigCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    result = controller.create_config(data)
    return StandardResponse(message="创建配置项成功", data=result)


@router.get(
    "/configs/{config_id}",
    response_model=StandardResponse[ConfigResponse],
    summary="配置项详情",
)
def get_config(
    config_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    result = controller.get_config_by_id(config_id)
    return StandardResponse(data=result)


@router.put(
    "/configs/{config_id}",
    response_model=StandardResponse[ConfigResponse],
    summary="更新配置项",
)
def update_config(
    config_id: int,
    data: ConfigUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    result = controller.update_config(config_id, data)
    return StandardResponse(message="更新配置项成功", data=result)


@router.delete(
    "/configs/{config_id}",
    response_model=StandardResponse,
    summary="删除配置项",
)
def delete_config(
    config_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    controller = SystemConfigController(db)
    controller.delete_config(config_id)
    return StandardResponse(message="删除配置项成功")


# ===== 看板模块配置 =====

@router.get(
    "/dashboard-modules",
    response_model=StandardResponse[List[DashboardModuleConfigResponse]],
    summary="看板模块配置列表",
)
def get_dashboard_modules(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取所有看板模块配置（管理员获取全部，普通用户获取自己角色可见的模块）"""
    # 库中无记录时自动初始化预置模块
    count = db.query(DashboardModuleConfig.id).count()
    if count == 0:
        _seed_default_dashboard_modules(db)
    records = db.query(DashboardModuleConfig).order_by(
        DashboardModuleConfig.sort_order.asc(), DashboardModuleConfig.id.asc()
    ).all()
    if is_admin_user(db, current_user.user_id):
        return StandardResponse(data=[DashboardModuleConfigResponse.model_validate(r) for r in records])
    # 非管理员：根据用户角色过滤
    from app.models import User, Role
    from sqlalchemy.orm import selectinload
    user = db.query(User).options(selectinload(User.roles)).filter(User.id == current_user.user_id).first()
    user_role_codes = {role.code for role in (user.roles or []) if role.is_active} if user else set()
    visible = []
    for r in records:
        if not r.is_active:
            continue
        allowed_roles = set(r.visible_role_codes or [])
        if not allowed_roles or allowed_roles & user_role_codes:
            visible.append(DashboardModuleConfigResponse.model_validate(r))
    return StandardResponse(data=visible)


@router.put(
    "/dashboard-modules/{module_id}",
    response_model=StandardResponse[DashboardModuleConfigResponse],
    summary="更新看板模块配置",
)
def update_dashboard_module(
    module_id: int,
    data: DashboardModuleConfigUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(db, current_user.user_id)
    record = db.query(DashboardModuleConfig).filter(DashboardModuleConfig.id == module_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="模块配置不存在")
    for field_name in ["module_name", "module_description", "category", "visible_role_codes", "sort_order", "is_active"]:
        value = getattr(data, field_name, None)
        if value is not None:
            setattr(record, field_name, value)
    db.commit()
    db.refresh(record)
    return StandardResponse(data=DashboardModuleConfigResponse.model_validate(record))


_DEFAULT_DASHBOARD_MODULES = [
    {"module_key": "kpi_overview", "module_name": "核心指标概览", "category": "general", "sort_order": 1,
     "module_description": "参训总数、课程完成率、平均考核分、考试通过率",
     "visible_role_codes": ["admin", "instructor", "student"]},
    {"module_key": "training_kpi", "module_name": "培训运营指标", "category": "training", "sort_order": 2,
     "module_description": "进行中培训班、本月参训人数、培训完成率、待审核学员",
     "visible_role_codes": ["admin", "instructor"]},
    {"module_key": "completion_trend", "module_name": "完成率趋势", "category": "general", "sort_order": 3,
     "module_description": "按月统计课程完成率变化趋势",
     "visible_role_codes": ["admin", "instructor"]},
    {"module_key": "training_trend", "module_name": "培训趋势", "category": "training", "sort_order": 4,
     "module_description": "近 6 个月培训完成率变化趋势",
     "visible_role_codes": ["admin", "instructor"]},
    {"module_key": "police_type_dist", "module_name": "警种分布", "category": "general", "sort_order": 5,
     "module_description": "按警种统计学习时长分布",
     "visible_role_codes": ["admin"]},
    {"module_key": "city_attendance", "module_name": "各单位参训人数", "category": "training", "sort_order": 6,
     "module_description": "各部门本月参训人数排名",
     "visible_role_codes": ["admin"]},
    {"module_key": "city_ranking", "module_name": "各单位考核排名", "category": "general", "sort_order": 7,
     "module_description": "各部门平均考核得分排名",
     "visible_role_codes": ["admin"]},
    {"module_key": "city_completion", "module_name": "各单位完成率排名", "category": "training", "sort_order": 8,
     "module_description": "各部门培训完成率排名",
     "visible_role_codes": ["admin"]},
]


def _seed_default_dashboard_modules(db: Session):
    """表中无记录时自动写入预置模块"""
    for item in _DEFAULT_DASHBOARD_MODULES:
        record = DashboardModuleConfig(**item, is_active=True)
        db.add(record)
    db.commit()
