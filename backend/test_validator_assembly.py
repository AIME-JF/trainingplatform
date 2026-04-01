"""
测试补题场景 — 模拟题库不足时 LLM 生成的题目 + 二次校验效果。
"""
import json
from openai import OpenAI

LLM_BASE_URL = "https://api.siliconflow.cn/v1"
LLM_API_KEY = "sk-csyibemmtsinofnouwodpjqrmkavhcnudoswubsstkfpecqm"
LLM_MODEL = "Pro/MiniMaxAI/MiniMax-M2.5"

client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL, timeout=60)

# 模拟补题场景：组卷需要 5 道单选题，知识点是"治安管理"，但题库只有 2 道，补 3 道
# 以下是 AIQuestionGenerator 生成的 3 道补题
TEST_QUESTIONS = [
    {
        "index": 1,
        "type": "single",
        "content": "治安管理处罚法规定，对扰乱公共场所秩序的行为，可以处以何种处罚？",
        "options": [
            {"key": "A", "text": "警告或者二百元以下罚款"},
            {"key": "B", "text": "五日以上十日以下拘留，可以并处五百元以下罚款"},
            {"key": "C", "text": "十日以上十五日以下拘留，可以并处一千元以下罚款"},
            {"key": "D", "text": "拘役或者管制"}
        ],
        "answer": "B",
        "explanation": "根据《治安管理处罚法》第二十三条，扰乱公共场所秩序的，处五日以上十日以下拘留，可以并处五百元以下罚款。",
        "difficulty": 3,
        "knowledge_points": ["治安管理", "处罚程序"]
    },
    {
        "index": 2,
        "type": "single",
        "content": "关于治安调解的适用范围，下列说法正确的是？",
        "options": [
            {"key": "A", "text": "所有治安案件都可以调解处理"},
            {"key": "B", "text": "因民间纠纷引起的打架斗殴可以调解"},
            {"key": "C", "text": "雇凶伤害他人的案件可以调解"},
            {"key": "D", "text": "多次违反治安管理的可以调解"}
        ],
        "answer": "B",
        "explanation": "治安调解适用于因民间纠纷引起的打架斗殴或者损毁他人财物等违反治安管理行为，情节较轻的。雇凶伤害、多次违法等不适用调解。",
        "difficulty": 3,
        "knowledge_points": ["治安管理", "调解程序"]
    },
    {
        "index": 3,
        "type": "single",
        "content": "民警在巡逻过程中发现可疑人员，正确的做法是？",
        "options": [
            {"key": "A", "text": "立即上前搜身检查"},
            {"key": "B", "text": "表明身份后进行盘问检查"},
            {"key": "C", "text": "直接带回派出所审查"},
            {"key": "D", "text": "不予理会继续巡逻"}
        ],
        "answer": "B",
        "explanation": "民警执行巡逻任务时发现可疑人员，应当先表明执法身份，然后依法进行盘问检查。搜身需要符合法定条件，不能随意进行。",
        "difficulty": 2,
        "knowledge_points": ["治安管理", "巡逻规范"]
    }
]

# 模拟题库已有题目（用于去重参考）
EXISTING_CONTENTS = [
    "治安管理处罚的种类不包括以下哪一项？",
    "下列哪项行为不属于扰乱公共秩序的行为？"
]

print("=" * 60)
print("补题场景测试：治安管理单选题补题校验")
print("=" * 60)
print(f"\n题库已有 {len(EXISTING_CONTENTS)} 道题：")
for c in EXISTING_CONTENTS:
    print(f"  - {c}")
print(f"\nAI 生成 {len(TEST_QUESTIONS)} 道补题，开始二次校验...\n")

PROMPT = f"""你是一名资深警务培训教官和题目质量审核专家。
请对以下 AI 生成的考试题目进行质量校验，并为每道题自动提取合适的标签。

期望题型：单选题
期望难度：3/5
关联知识点：["治安管理", "处罚程序", "巡逻规范"]
关联警种：治安

以下 {len(EXISTING_CONTENTS)} 道题的题干已从题库选出，请避免生成语义相近的重复题目：
""" + "\n".join(f"- {c}" for c in EXISTING_CONTENTS) + """

请逐题校验以下维度：
1. 题干是否完整、清晰，是否缺少上下文
2. 选项是否合理（单选题是否有且仅有 1 个正确答案）
3. 答案是否正确且与解析一致
4. 题目是否与警务训练相关
5. 题目是否与期望的知识点相关
6. 难度是否与期望难度匹配（允许 ±1 偏差）

同时为每道题自动提取以下标签：
- suggested_knowledge_points: 1-3 个知识点名称
- suggested_difficulty: 1-5 的整数
- suggested_police_type_hint: 题目最可能归属的警种名称

题目 JSON 内容：
""" + json.dumps(TEST_QUESTIONS, ensure_ascii=False) + """

请输出以下格式的 JSON 对象：
{
  "questions": [
    {
      "index": 题目序号,
      "passed": true/false,
      "quality_score": 0-100,
      "issues": ["问题列表"],
      "suggested_knowledge_points": ["知识点"],
      "suggested_difficulty": 3,
      "suggested_police_type_hint": "警种名称"
    }
  ]
}

请现在直接输出 JSON 对象。"""

try:
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "你是一个专业的警务训练题目质量审核助手。你必须严格输出一个合法 JSON 对象。"},
            {"role": "user", "content": PROMPT},
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        import re
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE | re.DOTALL).strip()

    result = json.loads(content)

    print(f"\n校验结果：共 {len(result['questions'])} 题")
    passed = sum(1 for q in result['questions'] if q['passed'])
    print(f"通过 {passed} 题，未通过 {len(result['questions']) - passed} 题\n")

    for item in result['questions']:
        status = "✅ 通过" if item['passed'] else "❌ 未通过"
        print(f"--- 第 {item['index']} 题 [{status}] ---")
        print(f"  质量分: {item['quality_score']}")
        if item['issues']:
            print(f"  问题: {'; '.join(item['issues'])}")
        print(f"  知识点: {item['suggested_knowledge_points']}")
        print(f"  难度: {item['suggested_difficulty']}")
        print(f"  警种: {item['suggested_police_type_hint']}")
        print()

except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
