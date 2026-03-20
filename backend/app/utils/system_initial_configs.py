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
    {
        "group_name": "培训排课默认规则",
        "group_key": "training_schedule",
        "group_description": "培训班排课的系统默认规则模板",
        "configs": [
            {
                "config_name": "单课时分钟数",
                "config_key": "lesson_unit_minutes",
                "config_description": "默认一个课时对应多少分钟",
                "config_format": ConfigFormat.INTEGER,
                "config_value": 40,
                "is_required": True,
                "is_public": False,
            },
            {
                "config_name": "课间休息分钟数",
                "config_key": "break_minutes",
                "config_description": "相邻两个课时之间的默认休息分钟数",
                "config_format": ConfigFormat.INTEGER,
                "config_value": 10,
                "is_required": True,
                "is_public": False,
            },
            {
                "config_name": "单节最多课时",
                "config_key": "max_units_per_session",
                "config_description": "一节课默认最多可连续安排的课时数",
                "config_format": ConfigFormat.INTEGER,
                "config_value": 3,
                "is_required": True,
                "is_public": False,
            },
            {
                "config_name": "单日最多课时",
                "config_key": "daily_max_units",
                "config_description": "培训班单日默认最多安排的课时数",
                "config_format": ConfigFormat.INTEGER,
                "config_value": 6,
                "is_required": True,
                "is_public": False,
            },
            {
                "config_name": "默认排课方式",
                "config_key": "preferred_planning_mode",
                "config_description": "新建培训班和 AI 排课默认采用的排课方式",
                "config_format": ConfigFormat.SELECT,
                "config_value": {
                    "selected": "fill_workdays",
                    "options": [
                        {"label": "排满工作日", "value": "fill_workdays"},
                        {"label": "排满", "value": "fill_all_days"},
                        {"label": "按课时排", "value": "by_hours"},
                    ],
                },
                "is_required": True,
                "is_public": False,
            },
            {
                "config_name": "拆分策略",
                "config_key": "split_strategy",
                "config_description": "默认连续课时拆分策略",
                "config_format": ConfigFormat.SELECT,
                "config_value": {
                    "selected": "balanced",
                    "options": [
                        {"label": "尽量平分", "value": "balanced"},
                    ],
                },
                "is_required": True,
                "is_public": False,
            },
            {
                "config_name": "可排课时间段",
                "config_key": "teaching_windows",
                "config_description": "每行一个时间段，格式如：上午|08:30-12:30",
                "config_format": ConfigFormat.LONG_TEXT,
                "config_value": "上午|08:30-12:30\n下午|14:00-17:30",
                "is_required": True,
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
