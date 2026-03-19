"""
AI 智能出题生成器。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable, List

from openai import OpenAI

from app.schemas import AIQuestionTaskCreateRequest, AITaskQuestionDraft
from app.services.system import get_config_value


@dataclass
class AIRuntimeConfig:
    """AI 运行时配置"""

    provider: str
    base_url: str | None
    api_key: str | None
    model: str
    max_tokens: int | None
    temperature: float | None
    timeout: int | float | None


class AIQuestionGenerator:
    """AI 智能出题生成器"""

    SUPPORTED_TYPES = ("single", "multi", "judge")

    def generate_questions(self, request: AIQuestionTaskCreateRequest) -> List[AITaskQuestionDraft]:
        config = self._load_runtime_config()
        prompt = self._build_generation_prompt(request)
        raw_content = self._call_provider(config, prompt)
        payload = self._parse_json_payload(raw_content)
        return self._build_question_drafts(payload, request)

    def _load_runtime_config(self) -> AIRuntimeConfig:
        provider = str(get_config_value("ai", "llm_type", "openai") or "openai").strip().lower()
        if provider not in {"openai", "ollama"}:
            raise ValueError(f"未支持的 AI 提供商类型: {provider}")

        model = str(get_config_value("ai", "default_text_model", "") or "").strip()
        if not model:
            raise ValueError("请先配置 AI 默认文本模型名称")

        base_url = str(get_config_value("ai", "api_base_url", "") or "").strip() or None
        api_key = str(get_config_value("ai", "api_key", "") or "").strip() or None

        max_tokens = self._to_int(get_config_value("ai", "max_tokens"))
        temperature = self._to_float(get_config_value("ai", "temperature"))
        timeout = self._to_int(get_config_value("ai", "timeout")) or 600

        if provider == "openai" and not api_key:
            raise ValueError("OpenAI 模式下请先配置 API 密钥")

        return AIRuntimeConfig(
            provider=provider,
            base_url=base_url,
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )

    def _build_generation_prompt(self, request: AIQuestionTaskCreateRequest) -> str:
        allowed_types = [str(item).strip() for item in (request.question_types or []) if str(item).strip()] or ["single"]
        knowledge_points = [item for item in (request.knowledge_points or []) if item] or [request.topic]

        type_schema_text = """
题型格式与约束：
1. single（单选题）
   - JSON 结构：
     {
       "type": "single",
       "content": "题干",
       "options": [
         {"key": "A", "text": "选项A"},
         {"key": "B", "text": "选项B"},
         {"key": "C", "text": "选项C"},
         {"key": "D", "text": "选项D"}
       ],
       "answer": "A",
       "explanation": "解析",
       "difficulty": 3,
       "knowledge_point": "知识点",
       "score": __SCORE__
     }
   - 约束：必须且只能有 1 个正确答案；选项数量 4-6 个；answer 必须是单个选项 key。
2. multi（多选题）
   - JSON 结构：
     {
       "type": "multi",
       "content": "题干",
       "options": [
         {"key": "A", "text": "选项A"},
         {"key": "B", "text": "选项B"},
         {"key": "C", "text": "选项C"},
         {"key": "D", "text": "选项D"}
       ],
       "answer": ["A", "C"],
       "explanation": "解析",
       "difficulty": 3,
       "knowledge_point": "知识点",
       "score": __SCORE__
     }
   - 约束：必须至少 2 个正确答案；answer 必须是去重后的选项 key 数组。
3. judge（判断题）
   - JSON 结构：
     {
       "type": "judge",
       "content": "题干",
       "options": [
         {"key": "A", "text": "正确"},
         {"key": "B", "text": "错误"}
       ],
       "answer": "A",
       "explanation": "解析",
       "difficulty": 3,
       "knowledge_point": "知识点",
       "score": __SCORE__
     }
   - 约束：options 固定为 A=正确、B=错误；answer 只能是 A 或 B。
