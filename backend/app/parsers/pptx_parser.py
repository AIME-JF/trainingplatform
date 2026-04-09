"""
PowerPoint 文档解析器
"""
from io import BytesIO
from typing import List
from .base import BaseParser, ParseResult, DocumentType, DocumentMetadata
from .image_parser import ImageParser, ParseImage
from logger import logger


class PptxParser(BaseParser):
    """PowerPoint 解析器"""

    def __init__(self):
        self.image_parser = ImageParser()

    @property
    def supported_extensions(self) -> list:
        return [".pptx"]

    @property
    def parser_name(self) -> str:
        return "PPT解析器"

    def can_parse(self, filename: str, mime_type: str = None) -> bool:
        return filename.lower().endswith(".pptx") or (
            mime_type and "presentation" in mime_type.lower()
        )

    def parse(self, file_data: bytes, filename: str) -> ParseResult:
        try:
            from pptx import Presentation
            prs = Presentation(BytesIO(file_data))

            parts = []
            images: List[ParseImage] = []

            for slide_idx, slide in enumerate(prs.slides):
                slide_texts = []
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            text = paragraph.text.strip()
                            if text:
                                slide_texts.append(text)
                    if shape.shape_type == 13:  # Picture
                        try:
                            image_data = shape.image.blob
                            images.append(ParseImage(
                                id=self.image_parser.get_image_hash(image_data),
                                index=len(images),
                                data=image_data,
                            ))
                        except Exception:
                            pass

                if slide_texts:
                    parts.append(f"--- 幻灯片 {slide_idx + 1} ---\n" + "\n".join(slide_texts))

            # 处理嵌入图片
            if images:
                image_results = self.image_parser.process_images_parallel(images)
                for r in sorted(image_results, key=lambda x: x.index):
                    if r.content:
                        parts.append(f"[幻灯片图片内容] {r.content}")

            content = "\n\n".join(parts)
            metadata = DocumentMetadata(
                parser=self.parser_name,
                document_type=DocumentType.POWERPOINT,
                size=len(file_data),
                lines=len(content.splitlines()),
            )
            return ParseResult(content, metadata)
        except Exception as e:
            logger.error("PPT 解析失败: %s, 错误: %s", filename, e)
            return ParseResult("", DocumentMetadata(
                parser=self.parser_name, document_type=DocumentType.POWERPOINT,
                size=len(file_data), lines=0,
            ))
