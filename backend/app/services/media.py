"""
文件管理服务
"""
import hashlib
import io
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from minio import Minio
from sqlalchemy.orm import Session

from app.models.media import MediaFile
from app.schemas.media import MediaFileResponse
from config import settings
from logger import logger

# 本地存储根目录（仅用于上传临时文件与兼容旧本地文件）
UPLOAD_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"
TMP_DIR = UPLOAD_ROOT / "_tmp"


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def _get_minio_client() -> Minio:
    return Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


class MediaService:
    """文件服务"""

    _bucket_ready = False
    _bucket_policy_ready = False

    # MinIO 同步 SDK，放在线程池中执行避免阻塞事件循环
    @staticmethod
    def _run_blocking(func, *args, **kwargs):
        import asyncio
        return asyncio.to_thread(func, *args, **kwargs)

    def __init__(self, db: Session):
        self.db = db
        self.minio = _get_minio_client()
        self._ensure_bucket()

    def _ensure_bucket(self):
        """确保桶存在并设置只读公共策略"""
        bucket = settings.MINIO_BUCKET

        if not MediaService._bucket_ready:
            if not self.minio.bucket_exists(bucket):
                self.minio.make_bucket(bucket)
                logger.info(f"MinIO桶不存在，已创建: {bucket}")
            MediaService._bucket_ready = True

        if not MediaService._bucket_policy_ready:
            public_readonly_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{bucket}/*"],
                    }
                ],
            }

            self.minio.set_bucket_policy(bucket, json.dumps(public_readonly_policy))
            MediaService._bucket_policy_ready = True
            logger.info(f"MinIO桶策略已设置为公共只读: {bucket}")

    async def upload_file(self, file: UploadFile, uploader_id: int) -> MediaFileResponse:
        """
        上传文件到 MinIO，写入数据库记录，返回文件信息。
        流式读取，支持大文件；相同 hash 文件自动秒传。
        """
        now = datetime.now()
        date_dir = f"{now.year}/{now.month:02d}/{now.day:02d}"

        ext = Path(file.filename or "file").suffix.lower()
        object_key = f"{date_dir}/{uuid.uuid4().hex}{ext}"

        _ensure_dir(TMP_DIR)
        tmp_path = TMP_DIR / f"{uuid.uuid4().hex}.upload"

        sha256 = hashlib.sha256()
        file_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        try:
            # 先流式写到本地临时文件并计算 hash
            with open(tmp_path, "wb") as f:
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    sha256.update(chunk)
                    file_size += len(chunk)

            file_hash = sha256.hexdigest()

            # 秒传检查：如果相同 hash 文件已存在直接复用
            existing = self.db.query(MediaFile).filter(MediaFile.hash == file_hash).first()
            if existing:
                logger.info(f"秒传命中: {file.filename} -> id={existing.id}")
                return self._to_response(existing)

            # 上传到 MinIO（线程池执行，避免阻塞 FastAPI 事件循环）
            with open(tmp_path, "rb") as f:
                await self._run_blocking(
                    self.minio.put_object,
                    bucket_name=settings.MINIO_BUCKET,
                    object_name=object_key,
                    data=f,
                    length=file_size,
                    content_type=file.content_type or "application/octet-stream",
                )

            # 写入数据库
            media = MediaFile(
                filename=file.filename or Path(object_key).name,
                storage_path=object_key,
                mime_type=file.content_type,
                size=file_size,
                hash=file_hash,
                uploader_id=uploader_id,
            )
            self.db.add(media)
            self.db.commit()
            self.db.refresh(media)

            logger.info(f"文件上传成功: {file.filename} -> minio://{settings.MINIO_BUCKET}/{object_key} ({file_size} bytes)")
            return self._to_response(media)
        finally:
            tmp_path.unlink(missing_ok=True)

    def get_file(self, file_id: int) -> Optional[MediaFile]:
        """获取文件记录"""
        return self.db.query(MediaFile).filter(MediaFile.id == file_id).first()

    def get_file_path(self, file_id: int) -> Optional[Path]:
        """
        获取本地文件绝对路径（兼容历史本地文件）
        新上传的 MinIO 文件通常不会命中这里。
        """
        media = self.get_file(file_id)
        if not media:
            return None
        abs_path = UPLOAD_ROOT / media.storage_path
        if abs_path.exists():
            return abs_path
        return None

    def build_url(self, media: MediaFile) -> str:
        """构建文件直链 URL（MinIO 公网地址）"""
        base = (settings.MINIO_PUBLIC_URL or "").rstrip("/")
        bucket = (settings.MINIO_BUCKET or "").strip("/")
        path = (media.storage_path or "").lstrip("/")
        if base and bucket and path:
            return f"{base}/{bucket}/{path}"

        return f"{settings.API_V1_STR}/media/files/{media.id}"

    def create_generated_text_file(
        self,
        *,
        filename: str,
        content: str,
        uploader_id: int,
        mime_type: str = "text/plain; charset=utf-8",
    ) -> MediaFile:
        """将服务端生成的文本内容直接写入对象存储并入库。"""
        now = datetime.now()
        date_dir = f"{now.year}/{now.month:02d}/{now.day:02d}"
        ext = Path(filename or "generated.txt").suffix.lower() or ".txt"
        object_key = f"{date_dir}/{uuid.uuid4().hex}{ext}"
        content_bytes = str(content or "").encode("utf-8")
        file_hash = hashlib.sha256(content_bytes).hexdigest()

        existing = self.db.query(MediaFile).filter(MediaFile.hash == file_hash).first()
        if existing:
            logger.info("生成文件秒传命中: %s -> id=%s", filename, existing.id)
            return existing

        stream = io.BytesIO(content_bytes)
        self.minio.put_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=object_key,
            data=stream,
            length=len(content_bytes),
            content_type=mime_type,
        )

        media = MediaFile(
            filename=filename or Path(object_key).name,
            storage_path=object_key,
            mime_type=mime_type,
            size=len(content_bytes),
            hash=file_hash,
            uploader_id=uploader_id,
        )
        self.db.add(media)
        self.db.flush()
        return media

    def _to_response(self, media: MediaFile) -> MediaFileResponse:
        return MediaFileResponse(
            id=media.id,
            filename=media.filename,
            mime_type=media.mime_type,
            size=media.size,
            url=self.build_url(media),
            created_at=media.created_at,
        )
