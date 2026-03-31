"""
教官与证书相关测试用例
"""


from datetime import date

from api_test_base import APITestRunner, TestFailure


def case_instructor_endpoints(runner: APITestRunner):
    il = runner._request("GET", "/users?page=1&size=10&role=instructor", role="admin", expected_code=200)
    data = il.get("data") or {}
    total = data.get("total")
    if total is None:
        raise TestFailure("教官用户列表无total")

    items = data.get("items") or []
    if items:
        iid = items[0].get("id")
        if iid:
            d = runner._request("GET", f"/users/{iid}", role="admin", expected_code=200)
            if (d.get("data") or {}).get("id") != iid:
                raise TestFailure("教官用户详情不匹配")

def case_certificate_flow(runner: APITestRunner):
    student_user_id = (runner.users.get("student") or {}).get("id")
    tid = runner.runtime.get("training_id")
    if not student_user_id:
        raise TestFailure("未获取student user_id")

    payload = {
        "user_id": student_user_id,
        "training_id": tid,
        "training_name": "自动化测试培训",
        "score": 88.5,
        "issue_date": date.today().isoformat(),
    }
    cert = runner._request("POST", "/certificates", role="instructor", json=payload, expected_code=200)
    cd = cert.get("data") or {}
    cid = cd.get("id")
    if not cid:
        raise TestFailure("签发证书未返回id")
    runner.runtime["certificate_id"] = cid

    lst = runner._request("GET", "/certificates?page=1&size=10", role="admin", expected_code=200)
    if ((lst.get("data") or {}).get("total")) is None:
        raise TestFailure("证书列表无total")


def get_cases(runner: APITestRunner):
    return [
        ("教官用户接口", lambda: case_instructor_endpoints(runner)),
        ("证书流程", lambda: case_certificate_flow(runner)),
    ]
