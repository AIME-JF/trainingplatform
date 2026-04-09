"""
场景切换检测：使用 scenedetect 识别镜头变化并生成补充帧。
"""
from __future__ import annotations

from typing import List

from logger import logger
from .base_sampler import CandidateFrame

# 场景切换点后的偏移(秒)，避免取到转场/黑场/模糊帧
SCENE_OFFSET_SECONDS = 0.5


def detect_scene_changes(video_path: str, duration: float) -> List[CandidateFrame]:
    """
    使用 scenedetect 检测场景切换点并生成候选帧。

    参数:
        video_path: 视频文件本地路径
        duration: 视频总时长(秒)
    返回:
        场景切换候选帧列表
    """
    try:
        from scenedetect import open_video, SceneManager
        from scenedetect.detectors import ContentDetector
    except ImportError:
        logger.warning("scenedetect 未安装，跳过场景检测")
        return []

    try:
        video = open_video(video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=27.0))
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()
    except Exception as exc:
        logger.warning("场景检测失败，降级为仅基础采样: {}", exc)
        return []

    candidates: List[CandidateFrame] = []
    for scene in scene_list:
        start_time = scene[0].get_seconds()
        # 在切换点后偏移取帧，避免转场帧
        t = start_time + SCENE_OFFSET_SECONDS
        if t >= duration:
            t = max(0, start_time)
        candidates.append(CandidateFrame(
            timestamp=t,
            minute_bucket=int(t // 60),
            source_type="scene",
            scene_score=None,
        ))

    logger.info("场景检测完成，发现 {} 个切换点", len(candidates))
    return candidates
