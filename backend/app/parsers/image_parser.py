"""
图像解析器（多模态 AI）
"""
import base64
import hashlib
from pydantic import BaseModel
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base import BaseParser, ParseResult, DocumentType, DocumentMetadata
from logger import logger


class ParseImage(BaseModel):
    id: str
    index: int
    data: bytes

    model_config = {"arbitrary_types_allowed": True}


class ParseImageResult(BaseModel):
    id: str
    index: int
    content: str


class ImageParser(BaseParser):
    """图像解析器，使用多模态 AI"""

    @property
    def supported_extensions(self) -> list:
        return ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif']

    @property
    def parser_name(self) -> str:
        return "图像解析器"

    def can_parse(self, filename: str, mime_type: str = None) -> bool:
        return filename.lower().endswith(tuple(self.supported_extensions)) or (
            mime_type and 'image' in mime_type.lower()
        )

    def parse(self, file_data: bytes, filename: str) -> ParseResult:
        image_base64 = base64.b64encode(file_data).decode('utf-8')
        content = self._call_vision(image_base64)

        metadata = DocumentMetadata(
            parser=self.parser_name,
            document_type=DocumentType.IMAGE,
            size=len(file_data),
            lines=len(content.splitlines()) if content else 0,
        )
        return ParseResult(content or "", metadata)

    def _call_vision(self, image_base64: str) -> str:
        """调用多模态模型解析图片内容"""
        try:
            from app.agents.base import BaseAIAgent
            agent = BaseAIAgent()
            return agent._generate_vision(
                system_prompt="你是一个文档 OCR 助手。请提取图片中的所有文本内容，保持原始排版结构。如果图片中没有文本，请描述图片内容。",
                image_base64=image_base64,
            )
        except Exception as e:
            logger.error("多模态图片解析失败: %s", e)
            return ""

    def parse_image_data(self, image_data: bytes, image_name: str = "embedded_image") -> str:
        result = self.parse(image_data, image_name)
        return result.content

    def get_image_hash(self, image_data: bytes) -> str:
        return hashlib.sha256(image_data).hexdigest()

    def process_images_parallel(self, images: List[ParseImage], max_workers: int = 3) -> List[ParseImageResult]:
        """并行处理图像"""
        if not images:
            return []

        results = []
        max_workers = min(len(images), max_workers)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_image = {}
            for img in images:
                future = executor.submit(self.parse_image_data, img.data)
                future_to_image[future] = img

            for future in as_completed(future_to_image):
                img = future_to_image[future]
                try:
                    content = future.result()
                    if content:
                        results.append(ParseImageResult(id=img.id, index=img.index, content=content))
                except Exception as e:
                    logger.warning("图像处理失败 (index=%d): %s", img.index, e)

        return results
