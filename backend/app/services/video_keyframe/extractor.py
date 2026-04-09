"""
视频关键帧抽取主编排：压缩缩略图 → 基础采样 → 场景检测 → 去重 → 限额裁剪 → 输出。
"""
from __future__ import annotations

import subprocess
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

import cv2
from minio import Minio
from sqlalchemy.orm import Session

from app.models import MediaFile, VideoKeyframeTask, VideoKeyframe
from config import settings
from logger import logger

from .base_sampler import CandidateFrame, generate_base_sample_points
from .scene_detector import detect_scene_changes
from .deduplicator import deduplicate_near_neighbors, deduplicate_by_image_hash
from .quota_limiter import apply_quota

TMP_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "keyframe_tmp"


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def _get_minio_client() -> Minio:
    return Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


def _ensure_bucket(client: Minio, bucket: str):
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def _download_from_minio(client: Minio, bucket: str, object_key: str, local_path: Path):
    """从 MinIO 下载文件到本地"""
    client.fget_object(bucket, object_key, str(local_path))


def _upload_to_minio(client: Minio, bucket: str, object_key: str, local_path: Path, content_type: str = "image/jpeg"):
    """上传本地文件到 MinIO"""
    client.fput_object(bucket, object_key, str(local_path), content_type=content_type)


def _compress_video(input_path: Path, output_path: Path, height: int = 480, fps: int = 5) -> float:
    """
    使用 ffmpeg 将视频压缩为缩略图视频。
    返回压缩后视频时长(秒)。
    """
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", f"scale=-2:{height}",
        "-r", str(fps),
        "-c:v", "libx264", "-preset", "fast", "-crf", "28",
        "-an",  # 去掉音频
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 压缩失败: {result.stderr[:500]}")

    # 用 ffprobe 获取压缩后时长
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(output_path),
    ]
    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
    try:
        return float(probe_result.stdout.strip())
    except (ValueError, AttributeError):
        return 0.0


def _extract_frame_image(video_path: Path, timestamp: float, output_path: Path, jpeg_quality: int = 80) -> tuple:
    """
    使用 OpenCV 从视频中抽取指定时间点的帧并保存为 JPEG。
    返回 (width, height)。
    """
    cap = cv2.VideoCapture(str(video_path))
    try:
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError(f"无法读取 {timestamp}s 处的帧")
        h, w = frame.shape[:2]
        cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
        return w, h
    finally:
        cap.release()


