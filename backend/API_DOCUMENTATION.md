# 警务训练平台 API 文档

本文档基于当前代码实现整理，路由来源为 `backend/app/views/*.py`。

- 默认服务地址：`http://127.0.0.1:8001`
- API 前缀：`/api/v1`
- OpenAPI：`/api/v1/openapi.json`
- Swagger：`/api/v1/docs`
- ReDoc：`/api/v1/redoc`

如果文档与运行结果不一致，请以 OpenAPI 和实际代码为准。

## 1. 通用约定

### 1.1 统一响应格式

除文件直链与二进制下载外，接口通常返回：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {}
}
```

分页接口的 `data` 结构：

```json
{
  "page": 1,
  "size": 10,
  "total": 100,
  "items": []
}
```

约定：

- `size=-1` 表示返回全部数据，适用于支持该约定的列表接口
- 业务失败时，部分异常会通过响应体 `code` 或 `detail` 表示，而不是完全依赖 HTTP 状态码

### 1.2 认证方式

- 登录后获取 `access_token`
- 受保护接口请求头：

```http
Authorization: Bearer <access_token>
```

### 1.3 特殊返回类型

以下接口不返回 `StandardResponse` 包装：

- `GET /api/v1/media/files/{file_id}`：返回文件内容或 307 跳转到 MinIO 直链
- `GET /api/v1/report/export`：返回 Excel 二进制流

### 1.4 命名说明

后端接口字段使用 `snake_case`。前端 `frontend/src/api/request.js` 会自动完成 `camelCase <-> snake_case` 转换。

### 1.5 数据范围说明

当前系统的访问控制由两层组成：

- 功能权限：是否拥有某个接口操作权限
- 数据范围：即使拥有功能权限，列表、详情、创建和更新仍会按对象归属做范围校验

当前已接入数据范围控制的对象：

- 用户
- 培训班
- 培训基地
- 题库题目

角色可配置的数据范围值：

- `all`
- `department`
- `department_and_sub`
- `police_type`
- `self`

当前规则摘要：

- 用户：按“部门或警种任一命中即可”控制，本人始终可见
- 培训班：如果同时配置了部门和警种，则必须同时满足；`created_by` 和 `instructor_id` 也计入“本人”
- 培训基地：按部门范围控制，`created_by` 计入“本人”
- 题目：按 `police_type_id` 控制，`created_by` 计入“本人”

## 2. 公共接口

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/` | 返回系统名称、版本、文档地址 |
| `GET` | `/health` | 健康检查 |

## 3. 认证模块

### 3.1 登录与当前用户

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/login` | 账号密码登录 | JSON：`username`、`password` |
| `POST` | `/api/v1/auth/login/phone` | 手机验证码登录 | Query：`phone`、`code` |
| `GET` | `/api/v1/auth/me` | 获取当前用户 | Bearer Token |

登录返回核心字段：

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "roles": [],
    "departments": [],
    "police_types": []
  }
}
```

说明：

- `login/phone` 当前只按手机号查用户，后端暂未校验验证码真伪

## 4. 工作台模块

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/dashboard` | 获取工作台数据 | Query：`role`，可选 `admin/instructor/student` |

## 5. 课程模块

### 5.1 课程主接口

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/courses` | 课程列表 | Query：`page` `size` `search` `category` `sort` |
| `POST` | `/api/v1/courses` | 创建课程 | JSON：`title` `category` `file_type` `description` `instructor_id` `duration` `difficulty` `is_required` `cover_color` `tags` `chapters[]` |
| `GET` | `/api/v1/courses/progress` | 当前用户学习进度 | 无 |
| `GET` | `/api/v1/courses/{course_id}` | 课程详情 | 返回章节与当前用户进度 |
| `PUT` | `/api/v1/courses/{course_id}` | 更新课程 | 字段同创建接口，均可选 |
| `DELETE` | `/api/v1/courses/{course_id}` | 删除课程 | 无 |

