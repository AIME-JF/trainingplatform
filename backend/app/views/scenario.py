"""
场景模拟路由
"""
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.controllers.scenario import ScenarioController
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, TokenData
from app.utils.authz import is_admin_user, is_instructor_user

router = APIRouter(prefix="/scenarios", tags=["scenario"])


def _require_admin_or_instructor(db: Session, user_id: int):
    if not (is_admin_user(db, user_id) or is_instructor_user(db, user_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员或教官可执行该操作")


@router.get("/templates", response_model=StandardResponse, summary="场景模板列表（管理）")
def list_templates(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    category: Optional[str] = Query(None),
    status_value: Optional[str] = Query(None, alias="status"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ScenarioController(db)
    data = controller.list_templates(
        page,
        size,
        category,
        status_value,
        current_user.user_id,
        is_admin=is_admin_user(db, current_user.user_id),
    )
    return StandardResponse(data=data)


@router.get("/templates/available", response_model=StandardResponse, summary="可用场景模板列表")
def list_available_templates(
    category: Optional[str] = Query(None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ScenarioController(db)
    data = controller.list_available_templates(category)
    return StandardResponse(data=data)


@router.get("/templates/{template_id}", response_model=StandardResponse, summary="场景模板详情")
def get_template(
    template_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ScenarioController(db)
    data = controller.get_template(template_id)
    return StandardResponse(data=data)


@router.post("/templates", response_model=StandardResponse, summary="创建场景模板")
def create_template(
    data: dict = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ScenarioController(db)
    result = controller.create_template(data, current_user.user_id)
    return StandardResponse(data=result)


@router.put("/templates/{template_id}", response_model=StandardResponse, summary="更新场景模板")
def update_template(
    template_id: int,
    data: dict = Body(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ScenarioController(db)
    result = controller.update_template(
        template_id,
        data,
        current_user.user_id,
        is_admin=is_admin_user(db, current_user.user_id),
    )
    return StandardResponse(data=result)


@router.delete("/templates/{template_id}", response_model=StandardResponse, summary="删除场景模板")
def delete_template(
    template_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ScenarioController(db)
    result = controller.delete_template(template_id, current_user.user_id, is_admin=is_admin_user(db, current_user.user_id))
    return StandardResponse(data=result)


@router.post("/templates/{template_id}/publish", response_model=StandardResponse, summary="发布场景模板")
def publish_template(
    template_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ScenarioController(db)
    result = controller.publish_template(
        template_id,
        current_user.user_id,
        is_admin=is_admin_user(db, current_user.user_id),
    )
    return StandardResponse(data=result)


@router.post("/sessions", response_model=StandardResponse, summary="开始场景模拟")
def start_session(
    template_id: int = Body(..., embed=True),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ScenarioController(db)
    data = controller.start_session(template_id, current_user.user_id)
    return StandardResponse(data=data)


@router.post("/sessions/{session_id}/messages", response_model=StandardResponse, summary="发送模拟对话消息")
def send_session_message(
    session_id: int,
    content: str = Body(..., embed=True),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ScenarioController(db)
    data = controller.send_session_message(session_id, current_user.user_id, content)
    return StandardResponse(data=data)


@router.post("/sessions/{session_id}/end", response_model=StandardResponse, summary="结束场景模拟并评分")
def end_session(
    session_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ScenarioController(db)
    data = controller.end_session(session_id, current_user.user_id)
    return StandardResponse(data=data)


@router.get("/sessions/my", response_model=StandardResponse, summary="我的模拟记录")
def list_my_sessions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ScenarioController(db)
    data = controller.list_user_sessions(current_user.user_id, page, size)
    return StandardResponse(data=data)


@router.get("/templates/{template_id}/sessions", response_model=StandardResponse, summary="模板下的模拟记录")
def list_template_sessions(
    template_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ScenarioController(db)
    data = controller.list_template_sessions(
        template_id,
        page,
        size,
        current_user.user_id,
        is_admin=is_admin_user(db, current_user.user_id),
    )
    return StandardResponse(data=data)


@router.get("/sessions/{session_id}", response_model=StandardResponse, summary="模拟会话详情")
def get_session_detail(
    session_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ScenarioController(db)
    data = controller.get_session_detail(
        session_id,
        current_user.user_id,
        is_admin=is_admin_user(db, current_user.user_id),
        is_instructor=is_instructor_user(db, current_user.user_id),
    )
    return StandardResponse(data=data)
