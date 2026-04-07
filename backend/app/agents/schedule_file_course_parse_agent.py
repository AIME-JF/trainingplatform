"""智能体B：从课表文件纯文本中解析课程和课次"""
from __future__ import annotations

from typing import Any

from app.agents.base import BaseAIAgent


class ScheduleFileCourseParseAgent(BaseAIAgent):
    """从课表 xlsx 提取的纯文本中结构化解析课程与课次"""

    def extract(self, raw_text: str) -> dict:
        """返回 dict，包含 courses(课程列表) 和 error(错误信息)"""
        system_prompt = (
            "你是警务训练平台的课表解析助手，专门从课表文件文本中解析课程安排。\n"
            "仅返回 JSON 对象，不要输出任何额外解释、注释或 markdown 格式。\n"
            "\n"
            "【输出格式】\n"
            "JSON 字段固定为：\n"
            "  courses - 课程数组，每个课程包含：\n"
            "    name             - 课程名称（字符串，必填，最多50字）\n"
            "    type             - 课程类型：theory 或 practice\n"
            "    location         - 上课地点（字符串，最多30字，提取不到返回 null）\n"
            "    primary_instructor_name   - 主讲教官姓名（最多10字，提取不到返回 null）\n"
            "    assistant_instructor_names - 辅助教官姓名列表（每个最多10字，提取不到返回 []）\n"
            "    sessions         - 课次数组，每个课次仅包含：\n"
            "      date           - 日期 YYYY-MM-DD\n"
            "      time_start     - 开始时间 HH:MM\n"
            "      time_end       - 结束时间 HH:MM\n"
            "      location       - 该课次地点（最多30字，与课程地点相同时返回 null）\n"
            "  error - 无法解析时返回错误说明字符串，正常解析返回 null\n"
            "\n"
            "【解析规则】\n"
            "1. 按课程名称分组，相同课程名称合并为一个对象，不同时间段作为不同课次\n"
            "2. 教官必须是具体人名；组织名称、活动形式（如'分组讨论'、'自习'、'全体学员'、'XX大队'）返回 null\n"
            "3. 课程类型：含'实操'、'演练'、'射击'、'体能'、'实战'、'格斗'、'驾驶'为 practice，其余为 theory\n"
            "4. 日期统一为 YYYY-MM-DD，时间统一为 HH:MM\n"
            "5. 课次 location 与课程默认地点相同时必须返回 null，不要重复填写\n"
            "6. 所有字符串字段严格按照上述最大长度截断\n"
            "7. 无法解析时 courses 返回 []，error 返回原因\n"
            "\n"
            "【重要约束】\n"
            "- 输出必须是完整、合法的 JSON，不得截断\n"
            "- 字段值尽量简短，不要添加任何多余内容\n"
            "- 严格按照上述字段定义输出，不要添加额外字段\n"
        )
        user_prompt = f"以下是课表文件提取的纯文本内容，请解析课程安排：\n\n{raw_text[:8000]}"

        try:
            payload = self._generate_json_payload(system_prompt=system_prompt, user_prompt=user_prompt)
            return self._normalize_result(payload)
        except Exception as exc:
            return {"courses": [], "error": f"AI 解析异常: {exc}"}

    def _normalize_result(self, payload: dict) -> dict:
        error = payload.get("error")
        if error is not None:
            error = str(error).strip() or None

        courses_raw = payload.get("courses") or []
        if not isinstance(courses_raw, list):
            return {"courses": [], "error": error or "课程数据格式异常"}

        courses = []
        for c in courses_raw:
            if not isinstance(c, dict):
                continue
            course = self._normalize_course(c)
            if course:
                courses.append(course)

        if not courses and not error:
            error = "未能从文本中解析出任何课程信息"

        return {"courses": courses, "error": error}

    def _normalize_course(self, raw: dict) -> dict | None:
        name = str(raw.get("name") or "").strip()
        if not name:
            return None

        course_type = str(raw.get("type") or "theory").strip()
        if course_type not in ("theory", "practice"):
            course_type = self._infer_course_type(name)

        location = raw.get("location")
        if location is not None:
            location = str(location).strip()[:200] or None

        primary_name = self._normalize_instructor_name(raw.get("primary_instructor_name"))
        assistant_names = []
        for an in (raw.get("assistant_instructor_names") or []):
            n = self._normalize_instructor_name(an)
            if n:
                assistant_names.append(n)

        sessions = []
        for s in (raw.get("sessions") or []):
            if not isinstance(s, dict):
                continue
            session = self._normalize_session(s)
            if session:
                sessions.append(session)

        return {
            "name": name[:200],
            "type": course_type,
            "location": location,
            "primary_instructor_name": primary_name,
            "assistant_instructor_names": assistant_names,
            "sessions": sessions,
        }

    @staticmethod
    def _normalize_instructor_name(value: Any) -> str | None:
        if value is None:
            return None
        name = str(value).strip()
        if not name or name.lower() == "null":
            return None
        # 如果是组织/形式而非人名，返回 None
        org_keywords = ("大队", "中队", "支队", "总队", "分局", "派出所",
                        "分组", "自习", "全体", "讨论", "考试", "测试")
        for kw in org_keywords:
            if kw in name:
                return None
        return name[:100]

    @staticmethod
    def _normalize_session(raw: dict) -> dict | None:
        import re
        date_str = str(raw.get("date") or "").strip()
        time_start = str(raw.get("time_start") or "").strip()
        time_end = str(raw.get("time_end") or "").strip()

        if not date_str or not time_start or not time_end:
            return None

        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return None
        if not re.match(r"^\d{2}:\d{2}$", time_start):
            return None
        if not re.match(r"^\d{2}:\d{2}$", time_end):
            return None

        location = raw.get("location")
        if location is not None:
            location = str(location).strip()[:200] or None

        return {
            "date": date_str,
            "time_start": time_start,
            "time_end": time_end,
            "location": location,
        }

    @staticmethod
    def _infer_course_type(name: str) -> str:
        practice_keywords = ("实操", "演练", "射击", "体能", "实战", "训练", "实训",
                             "格斗", "擒拿", "驾驶", "急救")
        for kw in practice_keywords:
            if kw in name:
                return "practice"
        return "theory"
