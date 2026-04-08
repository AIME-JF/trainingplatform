"""
候选帧去重：近邻时间去重 + 分钟内感知哈希去重。
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from logger import logger
from .base_sampler import CandidateFrame

# 两帧时间距离小于此值(秒)视为近邻
NEAR_NEIGHBOR_THRESHOLD = 2.0


def _source_priority(source_type: str) -> int:
    """场景切换帧优先于基础采样帧"""
    return 0 if source_type == "scene" else 1


def deduplicate_near_neighbors(candidates: List[CandidateFrame]) -> List[CandidateFrame]:
    """
    近邻时间去重：相邻时间点上的高重复帧只保留优先级更高的。
    """
    if len(candidates) <= 1:
        return candidates

    sorted_candidates = sorted(candidates, key=lambda c: c.timestamp)
    result: List[CandidateFrame] = [sorted_candidates[0]]

    for candidate in sorted_candidates[1:]:
        prev = result[-1]
        if candidate.timestamp - prev.timestamp < NEAR_NEIGHBOR_THRESHOLD:
            # 保留优先级更高的（scene > base）
            if _source_priority(candidate.source_type) < _source_priority(prev.source_type):
                result[-1] = candidate
        else:
            result.append(candidate)

    return result


def deduplicate_by_image_hash(
    candidates: List[CandidateFrame],
    frame_images: Dict[float, Path],
    hash_threshold: int = 8,
) -> List[CandidateFrame]:
    """
    分钟内感知哈希去重：同一分钟内视觉高度相似的帧只保留代表帧。

    参数:
        candidates: 候选帧列表
        frame_images: timestamp -> 图片路径 的映射
        hash_threshold: 哈希差异阈值，小于此值视为相似
    """
    try:
        import imagehash
        from PIL import Image
    except ImportError:
        logger.warning("imagehash/Pillow 未安装，跳过图片哈希去重")
        return candidates

    # 按分钟桶分组
    buckets: Dict[int, List[CandidateFrame]] = {}
    for c in candidates:
        buckets.setdefault(c.minute_bucket, []).append(c)

    result: List[CandidateFrame] = []

    for minute, group in sorted(buckets.items()):
        # 按优先级排序（scene优先）
        group.sort(key=lambda c: (_source_priority(c.source_type), c.timestamp))

        kept: List[tuple] = []  # (candidate, hash)
        for candidate in group:
            img_path = frame_images.get(candidate.timestamp)
            if not img_path or not img_path.exists():
                kept.append((candidate, None))
                continue

            try:
                h = imagehash.phash(Image.open(img_path))
            except Exception:
                kept.append((candidate, None))
                continue

            is_duplicate = False
            for _, existing_hash in kept:
                if existing_hash is not None and abs(h - existing_hash) < hash_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                kept.append((candidate, h))

        result.extend(c for c, _ in kept)

    return result