### 5.2 课程学习附属接口

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `PUT` | `/api/v1/courses/{course_id}/chapters/{chapter_id}/progress` | 更新章节进度 | JSON：`progress`，范围 `0-100` |
| `GET` | `/api/v1/courses/{course_id}/note` | 获取课程笔记 | 当前用户维度 |
| `PUT` | `/api/v1/courses/{course_id}/note` | 保存课程笔记 | JSON：`content` |
| `GET` | `/api/v1/courses/{course_id}/qa` | 获取课程答疑列表 | 无 |
| `POST` | `/api/v1/courses/{course_id}/qa` | 提交课程提问 | JSON：`question` |

### 5.3 课程与资源绑定

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/courses/{course_id}/resources` | 绑定课程资源 | JSON：`resource_id` `usage_type` `sort_order` |
| `GET` | `/api/v1/courses/{course_id}/resources` | 课程资源列表 | 无 |
| `DELETE` | `/api/v1/courses/{course_id}/resources/{resource_id}` | 解绑课程资源 | 无 |

## 6. 题库模块

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/questions` | 题目列表 | Query：`page` `size` `search` `type` `difficulty` `knowledge_point` |
| `POST` | `/api/v1/questions` | 创建题目 | JSON：`type` `content` `options` `answer` `explanation` `difficulty` `knowledge_point` `police_type_id` `score` |
| `PUT` | `/api/v1/questions/{question_id}` | 更新题目 | 字段同创建接口，均可选 |
| `DELETE` | `/api/v1/questions/{question_id}` | 删除题目 | 无 |
| `POST` | `/api/v1/questions/batch` | 批量导入题目 | JSON：`questions[]` |

题型约定：

- `single`
- `multi`
- `judge`

说明：

- 题目当前支持可选 `police_type_id`
- 题库接口已接入数据范围控制；如果角色数据范围不覆盖题目所属警种，则列表不可见、更新/删除也会被拒绝

## 7. 考试模块

### 7.1 业务说明

当前考试域使用统一题库和试卷快照，分成三类核心业务对象：

- `试卷`
  - 独立维护
  - 题目快照固化在试卷层
  - 支持 `draft / published / archived`
- `准入考试`
  - 独立维护
  - 不直接绑定培训班
  - 培训班通过 `admission_exam_id` 引用
  - 使用结构化适用范围限制
- `培训班内考试`
  - 必须关联 `training_id`
  - 用于随堂测、班内考核、结业考核、补考
  - 不再使用 `scope`

统一规则：

- 试卷创建和编辑时才允许配置 `question_ids[]`
- 考试和准入考试创建时只允许传 `paper_id`
- 只有已发布试卷才能用于创建考试
- 试卷发布后不能再修改题目
- 考试创建后不能再更换试卷
- 准入考试的适用范围由 `scope_type + scope_target_ids` 决定
- 准入考试范围支持：
  - `all`：全部学员
  - `user`：指定学员
  - `department`：指定部门
  - `role`：指定角色
- 准入考试的列表、详情和提交接口都会按适用范围做后端校验

