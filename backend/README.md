# 警务训练平台后端

本文档面向 `backend/` 目录的开发与运维，描述当前代码中的真实目录结构、启动流程、环境变量、迁移策略和业务边界。

## 服务定位

后端服务基于 FastAPI，负责以下能力：

- JWT 登录鉴权与权限解析
- 用户、角色、部门、权限、警种、培训基地、系统配置管理
- 课程、培训、考试、证书、公告、个人中心、数据看板
- 资源上传、资源库、推荐流、审核工作流
- AI 任务流：智能出题、自动组卷、自动生成试卷、排课建议、个训方案
- PostgreSQL、Redis、MinIO、Celery 的集成

## 当前核心业务模型

### 考试域

当前考试域已经拆成四层：

- `KnowledgePoint`：知识点主数据
- `Question`：统一题库，和知识点是多对多关系
- `ExamPaper`：独立试卷实体，维护题目快照与试卷状态
- `AdmissionExam`：独立准入考试，不直接隶属培训班
- `Exam`：培训班内考试，必须关联 `training_id`

对应业务规则：

- 试卷状态流：`draft -> published -> archived`
- 试卷发布后不可再修改题目；已被考试引用的试卷不能删除
- 题目不再使用单个知识点字符串，改为 `knowledge_points` 关联和知识点快照
- 准入考试和培训班考试都只关联 `paper_id`
- 只有已发布试卷才能创建准入考试和培训班考试
- 准入考试范围由 `scope_type + scope_target_ids` 控制，支持 `all`、`user`、`department`、`role`
- 准入考试列表、详情、交卷都会按适用范围做后端校验
- 培训班报名时，如果绑定了 `admission_exam_id`，必须先有通过记录

### AI 任务域

统一任务表：`AITask`

当前任务类型：

- `question_generation`
- `paper_assembly`
- `paper_generation`
- `schedule_generation`
- `personal_training_plan_generation`

统一任务状态：

- `pending`
- `processing`
- `completed`
- `confirmed`
- `failed`

#### 当前实现差异

- `AI 智能出题`
  - 创建任务后写入 `AITask`
  - 通过 `app.tasks.ai_question` 进入 Celery 队列
  - 真正调用模型生成题目
  - 每次仅允许一种题型，最多 20 题
- `AI 排课建议`
  - 创建任务后写入 `AITask`
  - 通过 `app.tasks.ai_schedule` 进入 Celery 队列
  - 采用“两阶段任务流”：先解析规则，再确认规则，再生成课表
  - 任务详情内可保存主方案、删除任务、删除任务中的课次，最终确认后回写培训班课程与课次
- `AI 自动组卷`
  - 创建任务后写入 `AITask`
  - 通过 `app.tasks.ai_paper_assembly` 进入 Celery 队列
  - 采用“解析自然语言要求 -> 按题型查题库 -> 不足时放宽条件 -> 生成试卷草稿”链路
  - 组卷过程只从题库选题，不再在任务执行中补生成题目
- `AI 自动生成试卷`
  - 也是任务化接口
  - 但创建任务时同步生成试卷草稿
  - 当前是规则 / 模拟生成，不走 Celery
- `AI 个训方案`
  - 创建任务时同步生成画像与方案
  - 确认后写入 `PersonalTrainingPlanSnapshot`
  - 同一培训班、同一学员按 `version_no` 递增保存快照

#### AI 排课当前流程

当前智能排课不是单次同步调用，而是任务流：

1. 创建任务
2. 后台异步解析自然语言规则
3. 任务进入“待确认规则”
4. 用户在任务详情内确认或修改结构化规则
5. 后台异步生成课表
6. 用户在任务详情内预览主方案、备选方案、冲突清单和周历视图
7. 用户保存修改并确认应用

当前支持的排课相关能力：

- 预览排课解析结果：`POST /api/v1/ai/schedule-tasks/preview`
- 在任务详情内确认规则：`POST /api/v1/ai/schedule-tasks/{task_id}/confirm-rules`
- 更新主方案：`PUT /api/v1/ai/schedule-tasks/{task_id}/result`
- 删除排课任务：`DELETE /api/v1/ai/schedule-tasks/{task_id}`
- 确认应用：`POST /api/v1/ai/schedule-tasks/{task_id}/confirm`
- 是否覆盖当前课表：`overwrite_existing_schedule`

