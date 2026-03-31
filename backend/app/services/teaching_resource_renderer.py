"""教学资源 HTML 渲染器"""
from __future__ import annotations

import html
import json
from pathlib import Path

from app.schemas import TeachingResourceGenerationPagePlan


class TeachingResourceRenderer:
    """将结构化页面方案渲染为单文件 HTML 课件"""

    TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "teaching_resource_slides.html"

    def render(
        self,
        *,
        title: str,
        summary: str | None,
        pages: list[TeachingResourceGenerationPagePlan],
    ) -> str:
        template = self.TEMPLATE_PATH.read_text(encoding="utf-8")
        presentation_payload = {
            "title": title,
            "summary": summary or "",
            "pages": [page.model_dump(mode="python") for page in pages],
        }
        presentation_json = json.dumps(presentation_payload, ensure_ascii=False).replace("</", "<\\/")
        return (
            template
            .replace("__DOCUMENT_TITLE__", html.escape(title or "AI课件", quote=True))
            .replace("__PRESENTATION_JSON__", presentation_json)
        )
