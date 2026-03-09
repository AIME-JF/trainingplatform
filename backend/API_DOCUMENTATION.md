# 警务训练平台后端接口文档

> 基于当前后端代码（FastAPI `app/views/*.py`）生成。
> 服务默认地址：`http://127.0.0.1:8001`
> API 前缀：`/api/v1`

---

## 1. 通用说明

### 1.1 统一响应格式

所有业务接口统一返回：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {}
}
```

- `code`：业务状态码（200/400/401/404/500 等）
- `message`：业务消息
- `data`：业务数据

> 项目启用了统一异常处理，很多异常场景 HTTP 状态可能仍为 200，请以 `code` 判断业务是否成功。

### 1.2 认证方式

- 登录后获取 `access_token`
- 受保护接口在请求头携带：

```http
Authorization: Bearer <access_token>
```

### 1.3 分页约定

列表接口通常使用以下参数：

- `page`：页码，默认 `1`
- `size`：每页条数，默认 `10`
- `size=-1`：返回全部数据

分页返回结构：

```json
{
  "page": 1,
  "size": 10,
  "total": 100,
  "items": []
}
```

### 1.4 文档地址

- OpenAPI JSON：`/api/v1/openapi.json`
- Swagger：`/api/v1/docs`
- ReDoc：`/api/v1/redoc`

---

## 2. 公共接口

### 2.1 根路径

- **Method**: `GET`
- **URL**: `/`
- **Auth**: 否
- **说明**: 返回系统名称、版本、文档地址

### 2.2 健康检查

- **Method**: `GET`
- **URL**: `/health`
- **Auth**: 否
- **说明**: 服务健康状态检查

---

## 3. 认证模块（`/api/v1/auth`）

### 3.1 账号密码登录

- **Method**: `POST`
- **URL**: `/api/v1/auth/login`
- **Auth**: 否
- **Body(JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

- **data 返回**：`LoginResponse`

| 字段 | 类型 | 说明 |
|---|---|---|
| access_token | string | JWT token |
| token_type | string | 固定 `bearer` |
| user | object | 当前用户信息（含角色/部门） |

### 3.2 手机验证码登录

- **Method**: `POST`
- **URL**: `/api/v1/auth/login/phone`
- **Auth**: 否
- **参数（Query）**:

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| phone | string | 是 | 手机号 |
| code | string | 是 | 验证码 |

### 3.3 获取当前用户

- **Method**: `GET`
- **URL**: `/api/v1/auth/me`
- **Auth**: 是
- **说明**: 返回当前登录用户详情

---

## 4. 工作台模块（`/api/v1/dashboard`）

### 4.1 获取工作台数据

- **Method**: `GET`
- **URL**: `/api/v1/dashboard`
- **Auth**: 是
- **参数（Query）**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---:|---|---|
| role | string | 否 | `student` | 角色视角：admin/instructor/student |

- **data 返回**：

| 字段 | 类型 | 说明 |
|---|---|---|
| stats | object | 统计数据 |
| recent_courses | array | 最近课程 |
| recent_exams | array | 最近考试 |
| recent_trainings | array | 最近培训 |
| announcements | array | 公告 |

---

## 5. 课程模块（`/api/v1/courses`）

### 5.1 课程列表

- **Method**: `GET`
- **URL**: `/api/v1/courses`
- **Auth**: 是
- **参数（Query）**:

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| page | int | 否 | 页码，默认 1 |
| size | int | 否 | 每页数量，默认 10，`-1` 为全部 |
| search | string | 否 | 搜索关键词 |
| category | string | 否 | 课程分类 |
| sort | string | 否 | 排序字段 |

### 5.2 创建课程

- **Method**: `POST`
- **URL**: `/api/v1/courses`
- **Auth**: 是
- **Body(JSON)**: `CourseCreate`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| title | string | 是 | 课程标题 |
| category | string | 是 | 课程分类 |
| file_type | string | 否 | 文件类型，默认 `video` |
| description | string | 否 | 描述 |
| instructor_id | int | 否 | 教官ID |
| duration | int | 否 | 总时长(分钟) |
| difficulty | int | 否 | 难度 1-5 |
| is_required | bool | 否 | 是否必修 |
| cover_color | string | 否 | 封面色 |
| tags | string[] | 否 | 标签 |
| chapters | ChapterCreate[] | 否 | 章节列表 |

### 5.3 当前用户学习进度

- **Method**: `GET`
- **URL**: `/api/v1/courses/progress`
- **Auth**: 是

### 5.4 课程详情

- **Method**: `GET`
- **URL**: `/api/v1/courses/{course_id}`
- **Auth**: 是

### 5.5 更新课程

- **Method**: `PUT`
- **URL**: `/api/v1/courses/{course_id}`
- **Auth**: 是
- **Body(JSON)**: `CourseUpdate`（字段均可选）

### 5.6 更新章节进度

- **Method**: `PUT`
- **URL**: `/api/v1/courses/{course_id}/chapters/{chapter_id}/progress`
- **Auth**: 是
- **Body(JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| progress | int | 是 | 0-100 |

---

## 6. 题库模块（`/api/v1/questions`）

### 6.1 题目列表

- **Method**: `GET`
- **URL**: `/api/v1/questions`
- **Auth**: 是
- **参数（Query）**:

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| page | int | 否 | 页码 |
| size | int | 否 | 每页条数，`-1` 全部 |
| search | string | 否 | 关键词 |
| type | string | 否 | single/multi/judge |
| difficulty | int | 否 | 难度 |
| knowledge_point | string | 否 | 知识点 |

### 6.2 创建题目

- **Method**: `POST`
- **URL**: `/api/v1/questions`
- **Auth**: 是
- **Body(JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| type | string | 是 | 题型：single/multi/judge |
| content | string | 是 | 题干 |
| options | object[] | 否 | 选项（如 `[{key,text}]`） |
| answer | any | 是 | 答案 |
| explanation | string | 否 | 解析 |
| difficulty | int | 否 | 1-5 |
| knowledge_point | string | 否 | 知识点 |
| score | int | 否 | 分值 |

### 6.3 更新题目

- **Method**: `PUT`
- **URL**: `/api/v1/questions/{question_id}`
- **Auth**: 是
- **Body(JSON)**: `QuestionUpdate`（字段可选）

### 6.4 删除题目

- **Method**: `DELETE`
- **URL**: `/api/v1/questions/{question_id}`
- **Auth**: 是

### 6.5 批量导入题目

- **Method**: `POST`
- **URL**: `/api/v1/questions/batch`
- **Auth**: 是
- **Body(JSON)**:

```json
{
  "questions": [
    {
      "type": "single",
      "content": "...",
      "options": [{"key": "A", "text": "..."}],
      "answer": "A",
      "difficulty": 3,
      "score": 2
    }
  ]
}
```

---

## 7. 考试模块（`/api/v1/exams`）

### 7.1 考试列表

- **Method**: `GET`
- **URL**: `/api/v1/exams`
- **Auth**: 是
- **参数（Query）**:

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| page | int | 否 | 页码 |
| size | int | 否 | 每页条数，`-1` 全部 |
| status | string | 否 | 考试状态 |
| type | string | 否 | formal/quiz |
| search | string | 否 | 关键词 |

### 7.2 创建考试

- **Method**: `POST`
- **URL**: `/api/v1/exams`
- **Auth**: 是
- **Body(JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| title | string | 是 | 考试标题 |
| description | string | 否 | 描述 |
| duration | int | 否 | 时长(分钟) |
| total_score | int | 否 | 总分 |
| passing_score | int | 否 | 及格分 |
| status | string | 否 | 状态 |
| type | string | 否 | formal/quiz |
| scope | string | 否 | 范围 |
| start_time | datetime | 否 | 开始时间 |
| end_time | datetime | 否 | 结束时间 |
| question_ids | int[] | 否 | 题目ID列表 |

### 7.3 考试详情

- **Method**: `GET`
- **URL**: `/api/v1/exams/{exam_id}`
- **Auth**: 是
- **说明**: 返回考试基础信息 + 题目列表

### 7.4 提交考试

- **Method**: `POST`
- **URL**: `/api/v1/exams/{exam_id}/submit`
- **Auth**: 是
- **Body(JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| answers | object | 是 | 作答映射 `{questionId: answer}` |
| start_time | datetime | 否 | 开考时间 |

### 7.5 获取考试结果

- **Method**: `GET`
- **URL**: `/api/v1/exams/{exam_id}/result`
- **Auth**: 是

### 7.6 成绩管理

- **Method**: `GET`
- **URL**: `/api/v1/exams/{exam_id}/scores`
- **Auth**: 是
- **参数（Query）**: `page`, `size`

---

## 8. 培训模块（`/api/v1/trainings`）

### 8.1 培训列表

- **Method**: `GET`
- **URL**: `/api/v1/trainings`
- **Auth**: 是
- **参数（Query）**: `page`, `size`, `status`, `type`, `search`

### 8.2 创建培训班

- **Method**: `POST`
- **URL**: `/api/v1/trainings`
- **Auth**: 是
- **Body(JSON)**: `TrainingCreate`

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| name | string | 是 | 培训名称 |
| type | string | 是 | basic/special/promotion/online |
| status | string | 否 | upcoming 等 |
| start_date | date | 否 | 开始日期 |
| end_date | date | 否 | 结束日期 |
| location | string | 否 | 地点 |
| instructor_id | int | 否 | 教官ID |
| capacity | int | 否 | 容量 |
| description | string | 否 | 描述 |
| subjects | string[] | 否 | 科目标签 |
| courses | TrainingCourseCreate[] | 否 | 课程安排 |

### 8.3 培训详情

- **Method**: `GET`
- **URL**: `/api/v1/trainings/{training_id}`
- **Auth**: 是

### 8.4 更新培训班

- **Method**: `PUT`
- **URL**: `/api/v1/trainings/{training_id}`
- **Auth**: 是
- **Body(JSON)**: `TrainingUpdate`（字段可选）

### 8.5 删除培训班

- **Method**: `DELETE`
- **URL**: `/api/v1/trainings/{training_id}`
- **Auth**: 是

### 8.6 学员列表

- **Method**: `GET`
- **URL**: `/api/v1/trainings/{training_id}/students`
- **Auth**: 是
- **参数（Query）**: `page`, `size`

### 8.7 周计划

- **Method**: `GET`
- **URL**: `/api/v1/trainings/{training_id}/schedule`
- **Auth**: 是

### 8.8 学员报名

- **Method**: `POST`
- **URL**: `/api/v1/trainings/{training_id}/enroll`
- **Auth**: 是
- **Body(JSON)**（可空对象）:

```json
{
  "note": "报名备注（可选）"
}
```

### 8.9 报名列表

- **Method**: `GET`
- **URL**: `/api/v1/trainings/{training_id}/enrollments`
- **Auth**: 是
- **参数（Query）**: `page`, `size`

### 8.10 审批通过

- **Method**: `PUT`
- **URL**: `/api/v1/trainings/{training_id}/enrollments/{eid}/approve`
- **Auth**: 是

### 8.11 审批拒绝

- **Method**: `PUT`
- **URL**: `/api/v1/trainings/{training_id}/enrollments/{eid}/reject`
- **Auth**: 是
- **Body(JSON)**:

```json
{
  "note": "拒绝原因（可选）"
}
```

### 8.12 签到记录

- **Method**: `GET`
- **URL**: `/api/v1/trainings/{training_id}/checkin/records`
- **Auth**: 是
- **参数（Query）**:

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| date | date | 否 | 过滤某天签到记录 |

### 8.13 签到

- **Method**: `POST`
- **URL**: `/api/v1/trainings/{training_id}/checkin`
- **Auth**: 是
- **Body(JSON)**（可空对象）:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| date | date | 否 | 签到日期（默认当天） |
| time | string | 否 | 签到时间，格式 HH:MM（默认当前时间） |

### 8.14 生成签到二维码

- **Method**: `GET`
- **URL**: `/api/v1/trainings/{training_id}/checkin/qr`
- **Auth**: 是
- **data 返回**:

| 字段 | 类型 | 说明 |
|---|---|---|
| training_id | int | 培训ID |
| token | string | 二维码 token |
| url | string | 移动端签到路径 |
| expire_at | string | 过期时间 |

---

## 9. 资源中心模块（`/api/v1/resources` + 审核/推荐扩展）

### 9.1 资源列表

- **Method**: `GET`
- **URL**: `/api/v1/resources`
- **Auth**: 是
- **参数（Query）**: `page`, `size`, `search`, `status`, `content_type`, `my_only`

### 9.2 创建资源

- **Method**: `POST`
- **URL**: `/api/v1/resources`
- **Auth**: 是
- **Body(JSON)**: `ResourceCreate`
- **说明**:
  - `content_type` 支持 `video` / `image_text` / `document`
  - `image_text` 表示图片类资源（jpg/jpeg/png/webp），文字说明通过 `summary` 提交
  - 一个资源可关联多个 `media_links` 文件，后端会按 `content_type` 严格校验扩展名

### 9.3 资源详情

- **Method**: `GET`
- **URL**: `/api/v1/resources/{resource_id}`
- **Auth**: 是

### 9.4 更新资源

- **Method**: `PUT`
- **URL**: `/api/v1/resources/{resource_id}`
- **Auth**: 是
- **Body(JSON)**: `ResourceUpdate`

### 9.5 发布资源

- **Method**: `POST`
- **URL**: `/api/v1/resources/{resource_id}/publish`
- **Auth**: 是

### 9.6 下线资源

- **Method**: `POST`
- **URL**: `/api/v1/resources/{resource_id}/offline`
- **Auth**: 是

### 9.7 提交审核

- **Method**: `POST`
- **URL**: `/api/v1/resources/{resource_id}/submit`
- **Auth**: 是

### 9.8 我的审核任务

- **Method**: `GET`
- **URL**: `/api/v1/reviews/tasks`
- **Auth**: 是
- **参数（Query）**: `status`

### 9.9 审核通过

- **Method**: `POST`
- **URL**: `/api/v1/reviews/tasks/{task_id}/approve`
- **Auth**: 是
- **Body(JSON)**: `ReviewTaskActionRequest`

### 9.10 审核驳回

- **Method**: `POST`
- **URL**: `/api/v1/reviews/tasks/{task_id}/reject`
- **Auth**: 是
- **Body(JSON)**: `ReviewTaskActionRequest`

### 9.11 审核轨迹

- **Method**: `GET`
- **URL**: `/api/v1/reviews/workflows/{resource_id}`
- **Auth**: 是

### 9.12 审核策略列表

- **Method**: `GET`
- **URL**: `/api/v1/review-policies`
- **Auth**: 是

### 9.13 创建审核策略

- **Method**: `POST`
- **URL**: `/api/v1/review-policies`
- **Auth**: 是
- **Body(JSON)**: `ReviewPolicyCreate`

### 9.14 更新审核策略

- **Method**: `PUT`
- **URL**: `/api/v1/review-policies/{policy_id}`
- **Auth**: 是
- **Body(JSON)**: `ReviewPolicyUpdate`

### 9.15 推荐流

- **Method**: `GET`
- **URL**: `/api/v1/resources/recommendations/feed`
- **Auth**: 是
- **参数（Query）**: `page`, `size`
- **说明**: 推荐接口返回资源流数据；前端当前推荐页按“文件名 + 下载按钮”展示，不在推荐页内直接预览媒体

### 9.16 行为埋点

- **Method**: `POST`
- **URL**: `/api/v1/resources/{resource_id}/events`
- **Auth**: 是
- **Body(JSON)**: `ResourceBehaviorEventCreate`（`event_type`: impression/click/play/complete）

### 9.17 课程资源绑定

- **Method**: `POST`
- **URL**: `/api/v1/courses/{course_id}/resources`
- **Auth**: 是
- **Body(JSON)**: `CourseResourceBindRequest`

### 9.18 课程资源列表

- **Method**: `GET`
- **URL**: `/api/v1/courses/{course_id}/resources`
- **Auth**: 是

### 9.19 课程资源解绑

- **Method**: `DELETE`
- **URL**: `/api/v1/courses/{course_id}/resources/{resource_id}`
- **Auth**: 是

### 9.20 培训资源绑定

- **Method**: `POST`
- **URL**: `/api/v1/trainings/{training_id}/resources`
- **Auth**: 是
- **Body(JSON)**: `TrainingResourceBindRequest`

### 9.21 培训资源列表

- **Method**: `GET`
- **URL**: `/api/v1/trainings/{training_id}/resources`
- **Auth**: 是

### 9.22 培训资源解绑

- **Method**: `DELETE`
- **URL**: `/api/v1/trainings/{training_id}/resources/{resource_id}`
- **Auth**: 是

---

## 10. 教官信息（通过用户接口）

> 教官专用接口 `/api/v1/instructors*` 已下线，请改用用户接口按角色筛选。

### 10.1 教官用户列表

- **Method**: `GET`
- **URL**: `/api/v1/users?role=instructor`
- **Auth**: 是
- **参数（Query）**: `page`, `size`, `search`, `role`

### 10.2 教官用户详情

- **Method**: `GET`
- **URL**: `/api/v1/users/{user_id}`
- **Auth**: 是

### 10.3 创建/更新教官信息

- **Method**: `POST` / `PUT`
- **URL**: `/api/v1/users` / `/api/v1/users/{user_id}`
- **Auth**: 是
- **教官扩展字段（请求/响应）**:

| 字段 | 类型 | 说明 |
|---|---|---|
| instructor_title | string | 教官职称 |
| instructor_level | string | 教官等级 |
| instructor_specialties | string[] | 教官专长 |
| instructor_qualification | string[] | 教官资质 |
| instructor_certificates | object[] | 教官证书列表 |
| instructor_intro | string | 教官简介 |
| instructor_rating | float | 教官评分 |
| instructor_course_count | int | 教官课程数 |
| instructor_student_count | int | 教官学员数 |
| instructor_review_count | int | 教官评价数 |

---

## 11. 证书模块（`/api/v1/certificates`）

### 11.1 证书列表

- **Method**: `GET`
- **URL**: `/api/v1/certificates`
- **Auth**: 是
- **参数（Query）**: `page`, `size`, `user_id`, `training_id`

### 11.2 签发证书

- **Method**: `POST`
- **URL**: `/api/v1/certificates`
- **Auth**: 是
- **Body(JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| user_id | int | 是 | 用户ID |
| training_id | int | 否 | 培训班ID |
| training_name | string | 否 | 培训名称 |
| score | float | 否 | 成绩 |
| issue_date | date | 否 | 发证日期 |
| expire_date | date | 否 | 失效日期 |

---

## 12. 个人中心模块（`/api/v1/profile`）

### 12.1 个人信息

- **Method**: `GET`
- **URL**: `/api/v1/profile`
- **Auth**: 是

### 12.2 更新个人信息

- **Method**: `PUT`
- **URL**: `/api/v1/profile`
- **Auth**: 是
- **Body(JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| nickname | string | 否 | 昵称 |
| gender | string | 否 | 性别 |
| email | string | 否 | 邮箱 |
| phone | string | 否 | 手机 |
| avatar | string | 否 | 头像 |

### 12.3 学习统计

- **Method**: `GET`
- **URL**: `/api/v1/profile/study-stats`
- **Auth**: 是

### 12.4 考试历史

- **Method**: `GET`
- **URL**: `/api/v1/profile/exam-history`
- **Auth**: 是

---

## 13. 数据看板模块（`/api/v1/report`）

### 13.1 KPI 数据

- **Method**: `GET`
- **URL**: `/api/v1/report/kpi`
- **Auth**: 是

### 13.2 月度趋势

- **Method**: `GET`
- **URL**: `/api/v1/report/trend`
- **Auth**: 是

### 13.3 警种分布

- **Method**: `GET`
- **URL**: `/api/v1/report/police-type-distribution`
- **Auth**: 是

### 13.4 城市排名

- **Method**: `GET`
- **URL**: `/api/v1/report/city-ranking`
- **Auth**: 是

---

## 14. AI 模块（`/api/v1/ai`）

### 14.1 AI 智能组卷

- **Method**: `POST`
- **URL**: `/api/v1/ai/generate-questions`
- **Auth**: 是
- **Body(JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| topic | string | 是 | 主题 |
| count | int | 否 | 题目数量（默认10） |
| difficulty | int | 否 | 难度1-5（默认3） |
| types | string[] | 否 | 题型列表 |

- **data 返回**:

| 字段 | 类型 | 说明 |
|---|---|---|
| questions | array | 生成题目列表 |
| total | int | 题目数量 |

### 14.2 AI 教案生成

- **Method**: `POST`
- **URL**: `/api/v1/ai/generate-lesson-plan`
- **Auth**: 是
- **Body(JSON)**:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| title | string | 是 | 教案标题 |
| subject | string | 是 | 科目 |
| duration | int | 否 | 时长（分钟） |
| objectives | string[] | 否 | 教学目标 |
| level | string | 否 | 学员等级 |

- **data 返回**:

| 字段 | 类型 | 说明 |
|---|---|---|
| title | string | 教案标题 |
| content | string | 教案正文 |
| outline | array | 教案大纲 |

> 若外部大模型鉴权失败，系统会记录错误并返回降级结果（如空题目/空教案），不影响其他模块接口。

---

## 15. 人才库模块（`/api/v1/talent`）

### 15.1 人才列表

- **Method**: `GET`
- **URL**: `/api/v1/talent`
- **Auth**: 是
- **参数（Query）**: `page`, `size`, `search`, `tier`, `unit`

### 15.2 统计概览

- **Method**: `GET`
- **URL**: `/api/v1/talent/stats`
- **Auth**: 是

---

## 16. 常见数据结构摘要

### 16.1 `UserResponse`（登录与用户接口常见）

| 字段 | 说明 |
|---|---|
| id / username / nickname | 用户基础信息 |
| gender / email / phone | 联系信息 |
| police_id / unit / police_type | 警务属性 |
| avatar / join_date / level | 个人资料 |
| study_hours / exam_count / avg_score | 学习统计 |
| instructor_* | 教官扩展信息（职称、等级、专长、资质、证书、简介、评分与统计） |
| roles | 角色列表 |
| departments | 部门列表 |

### 16.2 `EnrollmentResponse`（培训报名相关）

| 字段 | 说明 |
|---|---|
| id / training_id / user_id | 主键关系 |
| user_name / user_nickname | 用户信息 |
| police_id / unit | 警务信息 |
| status | pending/approved/rejected |
| note | 报名备注或拒绝原因 |
| enroll_time | 报名时间 |

### 16.3 `ExamRecordResponse`（考试结果相关）

| 字段 | 说明 |
|---|---|
| exam_id / exam_title | 考试信息 |
| user_id / user_name | 参考人信息 |
| score / result / grade | 成绩信息 |
| correct_count / wrong_count | 对错统计 |
| wrong_questions | 错题列表 |
| dimension_scores | 维度得分 |

---

## 17. 调用示例

### 17.1 登录并调用受保护接口

```bash
# 1) 登录
curl -X POST "http://127.0.0.1:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"police2025"}'

# 2) 使用 access_token 访问课程列表
curl "http://127.0.0.1:8001/api/v1/courses?page=1&size=10" \
  -H "Authorization: Bearer <access_token>"
```

### 17.2 创建培训班

```bash
curl -X POST "http://127.0.0.1:8001/api/v1/trainings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "name":"春季警务实战培训",
    "type":"special",
    "status":"upcoming",
    "capacity":60,
    "subjects":["执法规范","应急处突"]
  }'
```

---

## 18. 版本信息

- 文档生成依据：当前代码实现
- 应用版本：`1.0.0`
- 默认端口：`8001`
- API 前缀：`/api/v1`
