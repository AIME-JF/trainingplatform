"""教学资源内容填充智能体"""
from __future__ import annotations

import json

from app.agents.base import BaseAIAgent
from app.schemas import (
    TeachingResourceGenerationPagePlan,
    TeachingResourceGenerationParsedRequest,
    TeachingResourceGenerationTaskCreateRequest,
    TeachingResourceGenerationTemplatePayload,
)


class TeachingResourceContentAgent(BaseAIAgent):
    """基于固定内容模板填充每页内容"""

    def fill_template(
        self,
        request: TeachingResourceGenerationTaskCreateRequest,
        parsed_request: TeachingResourceGenerationParsedRequest,
        template: TeachingResourceGenerationTemplatePayload,
    ) -> list[TeachingResourceGenerationPagePlan]:
        subject_title = parsed_request.theme or "教学课件"
        system_prompt = (
            "你是教学课件内容助手。"
            "现在已经有固定的课件内容模板，请严格按照模板槽位填充每页内容。"
            "不要更改页数，不要新增或删除页面。"
            "仅返回 JSON 对象，字段固定为 pages。"
            "pages 数组里的每个元素必须包含 page_no、slot_key、page_type、layout、title、subtitle、bullets、highlight、notes。"
            "bullets 建议 3 到 5 条，内容短句化，适合 PPT 页面展示。"
        )
        user_prompt = (
            f"课件主题：{subject_title}\n"
            f"资源摘要：{request.resource_summary or '无'}\n"
            f"结构化解析：{json.dumps(parsed_request.model_dump(mode='python'), ensure_ascii=False)}\n"
            f"固定内容模板：{json.dumps(template.model_dump(mode='python'), ensure_ascii=False)}\n"
            "请按模板输出完整 pages。"
        )

        try:
            payload = self._generate_json_payload(system_prompt=system_prompt, user_prompt=user_prompt)
            pages = payload.get("pages") or []
            normalized_pages = [TeachingResourceGenerationPagePlan.model_validate(item) for item in pages]
            if len(normalized_pages) == template.page_count:
                return normalized_pages
        except Exception:
            pass

        return self._build_fallback_pages(request, parsed_request, template)

    def _build_fallback_pages(
        self,
        request: TeachingResourceGenerationTaskCreateRequest,
        parsed_request: TeachingResourceGenerationParsedRequest,
        template: TeachingResourceGenerationTemplatePayload,
    ) -> list[TeachingResourceGenerationPagePlan]:
        subject_title = parsed_request.theme or "教学课件"
        keywords = parsed_request.keywords or [subject_title]
        primary_keyword = keywords[0] if keywords else subject_title
        goals = parsed_request.learning_goals or ["理解背景", "掌握要点", "明确落实动作"]
        pages: list[TeachingResourceGenerationPagePlan] = []

        for index, slot in enumerate(template.slots, start=1):
            title = self._build_page_title(slot.slot_key, subject_title, keywords, index)
            subtitle = None
            bullets: list[str] = []
            highlight = None
            notes: list[str] = []

            if slot.slot_key == "cover":
                subtitle = parsed_request.summary or request.resource_summary or parsed_request.usage_scenario
                bullets = [
                    parsed_request.target_audience or "适用对象：平台学员",
                    parsed_request.usage_scenario or "使用场景：课堂讲解",
                ]
                highlight = parsed_request.tone or "建议课堂中结合业务案例讲解"
            elif slot.slot_key == "goals":
                bullets = goals[:4]
                highlight = "先建立整体理解，再进入细项展开"
            elif slot.slot_key == "background":
                bullets = [
                    f"主题背景：{parsed_request.theme}",
                    f"使用场景：{parsed_request.usage_scenario or '培训宣讲'}",
                    f"目标对象：{parsed_request.target_audience or '平台学员'}",
                ]
                highlight = f"重点围绕“{primary_keyword}”展开"
            elif slot.slot_key == "case":
                bullets = [
                    f"案例场景：围绕“{primary_keyword}”设置一个典型情境",
                    "识别过程中的关键风险点",
                    "结合规范动作给出处置建议",
                ]
                highlight = "案例页要突出易错点和纠偏动作"
            elif slot.slot_key == "practice":
                bullets = [
                    "先明确适用条件和触发场景",
                    "按步骤执行并记录关键节点",
                    "遇到异常情况及时上报或复核",
                    "复盘时对照规范查缺补漏",
                ]
                highlight = "落地建议必须可执行"
            elif slot.slot_key == "summary":
                bullets = [
                    f"回顾主题：{parsed_request.theme}",
                    "记住最重要的三个动作要点",
                    "结合岗位实际持续复盘和巩固",
                ]
                highlight = "用一句话收束全篇，形成记忆锚点"
            else:
                keyword = keywords[min(index - 1, len(keywords) - 1)]
                bullets = [
                    f"围绕“{keyword}”解释核心概念",
                    "拆分关键步骤或判断依据",
                    "强调常见误区与正确做法",
                ]
                highlight = f"本页核心：{keyword}"

            notes = [item for item in slot.content_requirements if item][:3]
            pages.append(
                TeachingResourceGenerationPagePlan(
                    page_no=slot.page_no,
                    slot_key=slot.slot_key,
                    page_type=slot.page_type,
                    layout=slot.layout,
                    title=title,
                    subtitle=subtitle,
                    bullets=bullets,
                    highlight=highlight,
                    notes=notes,
                )
            )
        return pages

    @staticmethod
    def _build_page_title(slot_key: str, resource_title: str, keywords: list[str], page_no: int) -> str:
        if slot_key == "cover":
            return resource_title
        if slot_key == "goals":
            return "学习目标"
        if slot_key == "background":
            return "背景与场景"
        if slot_key == "case":
            return "案例提示"
        if slot_key == "practice":
            return "实务建议"
        if slot_key == "summary":
            return "总结与提示"
        keyword = keywords[min(max(page_no - 4, 0), len(keywords) - 1)] if keywords else resource_title
        return f"{keyword}要点"
