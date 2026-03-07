"""
文件管理服务
"""
import hashlib
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.media import MediaFile
from app.schemas.media import MediaFileResponse
from config import settings
from logger import logger

# 存储根目录 (backend/data/uploads/)
UPLOAD_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


class MediaService:
    """文件服务"""

    def __init__(self, db: Session):
        self.db = db

    async def upload_file(self, file: UploadFile, uploader_id: int) -> MediaFileResponse:
        """
        上传文件到本地磁盘，写入数据库记录，返回文件信息。
        流式写入，支持大文件；相同 hash 文件自动秒传。
        """
        # 按日期分目录
        now = datetime.now()
        date_dir = f"{now.year}/{now.month:02d}/{now.day:02d}"
        save_dir = UPLOAD_ROOT / date_dir
        _ensure_dir(save_dir)

        ext = Path(file.filename or "file").suffix.lower()
        safe_name = f"{uuid.uuid4().hex}{ext}"
        rel_path = f"{date_dir}/{safe_name}"
        abs_path = save_dir / safe_name

        # 流式写入磁盘并计算 hash
        sha256 = hashlib.sha256()
        file_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        with open(abs_path, "wb") as f:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                sha256.update(chunk)
                file_size += len(chunk)

        file_hash = sha256.hexdigest()

        # 秒传检查：如果相同文件已存在，删除刚写入的文件并复用
        existing = self.db.query(MediaFile).filter(MediaFile.hash == file_hash).first()
        if existing:
            abs_path.unlink(missing_ok=True)
            logger.info(f"秒传命中: {file.filename} -> id={existing.id}")
            return self._to_response(existing)

        # 写入数据库
        media = MediaFile(
            filename=file.filename or safe_name,
            storage_path=rel_path,
            mime_type=file.content_type,
            size=file_size,
            hash=file_hash,
            uploader_id=uploader_id,
        )
        self.db.add(media)
        self.db.commit()
        self.db.refresh(media)

        logger.info(f"文件上传成功: {file.filename} -> {rel_path} ({file_size} bytes)")
        return self._to_response(media)

    def get_file(self, file_id: int) -> Optional[MediaFile]:
        """获取文件记录"""
        return self.db.query(MediaFile).filter(MediaFile.id == file_id).first()

    def get_file_path(self, file_id: int) -> Optional[Path]:
        """获取文件磁盘绝对路径"""
        media = self.get_file(file_id)
        if not media:
            return None
        abs_path = UPLOAD_ROOT / media.storage_path
        if abs_path.exists():
            return abs_path
        return None

    def build_url(self, media: MediaFile) -> str:
        """构建文件直链 URL"""
        return f"{settings.API_V1_STR}/media/files/{media.id}"

    def _to_response(self, media: MediaFile) -> MediaFileResponse:
        return MediaFileResponse(
            id=media.id,
            filename=media.filename,
            mime_type=media.mime_type,
            size=media.size,
            url=self.build_url(media),
            created_at=media.created_at,
        )
