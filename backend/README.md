# 警务训练平台后端

本文档面向 `backend/` 目录的开发与运维，描述当前代码中的真实目录结构、启动流程、环境变量、迁移策略和业务边界。

## 服务定位

后端服务基于 FastAPI，负责以下能力：

- JWT 登录鉴权与权限解析
- 用户、角色、部门、权限、警种、培训基地、系统配置管理
- 课程、培训、考试、证书、公告、个人中心、数据看板
- 资源上传、资源库、推荐流、审核工作流
- AI 任务流：智能出题、自动组卷、自动生成试卷、教学资源生成、排课建议、个训方案
- PostgreSQL、Redis、MinIO、Celery 的集成

## 技术栈

| 类别 | 技术 | 版本 |
| --- | --- | --- |
| Web 框架 | FastAPI | 0.104.1 |
| ASGI 服务器 | uvicorn | 0.24.0 |
| ORM | SQLAlchemy | 2.0.23 |
| 数据校验 | Pydantic | 2.10.6 |
| 配置 | pydantic-settings、python-dotenv | — |
| 数据库 | PostgreSQL（psycopg2-binary） | — |
| 迁移 | Alembic | 1.12.1 |
| 缓存 / 队列 | Redis 5.0、Celery 5.3（gevent） | — |
| 文件存储 | MinIO | 7.2.0 |
| 鉴权 | python-jose JWT | — |
| 密码加密 | passlib + bcrypt | — |
| 日志 | Loguru | 0.7.2 |
| Excel 导入导出 | openpyxl | 3.1.5 |
| AI | OpenAI 兼容客户端 2.6、Ollama 0.5 | — |

## 目录结构