### 7.2 试卷接口

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/exams/papers` | 试卷列表 | Query：`page` `size` `status` `type` `search` |
| `POST` | `/api/v1/exams/papers` | 创建试卷 | JSON：`title` `description` `duration` `total_score` `passing_score` `type` `question_ids[]` |
| `GET` | `/api/v1/exams/papers/{paper_id}` | 试卷详情 | 返回试卷基础信息和题目快照 |
| `PUT` | `/api/v1/exams/papers/{paper_id}` | 更新试卷 | 字段同创建接口，均可选 |
| `POST` | `/api/v1/exams/papers/{paper_id}/publish` | 发布试卷 | 无 |
| `POST` | `/api/v1/exams/papers/{paper_id}/archive` | 归档试卷 | 无 |
| `DELETE` | `/api/v1/exams/papers/{paper_id}` | 删除试卷 | 仅未被考试引用的试卷可删除 |

说明：

- `status` 常见值：`draft`、`published`、`archived`
- 试卷发布后不能再更新题目
- 已被准入考试或培训班考试引用的试卷不能删除

### 7.3 准入考试接口

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/exams/admission` | 准入考试列表 | Query：`page` `size` `status` `type` `search` |
| `POST` | `/api/v1/exams/admission` | 创建准入考试 | JSON：`title` `paper_id` `description` `duration` `passing_score` `status` `type` `scope_type` `scope_target_ids[]` `max_attempts` `start_time` `end_time` |
| `PUT` | `/api/v1/exams/admission/{exam_id}` | 更新准入考试 | 字段同创建接口，均可选 |
| `GET` | `/api/v1/exams/admission/{exam_id}` | 准入考试详情 | 返回考试基础信息和题目快照 |
| `POST` | `/api/v1/exams/admission/{exam_id}/submit` | 提交准入考试 | JSON：`answers` `start_time` |
| `GET` | `/api/v1/exams/admission/{exam_id}/result` | 获取当前用户准入考试结果 | 无 |
| `GET` | `/api/v1/exams/admission/{exam_id}/scores` | 准入考试成绩列表 | Query：`page` `size` |
| `GET` | `/api/v1/exams/admission/{exam_id}/records/analysis` | 准入考试分析报表 | 返回平铺成绩明细 |

说明：

- 创建、更新、成绩管理、分析接口要求管理员或教官
- `scope_type` 常见值：
  - `all`
  - `user`
  - `department`
  - `role`
- `scope_target_ids[]` 仅在 `scope_type != all` 时需要传值
- 响应中的 `scope` 为展示摘要；真实控制字段是 `scope_type` 和 `scope_target_ids`
- `paper_id` 必须指向已发布试卷
- 准入考试创建后不能再更换试卷
- 只有适用范围内的学员才能看到、进入并提交该准入考试
- 准入考试结果里的 `result` 常见值为 `pass` / `fail`

### 7.4 培训班内考试接口

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/exams` | 培训班内考试列表 | Query：`page` `size` `status` `type` `search` `training_id` `purpose` |
| `POST` | `/api/v1/exams` | 创建培训班内考试 | JSON：`title` `paper_id` `description` `duration` `passing_score` `status` `type` `purpose` `training_id` `max_attempts` `allow_makeup` `start_time` `end_time` |
| `PUT` | `/api/v1/exams/{exam_id}` | 更新培训班内考试 | 字段同创建接口，均可选 |
| `GET` | `/api/v1/exams/{exam_id}` | 培训班内考试详情 | 返回考试基础信息和题目快照 |
| `POST` | `/api/v1/exams/{exam_id}/submit` | 提交培训班内考试 | JSON：`answers` `start_time` |
| `GET` | `/api/v1/exams/{exam_id}/result` | 获取当前用户培训班考试结果 | 无 |
| `GET` | `/api/v1/exams/{exam_id}/scores` | 培训班考试成绩列表 | Query：`page` `size` |
| `GET` | `/api/v1/exams/{exam_id}/records/analysis` | 培训班考试分析报表 | 返回平铺成绩明细 |

说明：

- 培训班考试的参试范围由 `training_id` 决定，不存在 `scope`
- `paper_id` 必须指向已发布试卷
- 培训班考试创建后不能再更换试卷
- `purpose` 常见值：
  - `class_assessment`
  - `final_assessment`
  - `quiz`
  - `makeup`
- 创建、更新、成绩管理、分析接口要求管理员或教官

## 8. 培训模块

### 8.1 培训基地接口

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/training-bases` | 培训基地列表 | Query：`page` `size` `search` `department_id` |
| `GET` | `/api/v1/training-bases/{training_base_id}` | 培训基地详情 | 无 |
| `POST` | `/api/v1/training-bases` | 创建培训基地 | JSON：`name` `location` `department_id` `description` |
| `PUT` | `/api/v1/training-bases/{training_base_id}` | 更新培训基地 | 字段均可选 |
| `DELETE` | `/api/v1/training-bases/{training_base_id}` | 删除培训基地 | 仅管理员 |

