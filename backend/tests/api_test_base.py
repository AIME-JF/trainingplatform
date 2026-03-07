"""
API 集成测试基础能力
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, Optional, Tuple, List, Callable

import requests


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8001/api/v1")
TIMEOUT = 20


class TestFailure(Exception):
    pass


class APITestRunner:
    def __init__(self):
        self.api_base_url = API_BASE_URL
        self.timeout = TIMEOUT

        self.session = requests.Session()
        # 强制忽略系统代理，避免本地127.0.0.1请求被转发导致502
        self.session.trust_env = False

        self.summary: List[Tuple[str, bool, str]] = []
        self.tokens: Dict[str, str] = {}
        self.users: Dict[str, Dict[str, Any]] = {}

        self.runtime: Dict[str, Any] = {
            "question_ids": [],
            "exam_id": None,
            "training_id": None,
            "enrollment_id": None,
            "course_id": None,
            "chapter_id": None,
            "certificate_id": None,
        }

    def pass_case(self, name: str, detail: str = ""):
        self.summary.append((name, True, detail))
        print(f"[PASS] {name} {detail}")

    def fail_case(self, name: str, detail: str = ""):
        self.summary.append((name, False, detail))
        print(f"[FAIL] {name} {detail}")

    def _headers(self, role: Optional[str] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if role and role in self.tokens:
            headers["Authorization"] = f"Bearer {self.tokens[role]}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        role: Optional[str] = None,
        expected_code: Optional[int] = 200,
        **kwargs,
    ) -> Dict[str, Any]:
        url = f"{self.api_base_url}{path}"
        headers = self._headers(role)

        if "headers" in kwargs and kwargs["headers"]:
            headers.update(kwargs.pop("headers"))

        resp = self.session.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
        try:
            data = resp.json()
        except Exception:
            raise TestFailure(f"响应非JSON: {url} status={resp.status_code} body={resp.text[:300]}")

        code = data.get("code", None)
        if expected_code is not None and code != expected_code:
            raise TestFailure(
                f"接口返回code不符合预期: {method} {path} expect={expected_code} actual={code} msg={data.get('message')}"
            )

        return data

    def run_case(self, name: str, func: Callable[[], None]):
        try:
            func()
            self.pass_case(name)
        except Exception as e:
            self.fail_case(name, f"-> {e}")

    def run(self, cases: List[Tuple[str, Callable[[], None]]]):
        print("=" * 80)
        print("警务训练平台后端 API 集成测试")
        print(f"Base URL: {self.api_base_url}")
        print("=" * 80)

        for name, fn in cases:
            self.run_case(name, fn)

        print("\n" + "=" * 80)
        print("测试汇总")
        print("=" * 80)
        passed = sum(1 for _, ok, _ in self.summary if ok)
        failed = len(self.summary) - passed
        for name, ok, detail in self.summary:
            status = "PASS" if ok else "FAIL"
            print(f"[{status}] {name} {detail}")

        print("-" * 80)
        print(f"总计: {len(self.summary)} | 通过: {passed} | 失败: {failed}")

        if failed > 0:
            sys.exit(1)
        sys.exit(0)
