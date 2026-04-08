"""
分钟级限额裁剪：确保每分钟输出不超过配置上限。
"""
from __future__ import annotations

from typing import Dict, List

from .base_sampler import CandidateFrame


def _source_priority(source_type: str) -> int:
    return 0 if source_type == "scene" else 1


def apply_quota(candidates: List[CandidateFrame], max_per_minute: int = 6) -> List[CandidateFrame]:
    """
    按自然分钟分桶，每桶按优先级排序后裁剪到上限。

    优先级顺序:
    1. 场景切换帧
    2. 基础采样帧
    3. 同优先级内按时间均匀分布
    """
    buckets: Dict[int, List[CandidateFrame]] = {}
    for c in candidates:
        buckets.setdefault(c.minute_bucket, []).append(c)

    result: List[CandidateFrame] = []

    for minute in sorted(buckets.keys()):
        group = buckets[minute]
        # 按优先级排序：scene优先，然后按时间
        group.sort(key=lambda c: (_source_priority(c.source_type), c.timestamp))

        if len(group) <= max_per_minute:
            result.extend(group)
        else:
            # 超过限额时，按优先级取前 max_per_minute 个
            result.extend(group[:max_per_minute])

    # 最终按时间排序
    result.sort(key=lambda c: c.timestamp)
    return result
