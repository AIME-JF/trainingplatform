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
    CourseNoteUpdate, CourseNoteResponse
)
from app.controllers import CourseController

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
    data = controller.get_courses(page, size, search, category, sort)
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
    """获取课程详情"""
    controller = CourseController(db)
    data = controller.get_course_by_id(course_id)
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
