"""
系统初始化配置模板。
"""
from copy import deepcopy
from typing import Any, Optional

from app.models.system import ConfigFormat


INITIAL_CONFIG_GROUPS = [
    {
        "group_name": "AI配置",
        "group_key": "ai",
        "group_description": "AI 模型服务与推理参数配置",
        "configs": [
            {
                "config_name": "LLM类型",
                "config_key": "llm_type",
                "config_description": "使用的LLM提供商类型",
                "config_format": ConfigFormat.SELECT,
                "config_value": {
                    "selected": "openai",
                    "options": [
                        {
                            "label": "OpenAI API",
                            "value": "openai",
                        },
                        {
                            "label": "Ollama API",
                            "value": "ollama",
                        },
                    ],
                },
                "is_required": True,
                "is_public": False,
            },
            {
                "config_name": "API标准地址",
                "config_key": "api_base_url",
                "config_description": "根据API提供商填写API标准地址",
                "config_format": ConfigFormat.SHORT_TEXT,
                "config_value": "",
                "is_required": True,
                "is_public": False,
            },
            {
                "config_name": "API密钥",
                "config_key": "api_key",
                "config_description": "根据API提供商填写API访问密钥",
                "config_format": ConfigFormat.PASSWORD,
                "config_value": "",
                "is_required": True,
                "is_public": False,
            },
            {
                "config_name": "默认文本模型名称",
                "config_key": "default_text_model",
                "config_description": "用于文本分析的默认模型",
                "config_format": ConfigFormat.SHORT_TEXT,
                "config_value": "",
                "is_required": True,
                "is_public": False,
            },
            {
                "config_name": "默认多模态模型名称",
                "config_key": "default_vision_model",
                "config_description": "用于图像识别的默认模型",
                "config_format": ConfigFormat.SHORT_TEXT,
                "config_value": "",
                "is_required": True,
                "is_public": False,
            },
            {
                "config_name": "最大Token数",
                "config_key": "max_tokens",
                "config_description": "AI模型单次生成的最大Token数",
                "config_format": ConfigFormat.INTEGER,
                "config_value": None,
                "is_required": False,
                "is_public": False,
            },
            {
                "config_name": "温度参数",
                "config_key": "temperature",
                "config_description": "AI模型的创造性参数(0.0-2.0)",
                "config_format": ConfigFormat.FLOAT,
                "config_value": None,
                "is_required": False,
                "is_public": False,
            },
            {
                "config_name": "请求超时时间",
                "config_key": "timeout",
                "config_description": "API请求超时时间（秒）",
                "config_format": ConfigFormat.INTEGER,
                "config_value": 600,
                "is_required": False,
                "is_public": False,
            },
        ],
    },
]


def list_initial_config_groups() -> list[dict[str, Any]]:
    """返回全部初始化配置组模板。"""
    return deepcopy(INITIAL_CONFIG_GROUPS)


def get_initial_config_group(group_key: str) -> Optional[dict[str, Any]]:
    """按配置组标识获取初始化配置组模板。"""
    for group_definition in INITIAL_CONFIG_GROUPS:
        if str(group_definition.get("group_key")) == str(group_key):
            return deepcopy(group_definition)
    return None
