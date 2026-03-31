"""教学资源内容模板注册表"""
from __future__ import annotations

from app.schemas import TeachingResourceGenerationTemplatePayload, TeachingResourceGenerationTemplateSlot


GENERAL_TEACHING_TEMPLATE_CODE = "general_teaching_slides"


class TeachingResourceTemplateRegistry:
    """统一管理课件内容模板"""

    def get_template(self, template_code: str | None = None) -> TeachingResourceGenerationTemplatePayload:
        normalized_code = str(template_code or GENERAL_TEACHING_TEMPLATE_CODE).strip() or GENERAL_TEACHING_TEMPLATE_CODE
        if normalized_code != GENERAL_TEACHING_TEMPLATE_CODE:
            normalized_code = GENERAL_TEACHING_TEMPLATE_CODE
        return self._build_general_teaching_template()

    def _build_general_teaching_template(self) -> TeachingResourceGenerationTemplatePayload:
        slots = [
            TeachingResourceGenerationTemplateSlot(
                page_no=1,
                slot_key="cover",
                page_type="cover",
                layout="cover",
                purpose="交代课件主题和适用对象",
                content_requirements=["页面标题", "一句副标题", "适用对象或场景"],
            ),
            TeachingResourceGenerationTemplateSlot(
                page_no=2,
                slot_key="goals",
                page_type="goal",
                layout="focus-list",
                purpose="说明学习目标和预期收获",
                content_requirements=["3到4条学习目标", "目标要具体直接"],
            ),
            TeachingResourceGenerationTemplateSlot(
                page_no=3,
                slot_key="background",
                page_type="background",
                layout="two-column",
                purpose="解释背景、价值或业务场景",
                content_requirements=["背景说明", "典型场景提示", "一句重点提醒"],
            ),
            TeachingResourceGenerationTemplateSlot(
                page_no=4,
                slot_key="key-point-1",
                page_type="knowledge",
                layout="card-list",
                purpose="讲解第一个核心知识点",
                content_requirements=["页面标题", "3到4条讲解要点", "一句强调内容"],
            ),
            TeachingResourceGenerationTemplateSlot(
                page_no=5,
                slot_key="key-point-2",
                page_type="knowledge",
                layout="card-list",
                purpose="讲解第二个核心知识点",
                content_requirements=["页面标题", "3到4条讲解要点", "一句强调内容"],
            ),
            TeachingResourceGenerationTemplateSlot(
                page_no=6,
                slot_key="case",
                page_type="case",
                layout="two-column",
                purpose="给出案例或情境化提醒",
                content_requirements=["案例标题", "案例要点", "风险提示或常见误区"],
            ),
            TeachingResourceGenerationTemplateSlot(
                page_no=7,
                slot_key="practice",
                page_type="practice",
                layout="focus-list",
                purpose="提供实务建议或操作清单",
                content_requirements=["3到5条落地建议", "强调先后顺序或注意事项"],
            ),
            TeachingResourceGenerationTemplateSlot(
                page_no=8,
                slot_key="summary",
                page_type="summary",
                layout="summary",
                purpose="总结重点并形成记忆闭环",
                content_requirements=["关键结论", "复盘提示", "结束语"],
            ),
        ]
        return TeachingResourceGenerationTemplatePayload(
            code=GENERAL_TEACHING_TEMPLATE_CODE,
            name="通用教学课件模板",
            description="适用于常规教学讲解、政策宣导和业务流程说明的一套八页课件内容模板。",
            page_count=len(slots),
            slots=slots,
        )
