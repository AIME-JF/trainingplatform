"""
Parser factory with lazy loading for optional parser dependencies.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .base import BaseParser, ParseResult
from logger import logger


@dataclass(frozen=True)
class ParserRegistration:
    module_path: str
    class_name: str
    supported_extensions: tuple[str, ...]


class ParserFactory:
    """Load parsers lazily so optional dependencies do not break app startup."""

    _REGISTRATIONS: tuple[ParserRegistration, ...] = (
        ParserRegistration("app.parsers.pdf_parser", "PDFParser", (".pdf",)),
        ParserRegistration("app.parsers.word_parser", "WordParser", (".docx",)),
        ParserRegistration("app.parsers.pptx_parser", "PptxParser", (".pptx",)),
        ParserRegistration(
            "app.parsers.image_parser",
            "ImageParser",
            (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".gif"),
        ),
        ParserRegistration(
            "app.parsers.text_parser",
            "TextParser",
            (".txt", ".md", ".csv", ".log", ".json", ".xml", ".html", ".htm"),
        ),
        ParserRegistration("app.parsers.xlsx_parser", "XlsxParser", (".xlsx",)),
    )

    def __init__(self) -> None:
        self._parser_cache: Dict[str, BaseParser] = {}
        self._failed_parser_keys: set[str] = set()

    def list_supported_extensions(self) -> list[str]:
        extensions: list[str] = []
        for registration in self._REGISTRATIONS:
            for extension in registration.supported_extensions:
                normalized = extension.strip().lower()
                if normalized and normalized not in extensions:
                    extensions.append(normalized)
        return extensions

    def get_parser(self, filename: str, mime_type: str = None) -> Optional[BaseParser]:
        normalized_name = str(filename or "").strip().lower()
        suffix = Path(normalized_name).suffix.lower()

        if suffix:
            for registration in self._REGISTRATIONS:
                if suffix in registration.supported_extensions:
                    parser = self._load_parser(registration)
                    if parser is not None:
                        return parser

        for registration in self._REGISTRATIONS:
            parser = self._load_parser(registration)
            if parser is not None and parser.can_parse(filename, mime_type):
                return parser

        return None

    def parse_file(self, file_data: bytes, filename: str, mime_type: str = None) -> ParseResult:
        parser = self.get_parser(filename, mime_type)
        if not parser:
            logger.warning("Unsupported file type or parser unavailable: %s", filename)
            return ParseResult("")

        try:
            return parser.parse(file_data, filename)
        except Exception as exc:
            logger.error("File parsing failed: %s, error: %s", filename, exc)
            return ParseResult("")

    def _load_parser(self, registration: ParserRegistration) -> Optional[BaseParser]:
        cache_key = registration.class_name

        if cache_key in self._parser_cache:
            return self._parser_cache[cache_key]

        if cache_key in self._failed_parser_keys:
            return None

        try:
            module = importlib.import_module(registration.module_path)
        except ImportError as exc:
            self._failed_parser_keys.add(cache_key)
            logger.warning(
                "Skipping parser %s because its dependency is unavailable: %s",
                cache_key,
                exc,
            )
            return None

        try:
            parser_cls = getattr(module, registration.class_name)
            parser = parser_cls()
        except Exception as exc:
            self._failed_parser_keys.add(cache_key)
            logger.error(
                "Skipping parser %s because initialization failed: %s",
                cache_key,
                exc,
            )
            return None

        self._parser_cache[cache_key] = parser
        return parser
