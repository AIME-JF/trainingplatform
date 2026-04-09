"""
知识问答请求模型
"""
from typing import Any, List

from pydantic import BaseModel, Field, field_validator


def _normalize_id_list(value: Any) -> List[int]:
    normalized: List[int] = []
    seen = set()
    for raw_item in value or []:
        try:
            item = int(raw_item)
        except (TypeError, ValueError) as exc:
            raise ValueError("知识点 ID 列表必须全部为整数") from exc
        if item <= 0 or item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


class KnowledgeChatSessionCreateRequest(BaseModel):
    """创建知识问答会话请求"""

    knowledge_item_ids: List[int] = Field(default_factory=list, description="已选择的知识点 ID 列表")
    mode: str = Field("qa", description="对话模式")

    @field_validator("knowledge_item_ids", mode="before")
    @classmethod
    def validate_knowledge_item_ids(cls, value: Any) -> List[int]:
        return _normalize_id_list(value)

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        normalized = str(value or "qa").strip().lower() or "qa"
        if normalized not in {"qa", "case"}:
            raise ValueError("知识问答模式仅支持 qa 或 case")
        return normalized
