"""
AI 内容审核 Agent

根据审核规则对文本、图片、视频关键帧进行内容审核。
返回结构化的审核结果（通过/拒绝 + 原因）。
"""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.agents.base import BaseAIAgent
from config import settings
from logger import logger


@dataclass
class ReviewResult:
    """单项审核结果"""
    passed: bool
    reason: str
    item_type: str  # "text_chunk" / "image" / "keyframe"
    item_index: int = 0


@dataclass
class AggregatedReviewResult:
    """汇总审核结果"""
    passed: bool
    summary: str
    details: List[ReviewResult]
    error: Optional[str] = None


REVIEW_JSON_INSTRUCTION = '''
请以 JSON 格式返回审核结果：
{"passed": true/false, "reason": "审核通过" 或 "具体的违规描述"}
只返回 JSON，不要其他内容。
'''


class ContentReviewAgent(BaseAIAgent):
    """AI 内容审核 Agent"""

    def review_text(self, text: str, review_rules: str, chunk_size: int = 0) -> AggregatedReviewResult:
        """
        审核文本内容。超长文本会分段审核。

        参数:
            text: 待审核文本
            review_rules: 审核规则（管理员配置）
            chunk_size: 分段大小（0 表示使用配置项）
        """
        if not text or not text.strip():
            return AggregatedReviewResult(passed=True, summary="空内容，自动通过", details=[])

        chunk_size = chunk_size or settings.AI_REVIEW_TEXT_CHUNK_SIZE
        chunks = self._split_text(text, chunk_size)
        results: List[ReviewResult] = []

        for i, chunk in enumerate(chunks):
            try:
                result = self._review_single_text(chunk, review_rules, i)
                results.append(result)
                if not result.passed:
                    # 文本审核：发现违规立即停止后续分段
                    break
            except Exception as e:
                logger.error("文本审核第 %d 段失败: %s", i, e)
                return AggregatedReviewResult(
                    passed=False, summary="", details=results,
                    error=f"文本审核第 {i + 1} 段失败: {e}",
                )

        passed = all(r.passed for r in results)
        failed_reasons = [r.reason for r in results if not r.passed]
        summary = "审核通过" if passed else "；".join(failed_reasons)
        return AggregatedReviewResult(passed=passed, summary=summary, details=results)

    def review_image(self, image_data: bytes, review_rules: str) -> ReviewResult:
        """审核单张图片"""
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        system_prompt = f"你是一个内容审核专家。请根据以下审核规则检查图片内容。\n\n审核规则：\n{review_rules}\n\n{REVIEW_JSON_INSTRUCTION}"

        try:
            response = self._generate_vision(
                system_prompt=system_prompt,
                image_base64=image_base64,
                user_prompt="请审核这张图片。",
            )
            result = self._parse_review_response(response)
            return ReviewResult(passed=result["passed"], reason=result["reason"], item_type="image")
        except Exception as e:
            logger.error("图片审核失败: %s", e)
            raise

    def review_images_parallel(
        self,
        images: List[bytes],
        review_rules: str,
        max_parallel: int = 0,
    ) -> AggregatedReviewResult:
        """
        并行审核多张图片（用于视频关键帧）。
        任意一张不通过则整体不通过。
        """
        if not images:
            return AggregatedReviewResult(passed=True, summary="无图片，自动通过", details=[])

        max_parallel = max_parallel or settings.AI_REVIEW_MAX_PARALLEL
        max_workers = min(len(images), max_parallel)
        results: List[ReviewResult] = []
        error_msg = None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {}
            for i, img_data in enumerate(images):
                future = executor.submit(self.review_image, img_data, review_rules)
                future_to_idx[future] = i

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    result = future.result()
                    result.item_index = idx
                    results.append(result)
                except Exception as e:
                    error_msg = f"第 {idx + 1} 张图片审核失败: {e}"
                    logger.error(error_msg)
                    break

        if error_msg:
            return AggregatedReviewResult(
                passed=False, summary="", details=results, error=error_msg,
            )

        results.sort(key=lambda r: r.item_index)
        passed = all(r.passed for r in results)
        failed = [f"第{r.item_index + 1}张: {r.reason}" for r in results if not r.passed]
        summary = "审核通过" if passed else "；".join(failed)
        return AggregatedReviewResult(passed=passed, summary=summary, details=results)

    def _review_single_text(self, text: str, review_rules: str, chunk_index: int) -> ReviewResult:
        """审核单段文本"""
        system_prompt = f"你是一个内容审核专家。请根据以下审核规则检查文本内容。\n\n审核规则：\n{review_rules}\n\n{REVIEW_JSON_INSTRUCTION}"
        user_prompt = f"请审核以下文本内容：\n\n{text}"

        response = self._generate_text(system_prompt=system_prompt, user_prompt=user_prompt)
        result = self._parse_review_response(response)
        return ReviewResult(
            passed=result["passed"],
            reason=result["reason"],
            item_type="text_chunk",
            item_index=chunk_index,
        )

    def _parse_review_response(self, response: str) -> dict:
        """解析 AI 返回的审核 JSON"""
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            data = json.loads(text)
            return {
                "passed": bool(data.get("passed", False)),
                "reason": str(data.get("reason", "")),
            }
        except (json.JSONDecodeError, ValueError):
            # 无法解析，视为不确定，降级
            logger.warning("AI 审核返回非 JSON: %s", text[:200])
            raise ValueError(f"AI 审核返回格式异常: {text[:200]}")

    def _split_text(self, text: str, chunk_size: int) -> List[str]:
        """将文本按大小分段"""
        if len(text) <= chunk_size:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            # 尝试在段落或句子边界断开
            if end < len(text):
                for sep in ["\n\n", "\n", "。", ".", "！", "？"]:
                    pos = text.rfind(sep, start + chunk_size // 2, end)
                    if pos > start:
                        end = pos + len(sep)
                        break
            chunks.append(text[start:end])
            start = end
        return chunks
