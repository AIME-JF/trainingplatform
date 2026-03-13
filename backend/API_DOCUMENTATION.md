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
- 业务失败时，项目内有一部分异常会通过响应体 `code` 表示，而不是完全依赖 HTTP 状态码

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

后端接口字段使用 `snake_case`。前端 `src/api/request.js` 会自动完成 `camelCase <-> snake_case` 转换。

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
| `POST` | `/api/v1/questions` | 创建题目 | JSON：`type` `content` `options` `answer` `explanation` `difficulty` `knowledge_point` `score` |
| `PUT` | `/api/v1/questions/{question_id}` | 更新题目 | 字段同创建接口，均可选 |
| `DELETE` | `/api/v1/questions/{question_id}` | 删除题目 | 无 |
| `POST` | `/api/v1/questions/batch` | 批量导入题目 | JSON：`questions[]` |

题型约定：

- `single`
- `multi`
- `judge`

## 7. 考试模块

### 7.1 考试主接口

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/exams` | 考试列表 | Query：`page` `size` `status` `type` `search` |
| `POST` | `/api/v1/exams` | 创建考试 | JSON：`title` `description` `duration` `total_score` `passing_score` `status` `type` `scope` `start_time` `end_time` `question_ids[]` |
| `GET` | `/api/v1/exams/{exam_id}` | 考试详情 | 返回考试基本信息和题目 |
| `POST` | `/api/v1/exams/{exam_id}/submit` | 提交考试 | JSON：`answers` `start_time` |
| `GET` | `/api/v1/exams/{exam_id}/result` | 获取当前用户考试结果 | 无 |
| `GET` | `/api/v1/exams/{exam_id}/scores` | 成绩列表 | Query：`page` `size` |
| `GET` | `/api/v1/exams/{exam_id}/records/analysis` | 获取考试分析报表 | 返回平铺成绩明细 |

说明：

- 当前后端未暴露更新考试接口，前端代码中的 `updateExam` 不是已落地能力

## 8. 培训模块

### 8.1 培训班主接口

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/trainings` | 培训列表 | Query：`page` `size` `status` `type` `search` |
| `POST` | `/api/v1/trainings` | 创建培训班 | JSON：`name` `type` `status` `start_date` `end_date` `location` `instructor_id` `capacity` `description` `subjects[]` `courses[]` |
| `GET` | `/api/v1/trainings/{training_id}` | 培训详情 | 返回课程安排、已报名人数等 |
| `PUT` | `/api/v1/trainings/{training_id}` | 更新培训班 | `courses` 调课仅管理员可改 |
| `DELETE` | `/api/v1/trainings/{training_id}` | 删除培训班 | 无 |
| `POST` | `/api/v1/trainings/{training_id}/start` | 手动开班 | 管理员或教官 |
| `POST` | `/api/v1/trainings/{training_id}/end` | 手动结班 | 管理员或教官 |

### 8.2 学员、计划、报名、签到

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/trainings/{training_id}/students` | 培训学员列表 | Query：`page` `size` |
| `GET` | `/api/v1/trainings/{training_id}/schedule` | 周计划 | 无 |
| `POST` | `/api/v1/trainings/{training_id}/enroll` | 学员报名 | JSON：`note` |
| `GET` | `/api/v1/trainings/{training_id}/enrollments` | 报名列表 | Query：`page` `size` |
| `PUT` | `/api/v1/trainings/{training_id}/enrollments/{eid}/approve` | 审批通过 | 无 |
| `PUT` | `/api/v1/trainings/{training_id}/enrollments/{eid}/reject` | 审批拒绝 | JSON：`note` |
| `GET` | `/api/v1/trainings/{training_id}/checkin/records` | 签到记录 | Query：`date` |
| `POST` | `/api/v1/trainings/{training_id}/checkin` | 签到 | JSON：`date` `time` `session_key` `user_id` |
| `GET` | `/api/v1/trainings/{training_id}/checkin/qr` | 生成签到二维码 | 返回二维码 token、签到 URL、过期时间 |

### 8.3 培训导入接口

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

- 学员导入：管理员或教官可用
- 教官导入、课表导入：仅管理员可用
- 新建账号默认密码为 `Police@123456`

### 8.4 培训与资源绑定

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

权限说明：

- 创建资源需要 `CREATE_RESOURCE` 或 `VIEW_RESOURCE_ALL`
- 详情、更新、发布、下线、删除会结合当前用户权限和资源归属做判断

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

取值说明：

- `content_type`：`video` `image` `document`
- `source_type`：当前默认 `ugc`
- `visibility_type`：`public`、按部门或按警种等可见域

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

`ReviewPolicyCreate` 摘要：

```json
{
  "name": "默认资源审核策略",
  "enabled": true,
  "scope_type": "global",
  "scope_department_id": null,
  "uploader_constraint": "all",
  "constraint_ref_id": null,
  "priority": 100,
  "stages": [
    {
      "stage_order": 1,
      "reviewer_type": "role",
      "reviewer_ref_id": 2,
      "min_approvals": 1,
      "allow_self_review": false
    }
  ]
}
```

### 10.2 推荐流与行为埋点

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/resources/{resource_id}/events` | 记录资源行为事件 | JSON：`event_type` `watch_seconds` `context_json` |
| `GET` | `/api/v1/resources/recommendations/feed` | 推荐资源流 | Query：`page` `size`，`size` 范围 `1-100` |

