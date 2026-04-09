"""
AI 内容审核 Celery 任务
"""
from __future__ import annotations

from typing import Optional, List

from minio import Minio
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import MediaFile, Resource, ResourceMediaLink
from app.models.review import ReviewWorkflow, ReviewPolicyStage, ReviewPolicy
from app.models.video_keyframe import VideoKeyframeTask, VideoKeyframe
from app.agents.content_review_agent import ContentReviewAgent
from app.parsers import ParserFactory
from app.services.review import ReviewService
from celery_app import celery_app
from config import settings
from logger import logger


AI_REVIEW_TASK_NAME = "app.tasks.ai_review.run_ai_review"


def _get_minio_client() -> Minio:
    return Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


def _download_from_minio(client: Minio, object_key: str) -> bytes:
    """从 MinIO 下载文件内容"""
    response = client.get_object(settings.MINIO_BUCKET, object_key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def _get_review_rules(db: Session) -> str:
    """从系统配置读取审核规则"""
    from app.utils.system_initial_configs import get_initial_config_group
    from app.services.system import get_config_value
    rules = get_config_value("ai_review", "review_rules", "")
    if not rules:
        rules = "检查内容是否包含：1.暴力血腥内容 2.色情低俗内容 3.政治敏感内容 4.违法犯罪内容 5.其他不当内容"
    return rules


@celery_app.task(bind=True, name=AI_REVIEW_TASK_NAME, max_retries=1)
def run_ai_review(
    self,
    workflow_id: int,
    task_id: int,
    business_type: str,
    business_id: int,
    stage_order: int,
) -> None:
    """执行 AI 审核任务"""
    db = SessionLocal()
    try:
        # 获取阶段配置
        workflow = db.query(ReviewWorkflow).filter(ReviewWorkflow.id == workflow_id).first()
        if not workflow:
            logger.warning("AI 审核：工作流不存在 %s", workflow_id)
            return

        policy = db.query(ReviewPolicy).filter(ReviewPolicy.id == workflow.policy_id).first()
        if not policy:
            logger.warning("AI 审核：策略不存在")
            return

        stage_cfg = next((s for s in (policy.stages or []) if s.stage_order == stage_order), None)
        if not stage_cfg:
            logger.warning("AI 审核：阶段配置不存在")
            return

        review_rules = _get_review_rules(db)
        review_service = ReviewService(db)

        if business_type == 'resource':
            result = _review_resource(db, business_id, review_rules)
        else:
            # 其他业务类型暂不支持 AI 审核，降级
            review_service.complete_ai_review(
                workflow_id, task_id,
                passed=False, summary=f"不支持的业务类型: {business_type}",
                should_fallback=True,
            )
            return

        if result.get("error"):
            # AI 执行失败 → 降级到人工
            review_service.complete_ai_review(
                workflow_id, task_id,
                passed=False, summary=result["error"],
                should_fallback=True,
            )
            return

        passed = result["passed"]
        summary = result["summary"]

        if passed:
            review_service.complete_ai_review(
                workflow_id, task_id,
                passed=True, summary=summary,
                should_fallback=False,
            )
        else:
            # AI 判定不通过
            ai_reject_mode = stage_cfg.ai_reject_mode or 'fallback'
            if ai_reject_mode == 'direct':
                review_service.complete_ai_review(
                    workflow_id, task_id,
                    passed=False, summary=summary,
                    should_fallback=False,
                )
            else:
                # fallback 模式：降级到人工
                review_service.complete_ai_review(
                    workflow_id, task_id,
                    passed=False, summary=f"AI 判定不通过，降级人工确认: {summary}",
                    should_fallback=True,
                )

    except Exception as exc:
        db.rollback()
        logger.error("AI 审核任务失败(workflow=%s): %s", workflow_id, exc)

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=5)

        # 重试耗尽 → 降级到人工
        try:
            review_service = ReviewService(db)
            review_service.complete_ai_review(
                workflow_id, task_id,
                passed=False, summary=f"AI 审核任务执行失败: {exc}",
                should_fallback=True,
            )
        except Exception as fallback_exc:
            logger.error("AI 审核降级也失败: %s", fallback_exc)
    finally:
        db.close()


