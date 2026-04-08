"""
考试管理控制器
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import (
    AdmissionExamCreate,
    AdmissionExamUpdate,
    ExamCreate,
    ExamParticipantImportConfirmRequest,
    ExamPaperCreate,
    ExamPaperUpdate,
    ExamSubmit,
    ExamUpdate,
    PaperFolderCreate,
    PaperFolderUpdate,
    PaperMoveRequest,
)
from app.services import ExamService
from logger import logger


class ExamController:
    """考试控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = ExamService(db)

    def get_exam_papers(
        self,
        page: int = 1,
        size: int = 10,
        paper_status: Optional[str] = None,
        paper_type: Optional[str] = None,
        search: Optional[str] = None,
        current_user_id: Optional[int] = None,
        folder_id: Optional[int] = None,
    ):
        try:
            return self.service.get_exam_papers(page, size, paper_status, paper_type, search, current_user_id, folder_id)
        except Exception as exc:
            logger.error("获取试卷列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取试卷列表失败")

    def get_exam_paper_detail(self, paper_id: int, current_user_id: Optional[int] = None):
        result = self.service.get_exam_paper_detail(paper_id, current_user_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="试卷不存在")
        return result

    def create_exam_paper(self, data: ExamPaperCreate, user_id: int):
        try:
            return self.service.create_exam_paper(data, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("创建试卷异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建试卷失败")

    def update_exam_paper(self, paper_id: int, data: ExamPaperUpdate):
        try:
            return self.service.update_exam_paper(paper_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("更新试卷异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新试卷失败")

    def publish_exam_paper(self, paper_id: int):
        try:
            return self.service.publish_exam_paper(paper_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("发布试卷异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="发布试卷失败")

    def archive_exam_paper(self, paper_id: int):
        try:
            return self.service.archive_exam_paper(paper_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("归档试卷异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="归档试卷失败")

    def delete_exam_paper(self, paper_id: int):
        try:
            self.service.delete_exam_paper(paper_id)
            return {"deleted": True}
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("删除试卷异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除试卷失败")

    # ============== 文件夹管理 ==============

    def get_paper_folders(self, current_user_id: Optional[int] = None):
        try:
            return self.service.get_paper_folders(current_user_id)
        except Exception as exc:
            logger.error("获取文件夹列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取文件夹列表失败")

    def create_paper_folder(self, data: PaperFolderCreate, user_id: int):
        try:
            return self.service.create_paper_folder(data, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("创建文件夹异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建文件夹失败")

    def update_paper_folder(self, folder_id: int, data: PaperFolderUpdate):
        try:
            return self.service.update_paper_folder(folder_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("更新文件夹异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新文件夹失败")

    def delete_paper_folder(self, folder_id: int):
        try:
            self.service.delete_paper_folder(folder_id)
            return {"deleted": True}
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("删除文件夹异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除文件夹失败")

    def move_paper_to_folder(self, paper_id: int, data: PaperMoveRequest):
        try:
            return self.service.move_paper_to_folder(paper_id, data.folder_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("移动试卷异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="移动试卷失败")

    def get_exams(
        self,
        page: int = 1,
        size: int = 10,
        exam_status: Optional[str] = None,
        exam_type: Optional[str] = None,
        search: Optional[str] = None,
        scene: Optional[str] = None,
        training_id: Optional[int] = None,
        purpose: Optional[str] = None,
        department_id: Optional[int] = None,
        police_type_id: Optional[int] = None,
        current_user_id: Optional[int] = None,
    ):
        try:
            return self.service.get_exams(
                page,
                size,
                exam_status,
                exam_type,
                search,
                scene,
                training_id,
                purpose,
                department_id,
                police_type_id,
                current_user_id,
            )
        except Exception as exc:
            logger.error("获取考试列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取考试列表失败")

    def get_admission_exams(
        self,
        page: int = 1,
        size: int = 10,
        exam_status: Optional[str] = None,
        exam_type: Optional[str] = None,
        search: Optional[str] = None,
        current_user_id: Optional[int] = None,
    ):
        try:
            return self.service.get_admission_exams(page, size, exam_status, exam_type, search, current_user_id)
        except Exception as exc:
            logger.error("获取准入考试列表异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取准入考试列表失败")

    def create_exam(self, data: ExamCreate, user_id: int):
        try:
            return self.service.create_exam(data, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("创建培训班内考试异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建考试失败")

    def create_admission_exam(self, data: AdmissionExamCreate, user_id: int):
        try:
            return self.service.create_admission_exam(data, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("创建准入考试异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建准入考试失败")

    def update_exam(self, exam_id: int, data: ExamUpdate):
        try:
            return self.service.update_exam(exam_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("更新培训班内考试异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新考试失败")

    def update_admission_exam(self, exam_id: int, data: AdmissionExamUpdate):
        try:
            return self.service.update_admission_exam(exam_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("更新准入考试异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新准入考试失败")

    def delete_exam(self, exam_id: int):
        try:
            self.service.delete_exam(exam_id)
            return {"deleted": True}
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("删除培训班内考试异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除考试失败")

    def delete_admission_exam(self, exam_id: int):
        try:
            self.service.delete_admission_exam(exam_id)
            return {"deleted": True}
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("删除准入考试异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除准入考试失败")

    def get_exam_detail(self, exam_id: int, current_user_id: Optional[int] = None):
        result = self.service.get_exam_detail(exam_id, current_user_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="考试不存在")
        return result

    def get_admission_exam_detail(self, exam_id: int, current_user_id: Optional[int] = None):
        result = self.service.get_admission_exam_detail(exam_id, current_user_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="准入考试不存在")
        return result

    def submit_exam(self, exam_id: int, user_id: int, data: ExamSubmit):
        try:
            return self.service.submit_exam(exam_id, user_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("提交培训班内考试异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="提交考试失败")

    def submit_admission_exam(self, exam_id: int, user_id: int, data: ExamSubmit):
        try:
            return self.service.submit_admission_exam(exam_id, user_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("提交准入考试异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="提交准入考试失败")

    def get_exam_result(self, exam_id: int, user_id: int):
        result = self.service.get_exam_result(exam_id, user_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="考试记录不存在")
        return result

    def get_admission_exam_result(self, exam_id: int, user_id: int):
        result = self.service.get_admission_exam_result(exam_id, user_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="考试记录不存在")
        return result

    def get_exam_scores(self, exam_id: int, page: int = 1, size: int = 10):
        try:
            return self.service.get_exam_scores(exam_id, page, size)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("获取培训班内考试成绩异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取成绩列表失败")

    def get_admission_exam_scores(self, exam_id: int, page: int = 1, size: int = 10):
        try:
            return self.service.get_admission_exam_scores(exam_id, page, size)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("获取准入考试成绩异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取成绩列表失败")

    def get_exam_analysis(self, exam_id: int):
        try:
            return self.service.get_exam_analysis(exam_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("获取培训班内考试分析异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取考试分析数据失败")

    def get_admission_exam_analysis(self, exam_id: int):
        try:
            return self.service.get_admission_exam_analysis(exam_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("获取准入考试分析异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取考试分析数据失败")

    def build_exam_participant_import_template(self):
        try:
            return self.service.build_exam_participant_import_template()
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("生成考试名单导入模板异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="生成导入模板失败")

    def preview_exam_participant_import(self, exam_id: int, file_bytes: bytes, file_name: str, user_id: int):
        try:
            return self.service.preview_exam_participant_import(exam_id, file_bytes, file_name, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("预检考试名单导入异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="名单预检失败")

    def confirm_exam_participant_import(self, exam_id: int, data: ExamParticipantImportConfirmRequest, user_id: int):
        try:
            return self.service.confirm_exam_participant_import(data, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("确认考试名单导入异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="名单导入失败")

    def list_exam_participants(self, exam_id: int):
        try:
            return self.service.list_exam_participants(exam_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("获取考试名单异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取考试名单失败")

    def export_exam_participant_import_result(self, batch_id: int):
        try:
            return self.service.export_exam_participant_import_result(batch_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as exc:
            logger.error("导出考试名单导入结果异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="导出导入结果失败")

    def get_exam_dashboard(self):
        try:
            return self.service.get_exam_dashboard()
        except Exception as exc:
            logger.error("获取考试看板异常: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取考试看板失败")
