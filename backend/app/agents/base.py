"""智能体基础能力"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import httpx
from openai import OpenAI

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


class BaseAIAgent:
    """公共 AI provider 调用能力"""

    def _generate_text(self, *, system_prompt: str, user_prompt: str) -> str:
        config = self._load_runtime_config()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self._call_provider(config, messages)

    def _generate_json_payload(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        raw_content = self._generate_text(system_prompt=system_prompt, user_prompt=user_prompt)
        return self._parse_json_payload(raw_content)

    def _call_provider(self, config: AIRuntimeConfig, messages: list[dict[str, str]]) -> str:
        if config.provider == "ollama":
            return self._call_ollama(config, messages)
        return self._call_openai(config, messages)

    def _call_openai(self, config: AIRuntimeConfig, messages: list[dict[str, str]]) -> str:
        from logger import logger as _base_logger
        _base_logger.debug(f"[BaseAIAgent] timeout=%s, max_tokens=%s, temperature=%s", config.timeout, config.max_tokens, config.temperature)
        # 使用 httpx.Timeout 显式设置所有超时类别，避免个别操作超时
        httpx_timeout = httpx.Timeout(config.timeout or 120, connect=30)
        client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=httpx_timeout,
            max_retries=0,
        )

        request_kwargs: dict[str, Any] = {
            "model": config.model,
            "messages": messages,
        }
        if config.max_tokens:
            request_kwargs["max_tokens"] = config.max_tokens
        if config.temperature is not None:
            request_kwargs["temperature"] = config.temperature

        _base_logger.debug(f"[BaseAIAgent] calling {config.base_url} model={config.model} messages_count={len(messages)}")
        response = client.chat.completions.create(**request_kwargs)
        choices_count = len(response.choices) if response.choices else 0
        content = response.choices[0].message.content if response.choices else ""
        finish_reason = response.choices[0].finish_reason if response.choices else "N/A"
        _base_logger.debug(f"[BaseAIAgent] response choices={choices_count} finish_reason={finish_reason} content_len={len(content or '')} content_preview={str(content or '')[:200]}")
        if not content:
            raise ValueError("OpenAI 未返回有效内容")
        return str(content).strip()

    def _call_ollama(self, config: AIRuntimeConfig, messages: list[dict[str, str]]) -> str:
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
            "messages": messages,
        }
        if options:
            request_kwargs["options"] = options

        response = client.chat(**request_kwargs)
        content = (response.get("message") or {}).get("content", "")
        if not content:
            raise ValueError("Ollama 未返回有效内容")
        return str(content).strip()

    @staticmethod
    def _parse_json_payload(raw_content: str) -> dict[str, Any]:
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

    @staticmethod
    def _to_int(value: Any) -> int | None:
        if value in (None, ""):
            return None
        return int(value)

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value in (None, ""):
            return None
        return float(value)

    def _load_runtime_config(self) -> AIRuntimeConfig:
        from logger import logger as _base_logger
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
        timeout_raw = get_config_value("ai", "timeout")
        timeout = self._to_int(timeout_raw) if timeout_raw is not None else None
        _base_logger.debug(f"[BaseAIAgent] config loaded: timeout_raw=%r, timeout=%r, max_tokens=%r", timeout_raw, timeout, max_tokens)
        if timeout is None or timeout <= 0:
            timeout = 600

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