class VideoKeyframeExtractor:
    """视频关键帧抽取器"""

    def __init__(self, db: Session):
        self.db = db

    def execute(self, task_id: int) -> None:
        """执行完整的关键帧抽取流程"""
        task = self.db.query(VideoKeyframeTask).filter(VideoKeyframeTask.id == task_id).first()
        if not task:
            logger.warning("关键帧任务不存在: {}", task_id)
            return

        if task.status in ("success", "partial_success", "failed"):
            logger.info("关键帧任务已结束，跳过: {}", task_id)
            return

        task.status = "running"
        task.started_at = datetime.now()
        self.db.commit()

        media = self.db.query(MediaFile).filter(MediaFile.id == task.media_file_id).first()
        if not media:
            self._fail_task(task, "原始视频文件不存在")
            return

        _ensure_dir(TMP_DIR)
        work_id = uuid.uuid4().hex[:12]
        original_path = TMP_DIR / f"{work_id}_original.mp4"
        thumbnail_path = TMP_DIR / f"{work_id}_thumbnail.mp4"
        frames_dir = TMP_DIR / f"{work_id}_frames"
        _ensure_dir(frames_dir)

        minio_client = _get_minio_client()
        bucket = settings.MINIO_BUCKET
        _ensure_bucket(minio_client, bucket)
        scene_degraded = False

        try:
            # 1. 从 MinIO 下载原始视频
            logger.info("下载原始视频: {}", media.storage_path)
            _download_from_minio(minio_client, bucket, media.storage_path, original_path)

            # 2. 压缩为缩略图视频
            logger.info("压缩缩略图视频: {}", thumbnail_path)
            duration = _compress_video(
                original_path, thumbnail_path,
                height=settings.KEYFRAME_THUMBNAIL_HEIGHT,
                fps=settings.KEYFRAME_THUMBNAIL_FPS,
            )
            if duration <= 0:
                duration = float(media.duration_seconds or 0)
            if duration <= 0:
                self._fail_task(task, "无法获取视频时长")
                return

            task.video_duration = duration

            # 3. 上传缩略图视频到 MinIO（持久化）
            thumbnail_key = f"keyframes/{media.id}/thumbnail.mp4"
            _upload_to_minio(minio_client, bucket, thumbnail_key, thumbnail_path, "video/mp4")
            task.thumbnail_storage_path = thumbnail_key
            self.db.commit()

            # 可以删除原始视频本地副本，后续只用缩略图
            original_path.unlink(missing_ok=True)

            # 4. 基础时间采样
            base_candidates = generate_base_sample_points(duration, settings.KEYFRAME_BASE_INTERVAL_SECONDS)
            task.base_candidate_count = len(base_candidates)

            # 5. 场景切换检测
            scene_candidates = detect_scene_changes(str(thumbnail_path), duration)
            task.scene_candidate_count = len(scene_candidates)
            if not scene_candidates and base_candidates:
                scene_degraded = True

            # 6. 合并候选帧
            all_candidates = base_candidates + scene_candidates

            # 7. 近邻去重
            all_candidates = deduplicate_near_neighbors(all_candidates)

            # 8. 抽取候选帧图片
            frame_images: Dict[float, Path] = {}
            for candidate in all_candidates:
                frame_path = frames_dir / f"frame_{candidate.timestamp:.3f}.jpg"
                try:
                    _extract_frame_image(thumbnail_path, candidate.timestamp, frame_path, settings.KEYFRAME_JPEG_QUALITY)
                    frame_images[candidate.timestamp] = frame_path
                except Exception as exc:
                    logger.warning("抽帧失败 ({:.3f}s): {}", candidate.timestamp, exc)

            # 去掉抽帧失败的候选
            all_candidates = [c for c in all_candidates if c.timestamp in frame_images]

            # 9. 图片哈希去重
            all_candidates = deduplicate_by_image_hash(all_candidates, frame_images)
            task.dedup_count = len(all_candidates)

            # 10. 分钟级限额裁剪
            final_candidates = apply_quota(all_candidates, settings.KEYFRAME_MAX_PER_MINUTE)
            task.final_count = len(final_candidates)

            # 11. 上传最终关键帧到 MinIO 并写入数据库
            for idx, candidate in enumerate(final_candidates):
                frame_path = frame_images.get(candidate.timestamp)
                if not frame_path or not frame_path.exists():
                    continue

                object_key = f"keyframes/{media.id}/frame_{idx:04d}_{int(candidate.timestamp * 1000)}.jpg"
                _upload_to_minio(minio_client, bucket, object_key, frame_path)

                img = cv2.imread(str(frame_path))
                h, w = (img.shape[:2]) if img is not None else (0, 0)

                keyframe = VideoKeyframe(
                    task_id=task.id,
                    media_file_id=media.id,
                    timestamp=candidate.timestamp,
                    minute_bucket=candidate.minute_bucket,
                    source_type=candidate.source_type,
                    scene_score=candidate.scene_score,
                    storage_path=object_key,
                    width=w,
                    height=h,
                    sort_order=idx,
                )
                self.db.add(keyframe)

            task.status = "partial_success" if scene_degraded else "success"
            task.completed_at = datetime.now()
            self.db.commit()

            logger.info(
                "关键帧抽取完成: task=%s, 基础=%d, 场景=%d, 去重后=%d, 最终=%d",
                task_id, task.base_candidate_count, task.scene_candidate_count,
                task.dedup_count, task.final_count,
            )

        except Exception as exc:
            self.db.rollback()
            self._fail_task(task, str(exc))
            logger.error("关键帧抽取失败(task={}): {}", task_id, exc)
        finally:
            self._cleanup_tmp(original_path, thumbnail_path, frames_dir)

    def _fail_task(self, task: VideoKeyframeTask, error: str):
        task.status = "failed"
        task.error_message = error[:2000]
        task.completed_at = datetime.now()
        self.db.commit()

    def _cleanup_tmp(self, *paths):
        """清理临时文件"""
        import shutil
        for p in paths:
            try:
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
                elif p.exists():
                    p.unlink(missing_ok=True)
            except Exception:
                pass
