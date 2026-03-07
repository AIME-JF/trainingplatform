# 警务训练平台后端（FastAPI）

> 当前文档基于 `backend/` 实际代码结构与已注册路由整理（统一在 `app/views/*.py`，无 admin/app 拆分）。

---

## 1. 项目简介

本项目是“警务训练平台”的后端服务，提供：

- 认证与用户信息获取
- 课程与学习进度管理
- 题库与考试管理（出卷、交卷、成绩）
- 培训班管理（报名、审批、签到、二维码）
- 教官信息（基于用户角色）与证书管理
- 个人中心、数据看板、人才库
- AI 能力（智能组卷、教案生成）

后端采用 FastAPI + SQLAlchemy + PostgreSQL，支持 Alembic 迁移与 Redis。

---

## 2. 技术栈

- **Web 框架**: FastAPI
- **ORM**: SQLAlchemy 2.x
- **数据库**: PostgreSQL
- **迁移**: Alembic
- **缓存**: Redis
- **鉴权**: JWT（python-jose）
- **密码哈希**: passlib[bcrypt]
- **配置管理**: pydantic-settings + dotenv
- **日志**: Loguru
- **AI SDK**: OpenAI 兼容客户端（用于 DeepSeek 接口）

依赖见：`backend/requirements.txt`

---

## 3. 核心特性

### 3.1 统一响应结构

系统采用统一响应体：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {}
}
```

> 注意：全局异常处理会将异常也返回为 HTTP 200，但 `code` 为业务错误码（如 400/401/404/500）。

### 3.2 统一鉴权方式

- 认证接口：`/api/v1/auth/login`
- 受保护接口：`Authorization: Bearer <token>`
- token 过期配置：`ACCESS_TOKEN_EXPIRE_MINUTES`（默认 30 天）

### 3.3 自动迁移与初始化

启动时支持自动检查并执行迁移（`AUTO_MIGRATE_ON_STARTUP=True`）。

`main.py` 会执行：

1. `init_data.main()`（初始化种子数据）
2. 启动 uvicorn（默认 `0.0.0.0:8001`）

---

## 4. 目录结构

```text
backend/
├── app/
│   ├── __init__.py                 # FastAPI 应用创建、路由注册、startup/shutdown
│   ├── controllers/                # 控制器层（异常转换）
│   ├── services/                   # 业务层
│   ├── models/                     # SQLAlchemy 模型
│   ├── schemas/                    # Pydantic 请求/响应模型
│   ├── views/                      # 路由层（统一入口）
│   ├── database/                   # DB/Redis 初始化、会话依赖、自动迁移
│   ├── middleware/                 # 认证、日志、异常处理
│   └── utils/
├── alembic/                        # 迁移配置与版本
├── tests/
│   ├── test_api_integration.py     # 集成测试（覆盖 12 业务域）
│   └── ...
├── config.py                       # 项目配置
├── init_data.py                    # 初始权限/角色/用户（含教官扩展字段）
├── migrate.py                      # 迁移管理脚本
└── main.py                         # 启动入口
```

---

## 5. 分层架构说明

### Models (`app/models`)

- RBAC 与系统：`User`, `Role`, `Permission`, `Department`, `Config`, `ConfigGroup`, `SystemMeta`
- 业务域：
  - 课程：`Course`, `Chapter`, `CourseProgress`
  - 培训：`Training`, `TrainingCourse`, `Enrollment`, `CheckinRecord`, `ScheduleItem`
  - 考试：`Question`, `Exam`, `ExamQuestion`, `ExamRecord`
  - 证书：`Certificate`（教官扩展信息已并入 `User`）

### Schemas (`app/schemas`)

按业务域定义 Create/Update/Response 模型，统一响应模型为：
- `StandardResponse[T]`
- `PaginatedResponse[T]`

### Services (`app/services`)

封装业务逻辑与数据库操作，例如：
- `CourseService`, `QuestionService`, `ExamService`, `TrainingService`
- `CertificateService`, `ProfileService`
- `DashboardService`, `ReportService`, `TalentService`, `AIService`

### Controllers (`app/controllers`)

封装 service 调用并转换异常为 `HTTPException`。

### Views (`app/views`)

定义 API 路由与依赖注入，统一通过 `app/views/__init__.py` 汇总注册。

---

## 6. 配置项（`config.py`）

关键配置如下（可通过 `.env` / `.env.dev` 覆盖）：

- 基础：
  - `PROJECT_NAME`, `VERSION`, `DEBUG`
  - `API_V1_STR`（默认 `/api/v1`）
- 数据库：
  - `DATABASE_URL`
  - `DATABASE_ECHO`
- Redis：
  - `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_DB`
- JWT：
  - `SECRET_KEY`
  - `ACCESS_TOKEN_EXPIRE_MINUTES`
- 迁移：
  - `AUTO_MIGRATE_ON_STARTUP`
- AI：
  - `LLM_BASE_URL`
  - `LLM_API_KEY`
  - `LLM_MODEL`

---

## 7. 本地启动

### 7.1 安装依赖

```bash
pip install -r requirements.txt
```

### 7.2 启动服务

```bash
python main.py
```

默认端口：`8001`

### 7.3 文档与健康检查

- Swagger: `http://127.0.0.1:8001/api/v1/docs`
- ReDoc: `http://127.0.0.1:8001/api/v1/redoc`
- 健康检查: `http://127.0.0.1:8001/health`

