"""
个人中心、看板、人才库、AI 相关测试用例
"""

from __future__ import annotations

import time

from api_test_base import APITestRunner, TestFailure


def case_profile(runner: APITestRunner):
    p = runner._request("GET", "/profile", role="student", expected_code=200)
    if (p.get("data") or {}).get("id") is None:
        raise TestFailure("个人信息为空")

    upd = runner._request(
        "PUT",
        "/profile",
        role="student",
        json={"nickname": f"测试昵称-{int(time.time())}", "unit": "南宁市公安局测试"},
        expected_code=200,
    )
    if not (upd.get("data") or {}).get("nickname"):
        raise TestFailure("更新个人信息失败")

    st = runner._request("GET", "/profile/study-stats", role="student", expected_code=200)
    if (st.get("data") or {}).get("total_exams") is None:
        raise TestFailure("学习统计字段缺失")

    eh = runner._request("GET", "/profile/exam-history", role="student", expected_code=200)
    if not isinstance(eh.get("data"), list):
        raise TestFailure("考试历史不是list")


def case_report(runner: APITestRunner):
    kpi = runner._request("GET", "/report/kpi", role="admin", expected_code=200)
    if (kpi.get("data") or {}).get("total_students") is None:
        raise TestFailure("KPI缺少字段")

    tr = runner._request("GET", "/report/trend", role="admin", expected_code=200)
    if not isinstance(tr.get("data"), list):
        raise TestFailure("trend不是list")

    pd = runner._request("GET", "/report/police-type-distribution", role="admin", expected_code=200)
    if not isinstance(pd.get("data"), list):
        raise TestFailure("police-type-distribution不是list")

    cr = runner._request("GET", "/report/city-ranking", role="admin", expected_code=200)
    if not isinstance(cr.get("data"), list):
        raise TestFailure("city-ranking不是list")


def case_talent(runner: APITestRunner):
    tl = runner._request("GET", "/talent?page=1&size=10", role="admin", expected_code=200)
    if ((tl.get("data") or {}).get("total")) is None:
        raise TestFailure("人才列表无total")

    ts = runner._request("GET", "/talent/stats", role="admin", expected_code=200)
    if (ts.get("data") or {}).get("total") is None:
        raise TestFailure("人才统计缺少total")


def case_ai(runner: APITestRunner):
    q = runner._request(
        "POST",
        "/ai/generate-questions",
        role="instructor",
        json={"topic": "反诈基础", "count": 3, "difficulty": 3, "types": ["single", "judge"]},
        expected_code=200,
    )
    if (q.get("data") or {}).get("total") is None:
        raise TestFailure("AI组卷返回缺少total")

    lp = runner._request(
        "POST",
        "/ai/generate-lesson-plan",
        role="instructor",
        json={
            "title": "反诈宣讲课",
            "subject": "反诈骗",
            "duration": 90,
            "objectives": ["识别骗局", "掌握处置"],
            "level": "中级",
        },
        expected_code=200,
    )
    if (lp.get("data") or {}).get("title") is None:
        raise TestFailure("AI教案返回缺少title")


def get_cases(runner: APITestRunner):
    return [
        ("个人中心", lambda: case_profile(runner)),
        ("数据看板", lambda: case_report(runner)),
        ("人才库", lambda: case_talent(runner)),
        ("AI功能", lambda: case_ai(runner)),
    ]
