"""
独立测试脚本 — 不依赖 app 包，直接调用 LLM 测试校验效果。
"""
import json
import os
from openai import OpenAI

# 从 .env 读取配置
LLM_BASE_URL = "https://api.siliconflow.cn/v1"
LLM_API_KEY = "sk-csyibemmtsinofnouwodpjqrmkavhcnudoswubsstkfpecqm"
LLM_MODEL = "Pro/MiniMaxAI/MiniMax-M2.5"

print(f"LLM 配置: base_url={LLM_BASE_URL}, model={LLM_MODEL}, key_set={bool(LLM_API_KEY)}")

client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
    timeout=60,
)

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

PROMPT = """你是一名资深警务培训教官和题目质量审核专家。
请对以下 AI 生成的考试题目进行质量校验，并为每道题自动提取合适的标签。

期望题型：单选题
期望难度：3/5
关联知识点：["盘查规范", "证据固定", "执法程序"]
关联警种：刑侦

请逐题校验以下维度：
1. 题干是否完整、清晰，是否缺少上下文
2. 选项是否合理（单选题是否有且仅有 1 个正确答案，多选题是否至少 2 个正确答案）
3. 答案是否正确且与解析一致
4. 题目是否与警务训练相关
5. 题目是否与期望的知识点相关
6. 难度是否与期望难度匹配（允许 ±1 偏差）

同时为每道题自动提取以下标签：
- suggested_knowledge_points: 1-3 个知识点名称（优先从关联知识点中选择，如题目涉及新知识点可补充）
- suggested_difficulty: 1-5 的整数（根据题目实际难度评估）
- suggested_police_type_hint: 题目最可能归属的警种名称（如无法判断则为 null）

题目 JSON 内容：
""" + json.dumps(TEST_QUESTIONS, ensure_ascii=False) + """

请输出以下格式的 JSON 对象：
{
  "questions": [
    {
      "index": 题目序号（从 1 开始）,
      "passed": true/false,
      "quality_score": 0-100 的整数,
      "issues": ["问题描述列表，无问题则为空数组"],
      "suggested_knowledge_points": ["知识点1", "知识点2"],
      "suggested_difficulty": 3,
      "suggested_police_type_hint": "警种名称或 null"
    }
  ]
}

请现在直接输出 JSON 对象。"""

print("\n" + "=" * 60)
print("发送校验请求到 LLM...")
print("=" * 60)

try:
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "你是一个专业的警务训练题目质量审核助手。你必须严格输出一个合法 JSON 对象。"},
            {"role": "user", "content": PROMPT},
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    print(f"\nLLM 返回内容（前 2000 字符）：\n{content[:2000]}")

    # 尝试解析 JSON
    json_text = content.strip()
    if json_text.startswith("```"):
        import re
        json_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", json_text, flags=re.IGNORECASE | re.DOTALL).strip()

    result = json.loads(json_text)
    print("\n" + "=" * 60)
    print("解析结果：")
    print("=" * 60)

    for item in result.get("questions", []):
        print(f"\n--- 第 {item.get('index')} 题 ---")
        print(f"  通过: {item.get('passed')}")
        print(f"  质量分: {item.get('quality_score')}")
        print(f"  问题: {item.get('issues')}")
        print(f"  建议知识点: {item.get('suggested_knowledge_points')}")
        print(f"  建议难度: {item.get('suggested_difficulty')}")
        print(f"  建议警种: {item.get('suggested_police_type_hint')}")

except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
