"""
题库与考试相关测试用例
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta

from api_test_base import APITestRunner, TestFailure


def case_question_crud(runner: APITestRunner):
    q_payload = {
        "type": "single",
        "content": f"测试题目-单选-{int(time.time())}",
        "options": [
            {"key": "A", "text": "选项A"},
            {"key": "B", "text": "选项B"},
            {"key": "C", "text": "选项C"},
            {"key": "D", "text": "选项D"},
        ],
        "answer": "A",
        "explanation": "测试解析",
        "difficulty": 3,
        "knowledge_point": "测试知识点",
        "score": 5,
    }
    created = runner._request("POST", "/questions", role="instructor", json=q_payload, expected_code=200)
    q = created.get("data") or {}
    qid = q.get("id")
    if not qid:
        raise TestFailure("创建题目未返回id")
    runner.runtime["question_ids"].append(qid)

    upd = runner._request(
        "PUT",
        f"/questions/{qid}",
        role="instructor",
        json={"difficulty": 4, "score": 6},
        expected_code=200,
    )
    uq = upd.get("data") or {}
    if uq.get("difficulty") != 4:
        raise TestFailure("更新题目失败")

    batch_payload = {
        "questions": [
            {
                "type": "judge",
                "content": f"测试判断题-{int(time.time())}",
                "options": [{"key": "T", "text": "正确"}, {"key": "F", "text": "错误"}],
                "answer": "T",
                "difficulty": 2,
                "score": 4,
            },
            {
                "type": "single",
                "content": f"测试单选题2-{int(time.time())}",
                "options": [
                    {"key": "A", "text": "选项A"},
                    {"key": "B", "text": "选项B"},
                    {"key": "C", "text": "选项C"},
                    {"key": "D", "text": "选项D"},
                ],
                "answer": "B",
                "difficulty": 3,
                "score": 5,
            },
        ]
    }
    batch = runner._request("POST", "/questions/batch", role="instructor", json=batch_payload, expected_code=200)
    items = batch.get("data") or []
    if len(items) < 2:
        raise TestFailure("批量创建题目数量异常")
    runner.runtime["question_ids"].extend([x.get("id") for x in items if x.get("id")])

    qlist = runner._request("GET", "/questions?page=1&size=10", role="instructor", expected_code=200)
    total = (qlist.get("data") or {}).get("total")
    if total is None:
        raise TestFailure("题目列表缺少total")


def case_exam_flow(runner: APITestRunner):
    qids = [qid for qid in runner.runtime.get("question_ids", []) if qid]
    if not qids:
        raise TestFailure("没有可用于考试的题目")

    now = datetime.now()
    payload = {
        "title": f"集成测试考试-{int(time.time())}",
        "description": "自动化测试创建",
        "duration": 30,
        "total_score": 100,
        "passing_score": 60,
        "status": "active",
        "type": "quiz",
        "scope": "测试范围",
        "start_time": (now - timedelta(minutes=5)).isoformat(),
        "end_time": (now + timedelta(days=1)).isoformat(),
        "question_ids": qids[:3],
    }
    ex = runner._request("POST", "/exams", role="instructor", json=payload, expected_code=200)
    exam = ex.get("data") or {}
    exam_id = exam.get("id")
    if not exam_id:
        raise TestFailure("创建考试未返回id")
    runner.runtime["exam_id"] = exam_id

    detail = runner._request("GET", f"/exams/{exam_id}", role="student", expected_code=200)
    q_items = (detail.get("data") or {}).get("questions") or []
    if not q_items:
        raise TestFailure("考试详情未返回题目")

    answers = {}
    for q in q_items:
        qid = q.get("id")
        if not qid:
            continue
        q_type = q.get("type")
        if q_type == "multi":
            answers[str(qid)] = ["A"]
        elif q_type == "judge":
            answers[str(qid)] = "T"
        else:
            answers[str(qid)] = "A"

    submit_payload = {
        "answers": answers,
        "start_time": (datetime.now() - timedelta(minutes=10)).isoformat(),
    }
    submit = runner._request("POST", f"/exams/{exam_id}/submit", role="student", json=submit_payload, expected_code=200)
    rec = submit.get("data") or {}
    if rec.get("exam_id") != exam_id:
        raise TestFailure("提交考试返回异常")

    result = runner._request("GET", f"/exams/{exam_id}/result", role="student", expected_code=200)
    if (result.get("data") or {}).get("id") is None:
        raise TestFailure("考试结果为空")

    scores = runner._request("GET", f"/exams/{exam_id}/scores?page=1&size=10", role="instructor", expected_code=200)
    if ((scores.get("data") or {}).get("total")) is None:
        raise TestFailure("成绩列表无total")

    elist = runner._request("GET", "/exams?page=1&size=10", role="student", expected_code=200)
    if ((elist.get("data") or {}).get("total")) is None:
        raise TestFailure("考试列表无total")


def get_cases(runner: APITestRunner):
    return [
        ("题库流程", lambda: case_question_crud(runner)),
        ("考试流程", lambda: case_exam_flow(runner)),
    ]
