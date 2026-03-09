"""
文件管理控制器
"""
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.services.media import MediaService
from app.schemas.media import MediaFileResponse
from logger import logger

# 允许的文件类型
ALLOWED_EXTENSIONS = {'.mp4', '.pdf', '.ppt', '.pptx', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.webp'}
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500MB


class MediaController:
    """文件控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.service = MediaService(db)

    async def upload_file(self, file: UploadFile, uploader_id: int) -> MediaFileResponse:
        """上传文件"""
        # 校验文件名
        if not file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件名不能为空")

        # 校验扩展名
        import os
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {ext}，允许: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        try:
            return await self.service.upload_file(file, uploader_id)
        except Exception as e:
            logger.error(f"文件上传异常: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="文件上传失败")