说明：

- 培训基地当前支持可选 `department_id`
- 培训基地列表和详情已接入数据范围控制
- 培训基地被培训班引用时不可删除

### 8.2 培训班主接口

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/trainings` | 培训列表 | Query：`page` `size` `status` `type` `search` |
| `POST` | `/api/v1/trainings` | 创建培训班 | JSON：`name` `type` `status` `publish_status` `start_date` `end_date` `location` `department_id` `police_type_id` `training_base_id` `class_code` `instructor_id` `capacity` `description` `subjects[]` `enrollment_start_at` `enrollment_end_at` `admission_exam_id` `courses[]` |
| `GET` | `/api/v1/trainings/{training_id}` | 培训详情 | 返回课程、考试摘要、流程步骤、当前课次、权限标记 |
| `PUT` | `/api/v1/trainings/{training_id}` | 更新培训班 | 字段同创建接口，均可选；支持更新 `student_ids`、`roster_assignments` |
| `DELETE` | `/api/v1/trainings/{training_id}` | 删除培训班 | 仅管理员 |
| `POST` | `/api/v1/trainings/{training_id}/publish` | 发布培训班 | 可选 JSON：`skip_steps[]`；当前一般无需传 |
| `POST` | `/api/v1/trainings/{training_id}/lock` | 锁定名单 | 可选 JSON：`skip_steps[]`，可传 `["published"]` |
| `POST` | `/api/v1/trainings/{training_id}/start` | 手动开班 | 可选 JSON：`skip_steps[]`，可传 `["published","locked"]` |
| `POST` | `/api/v1/trainings/{training_id}/end` | 手动结班 | 管理员或班主任 |

培训详情常见返回摘要：

- `workflow_steps`
- `current_step_key`
- `current_session`
- `exam_sessions`
- `admission_exam_id`
- `admission_exam_title`
- `can_manage_all`
- `can_edit_training`
- `can_edit_courses`
- `can_review_enrollments`

说明：

- 培训班当前支持可选 `department_id`、`police_type_id`、`training_base_id`
- 选择培训基地时，服务层会优先使用基地地点，并在基地配置了部门时默认同步该部门
- 培训列表和详情已接入数据范围控制；如果角色范围不覆盖培训班归属的部门 / 警种，则不可见
- 培训班流程按 `发布招生 -> 锁定名单 -> 开班 -> 结班` 严格顺序执行
- 如果直接调用后续流程接口而未完成前置步骤，后端会拒绝；只有显式传入 `skip_steps[]` 才会自动补齐并锁定被跳过环节

### 8.3 培训课程与排课字段

`courses[]` 中每项常见字段：

```json
{
  "name": "课程名称",
  "instructor": "主讲教官名称（兼容旧字段）",
  "primary_instructor_id": 2,
  "assistant_instructor_ids": [3, 4],
  "hours": 4,
  "type": "theory",
  "schedules": [
    {
      "session_id": "course-1-2026-03-13-1",
      "date": "2026-03-13",
      "time_range": "09:00-10:40",
      "location": "教室 A",
      "status": "pending"
    }
  ]
}
```

课次状态常见值：

- `pending`：未开始
- `checkin_open`：签到中
- `checkin_closed`：课程进行中，签到窗口已结束
- `checkout_open`：签退中
- `completed`
- `skipped`
- `missed`

### 8.4 学员、报名、编组

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/trainings/{training_id}/students` | 学员列表 | Query：`page` `size`；仅管理员或班主任 |
| `POST` | `/api/v1/trainings/{training_id}/enroll` | 学员报名 | JSON：`note` `phone` `need_accommodation` |
| `GET` | `/api/v1/trainings/{training_id}/enrollments` | 报名列表 | Query：`page` `size`；管理员 / 班主任看全量，学员只看自己 |
| `PUT` | `/api/v1/trainings/{training_id}/enrollments/{eid}/approve` | 审批通过 | 管理员或班主任 |
| `PUT` | `/api/v1/trainings/{training_id}/enrollments/{eid}/reject` | 审批拒绝 | JSON：`note` |
| `PUT` | `/api/v1/trainings/{training_id}/roster` | 更新编组与班干部 | Body：`[{ enrollment_id, group_name, cadre_role }]` |

