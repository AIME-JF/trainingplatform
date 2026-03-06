"""
AI功能服务
"""
import json
from typing import Optional
from sqlalchemy.orm import Session

from config import settings
from app.schemas.ai import (
    AIGenerateQuestionsRequest, AIGenerateQuestionsResponse,
    AIGenerateLessonPlanRequest, AIGenerateLessonPlanResponse
)
from logger import logger


class AIService:
    """AI功能服务"""

    def __init__(self, db: Session):
        self.db = db

    def generate_questions(self, data: AIGenerateQuestionsRequest) -> AIGenerateQuestionsResponse:
        """AI智能组卷"""
        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL
            )

            types_str = "、".join(data.types) if data.types else "单选题、多选题、判断题"
            prompt = f"""你是一个警务培训考试出题专家。请根据以下要求生成考试题目：
主题：{data.topic}
数量：{data.count}题
难度：{data.difficulty}/5
题型：{types_str}

请按以下JSON格式返回，不要包含其他文字：
{{
  "questions": [
    {{
      "type": "single/multi/judge",
      "content": "题干",
      "options": [{{"key": "A", "text": "选项A"}}, {{"key": "B", "text": "选项B"}}, {{"key": "C", "text": "选项C"}}, {{"key": "D", "text": "选项D"}}],
      "answer": "A",
      "explanation": "解析",
      "difficulty": 3,
      "knowledge_point": "知识点",
      "score": 5
    }}
  ]
}}"""

            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4000
            )

            content = response.choices[0].message.content
            # 尝试解析JSON
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]

            result = json.loads(content)
            questions = result.get("questions", [])

            return AIGenerateQuestionsResponse(
                questions=questions, total=len(questions)
            )

        except ImportError:
            logger.warning("openai包未安装，返回空结果")
            return AIGenerateQuestionsResponse(questions=[], total=0)
        except Exception as e:
            logger.error(f"AI组卷失败: {e}")
            return AIGenerateQuestionsResponse(questions=[], total=0)

    def generate_lesson_plan(self, data: AIGenerateLessonPlanRequest) -> AIGenerateLessonPlanResponse:
        """AI教案生成"""
        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL
            )

            objectives_str = "、".join(data.objectives) if data.objectives else "掌握基本知识和技能"
            prompt = f"""你是一个警务培训教案设计专家。请根据以下要求生成教案：
标题：{data.title}
科目：{data.subject}
课时：{data.duration}分钟
教学目标：{objectives_str}
学员等级：{data.level or '中级'}

请按以下JSON格式返回，不要包含其他文字：
{{
  "title": "教案标题",
  "content": "完整教案内容（使用Markdown格式）",
  "outline": [
    {{"title": "环节标题", "duration": 10, "content": "环节内容描述"}}
  ]
}}"""

            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4000
            )

            content = response.choices[0].message.content
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]

            result = json.loads(content)

            return AIGenerateLessonPlanResponse(
                title=result.get("title", data.title),
                content=result.get("content", ""),
                outline=result.get("outline", [])
            )

        except ImportError:
            logger.warning("openai包未安装，返回空结果")
            return AIGenerateLessonPlanResponse(title=data.title, content="", outline=[])
        except Exception as e:
            logger.error(f"AI教案生成失败: {e}")
            return AIGenerateLessonPlanResponse(title=data.title, content="", outline=[])