行为事件常见值：

- `impression`
- `click`
- `play`
- `complete`
- `like`
- `favorite`

推荐流返回核心结构：

```json
{
  "items": [
    {
      "resource_id": 123,
      "score": 0.91
    }
  ],
  "page": 1,
  "size": 10,
  "total": 50
}
```

## 11. 媒体文件模块

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/media/upload` | 上传文件 | `multipart/form-data`：`file` |
| `GET` | `/api/v1/media/files/{file_id}` | 获取文件直链或下载 | 无鉴权 |

上传返回：

```json
{
  "id": 1,
  "filename": "demo.mp4",
  "mime_type": "video/mp4",
  "size": 1024,
  "url": "http://..."
}
```

说明：

- 上传接口要求登录
- 单文件最大体积受 `MAX_UPLOAD_SIZE` 控制，默认 500MB
- 相同文件会按哈希秒传复用

## 12. 公告模块

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/notices` | 公告列表 | Query：`page` `size` `type` `training_id` |
| `POST` | `/api/v1/notices` | 创建公告 | JSON：`title` `content` `type` `training_id` |
| `PUT` | `/api/v1/notices/{notice_id}` | 更新公告 | JSON：`title` `content` |
| `DELETE` | `/api/v1/notices/{notice_id}` | 删除公告 | 无 |

`type` 取值：