AI 运行时配置：

- AI 智能出题和 AI 排课自然语言解析读取系统配置组 `ai`
- 支持 `openai` 与 `ollama`
- 如果 AI 排课自然语言解析未配置模型或调用失败，会自动退化到规则兜底解析

### 资源与审核域

当前资源与审核相关实现包括：

- 资源标签已独立成 `ResourceTag / ResourceTagRelation`
- 资源标签支持列表查询与即时创建接口：`GET /api/v1/resources/tags`、`POST /api/v1/resources/tags`
- 上传页标签交互与课程标签一致，支持搜索已有标签并直接新建
- 审核策略支持 `global / department / department_tree` 三种作用域
- 审核策略支持上传者约束、连续多级审核、最小通过数校验
- 如果当前没有任何启用的自定义审核规则，资源提交审核时会自动回退到“管理员默认审核”

### 培训域

当前培训域主链路如下：

- 培训基地：独立 `TrainingBase` 模型
- 培训班流程：发布招生 -> 锁定名单 -> 开班 -> 结班
- 培训班报名模式：`enrollment_requires_approval`
  - `true`：报名进入 `pending`
  - `false`：报名直接通过
- 培训班数据归属：`department_id`、`police_type_id`、`training_base_id`、`created_by`
- 课次状态流：
  - `pending`
  - `checkin_open`
  - `checkin_closed`
  - `checkout_open`
  - `completed`
  - `skipped`
  - `missed`
- 培训班开班后，课程和课次的任何变更都会写入 `TrainingCourseChangeLog`
- 培训班支持 `schedule_rule_config`
  - AI 排课、手工排课、课时换算共用这套规则
  - 系统默认值来自系统配置组 `training_schedule`
- AI 排课任务支持：
  - 自然语言要求解析
  - 任务级规则覆盖
  - 固定课程键锁定
  - 主方案 / 备选方案 / 冲突清单
  - 教官 / 场地不可用、禁排时段、课程类型时段偏好、考前强化等结构化约束
- AI 个训任务支持：
  - 按学员画像生成目标、动作、资源推荐
  - 确认后落版本化快照

批量导入接口：

- 培训学员导入
- 培训教官导入
- 培训课程导入
- 培训课次导入
- `/import/schedule` 目前是 `/import/sessions` 的兼容别名

### 课程域

当前课程域的关键规则如下：

- 课程标签已独立成 `CourseTag / CourseTagRelation`
- 课程支持可见范围：
  - `all`
  - `user`
  - `department`
  - `role`
- 课程总进度由 `CourseProgressService` 聚合：
  - 按章节时长加权
  - 列表、详情、工作台、个人中心共用
- 视频学习进度会持久化 `playback_seconds`
- 课程学习情况接口：`GET /api/v1/courses/{course_id}/learning-status`
  - 仅课程创建者、课程主讲教官，或具备 `GET_COURSE_LEARNING_STATUS` 权限的用户可查看
- 课程可绑定资源，详情会返回绑定资源列表

### 系统配置域

当前系统配置走独立配置组与配置项模型：

- 配置组接口：`/api/v1/system/config-groups*`
- 配置项接口：`/api/v1/system/configs*`
- 当前核心初始化配置组：
  - `ai`
  - `training_schedule`
- `init_data.py` 会执行配置模板同步，并刷新 Redis 缓存
- 所有系统配置接口目前都只允许 `admin` 使用

### 数据范围域

当前系统把“功能权限”和“数据范围”拆开：

- 功能权限：由角色权限码与部门权限决定
- 数据范围：由角色上的 `data_scopes` 决定

支持的数据范围值：

- `all`
- `department`
- `department_and_sub`
- `police_type`
- `self`

当前已接入对象级范围控制：

- `User`
- `Training`
- `TrainingBase`
- `Question`
- `ExamPaper`
- `Exam`

当前内置角色默认范围：

- `admin`：`all`
- `instructor`：`department_and_sub + police_type + self`
- `student`：`department + police_type + self`

## 技术栈

| 类别 | 技术 |
| --- | --- |
| Web 框架 | FastAPI |
| ORM | SQLAlchemy 2 |
| 配置 | pydantic-settings、python-dotenv |
| 数据库 | PostgreSQL |
| 迁移 | Alembic |
| 缓存 / 队列 | Redis、Celery |
| 文件存储 | MinIO |
| 鉴权 | python-jose JWT |
| 密码加密 | passlib[bcrypt] |
| 日志 | Loguru |
| Excel 导入导出 | openpyxl |
| AI | OpenAI 兼容客户端、Ollama |


