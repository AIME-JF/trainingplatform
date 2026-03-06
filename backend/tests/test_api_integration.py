"""
后端API集成测试（拆分版总入口）

使用方式：
1) 先手动启动服务：python main.py
2) 再执行：python tests/test_api_integration.py

默认服务地址：http://127.0.0.1:8001/api/v1
可通过环境变量覆盖：
- API_BASE_URL
"""

from __future__ import annotations

from api_test_base import APITestRunner
from test_cases_auth import get_cases as auth_cases
from test_cases_question_exam import get_cases as question_exam_cases
from test_cases_course_training import get_cases as course_training_cases
from test_cases_instructor_certificate import get_cases as instructor_certificate_cases
from test_cases_profile_report_talent_ai import get_cases as profile_report_talent_ai_cases


def main():
    runner = APITestRunner()

    cases = []
    cases.extend(auth_cases(runner))
    cases.extend(question_exam_cases(runner))
    cases.extend(course_training_cases(runner))
    cases.extend(instructor_certificate_cases(runner))
    cases.extend(profile_report_talent_ai_cases(runner))

    runner.run(cases)


if __name__ == "__main__":
    main()
