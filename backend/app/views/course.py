"""
课程管理路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    StandardResponse, TokenData, PaginatedResponse,
    CourseCreate, CourseUpdate, CourseResponse, CourseListResponse,
    CourseProgressUpdate, CourseProgressResponse,
    CourseNoteUpdate, CourseNoteResponse,
    CourseQACreate, CourseQAResponse,
    CourseTagCreate, CourseTagResponse, CourseLearningStatusResponse,
    CourseResourceBindRequest, ResourceListItemResponse
)
from app.controllers import CourseController
from app.services.course import CourseService

router = APIRouter(prefix="/courses", tags=["课程管理"])


@router.get("", response_model=StandardResponse[PaginatedResponse[CourseListResponse]], summary="课程列表")
def get_courses(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    search: Optional[str] = None,
    category: Optional[str] = None,
    sort: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课程列表"""
    controller = CourseController(db)
    data = controller.get_courses(page, size, search, category, sort, user_id=current_user.user_id)
    return StandardResponse(data=data)


@router.get("/tags", response_model=StandardResponse[List[CourseTagResponse]], summary="课程标签列表")
def get_course_tags(
    search: Optional[str] = Query(None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课程标签列表"""
    controller = CourseController(db)
    data = controller.list_course_tags(search=search)
    return StandardResponse(data=data)


@router.post("/tags", response_model=StandardResponse[CourseTagResponse], summary="创建课程标签")
def create_course_tag(
    data: CourseTagCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建课程标签"""
    controller = CourseController(db)
    data = controller.create_course_tag(data)
    return StandardResponse(data=data)


@router.post("", response_model=StandardResponse[CourseResponse], summary="创建课程")
def create_course(
    data: CourseCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建课程"""
    controller = CourseController(db)
    result = controller.create_course(data, current_user.user_id)
    return StandardResponse(data=result)


@router.get("/progress", response_model=StandardResponse[List[CourseProgressResponse]], summary="当前用户学习进度")
def get_progress(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户学习进度"""
    controller = CourseController(db)
    data = controller.get_user_progress(current_user.user_id)
    return StandardResponse(data=data)


@router.get("/{course_id}", response_model=StandardResponse[CourseResponse], summary="课程详情")
def get_course(
    course_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课程详情（含当前用户章节进度）"""
    controller = CourseController(db)
    data = controller.get_course_by_id(
        course_id,
        user_id=current_user.user_id,
        user_permissions=current_user.permissions,
    )
    return StandardResponse(data=data)


@router.put("/{course_id}", response_model=StandardResponse[CourseResponse], summary="更新课程")
def update_course(
    course_id: int,
    data: CourseUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新课程"""
    controller = CourseController(db)
    result = controller.update_course(course_id, data)
    return StandardResponse(data=result)


@router.delete("/{course_id}", response_model=StandardResponse, summary="删除课程")
def delete_course(
    course_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除课程"""
    controller = CourseController(db)
    controller.delete_course(course_id)
    return StandardResponse(message="课程已删除")


@router.put("/{course_id}/chapters/{chapter_id}/progress",
            response_model=StandardResponse[CourseProgressResponse], summary="更新章节进度")
def update_chapter_progress(
    course_id: int,
    chapter_id: int,
    data: CourseProgressUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新章节学习进度"""
    controller = CourseController(db)
    result = controller.update_chapter_progress(course_id, chapter_id, current_user.user_id, data)
    return StandardResponse(data=result)


@router.get("/{course_id}/note", response_model=StandardResponse[CourseNoteResponse], summary="获取课程笔记")
def get_course_note(
    course_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户课程笔记"""
    controller = CourseController(db)
    result = controller.get_course_note(course_id, current_user.user_id)
    return StandardResponse(data=result)


@router.put("/{course_id}/note", response_model=StandardResponse[CourseNoteResponse], summary="保存课程笔记")
def update_course_note(
    course_id: int,
    data: CourseNoteUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """保存当前用户课程笔记"""
    controller = CourseController(db)
    result = controller.update_course_note(course_id, current_user.user_id, data)
    return StandardResponse(data=result)
@router.get("/{course_id}/qa", response_model=StandardResponse[List[CourseQAResponse]], summary="获取课程答疑列表")
def get_course_qa(
    course_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课程答疑列表"""
    controller = CourseController(db)
    result = controller.get_course_qa(course_id)
    return StandardResponse(data=result)


@router.post("/{course_id}/qa", response_model=StandardResponse[CourseQAResponse], summary="提交课程提问")
def create_course_qa(
    course_id: int,
    data: CourseQACreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交课程提问"""
    controller = CourseController(db)
    result = controller.create_course_qa(course_id, current_user.user_id, data)
    return StandardResponse(data=result)


@router.get(
    "/{course_id}/learning-status",
    response_model=StandardResponse[List[CourseLearningStatusResponse]],
    summary="课程学习情况",
)
def get_course_learning_status(
    course_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取课程学习情况"""
    controller = CourseController(db)
    result = controller.get_course_learning_status(
        course_id,
        current_user.user_id,
        current_user.permissions,
    )
    return StandardResponse(data=result)


@router.post("/{course_id}/resources", response_model=StandardResponse[ResourceListItemResponse], summary="课程绑定资源")
def add_course_resource(
    course_id: int,
    data: CourseResourceBindRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = CourseService(db)
    result = service.add_course_resource(course_id, data)
    return StandardResponse(data=result)


@router.get("/{course_id}/resources", response_model=StandardResponse[List[ResourceListItemResponse]], summary="课程资源列表")
def list_course_resources(
    course_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = CourseService(db)
    result = service.list_course_resources(course_id)
    return StandardResponse(data=result)


@router.delete("/{course_id}/resources/{resource_id}", response_model=StandardResponse, summary="课程解绑资源")
def remove_course_resource(
    course_id: int,
    resource_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = CourseService(db)
    ok = service.remove_course_resource(course_id, resource_id)
    if not ok:
        return StandardResponse(code=404, message="绑定关系不存在")
    return StandardResponse(message="解绑成功")