## 目录结构

```text
backend/
├── app/
│   ├── __init__.py              # FastAPI 应用实例、startup / shutdown
│   ├── views/                   # 路由层
│   ├── controllers/             # 控制器层
│   ├── services/                # 业务层、AI 服务
│   ├── tasks/                   # Celery 任务
│   ├── models/                  # SQLAlchemy 模型
│   ├── schemas/                 # Pydantic 模型
│   ├── middleware/              # 鉴权、日志、异常处理
│   ├── database/                # 数据库、Redis、自动迁移
│   └── utils/                   # 初始化配置、权限辅助等
├── alembic/                     # 数据库迁移版本
├── data/                        # 本地数据目录
├── docker/                      # 容器启动脚本
├── tests/                       # 现有测试脚本
├── main.py                      # uvicorn 启动入口
├── config.py                    # Settings 定义
├── migrate.py                   # Alembic 管理脚本
├── init_data.py                 # 种子数据与系统配置初始化
└── celery_app.py                # Celery 实例
```

## 路由组成

已注册业务模块来自 `app/views/*.py`，当前包括：

- `auth`
- `dashboard`
- `course`
- `exam`
- `question`
- `training`
- `training-base`
- `certificate`
- `profile`
- `report`
- `ai`
- `talent`
- `police-type`
- `media`
- `user`
- `notice`
- `role`
- `system`
- `department`
- `permission`
- `resource`
- `review`
- `recommendation`

统一前缀为 `settings.API_V1_STR`，默认 `/api/v1`。

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
2. 对关键表结构做兼容性校验
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

- API：`http://127.0.0.1:8001`
- Swagger：`http://127.0.0.1:8001/api/v1/docs`
- ReDoc：`http://127.0.0.1:8001/api/v1/redoc`
- OpenAPI：`http://127.0.0.1:8001/api/v1/openapi.json`

## Celery 与后台任务

### 当前注册到 Celery 的任务

`celery_app.py` 当前显式注册了三类任务：

- `app.tasks.ai_paper_assembly`
- `app.tasks.ai_question`
- `app.tasks.ai_schedule`

也就是说：

- `AI 自动组卷` 依赖 Worker
- `AI 智能出题` 依赖 Worker
- `AI 排课建议` 依赖 Worker
- `AI 自动生成试卷`、`AI 个训方案` 不依赖 Worker
- `app/tasks/recommendation.py` 目前只是占位脚本，没有注册成 Celery 定时任务

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
- 当前仓库没有现成启用的周期任务编排，`beat` 主要用于后续扩展

## Docker 启动入口

`backend/docker/entrypoint.sh` 支持三种模式：

- `api`
- `worker`
- `beat`

`api` 模式下会先探测数据库状态：

- 空库：执行 `init_data.py`，再 `python migrate.py stamp head`
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
| `CELERY_BROKER_URL` | Celery Broker |
| `CELERY_RESULT_BACKEND` | Celery 结果后端 |
| `SECRET_KEY` | JWT 签名密钥 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间 |
| `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` | 保留在 Settings 中的模型环境变量 |

### 需要特别注意的点

- `LLM_*` 仍保留在 `config.py` 中，但 AI 智能出题和 AI 排课自然语言解析实际优先读取系统配置组 `ai`
- 培训排课默认规则来自系统配置组 `training_schedule`
- 系统配置会同步到 Redis 缓存；修改配置后由配置服务负责刷新缓存

## 数据迁移

使用 `migrate.py` 管理 Alembic：

```powershell
python migrate.py upgrade
python migrate.py downgrade -1
python migrate.py current
python migrate.py history
python migrate.py status
python migrate.py generate "your message"
```

当前迁移已经覆盖的关键改造包括：

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

注意：

- `python migrate.py stamp head` 只适用于你已经确认库结构与最新迁移完全一致的场景
- `Base.metadata.create_all()` 不能替代 Alembic 字段迁移

## 认证与权限

### 认证方式

