"""
解析器工厂
"""
from typing import Optional, List
from .base import BaseParser, ParseResult
from .pdf_parser import PDFParser
from .word_parser import WordParser
from .pptx_parser import PptxParser
from .image_parser import ImageParser
from .text_parser import TextParser
from .xlsx_parser import XlsxParser
from logger import logger


class ParserFactory:
    """解析器工厂"""

    def __init__(self):
        self._parsers: List[BaseParser] = [
            PDFParser(),
            WordParser(),
            PptxParser(),
            ImageParser(),
            TextParser(),
            XlsxParser(),
        ]

    def get_parser(self, filename: str, mime_type: str = None) -> Optional[BaseParser]:
        for parser in self._parsers:
            if parser.can_parse(filename, mime_type):
                return parser
        return None

    def parse_file(self, file_data: bytes, filename: str, mime_type: str = None) -> ParseResult:
        parser = self.get_parser(filename, mime_type)
        if not parser:
            logger.warning("不支持的文件类型: %s", filename)
            return ParseResult("")
        try:
            return parser.parse(file_data, filename)
        except Exception as e:
            logger.error("文件解析异常: %s, 错误: %s", filename, e)
            return ParseResult("")