```text
backend/
├── app/
│   ├── __init__.py                 # FastAPI 应用实例、startup / shutdown
│   ├── views/                      # 路由层（24 个路由模块）
│   │   ├── auth.py                 # 登录鉴权
│   │   ├── user.py                 # 用户管理
│   │   ├── role.py                 # 角色管理
│   │   ├── department.py           # 部门管理
│   │   ├── permission.py           # 权限管理
│   │   ├── police_type.py          # 警种管理
│   │   ├── course.py               # 课程资源
│   │   ├── training.py             # 培训管理
│   │   ├── training_base.py        # 培训基地
│   │   ├── exam.py                 # 考试管理
│   │   ├── question.py             # 题库管理
│   │   ├── knowledge_point.py      # 知识点管理
│   │   ├── resource.py             # 资源库
│   │   ├── review.py               # 审核工作流
│   │   ├── recommendation.py       # 推荐流
│   │   ├── ai.py                   # AI 任务流（6 条任务线统一入口）
│   │   ├── media.py                # 文件上传与访问
│   │   ├── dashboard.py            # 工作台
│   │   ├── profile.py              # 个人中心
│   │   ├── report.py               # 数据看板
│   │   ├── certificate.py          # 结业证书
│   │   ├── talent.py               # 人才库
│   │   ├── notice.py               # 公告
│   │   └── system.py               # 系统配置
│   ├── controllers/                # 控制器层（22 个控制器）
│   ├── services/                   # 业务服务层（33 个服务模块）
│   │   ├── ai.py                   # AI 任务编排与调度
│   │   ├── training_ai.py          # 培训 AI（排课 + 个训）
│   │   ├── teaching_resource_*.py  # 教学资源生成 / 渲染 / 模板注册
│   │   ├── training_schedule_rule.py   # 排课规则
│   │   ├── training_portrait_aggregator.py  # 学员画像聚合
│   │   ├── training_course_change.py   # 课程变更留痕
│   │   ├── course_progress.py      # 学习进度聚合
│   │   ├── batch_import.py         # 批量导入
│   │   ├── system_exchange.py      # 数据导入导出
│   │   └── ...                     # auth, user, course, training, exam 等
│   ├── agents/                     # 智能体封装（8 个 Agent）
│   │   ├── base.py                 # BaseAIAgent（OpenAI / Ollama 双通道）
│   │   ├── question_generator.py   # 题目生成
│   │   ├── schedule_agent.py       # 排课引擎（冲突检测、多方案生成）
│   │   ├── schedule_config_parser.py   # 排课自然语言解析
│   │   ├── paper_assembly_parser.py    # 组卷需求解析
│   │   ├── personal_training_plan_agent.py  # 个训方案生成
│   │   ├── teaching_resource_parser.py      # 教学资源需求解析
│   │   └── teaching_resource_content_agent.py  # 教学资源内容生成
│   ├── tasks/                      # Celery 异步任务（5 个任务模块）
│   │   ├── ai_question.py          # 智能出题
│   │   ├── ai_paper_assembly.py    # 自动组卷
│   │   ├── ai_schedule.py          # 排课建议
│   │   ├── teaching_resource_generation.py  # 教学资源生成
│   │   └── recommendation.py       # 推荐刷新（占位）
│   ├── models/                     # SQLAlchemy 模型（18 个模型模块）
│   │   ├── user.py, role.py, permission.py, department.py, police_type.py
│   │   ├── course.py, training.py, exam.py
│   │   ├── resource.py, review.py, recommendation.py
│   │   ├── ai_task.py, media.py, notice.py, certificate.py, system.py
│   │   ├── personal_training_plan_snapshot.py
│   │   └── teaching_resource_generation_snapshot.py
│   ├── schemas/                    # Pydantic 模型（22 个 Schema 模块）
│   ├── templates/                  # HTML 模板
│   │   └── teaching_resource_slides.html  # 教学课件渲染模板
│   ├── middleware/                 # 中间件
│   │   ├── auth.py                 # JWT 鉴权（Bearer Token）
│   │   ├── logging.py              # 请求 / 响应日志
│   │   └── exception_handlers.py   # 全局异常处理
│   ├── database/                   # 数据库层
│   │   ├── __init__.py             # SQLAlchemy Session + Redis 客户端
│   │   └── auto_migrate.py         # 启动时自动迁移与结构校验
│   └── utils/                      # 工具函数
│       ├── authz.py                # 授权判断（can_view / can_manage 等）
│       ├── data_scope.py           # 数据范围过滤
│       ├── exceptions.py           # 自定义异常
│       ├── permission_group.py     # 权限分组推断
│       ├── system_initial_configs.py  # 初始化配置模板
│       └── utils.py                # 通用工具
├── alembic/                        # 数据库迁移版本（30 个版本文件）
├── data/                           # 本地临时文件目录（.gitignore）
├── docker/                         # 容器启动脚本（entrypoint.sh）
├── tests/                          # 测试脚本
├── main.py                         # uvicorn 启动入口
├── config.py                       # Settings 定义（DB / Redis / MinIO / JWT / LLM）
├── logger.py                       # Loguru 配置（控制台 + 按天轮转文件）
├── migrate.py                      # Alembic 管理脚本
├── init_data.py                    # 种子数据与系统配置初始化
├── celery_app.py                   # Celery 实例（gevent 池，并发 100）
├── requirements.txt
└── Dockerfile
```

## 当前核心业务模型

### 考试域

当前考试域已拆成四层：

| 层级 | 模型 | 说明 |
| --- | --- | --- |
| 知识点 | `KnowledgePoint` | 知识点主数据，与题目多对多 |
| 题库 | `Question` | 统一题库，关联知识点 |
| 试卷 | `ExamPaper` | 独立试卷，维护题目快照与状态 |
| 考试 | `AdmissionExam` / `Exam` | 准入考试（独立）/ 培训班考试（关联 `training_id`） |

对应业务规则：