报名约束：

- 培训班必须已发布
- 名单未锁定
- 当前时间位于报名窗口内
- 如果培训班配置了 `admission_exam_id`，报名人必须先通过该准入考试

### 8.5 课次签到、签退、评课

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/trainings/{training_id}/checkin/records` | 签到记录 | Query：`date` `session_key`；管理员 / 班主任或当前课次授课教官看全量，其他学员只看自己 |
| `GET` | `/api/v1/trainings/{training_id}/attendance/summary` | 课次签到统计 | Query：`session_key` `date` |
| `POST` | `/api/v1/trainings/{training_id}/sessions/{session_key}/checkin/start` | 开始课次签到 | 管理员 / 班主任 / 当前课次主讲或带教教官 |
| `POST` | `/api/v1/trainings/{training_id}/sessions/{session_key}/checkin/end` | 结束课次签到 | 同上 |
| `POST` | `/api/v1/trainings/{training_id}/sessions/{session_key}/checkout/start` | 开始课次签退 | 同上 |
| `POST` | `/api/v1/trainings/{training_id}/sessions/{session_key}/checkout/end` | 结束课次签退 | 同上 |
| `POST` | `/api/v1/trainings/{training_id}/sessions/{session_key}/skip` | 跳过课次 | JSON：`reason` |
| `POST` | `/api/v1/trainings/{training_id}/checkin` | 签到 | JSON：`date` `time` `session_key` `user_id` `status` |
| `POST` | `/api/v1/trainings/{training_id}/checkout` | 签退 | JSON：`date` `time` `session_key` `user_id` |
| `POST` | `/api/v1/trainings/{training_id}/evaluation` | 评课 | JSON：`date` `session_key` `user_id` `score` `comment` |

说明：

- 系统会对已过截止时间但未完成的课次自动转为 `missed`
- 已 `missed` 的课次不能再开始签到，也不能再跳过
- `skip` 是跳过整个课次，不是跳过单个学员
- 结束签到后课次会进入 `checkin_closed`，此时课程仍视为“进行中”，只是签到窗口已结束

### 8.6 二维码签到与训历

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/trainings/{training_id}/checkin/qr` | 生成签到二维码 | Query：`session_key` `date` |
| `GET` | `/api/v1/trainings/checkin/qr/{token}` | 扫码签到信息 | 可匿名访问，返回二维码负载 |
| `POST` | `/api/v1/trainings/checkin/qr/{token}` | 扫码签到 | 需要登录 |
| `GET` | `/api/v1/trainings/{training_id}/histories` | 培训训历 | Query：`user_id`；管理员 / 班主任可查全量，学员只可查自己 |
| `GET` | `/api/v1/trainings/histories/me` | 我的训历 | 当前用户 |
| `GET` | `/api/v1/trainings/{training_id}/schedule` | 周计划 | 返回 `ScheduleItemResponse[]` |

### 8.7 培训导入接口

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/trainings/{training_id}/import/students` | 批量导入学员并自动开户 | `multipart/form-data`：`file` |
| `POST` | `/api/v1/trainings/{training_id}/import/instructors` | 批量导入教官 | `multipart/form-data`：`file` |
| `POST` | `/api/v1/trainings/{training_id}/import/schedule` | 批量导入课表 | `multipart/form-data`：`file` `replace_existing` |

导入返回的是汇总信息，常见字段包括：

- `total_rows`
- `success_rows`
- `created_count`
- `updated_count`
- `matched_count`
- `skipped_count`
- `skipped_rows`

说明：

- 学员导入、教官导入、课表导入当前都要求管理员或班主任
- 新建账号默认密码为 `Police@123456`

### 8.8 培训与资源绑定

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/trainings/{training_id}/resources` | 绑定培训资源 | JSON：`resource_id` `usage_type` `sort_order` |
| `GET` | `/api/v1/trainings/{training_id}/resources` | 培训资源列表 | 无 |
| `DELETE` | `/api/v1/trainings/{training_id}/resources/{resource_id}` | 解绑培训资源 | 无 |