def _review_resource(db: Session, resource_id: int, review_rules: str) -> dict:
    """审核资源的所有关联文件"""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        return {"passed": False, "summary": "", "error": "资源不存在"}

    media_links = db.query(ResourceMediaLink).filter(
        ResourceMediaLink.resource_id == resource_id,
    ).all()
    if not media_links:
        return {"passed": True, "summary": "无关联文件，自动通过", "error": None}

    minio_client = _get_minio_client()
    agent = ContentReviewAgent()
    parser_factory = ParserFactory()
    all_summaries = []
    overall_passed = True

    for link in media_links:
        media = db.query(MediaFile).filter(MediaFile.id == link.media_file_id).first()
        if not media:
            continue

        mime = (media.mime_type or "").lower()

        try:
            if mime.startswith("video/"):
                result = _review_video_file(db, media, agent, minio_client, review_rules)
            elif mime.startswith("image/"):
                result = _review_image_file(media, agent, minio_client, review_rules)
            else:
                result = _review_document_file(media, agent, parser_factory, minio_client, review_rules)
        except Exception as exc:
            return {"passed": False, "summary": "", "error": f"文件 {media.filename} 审核异常: {exc}"}

        if result.get("error"):
            return {"passed": False, "summary": "", "error": result["error"]}

        all_summaries.append(f"[{media.filename}] {result['summary']}")
        if not result["passed"]:
            overall_passed = False
            break  # 一个文件不通过就停止

    summary = "；".join(all_summaries) if all_summaries else "审核通过"
    return {"passed": overall_passed, "summary": summary, "error": None}


def _review_video_file(db: Session, media: MediaFile, agent: ContentReviewAgent, minio_client: Minio, review_rules: str) -> dict:
    """审核视频文件：使用关键帧"""
    # 查询已提取的关键帧
    keyframes = db.query(VideoKeyframe).filter(
        VideoKeyframe.media_file_id == media.id,
    ).order_by(VideoKeyframe.sort_order).all()

    if not keyframes:
        return {"passed": False, "summary": "", "error": f"视频 {media.filename} 无关键帧数据，无法审核"}

    # 下载关键帧图片
    images: List[bytes] = []
    for kf in keyframes:
        try:
            img_data = _download_from_minio(minio_client, kf.storage_path)
            images.append(img_data)
        except Exception as exc:
            logger.warning("下载关键帧失败 %s: %s", kf.storage_path, exc)

    if not images:
        return {"passed": False, "summary": "", "error": f"视频 {media.filename} 关键帧下载全部失败"}

    result = agent.review_images_parallel(images, review_rules)
    if result.error:
        return {"passed": False, "summary": "", "error": result.error}
    return {"passed": result.passed, "summary": result.summary, "error": None}


def _review_image_file(media: MediaFile, agent: ContentReviewAgent, minio_client: Minio, review_rules: str) -> dict:
    """审核图片文件"""
    try:
        img_data = _download_from_minio(minio_client, media.storage_path)
        result = agent.review_image(img_data, review_rules)
        return {"passed": result.passed, "summary": result.reason, "error": None}
    except Exception as exc:
        return {"passed": False, "summary": "", "error": f"图片审核失败: {exc}"}


def _review_document_file(
    media: MediaFile, agent: ContentReviewAgent,
    parser_factory: ParserFactory, minio_client: Minio,
    review_rules: str,
) -> dict:
    """审核文档文件：解析为文本后分段审核"""
    try:
        file_data = _download_from_minio(minio_client, media.storage_path)
    except Exception as exc:
        return {"passed": False, "summary": "", "error": f"下载文件失败: {exc}"}

    # 尝试解析
    parse_result = parser_factory.parse_file(file_data, media.filename, media.mime_type)
    if not parse_result.success or not parse_result.content.strip():
        return {"passed": False, "summary": "", "error": f"文件 {media.filename} 无法解析，格式不支持"}

    result = agent.review_text(parse_result.content, review_rules)
    if result.error:
        return {"passed": False, "summary": "", "error": result.error}
    return {"passed": result.passed, "summary": result.summary, "error": None}


def schedule_ai_review_task(
    workflow_id: int,
    task_id: int,
    business_type: str,
    business_id: int,
    stage_order: int,
):
    """调度 AI 审核任务"""
    run_ai_review.apply_async(
        args=[workflow_id, task_id, business_type, business_id, stage_order],
        task_id=f"ai-review-{workflow_id}-{task_id}",
    )
    logger.info("AI 审核任务已调度: workflow=%s, task=%s", workflow_id, task_id)
