"""
视频关键帧抽取数据模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.database import Base


class VideoKeyframeTask(Base):
    """视频关键帧抽取任务"""
    __tablename__ = 'video_keyframe_tasks'

    id = Column(Integer, primary_key=True, index=True)
    media_file_id = Column(Integer, ForeignKey('media_files.id'), nullable=False, index=True, comment='原始视频文件ID')
    resource_id = Column(Integer, ForeignKey('resources.id'), nullable=True, index=True, comment='关联资源ID')
    status = Column(String(30), nullable=False, default='pending', comment='pending/running/success/partial_success/failed')
    video_duration = Column(Float, default=0, comment='视频时长(秒)')
    thumbnail_storage_path = Column(String(1000), nullable=True, comment='缩略图视频存储路径')
    base_candidate_count = Column(Integer, default=0, comment='基础采样候选数')
    scene_candidate_count = Column(Integer, default=0, comment='场景补充候选数')
    dedup_count = Column(Integer, default=0, comment='去重后数量')
    final_count = Column(Integer, default=0, comment='最终输出数')
    error_message = Column(Text, nullable=True, comment='错误信息')
    strategy_version = Column(String(20), default='v1', comment='抽帧策略版本')
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VideoKeyframe(Base):
    """视频关键帧"""
    __tablename__ = 'video_keyframes'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('video_keyframe_tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    media_file_id = Column(Integer, ForeignKey('media_files.id'), nullable=False, index=True, comment='原始视频文件ID')
    timestamp = Column(Float, nullable=False, comment='帧时间点(秒)')
    minute_bucket = Column(Integer, nullable=False, comment='所属分钟桶')
    source_type = Column(String(20), nullable=False, comment='base/scene')
    scene_score = Column(Float, nullable=True, comment='场景变化分数')
    storage_path = Column(String(1000), nullable=False, comment='关键帧图片MinIO路径')
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    sort_order = Column(Integer, default=0, comment='排序序号')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
