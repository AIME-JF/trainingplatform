"""
考试管理路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.controllers import ExamController
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import (
    AdmissionExamCreate,
    AdmissionExamDetailResponse,
    AdmissionExamRecordResponse,
    AdmissionExamResponse,
    AdmissionExamUpdate,
    ExamCreate,
    ExamDetailResponse,
    ExamPaperCreate,
    ExamPaperDetailResponse,
    ExamPaperResponse,
    ExamPaperUpdate,
    ExamRecordResponse,
    ExamResponse,
    ExamSubmit,
    ExamUpdate,
    PaginatedResponse,
    StandardResponse,
    TokenData,
)
from app.utils.authz import is_admin_user, is_instructor_user

router = APIRouter(prefix="/exams", tags=["考试管理"])


def _require_admin_or_instructor(db: Session, user_id: int):
    if not (is_admin_user(db, user_id) or is_instructor_user(db, user_id)):
        raise HTTPException(status_code=403, detail="仅管理员或教官可执行该操作")


@router.get("/papers", response_model=StandardResponse[PaginatedResponse[ExamPaperResponse]], summary="试卷列表")
def get_exam_papers(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    status: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ExamController(db)
    data = controller.get_exam_papers(page, size, status, type, search)
    return StandardResponse(data=data)


@router.post("/papers", response_model=StandardResponse[ExamPaperDetailResponse], summary="创建试卷")
def create_exam_paper(
    data: ExamPaperCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ExamController(db)
    result = controller.create_exam_paper(data, current_user.user_id)
    return StandardResponse(data=result)


@router.get("/papers/{paper_id}", response_model=StandardResponse[ExamPaperDetailResponse], summary="试卷详情")
def get_exam_paper(
    paper_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ExamController(db)
    data = controller.get_exam_paper_detail(paper_id)
    return StandardResponse(data=data)


@router.put("/papers/{paper_id}", response_model=StandardResponse[ExamPaperDetailResponse], summary="更新试卷")
def update_exam_paper(
    paper_id: int,
    data: ExamPaperUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ExamController(db)
    result = controller.update_exam_paper(paper_id, data)
    return StandardResponse(data=result)


@router.post("/papers/{paper_id}/publish", response_model=StandardResponse[ExamPaperDetailResponse], summary="发布试卷")
def publish_exam_paper(
    paper_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ExamController(db)
    result = controller.publish_exam_paper(paper_id)
    return StandardResponse(data=result)


@router.post("/papers/{paper_id}/archive", response_model=StandardResponse[ExamPaperDetailResponse], summary="归档试卷")
def archive_exam_paper(
    paper_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ExamController(db)
    result = controller.archive_exam_paper(paper_id)
    return StandardResponse(data=result)


@router.delete("/papers/{paper_id}", response_model=StandardResponse[dict], summary="删除试卷")
def delete_exam_paper(
    paper_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ExamController(db)
    result = controller.delete_exam_paper(paper_id)
    return StandardResponse(data=result)


@router.get("/admission", response_model=StandardResponse[PaginatedResponse[AdmissionExamResponse]], summary="准入考试列表")
def get_admission_exams(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    status: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ExamController(db)
    data = controller.get_admission_exams(page, size, status, type, search, current_user.user_id)
    return StandardResponse(data=data)


@router.post("/admission", response_model=StandardResponse[AdmissionExamResponse], summary="创建准入考试")
def create_admission_exam(
    data: AdmissionExamCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ExamController(db)
    result = controller.create_admission_exam(data, current_user.user_id)
    return StandardResponse(data=result)


@router.put("/admission/{exam_id}", response_model=StandardResponse[AdmissionExamResponse], summary="更新准入考试")
def update_admission_exam(
    exam_id: int,
    data: AdmissionExamUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ExamController(db)
    result = controller.update_admission_exam(exam_id, data)
    return StandardResponse(data=result)


@router.get("/admission/{exam_id}", response_model=StandardResponse[AdmissionExamDetailResponse], summary="准入考试详情")
def get_admission_exam(
    exam_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ExamController(db)
    data = controller.get_admission_exam_detail(exam_id)
    return StandardResponse(data=data)


@router.post("/admission/{exam_id}/submit", response_model=StandardResponse[AdmissionExamRecordResponse], summary="提交准入考试")
def submit_admission_exam(
    exam_id: int,
    data: ExamSubmit,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ExamController(db)
    result = controller.submit_admission_exam(exam_id, current_user.user_id, data)
    return StandardResponse(data=result)


@router.get("/admission/{exam_id}/result", response_model=StandardResponse[AdmissionExamRecordResponse], summary="准入考试结果")
def get_admission_exam_result(
    exam_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ExamController(db)
    data = controller.get_admission_exam_result(exam_id, current_user.user_id)
    return StandardResponse(data=data)


@router.get(
    "/admission/{exam_id}/scores",
    response_model=StandardResponse[PaginatedResponse[AdmissionExamRecordResponse]],
    summary="准入考试成绩管理",
)
def get_admission_exam_scores(
    exam_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ExamController(db)
    data = controller.get_admission_exam_scores(exam_id, page, size)
    return StandardResponse(data=data)


@router.get("/admission/{exam_id}/records/analysis", summary="准入考试分析报表")
def get_admission_exam_analysis(
    exam_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ExamController(db)
    data = controller.get_admission_exam_analysis(exam_id)
    return StandardResponse(data=data)


@router.get("", response_model=StandardResponse[PaginatedResponse[ExamResponse]], summary="培训班内考试列表")
def get_exams(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    status: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    training_id: Optional[int] = None,
    purpose: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ExamController(db)
    data = controller.get_exams(page, size, status, type, search, training_id, purpose, current_user.user_id)
    return StandardResponse(data=data)


@router.post("", response_model=StandardResponse[ExamResponse], summary="创建培训班内考试")
def create_exam(
    data: ExamCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ExamController(db)
    result = controller.create_exam(data, current_user.user_id)
    return StandardResponse(data=result)


@router.put("/{exam_id}", response_model=StandardResponse[ExamResponse], summary="更新培训班内考试")
def update_exam(
    exam_id: int,
    data: ExamUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ExamController(db)
    result = controller.update_exam(exam_id, data)
    return StandardResponse(data=result)


@router.get("/{exam_id}", response_model=StandardResponse[ExamDetailResponse], summary="培训班内考试详情")
def get_exam(
    exam_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ExamController(db)
    data = controller.get_exam_detail(exam_id)
    return StandardResponse(data=data)


@router.post("/{exam_id}/submit", response_model=StandardResponse[ExamRecordResponse], summary="提交培训班内考试")
def submit_exam(
    exam_id: int,
    data: ExamSubmit,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ExamController(db)
    result = controller.submit_exam(exam_id, current_user.user_id, data)
    return StandardResponse(data=result)


@router.get("/{exam_id}/result", response_model=StandardResponse[ExamRecordResponse], summary="培训班内考试结果")
def get_exam_result(
    exam_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    controller = ExamController(db)
    data = controller.get_exam_result(exam_id, current_user.user_id)
    return StandardResponse(data=data)


@router.get(
    "/{exam_id}/scores",
    response_model=StandardResponse[PaginatedResponse[ExamRecordResponse]],
    summary="培训班内考试成绩管理",
)
def get_exam_scores(
    exam_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=-1),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ExamController(db)
    data = controller.get_exam_scores(exam_id, page, size)
    return StandardResponse(data=data)


@router.get("/{exam_id}/records/analysis", summary="培训班内考试分析报表")
def get_exam_analysis(
    exam_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin_or_instructor(db, current_user.user_id)
    controller = ExamController(db)
    data = controller.get_exam_analysis(exam_id)
    return StandardResponse(data=data)