- 试卷状态流：`draft → published → archived`
- 试卷发布后不可再修改题目；已被考试引用的试卷不能删除
- 题目不再使用单个知识点字符串，改为 `knowledge_points` 关联和知识点快照
- 只有已发布试卷才能创建准入考试和培训班考试
- 准入考试范围由 `scope_type + scope_target_ids` 控制，支持 `all`、`user`、`department`、`role`
- 准入考试列表、详情、交卷都会按适用范围做后端校验
- 培训班报名时，如果绑定了 `admission_exam_id`，必须先有通过记录

### AI 任务域

统一任务表：`AITask`

| 任务类型 | 标识 | 执行方式 | Agent |
| --- | --- | --- | --- |
| AI 智能出题 | `question_generation` | Celery 异步 | `question_generator` |
| AI 自动组卷 | `paper_assembly` | Celery 异步 | `paper_assembly_parser` |
| AI 自动生成试卷 | `paper_generation` | 同步 | — |
| 教学资源生成 | `resource_generation` | Celery 异步 | `teaching_resource_parser` + `content_agent` |
| AI 排课建议 | `schedule_generation` | Celery 异步 | `schedule_config_parser` + `schedule_agent` |
| AI 个训方案 | `personal_training_plan_generation` | 同步 | `personal_training_plan_agent` |

统一任务状态：`pending → processing → completed → confirmed`（异常则 `failed`）

#### 各任务线实现差异

- **AI 智能出题**
  - 通过 `app.tasks.ai_question` 进入 Celery 队列
  - 真正调用模型生成题目
  - 每次仅允许一种题型，最多 20 题
- **AI 自动组卷**
  - 通过 `app.tasks.ai_paper_assembly` 进入 Celery 队列
  - 采用"解析自然语言要求 → 按题型查题库 → 不足时放宽条件 → 生成试卷草稿"链路
  - 组卷过程只从题库选题，不再补生成题目
  - 题型配置允许单个题型数量为 `0`，但服务层强制至少一种题型数量大于 `0`
- **AI 自动生成试卷**
  - 任务化接口，但创建后同步生成试卷草稿
  - 当前是规则 / 模拟生成，不走 Celery
  - 题型配置与自动组卷共用同一套标准化校验
- **教学资源生成**
  - 通过 `app.tasks.teaching_resource_generation` 进入 Celery 队列
  - 先解析自然语言需求，再按固定"通用教学课件模板"填充页面内容
  - 服务端渲染成单个可翻页 HTML 课件（模板：`app/templates/teaching_resource_slides.html`）
  - 预览生成结果后，再补资源摘要、标签和可见范围
  - 确认后创建资源草稿并挂接现有审核流
- **AI 排课建议**
  - 通过 `app.tasks.ai_schedule` 进入 Celery 队列
  - 采用"两阶段任务流"：先解析规则 → 确认规则 → 生成课表
  - 任务详情内可保存主方案、删除任务 / 课次，最终确认后回写培训班课程与课次
- **AI 个训方案**
  - 创建任务时同步生成画像与方案
  - 确认后写入 `PersonalTrainingPlanSnapshot`
  - 同一培训班、同一学员按 `version_no` 递增保存快照

#### AI 排课当前流程

智能排课是两阶段异步任务流：

1. 创建任务
2. 后台异步解析自然语言规则
3. 任务进入"待确认规则"
4. 用户在任务详情内确认或修改结构化规则
5. 后台异步生成课表（主方案 + 备选方案 + 冲突清单）
6. 用户预览并可编辑
7. 用户确认应用

排课相关接口：

| 接口 | 说明 |
| --- | --- |
| `POST /api/v1/ai/schedule-tasks/preview` | 预览排课解析结果 |
| `POST /api/v1/ai/schedule-tasks/{task_id}/confirm-rules` | 确认规则 |
| `PUT /api/v1/ai/schedule-tasks/{task_id}/result` | 更新主方案 |
| `DELETE /api/v1/ai/schedule-tasks/{task_id}` | 删除排课任务 |
| `POST /api/v1/ai/schedule-tasks/{task_id}/confirm` | 确认应用（支持 `overwrite_existing_schedule`） |