- 登录接口：`POST /api/v1/auth/login`
- 手机登录接口：`POST /api/v1/auth/login/phone`
- 当前用户：`GET /api/v1/auth/me`

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
- 智能排课页面和相关接口权限已与培训班管理口径对齐：
  - 路由层要求 `UPDATE_TRAINING` 或 `MANAGE_TRAINING`
  - 任务访问和操作继续校验具体培训班管理权限
- 课程学习情况接口：`GET /api/v1/courses/{id}/learning-status`
  - 课程创建者、课程主讲教官可直接查看
  - 其余用户需具备 `GET_COURSE_LEARNING_STATUS`
- 系统配置接口当前统一要求 `admin`

### 受保护对象

- `admin` 角色不可编辑、不可删除、不可重分配权限
- `admin` 用户不可修改角色
- 用户删除采用软删除：`is_active=False`

## 文件上传与对象存储

资源和媒体能力依赖 MinIO：

- 上传接口：`POST /api/v1/media/upload`
- 取文件接口：`GET /api/v1/media/files/{file_id}`

实现特性：

- 上传时按 SHA-256 秒传去重
- 文件写入 MinIO
- 数据库保留文件元数据
- 历史本地文件仍支持兼容读取
- `GET /media/files/{id}` 可能直接返回文件，也可能 307 跳转到 MinIO 直链

## 批量导入

当前提供以下导入能力：

- 全员底库导入：`POST /api/v1/users/import/police-base`
- 培训学员导入：`POST /api/v1/trainings/{training_id}/import/students`
- 培训教官导入：`POST /api/v1/trainings/{training_id}/import/instructors`
- 培训课程导入：`POST /api/v1/trainings/{training_id}/import/courses`
- 培训课次导入：`POST /api/v1/trainings/{training_id}/import/sessions`
- 培训课次导入兼容别名：`POST /api/v1/trainings/{training_id}/import/schedule`

导入特点：

- 基于 `openpyxl` 解析 `.xlsx`
- 自动识别中英文表头别名
- 缺失部门与警种会自动创建
- 新建账号默认密码为 `Police@123456`

## 种子数据

`python init_data.py` 会初始化：

- 权限
- 根部门 `ROOT`
- 基础警种
- `admin` / `instructor` / `student` 三个默认角色
- 三个示例用户
- 系统配置模板：
  - `ai`
  - `training_schedule`

说明：

- `init_data.py` 不会预置审核策略
- 当资源提交审核时，如果库里没有启用的自定义审核规则，后端会自动创建或复用“系统默认审核策略”，默认只走管理员审核

默认账号：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `police2025` |
| 教官 | `instructor` | `teach2025` |
| 学员 | `student` | `learn2025` |

## 已知行为与注意事项

- `POST /api/v1/auth/login/phone` 目前不会校验验证码内容，只按手机号查用户并发 token。
- `AI 智能出题`、`AI 自动组卷`、`AI 排课建议` 需要 Worker；只启动 API 时任务不会自动完成。
- AI 智能出题依赖系统配置组 `ai` 中的模型配置；如果 `default_text_model`、`api_base_url` 或 `api_key` 未配置，任务会失败。
- AI 排课自然语言解析未配置模型或调用失败时，会在任务详情里留下 `parse_warnings`，并按规则兜底继续生成。
- 智能排课当前是两阶段异步任务流，不是同步接口。
- `AI 自动组卷` 当前已经是异步队列任务；`AI 自动生成试卷`、`AI 个训方案` 仍是同步结果任务。
- AI 自动组卷会先解析自然语言要求，再按题型、警种、难度、知识点关键词查题；题库不足时会放宽条件并把放宽记录写回任务结果。
- 资源审核策略页允许维护复杂规则，但如无明确业务需要，建议优先沿用现有规则；空规则场景由管理员默认审核兜底。
- 培训二维码签到依赖 Redis；Redis 不可用时，扫码签到链路不可用。
- `checkin_closed` 的真实语义是“课程仍在进行，但签到窗口已结束”，前端应按“进行中”理解。
- 默认 Compose 没有启动 `beat`，推荐刷新脚本也还没有接入正式周期调度。
- 仓库里仍然存在 `from __future__ import annotations` 的历史文件，当前代码并未做到“全面移除”这条约束；以后如果继续处理 Pydantic / 注解兼容问题，应以实际文件为准，不要依赖旧文档描述。

## 进一步阅读

- 接口明细：`backend/API_DOCUMENTATION.md`
- 前后端整体说明：仓库根目录 `README.md`
