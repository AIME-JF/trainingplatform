"""
测试 AIQuestionValidator 的二次校验和自动打标签功能。
直接调用 agent 方法，不依赖 HTTP 服务。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# 直接导入 validator，绕过 app.__init__.py 的 FastAPI 初始化
from app.agents.base import BaseAIAgent
from app.agents.question_validator import AIQuestionValidator, BatchValidationResult

# 模拟 LLM 生成的题目
TEST_QUESTIONS = [
    {
        "index": 1,
        "type": "single",
        "content": "关于盘查程序，下列说法正确的是？",
        "options": [
            {"key": "A", "text": "盘查时必须出示执法证件"},
            {"key": "B", "text": "可以口头告知盘查理由"},
            {"key": "C", "text": "盘查时间不得超过2小时"},
            {"key": "D", "text": "盘查无需记录"}
        ],
        "answer": "A",
        "explanation": "根据《人民警察法》规定，盘查时必须出示执法证件。",
        "difficulty": 3,
        "knowledge_points": ["盘查规范", "执法程序"]
    },
    {
        "index": 2,
        "type": "single",
        "content": "现场证据固定时，以下哪项做法是错误的？",
        "options": [
            {"key": "A", "text": "拍照记录现场全貌"},
            {"key": "B", "text": "使用执法记录仪全程录像"},
            {"key": "C", "text": "先移动证据再拍照"},
            {"key": "D", "text": "标注证据位置和编号"}
        ],
        "answer": "C",
        "explanation": "证据固定应先拍照记录原始状态，再移动或提取。",
        "difficulty": 4,
        "knowledge_points": ["证据固定", "现场勘查"]
    },
    {
        "index": 3,
        "type": "judge",
        "content": "民警在执行抓捕任务时，可以不用出示搜查证直接进入嫌疑人住所。",
        "options": [
            {"key": "A", "text": "正确"},
            {"key": "B", "text": "错误"}
        ],
        "answer": "B",
        "explanation": "除紧急情况外，进入公民住所搜查必须出示搜查证。",
        "difficulty": 2,
        "knowledge_points": ["搜查程序", "执法规范"]
    }
]

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("AIQuestionValidator 测试")
    print("=" * 60)

    questions_json = json.dumps(TEST_QUESTIONS, ensure_ascii=False)

    validator = AIQuestionValidator()

    try:
        result = validator.validate_and_tag_questions(
            questions_json,
            expected_type="single",
            expected_difficulty=3,
            expected_knowledge_points=["盘查规范", "证据固定", "执法程序"],
            police_type_name="刑侦",
        )

        print(f"\n校验结果：共 {result.total} 题，通过 {result.passed_count} 题")

        for i, r in enumerate(result.results):
            print(f"\n--- 第 {i+1} 题 ---")
            print(f"  通过: {r.passed}")
            print(f"  质量分: {r.quality_score}")
            print(f"  问题: {r.issues}")
            print(f"  建议知识点: {r.suggested_knowledge_points}")
            print(f"  建议难度: {r.suggested_difficulty}")
            print(f"  建议警种: {r.suggested_police_type_hint}")

        if result.overall_issues:
            print(f"\n整体问题: {result.overall_issues}")

    except Exception as e:
        print(f"\n校验异常: {e}")
        import traceback
        traceback.print_exc()
