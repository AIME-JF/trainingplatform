"""
课程与培训相关测试用例
"""


import time
from datetime import datetime, timedelta, date

from api_test_base import APITestRunner, TestFailure


def case_course_flow(runner: APITestRunner):
    instructor_id = (runner.users.get("instructor") or {}).get("id")
    payload = {
        "title": f"集成测试课程-{int(time.time())}",
        "category": "law",
        "file_type": "video",
        "description": "自动化测试课程",
        "instructor_id": instructor_id,
        "duration": 120,
        "difficulty": 3,
        "is_required": True,
        "cover_color": "blue",
        "tags": ["测试", "法学"],
        "chapters": [
            {
                "title": "第一章",
                "sort_order": 1,
                "duration": 30,
                "video_url": "https://example.com/v1.mp4",
                "doc_url": "https://example.com/d1.pdf",
            },
            {
                "title": "第二章",
                "sort_order": 2,
                "duration": 45,
                "video_url": "https://example.com/v2.mp4",
            },
        ],
    }
    c = runner._request("POST", "/courses", role="instructor", json=payload, expected_code=200)
    course = c.get("data") or {}
    course_id = course.get("id")
    if not course_id:
        raise TestFailure("创建课程未返回id")
    runner.runtime["course_id"] = course_id

    chapters = course.get("chapters") or []
    if not chapters:
        detail = runner._request("GET", f"/courses/{course_id}", role="student", expected_code=200)
        chapters = ((detail.get("data") or {}).get("chapters") or [])
    if not chapters:
        raise TestFailure("课程无章节，无法测进度")
    chapter_id = chapters[0].get("id")
    runner.runtime["chapter_id"] = chapter_id

    clist = runner._request("GET", "/courses?page=1&size=10&sort=newest", role="student", expected_code=200)
    if ((clist.get("data") or {}).get("total")) is None:
        raise TestFailure("课程列表无total")

    upd = runner._request("PUT", f"/courses/{course_id}", role="instructor", json={"difficulty": 4}, expected_code=200)
    if (upd.get("data") or {}).get("difficulty") != 4:
        raise TestFailure("更新课程失败")

    runner._request(
        "PUT",
        f"/courses/{course_id}/chapters/{chapter_id}/progress",
        role="student",
        json={"progress": 60},
        expected_code=200,
    )

    pr = runner._request("GET", "/courses/progress", role="student", expected_code=200)
    if not isinstance(pr.get("data"), list):
        raise TestFailure("课程进度返回不是list")


def case_training_flow(runner: APITestRunner):
    instructor_id = (runner.users.get("instructor") or {}).get("id")
    payload = {
        "name": f"集成测试培训班-{int(time.time())}",
        "type": "special",
        "status": "active",
        "start_date": date.today().isoformat(),
        "end_date": (date.today() + timedelta(days=10)).isoformat(),
        "location": "南宁训练基地",
        "instructor_id": instructor_id,
        "capacity": 60,
        "description": "自动化测试培训班",
        "subjects": ["反诈", "执法规范"],
        "courses": [
            {"name": "执法规范实训", "instructor": "张教官", "hours": 8, "type": "practice"},
            {"name": "警务法律基础", "instructor": "李教官", "hours": 6, "type": "theory"},
        ],
    }
    tr = runner._request("POST", "/trainings", role="instructor", json=payload, expected_code=200)
    training = tr.get("data") or {}
    tid = training.get("id")
    if not tid:
        raise TestFailure("创建培训班未返回id")
    runner.runtime["training_id"] = tid

    tlist = runner._request("GET", "/trainings?page=1&size=10&status=active", role="student", expected_code=200)
    if ((tlist.get("data") or {}).get("total")) is None:
        raise TestFailure("培训列表无total")

    detail = runner._request("GET", f"/trainings/{tid}", role="student", expected_code=200)
    if (detail.get("data") or {}).get("id") != tid:
        raise TestFailure("培训详情不匹配")

    en = runner._request("POST", f"/trainings/{tid}/enroll", role="student", json={"note": "申请参加"}, expected_code=200)
    enrollment = en.get("data") or {}
    eid = enrollment.get("id")
    if not eid:
        raise TestFailure("报名未返回id")
    runner.runtime["enrollment_id"] = eid

    el = runner._request("GET", f"/trainings/{tid}/enrollments?page=1&size=10", role="instructor", expected_code=200)
    if ((el.get("data") or {}).get("total")) is None:
        raise TestFailure("报名列表无total")

    ap = runner._request("PUT", f"/trainings/{tid}/enrollments/{eid}/approve", role="instructor", expected_code=200)
    if (ap.get("data") or {}).get("status") != "approved":
        raise TestFailure("审批通过失败")

    st = runner._request("GET", f"/trainings/{tid}/students?page=1&size=10", role="instructor", expected_code=200)
    if ((st.get("data") or {}).get("total")) is None:
        raise TestFailure("学员列表无total")

    ck = runner._request("POST", f"/trainings/{tid}/checkin", role="student", json={}, expected_code=200)
    if (ck.get("data") or {}).get("id") is None:
        raise TestFailure("签到失败")

    ckr = runner._request("GET", f"/trainings/{tid}/checkin/records", role="instructor", expected_code=200)
    if not isinstance(ckr.get("data"), list):
        raise TestFailure("签到记录不是list")

    qr = runner._request("GET", f"/trainings/{tid}/checkin/qr", role="instructor", expected_code=200)
    qd = qr.get("data") or {}
    if not qd.get("token"):
        raise TestFailure("签到二维码token缺失")

    sch = runner._request("GET", f"/trainings/{tid}/schedule", role="student", expected_code=200)
    if not isinstance(sch.get("data"), list):
        raise TestFailure("训练计划不是list")

    up = runner._request("PUT", f"/trainings/{tid}", role="instructor", json={"capacity": 80}, expected_code=200)
    if (up.get("data") or {}).get("capacity") != 80:
        raise TestFailure("更新培训班失败")


def case_training_delete(runner: APITestRunner):
    tid = runner.runtime.get("training_id")
    if not tid:
        return
    runner._request("DELETE", f"/trainings/{tid}", role="instructor", expected_code=200)


def get_cases(runner: APITestRunner):
    return [
        ("课程流程", lambda: case_course_flow(runner)),
        ("培训流程", lambda: case_training_flow(runner)),
        ("清理培训数据", lambda: case_training_delete(runner)),
    ]