---

## 8. 初始化数据（`init_data.py`）

首次初始化会创建权限、部门、角色、用户（含教官扩展字段）。

### 默认账号

- 管理员：`admin / police2025`
- 教官：`instructor / teach2025`
- 学员：`student / learn2025`

### 默认角色

- `admin`：全权限
- `instructor`：教学/培训/题库/考试/证书等管理权限
- `student`：学习/考试/报名/签到/个人中心权限

---

## 9. API 总览（当前实际路由）

统一前缀：`/api/v1`

### 9.1 认证（`/auth`）

- `POST /auth/login` 账号密码登录
- `POST /auth/login/phone` 手机验证码登录
- `GET /auth/me` 获取当前用户信息

### 9.2 工作台（`/dashboard`）

- `GET /dashboard` 根据 `role` 返回工作台数据

### 9.3 课程管理（`/courses`）

- `GET /courses` 课程列表（分页/搜索/分类/排序）
- `POST /courses` 创建课程
- `GET /courses/progress` 当前用户学习进度
- `GET /courses/{course_id}` 课程详情
- `PUT /courses/{course_id}` 更新课程
- `PUT /courses/{course_id}/chapters/{chapter_id}/progress` 更新章节进度

### 9.4 题库管理（`/questions`）

- `GET /questions` 题目列表（分页/筛选）
- `POST /questions` 创建题目
- `PUT /questions/{question_id}` 更新题目
- `DELETE /questions/{question_id}` 删除题目
- `POST /questions/batch` 批量导入题目

### 9.5 考试管理（`/exams`）

- `GET /exams` 考试列表
- `POST /exams` 创建考试
- `GET /exams/{exam_id}` 考试详情（含题目）
- `POST /exams/{exam_id}/submit` 提交考试
- `GET /exams/{exam_id}/result` 获取考试结果
- `GET /exams/{exam_id}/scores` 成绩管理

### 9.6 培训管理（`/trainings`）