## 9. 资源库模块

### 9.1 资源主接口

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/resources` | 资源列表 | Query：`page` `size` `search` `status` `content_type` `my_only` |
| `POST` | `/api/v1/resources` | 创建资源 | JSON：见下方 `ResourceCreate` 摘要 |
| `GET` | `/api/v1/resources/{resource_id}` | 资源详情 | 无 |
| `PUT` | `/api/v1/resources/{resource_id}` | 更新资源 | 字段同创建接口，均可选 |
| `POST` | `/api/v1/resources/{resource_id}/publish` | 发布资源 | 无 |
| `POST` | `/api/v1/resources/{resource_id}/offline` | 下线资源 | 无 |
| `DELETE` | `/api/v1/resources/{resource_id}` | 删除资源 | 返回删除结果对象 |

### 9.2 `ResourceCreate` 摘要

```json
{
  "title": "资源标题",
  "summary": "资源摘要",
  "content_type": "video",
  "source_type": "ugc",
  "visibility_type": "public",
  "owner_department_id": 1,
  "cover_media_file_id": 10,
  "tags": ["刑侦", "反诈"],
  "media_links": [
    {
      "media_file_id": 100,
      "media_role": "main",
      "sort_order": 0
    }
  ],
  "visibility_scopes": [1, 2]
}
```

## 10. 资源审核与推荐

### 10.1 审核工作流

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/resources/{resource_id}/submit` | 提交审核 | 需要 `SUBMIT_RESOURCE_REVIEW` 或全局资源权限 |
| `GET` | `/api/v1/reviews/tasks` | 我的审核任务 | Query：`status`，默认 `pending` |
| `POST` | `/api/v1/reviews/tasks/{task_id}/approve` | 审核通过 | JSON：`comment` |
| `POST` | `/api/v1/reviews/tasks/{task_id}/reject` | 审核驳回 | JSON：`comment` |
| `GET` | `/api/v1/reviews/workflows/{resource_id}` | 查看审核轨迹 | 无 |
| `GET` | `/api/v1/review-policies` | 审核策略列表 | 需要 `MANAGE_REVIEW_POLICY` 或全局资源权限 |
| `POST` | `/api/v1/review-policies` | 创建审核策略 | JSON：见下方摘要 |
| `PUT` | `/api/v1/review-policies/{policy_id}` | 更新审核策略 | 字段均可选 |

### 10.2 推荐流与行为埋点

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/resources/{resource_id}/events` | 记录资源行为事件 | JSON：`event_type` `watch_seconds` `context_json` |
| `GET` | `/api/v1/resources/recommendations/feed` | 推荐资源流 | Query：`page` `size`，`size` 范围 `1-100` |

## 11. 媒体文件模块

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/media/upload` | 上传文件 | `multipart/form-data`：`file` |
| `GET` | `/api/v1/media/files/{file_id}` | 获取文件直链或下载 | 无鉴权 |

## 12. 公告模块

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/notices` | 公告列表 | Query：`page` `size` `type` `training_id` |
| `POST` | `/api/v1/notices` | 创建公告 | JSON：`title` `content` `type` `training_id` |
| `PUT` | `/api/v1/notices/{notice_id}` | 更新公告 | JSON：`title` `content` |
| `DELETE` | `/api/v1/notices/{notice_id}` | 删除公告 | 无 |

## 13. 证书模块

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/certificates` | 证书列表 | Query：`page` `size` `user_id` `training_id` |
| `POST` | `/api/v1/certificates` | 签发证书 | JSON：`user_id` `training_id` `training_name` `score` `issue_date` `expire_date` |

