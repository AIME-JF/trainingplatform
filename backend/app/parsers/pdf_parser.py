"""
PDF parser that converts pages to images and runs OCR.
"""

from typing import List

from .base import BaseParser, DocumentMetadata, DocumentType, ParseResult
from .image_parser import ImageParser, ParseImage
from logger import logger


class PDFParser(BaseParser):
    """Parse PDF files page by page."""

    def __init__(self) -> None:
        self.image_parser = ImageParser()

    @property
    def supported_extensions(self) -> list:
        return [".pdf"]

    @property
    def parser_name(self) -> str:
        return "PDFParser"

    def can_parse(self, filename: str, mime_type: str = None) -> bool:
        normalized_name = str(filename or "").lower()
        return normalized_name.endswith(".pdf") or (
            mime_type and "pdf" in mime_type.lower()
        )

    def parse(self, file_data: bytes, filename: str) -> ParseResult:
        try:
            images = self._convert_pages_to_images(file_data)
            image_results = self.image_parser.process_images_parallel(images)
            image_results.sort(key=lambda item: item.index)
            content = "\n".join(result.content for result in image_results)

            metadata = DocumentMetadata(
                parser=self.parser_name,
                document_type=DocumentType.PDF,
                size=len(file_data),
                lines=len(content.splitlines()),
            )
            return ParseResult(content, metadata)
        except ImportError as exc:
            logger.error("PDF parser dependency missing for %s: %s", filename, exc)
            return self._empty_result(len(file_data))
        except Exception as exc:
            logger.error("PDF parse failed for %s: %s", filename, exc)
            return self._empty_result(len(file_data))

    def _convert_pages_to_images(self, file_data: bytes) -> List[ParseImage]:
        try:
            import fitz
        except ImportError as exc:
            raise ImportError("PyMuPDF is required to parse PDF files") from exc

        document = fitz.open(stream=file_data, filetype="pdf")
        try:
            images: List[ParseImage] = []
            for page in document:
                pixmap = page.get_pixmap()
                images.append(
                    ParseImage(
                        id=str(page.number),
                        index=page.number,
                        data=pixmap.tobytes("png"),
                    )
                )
            return images
        finally:
            document.close()

    def _empty_result(self, file_size: int) -> ParseResult:
        return ParseResult(
            "",
            DocumentMetadata(
                parser=self.parser_name,
                document_type=DocumentType.PDF,
                size=file_size,
                lines=0,
            ),
        )