- `GET /trainings` 培训列表
- `POST /trainings` 创建培训班
- `GET /trainings/{training_id}` 培训详情
- `PUT /trainings/{training_id}` 更新培训班
- `DELETE /trainings/{training_id}` 删除培训班
- `GET /trainings/{training_id}/students` 学员列表
- `GET /trainings/{training_id}/schedule` 周计划
- `POST /trainings/{training_id}/enroll` 学员报名
- `GET /trainings/{training_id}/enrollments` 报名列表
- `PUT /trainings/{training_id}/enrollments/{eid}/approve` 审批通过
- `PUT /trainings/{training_id}/enrollments/{eid}/reject` 审批拒绝
- `GET /trainings/{training_id}/checkin/records` 签到记录
- `POST /trainings/{training_id}/checkin` 签到
- `GET /trainings/{training_id}/checkin/qr` 生成签到二维码

### 9.7 教官信息（通过用户接口）

- `GET /users?role=instructor` 教官用户列表
- `GET /users/{user_id}` 教官用户详情
- `POST /users` / `PUT /users/{user_id}` 支持教官扩展字段：
  - `instructor_title`
  - `instructor_level`
  - `instructor_specialties`
  - `instructor_qualification`
  - `instructor_certificates`
  - `instructor_intro`
  - `instructor_rating`
  - `instructor_course_count`
  - `instructor_student_count`
  - `instructor_review_count`

> `/instructors` 专用接口已下线。

### 9.8 证书管理（`/certificates`）

- `GET /certificates` 证书列表
- `POST /certificates` 签发证书

### 9.9 个人中心（`/profile`）

- `GET /profile` 个人信息
- `PUT /profile` 更新个人信息
- `GET /profile/study-stats` 学习统计
- `GET /profile/exam-history` 考试历史

### 9.10 数据看板（`/report`）

- `GET /report/kpi` KPI 数据
- `GET /report/trend` 月度趋势
- `GET /report/police-type-distribution` 警种分布
- `GET /report/city-ranking` 城市/单位排名

### 9.11 AI 功能（`/ai`）

- `POST /ai/generate-questions` AI 智能组卷
- `POST /ai/generate-lesson-plan` AI 教案生成

> 若外部大模型鉴权失败，服务会记录错误日志并返回降级结果（空题目/空教案），接口本身仍可返回成功结构。

### 9.12 人才库（`/talent`）

- `GET /talent` 人才列表（search/tier/unit）
- `GET /talent/stats` 统计概览

---

## 10. 迁移与数据库管理

使用 `migrate.py`：

```bash
# 初始化数据库（首次）
python migrate.py init

# 生成迁移（自动）
python migrate.py generate "add police training models"

# 升级到最新
python migrate.py upgrade

# 回滚一个版本
python migrate.py downgrade -1

# 查看状态
python migrate.py status
```

---

## 11. 测试

已提供集成测试脚本：

- `tests/test_api_integration.py`

执行方式：

```bash
python tests/test_api_integration.py
```

说明：
- 脚本会自动登录三角色并覆盖主要业务流程。
- 已内置 `session.trust_env = False`，避免本机代理导致 `127.0.0.1` 请求异常。

---

## 12. 常见问题

### Q1：为什么 HTTP 状态码是 200，但业务失败？

因为项目统一异常响应格式，业务错误通过 `code` 字段体现（如 `code=500`）。

### Q2：AI 接口日志报 `Authentication Fails` 是否会影响主流程？

不会影响其他业务模块。AI 模块失败时会降级返回默认结果。

### Q3：删除培训班时外键冲突怎么办？

当前实现已处理证书外键：删除培训班前会先清空 `certificates.training_id` 的关联。

---

## 13. 开发约定

- 所有新业务建议遵循分层：`views -> controllers -> services -> models/schemas`
- 新增模型后同步更新：
  - `app/models/__init__.py`
  - `app/database/__init__.py`（`init_db` 导入）
  - `alembic/env.py`（metadata 导入）
- 新增路由后同步更新：
  - `app/views/__init__.py`
  - `app/__init__.py`（统一注册）

---

## 14. 版本信息

- 应用版本：`1.0.0`
- 默认 API 前缀：`/api/v1`
- 默认服务端口：`8001`