AI 运行时配置：

- AI 智能出题和 AI 排课自然语言解析读取系统配置组 `ai`
- 支持 `openai` 与 `ollama` 双通道
- 如果 AI 排课自然语言解析未配置模型或调用失败，会自动退化到规则兜底解析

### 资源与审核域

- 资源标签已独立成 `ResourceTag / ResourceTagRelation`
- 资源标签支持列表查询与即时创建接口：`GET /api/v1/resources/tags`、`POST /api/v1/resources/tags`
- 资源上传入口的标签交互与课程标签一致，支持搜索已有标签并直接新建
- 审核策略支持 `global / department / department_tree` 三种作用域
- 审核策略支持上传者约束、连续多级审核、最小通过数校验
- 如果当前没有任何启用的自定义审核规则，资源提交审核时会自动回退到"管理员默认审核"
- 教学资源生成确认后自动创建资源草稿，并生成 `TeachingResourceGenerationSnapshot` 快照

### 培训域

当前培训域主链路：

- 培训基地：独立 `TrainingBase` 模型
- 培训班流程：`发布招生 → 锁定名单 → 开班 → 结班`
- 培训班报名模式：`enrollment_requires_approval`（`true` = 待审核，`false` = 直接通过）
- 培训班数据归属：`department_id`、`police_type_id`、`training_base_id`、`created_by`
- 课次状态流：`pending → checkin_open → checkin_closed → checkout_open → completed`（另有 `skipped`、`missed`）
- 培训班开班后，课程和课次的任何变更都会写入 `TrainingCourseChangeLog`
- 培训班支持 `schedule_rule_config`（AI 排课、手工排课、课时换算共用，系统默认值来自配置组 `training_schedule`）

AI 排课任务支持的结构化约束：

- 自然语言要求解析、任务级规则覆盖、固定课程键锁定
- 主方案 / 备选方案 / 冲突清单
- 教官 / 场地不可用、禁排时段、课程类型时段偏好、考前强化

AI 个训任务支持：

- 按学员画像生成目标、动作、资源推荐
- 确认后落版本化快照（`PersonalTrainingPlanSnapshot`）

批量导入接口：

| 接口 | 说明 |
| --- | --- |
| `POST /api/v1/users/import/police-base` | 全员底库导入 |
| `POST /api/v1/trainings/{id}/import/students` | 培训学员导入 |
| `POST /api/v1/trainings/{id}/import/instructors` | 培训教官导入 |
| `POST /api/v1/trainings/{id}/import/courses` | 培训课程导入 |
| `POST /api/v1/trainings/{id}/import/sessions` | 培训课次导入 |
| `POST /api/v1/trainings/{id}/import/schedule` | 培训课次导入（兼容别名） |

导入特点：基于 openpyxl 解析 `.xlsx`，自动识别中英文表头别名，缺失部门与警种会自动创建，新建账号默认密码为 `Police@123456`。

### 课程域

- 课程标签已独立成 `CourseTag / CourseTagRelation`
- 课程支持可见范围：`all`、`user`、`department`、`role`
- 课程章节创建 / 编辑时不再直接上传文件，而是引用当前操作用户自己已发布的资源
- 章节可绑定资源中的具体文件；未显式指定时默认取第一个文件，对外摘要按 `文件1 / 文件2 ...` 返回
- 课程总进度由 `CourseProgressService` 聚合（按章节平均，列表 / 详情 / 工作台 / 个人中心共用）
- 视频学习进度会持久化 `playback_seconds`
- 课程文件类型已覆盖 `video`、`document`、`image`、`mixed`
- 课程学习情况接口 `GET /api/v1/courses/{id}/learning-status`：仅课程创建者、主讲教官或具备 `GET_COURSE_LEARNING_STATUS` 权限的用户可查看
- 课程详情会返回章节所引用的资源与具体文件摘要

