"""
基础解析器接口
"""
from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel

class DocumentType(Enum):
    """文档类型枚举"""
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"
    IMAGE = "image"
    TEXT = "text"
    UNKNOWN = "unknown"


class DocumentMetadata(BaseModel):
    """文档元数据"""
    parser: str
    document_type: DocumentType
    size: int
    lines: int

class ParseResult:
    """解析结果封装"""
    def __init__(self, content: str, metadata: DocumentMetadata = None):
        self.content = content
        self.metadata = metadata or DocumentMetadata(parser="", document_type=DocumentType.UNKNOWN, size=0, lines=0)
        self.success = bool(content)


class BaseParser(ABC):
    """解析器基类"""

    @abstractmethod
    def can_parse(self, filename: str, mime_type: str = None) -> bool:
        """判断是否能解析该文件"""
        pass

    @abstractmethod
    def parse(self, file_data: bytes, filename: str) -> ParseResult:
        """解析文件内容"""
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> list:
        """支持的文件扩展名"""
        pass

    @property
    @abstractmethod
    def parser_name(self) -> str:
        """解析器名称"""
        pass