- `system`
- `training`

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

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/ai/generate-questions` | AI 智能组卷 | JSON：`topic` `count` `difficulty` `types[]` |
| `POST` | `/api/v1/ai/generate-lesson-plan` | AI 教案生成 | JSON：`title` `subject` `duration` `objectives[]` `level` |

返回摘要：

- 组卷：`questions[]` `total`
- 教案：`title` `content` `outline[]`

说明：

- AI 调用失败时，系统会记录日志并返回降级结果，不影响其他业务接口

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
| `POST` | `/api/v1/users` | 创建用户 | JSON：见下方摘要 |
| `PUT` | `/api/v1/users/{user_id}` | 更新用户 | 字段均可选 |
| `PUT` | `/api/v1/users/{user_id}/roles` | 更新用户角色 | JSON：`role_ids[]` |
| `PUT` | `/api/v1/users/{user_id}/departments` | 更新用户所属单位 | JSON：`department_ids[]` |
| `PUT` | `/api/v1/users/{user_id}/police-types` | 更新用户警种 | JSON：`police_type_ids[]` |
| `PUT` | `/api/v1/users/{user_id}/password` | 重置密码 | JSON：`password` |
| `DELETE` | `/api/v1/users/{user_id}` | 删除用户 | 软删除，设置 `is_active=false` |

`UserCreate` 摘要：

```json
{
  "username": "newuser",
  "password": "123456",
  "nickname": "张三",
  "gender": "男",
  "email": "a@example.com",
  "phone": "13800000000",
  "police_id": "GX-001",
  "avatar": "",
  "join_date": "2025-01-01",
  "level": "中级",
  "instructor_title": null,
  "instructor_level": null,
  "instructor_specialties": [],
  "instructor_qualification": [],
  "instructor_certificates": [],
  "instructor_intro": null,
  "instructor_rating": 0,
  "instructor_course_count": 0,
  "instructor_student_count": 0,
  "instructor_review_count": 0,
  "role_ids": [1],
  "department_ids": [1],
  "police_type_ids": [1]
}
```

说明：

- `admin` 用户的角色不可修改
- 底库导入会自动创建缺失的部门和警种，并为新账号设置默认密码 `Police@123456`

### 18.2 角色管理

同一能力同时保留 REST 风格接口和兼容旧前端的别名接口。

| Method | Path | 说明 |
| --- | --- | --- |
| `POST` | `/api/v1/roles` | 创建角色 |
| `POST` | `/api/v1/roles/create` | 创建角色别名 |
| `GET` | `/api/v1/roles/list` | 角色列表，支持 `page` `size` `name` `is_active` `order` |
| `GET` | `/api/v1/roles/{role_id}/detail` | 角色详情 |
| `PUT` | `/api/v1/roles/{role_id}` | 更新角色 |
| `POST` | `/api/v1/roles/{role_id}/update` | 更新角色别名 |
| `DELETE` | `/api/v1/roles/{role_id}` | 删除角色 |
| `POST` | `/api/v1/roles/{role_id}/delete` | 删除角色别名 |
| `POST` | `/api/v1/roles/{role_id}/permissions` | 更新角色权限 |

请求摘要：

- 创建角色：`code` `name` `description` `permission_ids[]`
- 更新角色：`name` `description` `is_active`
- 更新角色权限：`permission_ids[]`

约束：

- `admin` 角色不可编辑、不可删除、不可改权限

### 18.3 部门管理

| Method | Path | 说明 |
| --- | --- | --- |
| `POST` | `/api/v1/departments` | 创建部门 |
| `POST` | `/api/v1/departments/create` | 创建部门别名 |
| `GET` | `/api/v1/departments/list` | 部门列表，支持 `page` `size` `parent_id` |
| `GET` | `/api/v1/departments/tree` | 部门树 |
| `GET` | `/api/v1/departments/{department_id}/detail` | 部门详情 |
| `PUT` | `/api/v1/departments/{department_id}` | 更新部门 |
| `POST` | `/api/v1/departments/{department_id}/update` | 更新部门别名 |
| `DELETE` | `/api/v1/departments/{department_id}` | 删除部门 |
| `POST` | `/api/v1/departments/{department_id}/delete` | 删除部门别名 |
| `POST` | `/api/v1/departments/{department_id}/permissions` | 更新部门权限 |

请求摘要：

- 创建部门：`name` `code` `parent_id` `inherit_sub_permissions` `description` `permission_ids[]`
- 更新部门：`name` `parent_id` `inherit_sub_permissions` `description` `is_active`
- 更新部门权限：`permission_ids[]`

### 18.4 权限管理

| Method | Path | 说明 |
| --- | --- | --- |
| `POST` | `/api/v1/permissions` | 创建权限 |
| `POST` | `/api/v1/permissions/create` | 创建权限别名 |
| `GET` | `/api/v1/permissions/list` | 权限列表，支持 `page` `size` |
| `GET` | `/api/v1/permissions/{permission_id}/detail` | 权限详情 |
| `PUT` | `/api/v1/permissions/{permission_id}` | 更新权限 |
| `POST` | `/api/v1/permissions/{permission_id}/update` | 更新权限别名 |
| `DELETE` | `/api/v1/permissions/{permission_id}` | 删除权限 |
| `POST` | `/api/v1/permissions/{permission_id}/delete` | 删除权限别名 |
| `POST` | `/api/v1/permissions/sync` | 从当前 FastAPI 路由同步权限 |

请求摘要：

- 创建权限：`path` `code` `group` `description`
- 更新权限：`path` `group` `description` `is_active`

权限分组说明：

- `group` 为空时会根据路由路径自动推断
- 未命中规则时默认归到 `SYSTEM`

### 18.5 警种管理

| Method | Path | 说明 | 请求要点 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/police-types` | 警种列表 | Query：`page` `size` `name` `is_active` |
| `POST` | `/api/v1/police-types` | 创建警种 | JSON：`name` `code` `description` |
| `GET` | `/api/v1/police-types/{police_type_id}` | 警种详情 | 无 |
| `PUT` | `/api/v1/police-types/{police_type_id}` | 更新警种 | JSON：`name` `description` `is_active` |
| `DELETE` | `/api/v1/police-types/{police_type_id}` | 删除警种 | 无 |

## 19. 默认账号与初始化数据

首次执行 `python init_data.py` 后会创建以下示例账号：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `police2025` |
| 教官 | `instructor` | `teach2025` |
| 学员 | `student` | `learn2025` |

同时会初始化：

- 根部门 `ROOT`
- 多个基础警种
- 默认角色与权限

## 20. 当前实现注意事项

- 手机验证码登录接口尚未真正校验验证码。
- `GET /api/v1/media/files/{file_id}` 和 `GET /api/v1/report/export` 是本项目最主要的两个非标准响应接口。
- 系统管理中的角色、部门、权限接口保留了双写法，是为了兼容已有前端实现。
- 资源、审核、推荐、权限分组的细节较多，若要调试具体字段，建议直接查看 Swagger 或对应 `app/schemas/*.py`。