### 系统配置域

- 配置组接口：`/api/v1/system/config-groups*`
- 配置项接口：`/api/v1/system/configs*`
- 当前核心初始化配置组：`ai`、`training_schedule`
- `init_data.py` 会执行配置模板同步，并刷新 Redis 缓存
- 所有系统配置接口目前都只允许 `admin` 使用

### 数据范围域

系统把"功能权限"和"数据范围"拆开：

- 功能权限：由角色权限码与部门权限决定
- 数据范围：由角色上的 `data_scopes` 决定

| 数据范围值 | 说明 |
| --- | --- |
| `all` | 全部数据 |
| `department` | 本部门 |
| `department_and_sub` | 本部门及下级 |
| `police_type` | 本警种 |
| `self` | 仅自己 |

已接入对象级范围控制：`User`、`Training`、`TrainingBase`、`Question`、`ExamPaper`、`Exam`

内置角色默认范围：

| 角色 | 默认数据范围 |
| --- | --- |
| `admin` | `all` |
| `instructor` | `department_and_sub` + `police_type` + `self` |
| `student` | `department` + `police_type` + `self` |

## 路由组成

已注册的 24 个业务路由模块（统一前缀 `/api/v1`）：

`auth` · `user` · `role` · `department` · `permission` · `police-type` · `course` · `training` · `training-base` · `exam` · `question` · `knowledge-point` · `resource` · `review` · `recommendation` · `ai` · `media` · `dashboard` · `profile` · `report` · `certificate` · `talent` · `notice` · `system`

## 启动流程

### `python main.py` 做了什么

`main.py` 只负责启动 uvicorn：

```python
uvicorn.run("app:app", host="0.0.0.0", port=8001)
```

真正的应用初始化逻辑在 `app/__init__.py`。

### FastAPI startup 事件做了什么

应用启动时会依次执行：

1. 如果 `AUTO_MIGRATE_ON_STARTUP=True`，先尝试自动迁移
2. 对关键表结构做兼容性校验（字段缺失则阻断启动）
3. 调用 `init_db()`，仅补齐缺失表，不负责历史字段升级
4. 测试 Redis 连接

注意：

- 这些步骤不会自动执行 `init_data.py`
- 本地首次初始化仍需手动运行 `python init_data.py`
- 自动迁移不能替代 Alembic 历史迁移链

## 本地启动

以下命令以 PowerShell 7 为例。

### 1. 安装依赖

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. 初始化环境变量

```powershell
Copy-Item .env.example .env
```

说明：

- `config.py` 会先加载 `.env`
- 如果存在 `.env.dev`，会在 `.env` 之上继续覆盖

### 3. 执行迁移

```powershell
python migrate.py upgrade
```

### 4. 初始化种子数据与系统配置

```powershell
python init_data.py
```

### 5. 启动 API

```powershell
python main.py
```

默认地址：

| 入口 | 地址 |
| --- | --- |
| API | `http://127.0.0.1:8001` |
| Swagger | `http://127.0.0.1:8001/api/v1/docs` |
| ReDoc | `http://127.0.0.1:8001/api/v1/redoc` |
| OpenAPI | `http://127.0.0.1:8001/api/v1/openapi.json` |

## Celery 与后台任务

### 当前注册到 Celery 的任务

`celery_app.py` 当前显式注册了四类任务：

| 任务模块 | 对应功能 | 是否必须 |
| --- | --- | --- |
| `app.tasks.ai_question` | AI 智能出题 | 需要 Worker |
| `app.tasks.ai_paper_assembly` | AI 自动组卷 | 需要 Worker |
| `app.tasks.ai_schedule` | AI 排课建议 | 需要 Worker |
| `app.tasks.teaching_resource_generation` | 教学资源生成 | 需要 Worker |