## 14. 个人中心模块

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/profile` | 获取个人信息 | 无 |
| `PUT` | `/api/v1/profile` | 更新个人信息 | JSON：`nickname` `gender` `email` `phone` `avatar` |
| `GET` | `/api/v1/profile/study-stats` | 学习统计 | 无 |
| `GET` | `/api/v1/profile/exam-history` | 考试历史 | 无 |

## 15. 数据看板模块

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/report/kpi` | KPI 数据 | 无 |
| `GET` | `/api/v1/report/trend` | 月度趋势 | 无 |
| `GET` | `/api/v1/report/training-trend` | 近 6 月培训完成率趋势 | 无 |
| `GET` | `/api/v1/report/training-city-attendance` | 各市参训人数 | 无 |
| `GET` | `/api/v1/report/training-city-completion` | 各市培训完成率 | 无 |
| `GET` | `/api/v1/report/police-type-distribution` | 警种分布 | 无 |
| `GET` | `/api/v1/report/city-ranking` | 城市排名 | 无 |
| `GET` | `/api/v1/report/export` | 导出 Excel 报告 | 返回二进制流 |

## 16. AI 模块

当前 AI 能力已经统一改成任务流，不再使用同步生成接口。

统一任务状态：

- `pending`
- `processing`
- `completed`
- `confirmed`
- `failed`

统一任务流程：

- 填写信息
- 创建任务
- 后端模拟生成结果
- 查看任务
- 编辑题目 / 试卷草稿
- 确认写入题库 / 卷库

### 16.1 AI 智能出题任务

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/ai/question-tasks` | AI 智能出题任务列表 | Query：`page` `size` `status` |
| `POST` | `/api/v1/ai/question-tasks` | 创建 AI 智能出题任务 | JSON：`task_name` `topic` `source_text` `knowledge_points[]` `question_count` `question_types[]` `difficulty` `police_type_id` `score` `requirements` |
| `GET` | `/api/v1/ai/question-tasks/{task_id}` | AI 智能出题任务详情 | 无 |
| `PUT` | `/api/v1/ai/question-tasks/{task_id}/result` | 更新 AI 智能出题任务结果 | JSON：`task_name` `questions[]` |
| `POST` | `/api/v1/ai/question-tasks/{task_id}/confirm` | 确认 AI 智能出题任务 | 写入题库 |

### 16.2 AI 自动组卷任务

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/ai/paper-assembly-tasks` | AI 自动组卷任务列表 | Query：`page` `size` `status` |
| `POST` | `/api/v1/ai/paper-assembly-tasks` | 创建 AI 自动组卷任务 | JSON：`task_name` `paper_title` `paper_type` `description` `duration` `passing_score` `assembly_mode` `police_type_id` `knowledge_points[]` `exclude_question_ids[]` `type_configs[]` `requirements` |
| `GET` | `/api/v1/ai/paper-assembly-tasks/{task_id}` | AI 自动组卷任务详情 | 无 |
| `PUT` | `/api/v1/ai/paper-assembly-tasks/{task_id}/result` | 更新 AI 自动组卷任务结果 | JSON：`task_name` `paper_draft` |
| `POST` | `/api/v1/ai/paper-assembly-tasks/{task_id}/confirm` | 确认 AI 自动组卷任务 | 写入卷库 |

