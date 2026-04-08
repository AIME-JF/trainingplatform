"""
基础时间采样：按固定间隔生成保底帧时间点。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class CandidateFrame:
    """候选帧"""
    timestamp: float
    minute_bucket: int
    source_type: str  # "base" | "scene"
    scene_score: float | None = None


def generate_base_sample_points(duration: float, interval: int = 15) -> List[CandidateFrame]:
    """
    按固定时间间隔生成基础采样时间点。

    参数:
        duration: 视频总时长(秒)
        interval: 采样间隔(秒)，默认15秒
    返回:
        候选帧列表
    """
    if duration <= 0:
        return []

    points: List[CandidateFrame] = []
    t = 0.0
    while t < duration:
        points.append(CandidateFrame(
            timestamp=t,
            minute_bucket=int(t // 60),
            source_type="base",
        ))
        t += interval

    # 确保最后一帧在视频末尾附近
    if points and (duration - points[-1].timestamp) > interval * 0.5:
        points.append(CandidateFrame(
            timestamp=max(0, duration - 0.5),
            minute_bucket=int((duration - 0.5) // 60),
            source_type="base",
        ))

    return points