不依赖 Worker 的任务：`AI 自动生成试卷`、`AI 个训方案`（同步生成）

`app/tasks/recommendation.py` 目前只是占位脚本，没有注册成 Celery 定时任务。

### 启动 Worker

```powershell
Set-Location backend
.\.venv\Scripts\Activate.ps1
celery -A celery_app worker --loglevel=info --pool=gevent --concurrency=10
```

### 启动 Beat

```powershell
Set-Location backend
.\.venv\Scripts\Activate.ps1
celery -A celery_app beat --loglevel=info
```

说明：

- Worker 镜像与 API 镜像共用 `backend/Dockerfile`
- 默认 Compose 只启动 `worker`，不启动 `beat`
- 当前仓库没有启用的周期任务编排，`beat` 主要用于后续扩展

## Docker 启动入口

`backend/docker/entrypoint.sh` 支持三种模式：

| 模式 | 行为 |
| --- | --- |
| `api` | 探测数据库 → 空库则初始化 → 启动 API |
| `worker` | 启动 Celery Worker |
| `beat` | 启动 Celery Beat |

`api` 模式下会先探测数据库状态：

- 空库：执行 `init_data.py` → `python migrate.py stamp head`
- 有业务表但缺种子数据：执行 `init_data.py`
- 已初始化：跳过种子数据，直接启动 API

## 环境变量与运行时配置

推荐从 `backend/.env.example` 复制为 `backend/.env`。

### 常用环境变量

| 变量 | 说明 |
| --- | --- |
| `DEBUG` | 调试模式 |
| `API_V1_STR` | API 前缀，默认 `/api/v1` |
| `AUTO_MIGRATE_ON_STARTUP` | 启动时自动检查迁移 |
| `DATABASE_URL` | PostgreSQL 连接串 |
| `DATABASE_ECHO` | 是否打印 SQL |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | Redis 连接信息 |
| `MINIO_PUBLIC_URL` | 文件对外访问基础地址 |
| `MINIO_ENDPOINT` | MinIO 内部连接地址 |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | MinIO 账号密码 |
| `MINIO_BUCKET` | 存储桶名称 |
| `CELERY_BROKER_URL` | Celery Broker（默认 Redis DB 1） |
| `CELERY_RESULT_BACKEND` | Celery 结果后端（默认 Redis DB 2） |
| `SECRET_KEY` | JWT 签名密钥 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间（默认 30 天） |
| `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` | 保留在 Settings 中的模型环境变量 |
| `MAX_UPLOAD_SIZE` | 最大上传文件大小（默认 500MB） |

### 需要特别注意的点

- `LLM_*` 仍保留在 `config.py` 中，但 AI 智能出题和 AI 排课自然语言解析实际优先读取系统配置组 `ai`
- 培训排课默认规则来自系统配置组 `training_schedule`
- 系统配置会同步到 Redis 缓存；修改配置后由配置服务负责刷新缓存
- 数据库连接池配置：`pool_size=20`、`max_overflow=50`、`pool_timeout=30s`、`pool_recycle=1h`

## 数据迁移

使用 `migrate.py` 管理 Alembic：

```powershell
python migrate.py upgrade          # 升级到最新
python migrate.py downgrade -1     # 回退一个版本
python migrate.py current          # 查看当前版本
python migrate.py history          # 查看历史
python migrate.py status           # 查看状态
python migrate.py generate "msg"   # 生成新迁移
```

当前迁移已覆盖的关键改造（30 个版本文件）：

- 考试 P0 重构、试卷状态字段、准入考试结构化适用范围
- 题目知识点拆表、多对多关联与试卷知识点快照
- 培训基地与数据归属字段
- 角色 `data_scopes` 与创建人字段
- AI 任务表 `ai_tasks`
- 培训报名审批开关
- 课程标签、学习位置、学习情况
- 培训班课程变更日志
- 课程可见范围字段
- 个训方案快照表 `personal_training_plan_snapshots`
- 培训排课规则字段 `training_schedule_rule_config`
- 知识点独立管理与多对多关联
- 教学资源生成快照表 `teaching_resource_generation_snapshots`

