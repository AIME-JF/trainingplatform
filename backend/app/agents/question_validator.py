"""
AI 题目质量校验器 — 二次校验 + 自动打标签。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, List, Optional

from .base import BaseAIAgent


@dataclass
class QuestionValidationResult:
    """单道题的校验结果"""

    passed: bool
    quality_score: float  # 0-100
    issues: List[str] = field(default_factory=list)
    suggested_knowledge_points: List[str] = field(default_factory=list)
    suggested_difficulty: Optional[int] = None
    suggested_police_type_hint: Optional[str] = None


@dataclass
class BatchValidationResult:
    """整批题目的校验结果"""

    total: int
    passed_count: int
    results: List[QuestionValidationResult] = field(default_factory=list)
    overall_issues: List[str] = field(default_factory=list)


class AIQuestionValidator(BaseAIAgent):
    """对 AI 生成的题目进行二次质量校验，并自动提取/校准标签。"""

    def validate_and_tag_questions(
        self,
        questions_json: str,
        *,
        expected_type: str,
        expected_difficulty: int,
        expected_knowledge_points: List[str],
        police_type_name: Optional[str] = None,
    ) -> BatchValidationResult:
        prompt = self._build_validation_prompt(
            questions_json=questions_json,
            expected_type=expected_type,
            expected_difficulty=expected_difficulty,
            expected_knowledge_points=expected_knowledge_points,
            police_type_name=police_type_name,
        )
        payload = self._generate_json_payload(
            system_prompt="你是一个专业的警务训练题目质量审核助手。你必须严格输出一个合法 JSON 对象。",
            user_prompt=prompt,
        )
        return self._parse_validation_result(payload)

    def _build_validation_prompt(
        self,
        *,
        questions_json: str,
        expected_type: str,
        expected_difficulty: int,
        expected_knowledge_points: List[str],
        police_type_name: Optional[str],
    ) -> str:
        type_label = {"single": "单选题", "multi": "多选题", "judge": "判断题"}.get(expected_type, expected_type)

        lines = [
            "你是一名资深警务培训教官和题目质量审核专家。",
            "请对以下 AI 生成的考试题目进行质量校验，并为每道题自动提取合适的标签。",
            "",
            f"期望题型：{type_label}",
            f"期望难度：{expected_difficulty}/5",
            f"关联知识点：{json.dumps(expected_knowledge_points, ensure_ascii=False)}",
        ]
        if police_type_name:
            lines.append(f"关联警种：{police_type_name}")
        lines.extend([
            "",
            "请逐题校验以下维度：",
            "1. 题干是否完整、清晰，是否缺少上下文",
            "2. 选项是否合理（单选题是否有且仅有 1 个正确答案，多选题是否至少 2 个正确答案）",
            "3. 答案是否正确且与解析一致",
            "4. 题目是否与警务训练相关",
            "5. 题目是否与期望的知识点相关",
            "6. 难度是否与期望难度匹配（允许 ±1 偏差）",
            "",
            "同时为每道题自动提取以下标签：",
            "- suggested_knowledge_points: 1-3 个知识点名称（优先从关联知识点中选择，如题目涉及新知识点可补充）",
            "- suggested_difficulty: 1-5 的整数（根据题目实际难度评估）",
            "- suggested_police_type_hint: 题目最可能归属的警种名称（如无法判断则为 null）",
            "",
            f"题目 JSON 内容：",
            questions_json,
            "",
            "请输出以下格式的 JSON 对象：",
            '{',
            '  "questions": [',
            '    {',
            '      "index": 题目序号（从 1 开始）,',
            '      "passed": true/false,',
            '      "quality_score": 0-100 的整数,',
            '      "issues": ["问题描述列表，无问题则为空数组"],',
            '      "suggested_knowledge_points": ["知识点1", "知识点2"],',
            '      "suggested_difficulty": 3,',
            '      "suggested_police_type_hint": "警种名称或 null"',
            '    }',
            '  ]',
            '}',
            "",
            "请现在直接输出 JSON 对象。",
        ])
        return "\n".join(lines)

    def _parse_validation_result(self, payload: dict[str, Any]) -> BatchValidationResult:
        questions_payload = payload.get("questions", [])
        if not isinstance(questions_payload, list):
            raise ValueError("校验返回格式非法，缺少 questions 数组")

        results: List[QuestionValidationResult] = []
        passed_count = 0
        overall_issues: List[str] = []

        for item in questions_payload:
            if not isinstance(item, dict):
                continue

            passed = bool(item.get("passed", False))
            quality_score = float(item.get("quality_score", 0))
            issues = item.get("issues", [])
            if isinstance(issues, list):
                issues = [str(i) for i in issues if i]
            else:
                issues = []

            kp = item.get("suggested_knowledge_points", [])
            if isinstance(kp, list):
                kp = [str(k).strip()[:100] for k in kp if str(k).strip()]
            else:
                kp = []

            suggested_difficulty = item.get("suggested_difficulty")
            if suggested_difficulty is not None:
                try:
                    suggested_difficulty = int(suggested_difficulty)
                    if suggested_difficulty < 1 or suggested_difficulty > 5:
                        suggested_difficulty = None
                except (TypeError, ValueError):
                    suggested_difficulty = None

            suggested_police_type_hint = item.get("suggested_police_type_hint")
            if suggested_police_type_hint is not None:
                suggested_police_type_hint = str(suggested_police_type_hint).strip() or None

            result = QuestionValidationResult(
                passed=passed,
                quality_score=quality_score,
                issues=issues,
                suggested_knowledge_points=kp,
                suggested_difficulty=suggested_difficulty,
                suggested_police_type_hint=suggested_police_type_hint,
            )
            results.append(result)
            if passed:
                passed_count += 1
            else:
                overall_issues.extend(issues)

        return BatchValidationResult(
            total=len(results),
            passed_count=passed_count,
            results=results,
            overall_issues=overall_issues,
        )
