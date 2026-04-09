"""
Word 文档解析器
"""
from docx import Document
from io import BytesIO
from typing import List
from .base import BaseParser, ParseResult, DocumentType, DocumentMetadata
from .image_parser import ImageParser, ParseImage, ParseImageResult
from logger import logger


class WordParser(BaseParser):
    """Word 文档解析器"""

    def __init__(self):
        self.image_parser = ImageParser()

    @property
    def supported_extensions(self) -> list:
        return [".docx"]

    @property
    def parser_name(self) -> str:
        return "Word解析器"

    def can_parse(self, filename: str, mime_type: str = None) -> bool:
        return filename.lower().endswith(tuple(self.supported_extensions)) or (
            mime_type and ("word" in mime_type.lower() or "document" in mime_type.lower())
        )

    def parse(self, file_data: bytes, filename: str) -> ParseResult:
        try:
            doc = Document(BytesIO(file_data))
            images = self._extract_images(doc)
            image_results = self.image_parser.process_images_parallel(images)
            doc = self._insert_image_content(doc, image_results)

            file_stream = BytesIO()
            doc.save(file_stream)

            try:
                from markitdown import MarkItDown
                md = MarkItDown()
                content = md.convert(file_stream).text_content
            except ImportError:
                content = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

            metadata = DocumentMetadata(
                parser=self.parser_name,
                document_type=DocumentType.WORD,
                size=len(file_data),
                lines=len(content.splitlines()),
            )
            return ParseResult(content, metadata)
        except Exception as e:
            logger.error("Word 解析失败: %s, 错误: %s", filename, e)
            return ParseResult("", DocumentMetadata(
                parser=self.parser_name, document_type=DocumentType.WORD,
                size=len(file_data), lines=0,
            ))

    def _extract_images(self, doc: Document) -> List[ParseImage]:
        images = []
        for paragraph in doc.paragraphs:
            for run in paragraph.runs:
                drawing_elements = run.element.xpath(".//w:drawing")
                if not drawing_elements:
                    continue
                blip_elements = run.element.xpath(".//a:blip")
                for blip in blip_elements:
                    embed_id = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                    if embed_id and embed_id in doc.part.related_parts:
                        image_data = doc.part.related_parts[embed_id].blob
                        images.append(ParseImage(
                            id=self.image_parser.get_image_hash(image_data),
                            index=len(images),
                            data=image_data,
                        ))
                        break
        return images

    def _insert_image_content(self, doc: Document, image_results: List[ParseImageResult]) -> Document:
        for paragraph in doc.paragraphs:
            for run in paragraph.runs:
                drawing_elements = run.element.xpath(".//w:drawing")
                if not drawing_elements:
                    continue
                blip_elements = run.element.xpath(".//a:blip")
                for blip in blip_elements:
                    embed_id = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                    if embed_id and embed_id in doc.part.related_parts:
                        image_data = doc.part.related_parts[embed_id].blob
                        img_hash = self.image_parser.get_image_hash(image_data)
                        result = next((r for r in image_results if r.id == img_hash), None)
                        if result:
                            run.clear()
                            run.add_text(result.content)
                        break
        return doc