""".strip().replace("__SCORE__", str(request.score))

        prompt_lines = [
            "你是警务训练平台的智能出题引擎。",
            "你必须严格输出一个合法 JSON 对象，不允许输出 Markdown、代码块、额外说明、前后缀文本。",
            "JSON 顶层格式必须是：",
            '{',
            '  "questions": [',
            "    ...题目对象...",
            "  ]",
            "}",
            type_schema_text,
            "全局生成约束：",
            f"- questions 数组长度必须严格等于 {request.question_count}。",
            f"- 本次允许的题型只有：{', '.join(allowed_types)}。禁止输出其他题型。",
            f"- 每题默认分值固定为 {request.score}，score 字段必须填写 {request.score}。",
            f"- 难度 difficulty 必须为 1-5 的整数，整体目标难度为 {request.difficulty}。",
            "- 所有题目必须使用简体中文。",
            "- 所有题目必须唯一，不能出现重复题干或语义重复的题目。",
            "- 题干必须完整、明确，不要出现“根据上文”“根据材料”之类缺少上下文的表达。",
            "- explanation 必须给出简洁且明确的解析。",
            "- knowledge_point 必须优先从提供的知识点列表中选择或贴近生成。",
            "- 不要生成与警务训练无关的内容。",
            "任务上下文：",
            f"- 任务名称：{request.task_name}",
            f"- 出题主题：{request.topic}",
            f"- 知识点列表：{json.dumps(knowledge_points, ensure_ascii=False)}",
            f"- 目标题目数量：{request.question_count}",
            f"- 允许题型：{json.dumps(allowed_types, ensure_ascii=False)}",
            f"- 目标难度：{request.difficulty}",
            f"- 默认分值：{request.score}",
            f"- 警种ID：{request.police_type_id if request.police_type_id is not None else '未指定'}",
        ]

        if request.source_text:
            prompt_lines.extend(
                [
                    "参考文本：",
                    request.source_text.strip(),
                ]
            )

        if request.requirements:
            prompt_lines.append(f"- 补充要求：{request.requirements.strip()}")

        prompt_lines.append("请现在直接输出 JSON 对象。")
        return "\n".join(prompt_lines)

    def _call_provider(self, config: AIRuntimeConfig, prompt: str) -> str:
        if config.provider == "ollama":
            return self._call_ollama(config, prompt)
        return self._call_openai(config, prompt)

    def _call_openai(self, config: AIRuntimeConfig, prompt: str) -> str:
        client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=0,
        )

        request_kwargs: dict[str, Any] = {
            "model": config.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个只输出合法 JSON 的警务训练出题助手。",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }
        if config.max_tokens:
            request_kwargs["max_tokens"] = config.max_tokens
        if config.temperature is not None:
            request_kwargs["temperature"] = config.temperature

        response = client.chat.completions.create(**request_kwargs)
        content = response.choices[0].message.content if response.choices else ""
        if not content:
            raise ValueError("OpenAI 未返回有效内容")
        return str(content).strip()

    def _call_ollama(self, config: AIRuntimeConfig, prompt: str) -> str:
        try:
            from ollama import Client
        except ImportError as exc:
            raise ValueError("未安装 ollama Python 库，请先安装依赖") from exc

        client = Client(
            host=config.base_url,
            timeout=config.timeout,
        )

        options: dict[str, Any] = {}
        if config.temperature is not None:
            options["temperature"] = config.temperature
        if config.max_tokens:
            options["num_predict"] = config.max_tokens

        request_kwargs: dict[str, Any] = {
            "model": config.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个只输出合法 JSON 的警务训练出题助手。",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }
        if options:
            request_kwargs["options"] = options

        response = client.chat(**request_kwargs)
        content = (response.get("message") or {}).get("content", "")
        if not content:
            raise ValueError("Ollama 未返回有效内容")
        return str(content).strip()

    def _parse_json_payload(self, raw_content: str) -> dict[str, Any]:
        json_text = raw_content.strip()
        if json_text.startswith("```"):
            json_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", json_text, flags=re.IGNORECASE | re.DOTALL).strip()

        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", json_text)
            if not match:
                raise ValueError("AI 返回内容不是合法 JSON 对象")
            payload = json.loads(match.group(0))

        if not isinstance(payload, dict):
            raise ValueError("AI 返回的 JSON 顶层必须是对象")
        return payload

    def _build_question_drafts(
        self,
        payload: dict[str, Any],
        request: AIQuestionTaskCreateRequest,
    ) -> List[AITaskQuestionDraft]:
        questions_payload = payload.get("questions")
        if not isinstance(questions_payload, list):
            raise ValueError("AI 返回结果缺少 questions 数组")
        if len(questions_payload) != request.question_count:
            raise ValueError(f"AI 返回题目数量不正确，期望 {request.question_count}，实际 {len(questions_payload)}")

        allowed_types = {
            str(item).strip()
            for item in (request.question_types or [])
            if str(item).strip()
        } or {"single"}

        questions: List[AITaskQuestionDraft] = []
        existed_contents: set[str] = set()
        for index, item in enumerate(questions_payload, start=1):
            draft = self._build_single_question_draft(index, item, request, allowed_types)
            normalized_content = draft.content.strip()
            if normalized_content in existed_contents:
                raise ValueError("AI 生成了重复题目，请重试")
            existed_contents.add(normalized_content)
            questions.append(draft)
        return questions

    def _build_single_question_draft(
        self,
        index: int,
        item: Any,
        request: AIQuestionTaskCreateRequest,
        allowed_types: set[str],
    ) -> AITaskQuestionDraft:
        if not isinstance(item, dict):
            raise ValueError(f"第 {index} 题格式错误，必须是对象")

        question_type = str(item.get("type") or "").strip()
        if question_type not in allowed_types:
            allowed_text = "、".join(sorted(allowed_types))
            raise ValueError(f"第 {index} 题题型非法，仅允许：{allowed_text}")

        content = str(item.get("content") or "").strip()
        if not content:
            raise ValueError(f"第 {index} 题缺少题干")

        difficulty = self._to_int(item.get("difficulty")) or int(request.difficulty)
        if difficulty < 1 or difficulty > 5:
            raise ValueError(f"第 {index} 题难度必须在 1-5 之间")

        knowledge_point = str(item.get("knowledge_point") or item.get("knowledgePoint") or "").strip() or None
        explanation = str(item.get("explanation") or "").strip() or None

        options, answer = self._normalize_question_content(question_type, item.get("options"), item.get("answer"), index)

        return AITaskQuestionDraft(
            temp_id=f"draft-{index}",
            origin="generated",
            type=question_type,
            content=content,
            options=options,
            answer=answer,
            explanation=explanation,
            difficulty=difficulty,
            knowledge_point=knowledge_point,
            police_type_id=request.police_type_id,
            score=int(request.score),
        )

    def _normalize_question_content(
        self,
        question_type: str,
        raw_options: Any,
        raw_answer: Any,
        index: int,
    ) -> tuple[list[dict[str, str]] | None, Any]:
        if question_type == "judge":
            answer = self._normalize_judge_answer(raw_answer)
            return [
                {"key": "A", "text": "正确"},
                {"key": "B", "text": "错误"},
            ], answer

        options = self._normalize_choice_options(raw_options, index)
        option_keys = [item["key"] for item in options]

        if question_type == "single":
            answer = self._normalize_single_answer(raw_answer, option_keys, index)
        else:
            answer = self._normalize_multi_answer(raw_answer, option_keys, index)
        return options, answer

    def _normalize_choice_options(self, raw_options: Any, index: int) -> list[dict[str, str]]:
        if not isinstance(raw_options, list):
            raise ValueError(f"第 {index} 题缺少选项数组")

        normalized_texts: list[str] = []
        for item in raw_options:
            if isinstance(item, dict):
                text = str(item.get("text") or "").strip()
            else:
                text = str(item or "").strip()
            if text:
                normalized_texts.append(text)

        normalized_texts = list(dict.fromkeys(normalized_texts))
        if len(normalized_texts) < 4 or len(normalized_texts) > 6:
            raise ValueError(f"第 {index} 题选项数量必须在 4-6 个之间")

        return [
            {
                "key": chr(65 + option_index),
                "text": text,
            }
            for option_index, text in enumerate(normalized_texts)
        ]

    def _normalize_single_answer(self, raw_answer: Any, option_keys: Iterable[str], index: int) -> str:
        if isinstance(raw_answer, list):
            raw_answer = raw_answer[0] if raw_answer else None

        answer = str(raw_answer or "").strip().upper()
        if answer not in option_keys:
            raise ValueError(f"第 {index} 题单选答案非法")
        return answer

    def _normalize_multi_answer(self, raw_answer: Any, option_keys: Iterable[str], index: int) -> list[str]:
        answers: list[str] = []
        if isinstance(raw_answer, list):
            answers = [str(item).strip().upper() for item in raw_answer if str(item).strip()]
        elif raw_answer is not None:
            answers = [str(item).strip().upper() for item in re.split(r"[,，/、\s]+", str(raw_answer)) if str(item).strip()]

        answers = list(dict.fromkeys(answers))
        if len(answers) < 2:
            raise ValueError(f"第 {index} 题多选答案至少需要 2 个")
        if any(item not in option_keys for item in answers):
            raise ValueError(f"第 {index} 题多选答案非法")
        return answers

    def _normalize_judge_answer(self, raw_answer: Any) -> str:
        answer = str(raw_answer or "").strip().upper()
        if answer in {"A", "正确", "TRUE", "YES", "1"}:
            return "A"
        if answer in {"B", "错误", "FALSE", "NO", "0"}:
            return "B"
        raise ValueError("判断题答案非法")

    def _to_int(self, value: Any) -> int | None:
        if value in (None, ""):
            return None
        return int(value)

    def _to_float(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        return float(value)
