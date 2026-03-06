"""
认证与基础相关测试用例
"""

from __future__ import annotations

from typing import Any, Dict

from api_test_base import APITestRunner, TestFailure


def case_health(runner: APITestRunner):
    url = runner.api_base_url.replace("/api/v1", "") + "/health"
    resp = runner.session.get(url, timeout=runner.timeout)
    data = resp.json()
    if data.get("code") != 200:
        raise TestFailure("health check 失败")


def _login(runner: APITestRunner, username: str, password: str) -> Dict[str, Any]:
    data = runner._request(
        "POST",
        "/auth/login",
        json={"username": username, "password": password},
        expected_code=200,
    )
    payload = data.get("data") or {}
    token = payload.get("access_token")
    user = payload.get("user")
    if not token or not user:
        raise TestFailure(f"登录返回缺少token/user: {username}")
    return {"token": token, "user": user}


def case_auth_login_and_me(runner: APITestRunner):
    creds = {
        "admin": ("admin", "police2025"),
        "instructor": ("instructor", "teach2025"),
        "student": ("student", "learn2025"),
    }
    for role, (u, p) in creds.items():
        res = _login(runner, u, p)
        runner.tokens[role] = res["token"]
        runner.users[role] = res["user"]

        me = runner._request("GET", "/auth/me", role=role, expected_code=200)
        me_user = me.get("data") or {}
        if me_user.get("username") != u:
            raise TestFailure(f"/auth/me 用户不一致 role={role}")


def case_dashboard(runner: APITestRunner):
    for role in ["admin", "instructor", "student"]:
        data = runner._request("GET", f"/dashboard?role={role}", role=role, expected_code=200)
        stats = (data.get("data") or {}).get("stats")
        if not isinstance(stats, dict):
            raise TestFailure(f"dashboard stats 非dict role={role}")


def get_cases(runner: APITestRunner):
    return [
        ("健康检查", lambda: case_health(runner)),
        ("认证登录 + /auth/me", lambda: case_auth_login_and_me(runner)),
        ("工作台", lambda: case_dashboard(runner)),
    ]
