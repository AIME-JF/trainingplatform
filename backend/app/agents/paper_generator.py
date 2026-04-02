"""
AI 智能试卷生成器 - 根据主题和题型配置生成完整试卷
"""
from __future__ import annotations

import time
from typing import List

from app.schemas import AIPaperGenerationTaskCreateRequest, AITaskPaperDraft, AITaskQuestionDraft

from .base import BaseAIAgent
from .question_generator import AIQuestionGenerator


class AIPaperGenerator(BaseAIAgent):
    """AI 智能试卷生成器"""

    MAX_RETRIES = 3
    RETRY_DELAY = 3  # 秒

    def generate_paper(
        self,
        request: AIPaperGenerationTaskCreateRequest,
        *,
        allow_fallback: bool = True,
    ) -> AITaskPaperDraft:
        """
        根据请求生成完整试卷

        Args:
            request: 包含主题、题型配置等的生成请求

        Returns:
            生成的试卷草稿
        """
        # 使用 AIQuestionGenerator 生成各题型题目
        from app.schemas import AIQuestionTaskCreateRequest

        all_drafts: List[AITaskQuestionDraft] = []
        type_configs = request.type_configs or []

        for config in type_configs:
            if config.count <= 0:
                continue

            # 构建题目生成请求
            question_request = AIQuestionTaskCreateRequest(
                task_name=f"{request.paper_title or request.topic} - {config.type}",
                topic=request.topic,
                question_types=[config.type],
                question_count=config.count,
                knowledge_points=request.knowledge_points or [request.topic] if request.knowledge_points else [request.topic],
                difficulty=config.difficulty or request.difficulty,
                score=config.score,
                source_text=request.source_text,
                requirements=request.requirements,
            )

            # 调用 AI 生成该题型题目，带重试
            generator = AIQuestionGenerator()
            drafts = self._generate_with_retry(
                generator,
                question_request,
                allow_fallback=allow_fallback,
            )
            all_drafts.extend(drafts)

            # 题型之间添加延迟，避免 API 限流
            if len(type_configs) > 1:
                time.sleep(1)

        # 构建试卷
        return self._build_paper_draft(
            title=request.paper_title,
            description=request.description,
            paper_type=request.paper_type,
            duration=request.duration,
            passing_score=request.passing_score,
            questions=all_drafts,
        )

    def _generate_with_retry(
        self,
        generator: AIQuestionGenerator,
        question_request,
        *,
        allow_fallback: bool = True,
    ) -> List[AITaskQuestionDraft]:
        """带重试的题目生成"""
        from logger import logger

        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                return generator.generate_questions(question_request)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "AI 生成题目失败 (尝试 %d/%d): %s",
                    attempt + 1,
                    self.MAX_RETRIES,
                    str(exc),
                )
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))  # 递增延迟

        if not allow_fallback:
            logger.error("AI 生成题目最终失败，不允许降级: %s", last_error)
            raise RuntimeError(f"AI 生成题目最终失败: {last_error}") from last_error

        # 所有重试都失败了，返回模拟数据作为降级方案
        logger.error("AI 生成题目最终失败，使用模拟数据: %s", last_error)
        return self._generate_fallback_questions(question_request)

    def _generate_fallback_questions(self, request) -> List[AITaskQuestionDraft]:
        """当 AI 生成失败时，返回基于模板的模拟题目"""
        from app.schemas import AITaskQuestionDraft

        topic = request.topic or "未知主题"
        drafts = []

        for i in range(request.question_count):
            idx = i + 1
            if request.question_types == ["judge"]:
                drafts.append(AITaskQuestionDraft(
                    temp_id=f"fallback-{idx}",
                    origin="generated",
                    type="judge",
                    content=f"关于「{topic}」，下列说法是否正确？",
                    options=[{"key": "A", "text": "正确"}, {"key": "B", "text": "错误"}],
                    answer="A",
                    explanation=f"本题考察 {topic} 相关知识点。",
                    difficulty=request.difficulty or 3,
                    knowledge_points=request.knowledge_points or [topic],
                    score=request.score or 2,
                ))
            elif request.question_types == ["multi"]:
                drafts.append(AITaskQuestionDraft(
                    temp_id=f"fallback-{idx}",
                    origin="generated",
                    type="multi",
                    content=f"关于「{topic}」，下列说法正确的有哪些？（多选）",
                    options=[
                        {"key": "A", "text": f"{topic}要点一"},
                        {"key": "B", "text": f"{topic}要点二"},
                        {"key": "C", "text": f"{topic}要点三"},
                        {"key": "D", "text": "以上都不对"},
                    ],
                    answer=["A", "B"],
                    explanation=f"本题考察 {topic} 相关知识点。",
                    difficulty=request.difficulty or 3,
                    knowledge_points=request.knowledge_points or [topic],
                    score=request.score or 3,
                ))
            else:
                drafts.append(AITaskQuestionDraft(
                    temp_id=f"fallback-{idx}",
                    origin="generated",
                    type="single",
                    content=f"关于「{topic}」，下列说法哪项最准确？",
                    options=[
                        {"key": "A", "text": f"{topic}正确理解"},
                        {"key": "B", "text": f"{topic}常见误区"},
                        {"key": "C", "text": f"{topic}注意事项"},
                        {"key": "D", "text": "以上都不对"},
                    ],
                    answer="A",
                    explanation=f"本题考察 {topic} 相关知识点。",
                    difficulty=request.difficulty or 3,
                    knowledge_points=request.knowledge_points or [topic],
                    score=request.score or 2,
                ))

        return drafts

    def _build_paper_draft(
        self,
        title: str,
        description: str | None,
        paper_type: str,
        duration: int,
        passing_score: int,
        questions: List[AITaskQuestionDraft],
    ) -> AITaskPaperDraft:
        """构建试卷草稿"""
        total_score = sum(int(q.score or 0) for q in questions)
        return AITaskPaperDraft(
            title=title,
            description=description,
            type=paper_type,
            duration=duration,
            passing_score=passing_score,
            total_score=total_score,
            questions=questions,
        )
