"""
PDF 文档解析器（按页转图片 + OCR）
"""
import fitz
from typing import List
from .base import BaseParser, ParseResult, DocumentType, DocumentMetadata
from .image_parser import ImageParser, ParseImage
from logger import logger


class PDFParser(BaseParser):
    """PDF 解析器"""

    def __init__(self):
        self.image_parser = ImageParser()

    @property
    def supported_extensions(self) -> list:
        return [".pdf"]

    @property
    def parser_name(self) -> str:
        return "PDF解析器"

    def can_parse(self, filename: str, mime_type: str = None) -> bool:
        return filename.lower().endswith(".pdf") or (
            mime_type and "pdf" in mime_type.lower()
        )

    def parse(self, file_data: bytes, filename: str) -> ParseResult:
        try:
            images = self._convert_pages_to_images(file_data)
            image_results = self.image_parser.process_images_parallel(images)
            image_results.sort(key=lambda x: x.index)
            content = "\n".join(r.content for r in image_results)

            metadata = DocumentMetadata(
                parser=self.parser_name,
                document_type=DocumentType.PDF,
                size=len(file_data),
                lines=len(content.splitlines()),
            )
            return ParseResult(content, metadata)
        except Exception as e:
            logger.error("PDF 解析失败: %s, 错误: %s", filename, e)
            return ParseResult("", DocumentMetadata(
                parser=self.parser_name, document_type=DocumentType.PDF,
                size=len(file_data), lines=0,
            ))

    def _convert_pages_to_images(self, file_data: bytes) -> List[ParseImage]:
        doc = fitz.open(stream=file_data, filetype="pdf")
        images = []
        for page in doc:
            pix = page.get_pixmap()
            images.append(ParseImage(id=str(page.number), index=page.number, data=pix.tobytes("png")))
        return images
