"""
文本文件解析器
"""
from io import BytesIO
from .base import BaseParser, ParseResult, DocumentType, DocumentMetadata
from logger import logger


class TextParser(BaseParser):
    """文本文件解析器"""

    @property
    def supported_extensions(self) -> list:
        return [".txt", ".md", ".csv", ".log", ".json", ".xml", ".html", ".htm"]

    @property
    def parser_name(self) -> str:
        return "文本解析器"

    def can_parse(self, filename: str, mime_type: str = None) -> bool:
        return filename.lower().endswith(tuple(self.supported_extensions)) or (
            mime_type and "text" in mime_type.lower()
        )

    def parse(self, file_data: bytes, filename: str) -> ParseResult:
        try:
            from markitdown import MarkItDown
            md = MarkItDown()
            content = md.convert(BytesIO(file_data)).text_content
        except ImportError:
            content = file_data.decode("utf-8", errors="replace")
        except Exception as e:
            logger.warning("MarkItDown 解析失败，降级为直接解码: %s", e)
            content = file_data.decode("utf-8", errors="replace")

        metadata = DocumentMetadata(
            parser=self.parser_name,
            document_type=DocumentType.TEXT,
            size=len(file_data),
            lines=len(content.splitlines()),
        )
        return ParseResult(content, metadata)