注意：

- `python migrate.py stamp head` 只适用于你已经确认库结构与最新迁移完全一致的场景
- `Base.metadata.create_all()` 不能替代 Alembic 字段迁移

## 认证与权限

### 认证方式

| 接口 | 说明 |
| --- | --- |
| `POST /api/v1/auth/login` | 用户名密码登录 |
| `POST /api/v1/auth/login/phone` | 手机号登录（当前不校验验证码） |
| `GET /api/v1/auth/me` | 获取当前用户信息 |

### 统一响应

除下载流和文件直链外，接口通常返回：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {}
}
```

### 权限模型

- 用户权限由角色权限与部门权限共同决定
- 角色还可配置 `data_scopes`
- 培训域更新接口已拆成两条：
  - `PUT /api/v1/trainings/{id}`：要求 `UPDATE_TRAINING`，且必须是当前班主任
  - `PUT /api/v1/trainings/{id}/manage`：要求 `MANAGE_TRAINING`
- 智能排课接口权限已与培训班管理口径对齐
- 系统配置接口当前统一要求 `admin`

### 受保护对象

- `admin` 角色不可编辑、不可删除、不可重分配权限
- `admin` 用户不可修改角色
- 用户删除采用软删除：`is_active=False`

## 文件上传与对象存储

资源和媒体能力依赖 MinIO：

| 接口 | 说明 |
| --- | --- |
| `POST /api/v1/media/upload` | 上传文件 |
| `GET /api/v1/media/files/{file_id}` | 获取文件 |

实现特性：

- 上传时按 SHA-256 秒传去重
- 文件写入 MinIO，数据库保留文件元数据
- 历史本地文件仍支持兼容读取
- `GET /media/files/{id}` 可能直接返回文件，也可能 307 跳转到 MinIO 直链

## 种子数据

`python init_data.py` 会初始化：

- 权限、根部门 `ROOT`、基础警种
- `admin` / `instructor` / `student` 三个默认角色
- 三个示例用户
- 系统配置模板：`ai`、`training_schedule`

默认账号：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `police2025` |
| 教官 | `instructor` | `teach2025` |
| 学员 | `student` | `learn2025` |

说明：

- `init_data.py` 不会预置审核策略
- 空规则场景由管理员默认审核兜底（后端自动创建或复用"系统默认审核策略"）

## 已知行为与注意事项

- `POST /api/v1/auth/login/phone` 目前不会校验验证码内容，只按手机号查用户并发 token
- AI 智能出题、AI 自动组卷、AI 排课建议、教学资源生成需要 Worker；只启动 API 时任务不会自动完成
- AI 自动生成试卷、AI 个训方案仍是同步结果任务，不依赖 Worker
- AI 智能出题依赖系统配置组 `ai` 中的模型配置；未配置则任务失败
- AI 排课自然语言解析未配置模型或调用失败时，会留下 `parse_warnings` 并按规则兜底继续生成
- AI 自动组卷 / 自动生成试卷的题型配置允许单项题型数量为 `0`，但不允许全部为 `0`
- 培训二维码签到依赖 Redis；Redis 不可用时，扫码签到链路不可用
- `checkin_closed` 的真实语义是"课程仍在进行，但签到窗口已结束"，前端应按"进行中"理解
- 默认 Compose 没有启动 `beat`，推荐刷新脚本也还没有接入正式周期调度

## 进一步阅读

| 文档 | 用途 |
| --- | --- |
| `backend/API_DOCUMENTATION.md` | 接口明细（20 个模块） |
| `README.md`（仓库根目录） | 前后端整体说明 |
| `frontend/README.md` | 前端维护说明 |
| `docs/` | 需求、设计方案与阶段性研究文档 |
