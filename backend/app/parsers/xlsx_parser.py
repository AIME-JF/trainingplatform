"""
Excel文件解析器
"""
from io import BytesIO
from .base import BaseParser, ParseResult, DocumentType, DocumentMetadata
from logger import logger


class XlsxParser(BaseParser):
    """Excel文件解析器"""

    @property
    def supported_extensions(self) -> list:
        return [".xlsx"]

    @property
    def parser_name(self) -> str:
        return "Excel解析器"

    def can_parse(self, filename: str, mime_type: str = None) -> bool:
        """判断是否能解析Excel文件"""
        return filename.lower().endswith(tuple(self.supported_extensions)) or (
            mime_type and "spreadsheet" in mime_type.lower()
        )

    def parse(self, file_data: bytes, filename: str) -> ParseResult:
        """解析Excel内容"""
        try:
            from markitdown import MarkItDown
            md = MarkItDown()
            content = md.convert(BytesIO(file_data)).text_content
        except ImportError:
            content = file_data.decode("utf-8", errors="replace")
        except Exception as e:
            logger.error("Excel解析失败: %s, 错误: %s", filename, e)
            return ParseResult("", DocumentMetadata(
                parser=self.parser_name,
                document_type=DocumentType.EXCEL,
                size=len(file_data),
                lines=0,
            ))

        metadata = DocumentMetadata(
            parser=self.parser_name,
            document_type=DocumentType.EXCEL,
            size=len(file_data),
            lines=len(content.splitlines()),
        )
        return ParseResult(content, metadata)