### 16.3 AI 自动生成试卷任务

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/ai/paper-generation-tasks` | AI 自动生成试卷任务列表 | Query：`page` `size` `status` |
| `POST` | `/api/v1/ai/paper-generation-tasks` | 创建 AI 自动生成试卷任务 | JSON：`task_name` `paper_title` `paper_type` `description` `duration` `passing_score` `topic` `source_text` `knowledge_points[]` `difficulty` `police_type_id` `type_configs[]` `requirements` |
| `GET` | `/api/v1/ai/paper-generation-tasks/{task_id}` | AI 自动生成试卷任务详情 | 无 |
| `PUT` | `/api/v1/ai/paper-generation-tasks/{task_id}/result` | 更新 AI 自动生成试卷任务结果 | JSON：`task_name` `paper_draft` |
| `POST` | `/api/v1/ai/paper-generation-tasks/{task_id}/confirm` | 确认 AI 自动生成试卷任务 | 写入题库和卷库 |

说明：

- AI 结果当前由后端模拟生成，不接真实模型
- 任务详情会返回请求快照、题目草稿或试卷草稿
- 只有 `completed` 状态的任务才允许编辑结果
- `confirm` 后任务会变成 `confirmed`

## 17. 人才库模块

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/talent` | 人才列表 | Query：`page` `size` `search` `tier` `department_id` |
| `GET` | `/api/v1/talent/stats` | 人才统计概览 | 无 |

## 18. 用户与系统管理模块

### 18.1 用户管理

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/users` | 用户列表 | Query：`page` `size` `role` `search` |
| `POST` | `/api/v1/users/import/police-base` | 全员底库导入 | `multipart/form-data`：`file` `default_role` |
| `GET` | `/api/v1/users/{user_id}` | 用户详情 | 无 |
| `POST` | `/api/v1/users` | 创建用户 | JSON：见对应 schema |
| `PUT` | `/api/v1/users/{user_id}` | 更新用户 | 字段均可选 |
| `PUT` | `/api/v1/users/{user_id}/roles` | 更新用户角色 | JSON：`role_ids[]` |
| `PUT` | `/api/v1/users/{user_id}/departments` | 更新用户所属单位 | JSON：`department_ids[]` |
| `PUT` | `/api/v1/users/{user_id}/police-types` | 更新用户警种 | JSON：`police_type_ids[]` |
| `PUT` | `/api/v1/users/{user_id}/password` | 重置密码 | JSON：`password` |
| `DELETE` | `/api/v1/users/{user_id}` | 删除用户 | 软删除，设置 `is_active=false` |

说明：

- 用户接口当前同时受“功能权限 + 数据范围”控制
- 数据范围以部门和警种为主；如果目标用户命中了当前操作者的任一部门或警种范围，即可被查看或操作
- 具有 `police_type` 数据范围的警种管理员，可查看本警种下的所有用户

### 18.2 角色管理

角色管理当前除了权限分配，还支持配置数据范围。常用接口包括：

- `POST /api/v1/roles` / `POST /api/v1/roles/create`
- `GET /api/v1/roles/list`
- `GET /api/v1/roles/{role_id}/detail`
- `PUT /api/v1/roles/{role_id}` / `POST /api/v1/roles/{role_id}/update`
- `DELETE /api/v1/roles/{role_id}` / `POST /api/v1/roles/{role_id}/delete`
- `POST /api/v1/roles/{role_id}/permissions`

角色 `data_scopes` 支持：

- `all`
- `department`
- `department_and_sub`
- `police_type`
- `self`

### 18.3 部门、权限、警种

系统管理接口保留 REST 风格和兼容旧前端的别名接口，建议以 Swagger 为准。当前主要能力包括：

- 部门：树结构、权限分配
- 权限：创建、更新、同步
- 警种：创建、更新、删除

## 19. 默认账号与初始化数据

首次执行 `python init_data.py` 后会创建以下示例账号：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `police2025` |
| 教官 | `instructor` | `teach2025` |
| 学员 | `student` | `learn2025` |

## 20. 当前实现注意事项

- 手机验证码登录接口尚未真正校验验证码。
- 准入考试和培训班考试已拆分为两套接口，不要再把培训班考试当成独立准入考试使用。
- 培训班考试不再有 `scope`，参试范围由 `training_id` 决定。
- 培训二维码签到依赖 Redis。
- 系统管理中的角色、部门、权限接口保留了双写法，是为了兼容已有前端实现。
