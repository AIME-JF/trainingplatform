# 警务训练平台

警务训练平台是一个前后端分离的警务教育训练系统，覆盖课程资源、培训组织、在线考试、资源中心、AI 任务流、数据看板和系统管理等业务域。

本仓库同时包含：

- `frontend/` Vue 3 前端应用
- `backend/` FastAPI 后端服务
- `docker/` Docker Compose 与 Nginx 部署配置
- `docs/` 需求、方案和阶段性研究文档

## 项目概览

### 业务模块

| 模块 | 说明 |
| --- | --- |
| 工作台 | 按当前用户角色与权限展示首页数据（管理员 / 教官 / 学员三视图） |
| 课程资源 | 课程中心、章节学习、课程笔记、课程答疑、学习情况、标签管理 |
| 培训管理 | 培训班、培训基地、报名审核、学员名单、课程安排、课次签到 / 签退、课程变更记录、训历、培训看板 |
| 考试系统 | 题库、知识点管理、试卷仓库、准入考试、培训班内考试、成绩管理、考试分析 |
| 资源中心 | 资源库、我的资源、审核工作台、审核策略、推荐流、资源详情与预览 |
| AI 任务流 | AI 智能出题、AI 自动组卷、AI 自动生成试卷、教学资源生成、AI 排课建议、AI 个训方案 |
| 系统管理 | 用户、角色、部门、权限、警种、培训基地、系统配置 |
| 人员档案 | 学员库、教官库、人才库、结业证书 |
| 其他 | 公告、个人中心、数据看板（KPI / 趋势 / 排名 / 分布） |

### 当前业务口径

#### 考试域

- 考试已拆成 `题库 → 知识点 → 试卷 → 准入考试 / 培训班考试` 四层
- 知识点已独立成 `KnowledgePoint`，题目与知识点是多对多；前端提供独立"知识点管理"页面
- `ExamPaper` 独立维护试卷草稿、发布、归档；题目快照固化在试卷层
- 只有已发布试卷才能创建准入考试和培训班考试
- 培训班考试必须关联 `training_id`
- 准入考试通过 `scope_type + scope_target_ids` 控制适用范围，后端会做真实拦截
- 培训班可通过 `admission_exam_id` 绑定准入考试，报名时会校验是否已通过

#### 培训域

- 培训基地已独立成表，培训班支持维护 `department_id`、`police_type_id`、`training_base_id`
- 培训班流程按 `发布招生 → 锁定名单 → 开班 → 结班` 顺序推进
- 可通过 `enrollment_requires_approval` 配置报名后是"待审核"还是"直接通过"
- 培训班详情页围绕"步骤条 + 详情页操作"组织，而不是把重操作堆在列表页
- 培训开班后，课程 / 课次变更、签到状态流转都会写入 `TrainingCourseChangeLog`
- 培训班支持 `schedule_rule_config` 排课规则，AI 排课和手工排课都按同一套规则计算课时

#### 课程域

- 课程标签已独立成表，创建 / 编辑时支持远程搜索并直接新建标签
- 课程支持可见范围配置：`all`、`user`、`department`、`role`
- 课程章节不再直接上传文件；创建 / 编辑时需引用当前用户自己已发布的资源，并可选择资源内具体 `文件1 / 文件2 ...`
- 课程支持 `video`、`document`、`image`、`mixed` 四类文件类型，课程详情页可按资源类型预览视频、文档或图片
- 学习进度按章节平均汇总；视频学习过程仍会保存 `playback_seconds`
- 课程详情页提供"学习情况"标签，只有创建者、主讲教官或具备对应权限的用户可查看

#### 资源域

- 资源库具备上传、发布、下线、审核流、推荐流
- 资源标签已独立成表，资源库和我的资源中的上传弹窗支持搜索已有标签并直接创建新标签，交互与课程标签一致
- 我的资源新增"教学资源生成"入口：先输入自然语言要求生成预览课件，再补资源摘要、标签和可见范围，标题由系统自动生成
- 审核能力分成资源提交、审核任务、审核轨迹、审核策略四条接口
- 审核策略支持作用域、上传者约束、多级审核；没有启用规则时会回退到"管理员默认审核"
- 推荐流使用资源行为事件和预计算分数；仓库里保留了推荐刷新占位脚本

#### AI 任务域

当前共有 6 条 AI 任务线：

| 任务类型 | 标识 | 执行方式 |
| --- | --- | --- |
| AI 智能出题 | `question_generation` | Celery 异步 |
| AI 自动组卷 | `paper_assembly` | Celery 异步 |
| AI 自动生成试卷 | `paper_generation` | 同步生成 |
| 教学资源生成 | `resource_generation` | Celery 异步 |
| AI 排课建议 | `schedule_generation` | Celery 异步 |
| AI 个训方案 | `personal_training_plan_generation` | 同步生成 |

统一状态流转：`pending → processing → completed → confirmed`（异常则 `failed`）

各任务线实现差异：

- **AI 智能出题**：创建任务后进入 Celery 队列，异步调用模型生成题目
- **AI 自动组卷**：Celery 异步，按"解析需求 → 题库选题 → 不足时放宽条件 → 生成试卷草稿"处理
- **AI 自动生成试卷**：任务化接口，但创建后同步生成试卷草稿
- **教学资源生成**：Celery 异步，按"解析需求 → 固定内容模板填充 → 渲染单文件 HTML 课件 → 预览后补基础信息 → 确认入资源草稿"处理
- **AI 排课建议**：Celery 异步，按"解析规则 → 确认规则 → 生成课表（主方案 + 备选方案 + 冲突清单）→ 确认应用"流转
- **AI 个训方案**：任务化接口，但创建后同步生成画像和方案，确认后会生成个训快照

智能排课能力：

- 支持"智能排课"和"手动排课"两种创建方式
- 自然语言要求先异步解析，再在任务详情内确认结构化规则
- 规则确认后异步生成主方案、备选方案和冲突清单
- 支持是否覆盖当前课表
- 支持在任务结果中删除任务、删除任务中的课次、保存修改、周历预览和确认应用
- 权限口径与培训班管理一致

AI 出题 / 组卷 / 生成试卷的知识点选择已改成远程搜索，默认只加载前 20 条候选项。组卷 / 生成试卷的题型配置块支持单个题型数量为 `0`，但不允许全部为 `0`。

#### 权限与范围

- 菜单、路由和页面操作已从角色硬编码切换为权限驱动
- 角色支持 `data_scopes`：`all`、`department`、`department_and_sub`、`police_type`、`self`
- 用户、培训班、培训基地、题库、试卷、培训班考试已接入对象级范围控制

#### 系统配置

- `init_data.py` 会初始化两组默认系统配置模板：
  - `ai`：AI 提供商、地址、密钥、模型和推理参数
  - `training_schedule`：培训排课默认规则
- AI 智能出题和 AI 排课自然语言解析读取的是系统配置，而不是前端环境变量

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3.5、Vite 7、Ant Design Vue 4、Pinia 3、Vue Router 4、ECharts 6、xgplayer 3 |
| 后端 | FastAPI 0.104、SQLAlchemy 2.0、Alembic 1.12、Pydantic 2.10、pydantic-settings |
| 数据与中间件 | PostgreSQL 15、Redis 5、MinIO 7、Celery 5（gevent） |
| AI | OpenAI 兼容 SDK 2.6、Ollama 0.5、任务化调度 |
| 部署 | Docker Compose、Nginx |

## 仓库结构

```text
police-training-platform/
├── frontend/
│   ├── src/
│   │   ├── api/                 # 接口封装（24 个模块 + request 基础层）
│   │   ├── assets/styles/       # 全局样式、CSS 变量、移动端适配
│   │   ├── components/          # 通用组件（PermissionsTooltip 等）
│   │   ├── constants/           # 页面权限常量
│   │   ├── layouts/             # 主布局、登录布局、菜单配置
│   │   ├── router/              # 路由定义与守卫（40+ 路由）
│   │   ├── stores/              # Pinia 状态（auth store）
│   │   ├── utils/               # 前端工具函数（权限、日期、下载等）
│   │   ├── views/               # 页面模块（15 个业务域、50+ 页面）
│   │   │   ├── auth/            # 登录（用户名密码 / 手机验证码双模式）
│   │   │   ├── dashboard/       # 工作台（角色分视图）
│   │   │   ├── courses/         # 课程列表、课程详情、编辑器
│   │   │   ├── training/        # 培训班、排课、签到、报名、看板、AI 排课 / 个训
│   │   │   ├── exam/            # 考试管理、作答、成绩、试卷、题库、知识点、AI 出题 / 组卷
│   │   │   ├── resource/        # 资源库、我的资源、审核、策略、推荐、AI 资源生成
│   │   │   ├── instructor/      # 教官档案
│   │   │   ├── trainee/         # 学员档案
│   │   │   ├── talent/          # 人才库
│   │   │   ├── certificate/     # 结业证书
│   │   │   ├── report/          # 数据看板
│   │   │   ├── system/          # 用户 / 角色 / 部门 / 配置管理
│   │   │   ├── profile/         # 个人中心
│   │   │   └── mobile/          # 移动端扫码签到
│   │   └── mock/                # 历史 mock 与少量兜底逻辑
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── backend/
│   ├── app/
│   │   ├── views/               # 路由层（24 个路由模块）
│   │   ├── controllers/         # 控制器层
│   │   ├── agents/              # 智能体封装（8 个 Agent）
│   │   │   ├── base.py          # BaseAIAgent（OpenAI / Ollama 双通道）
│   │   │   ├── question_generator.py
│   │   │   ├── schedule_agent.py
│   │   │   ├── schedule_config_parser.py
│   │   │   ├── paper_assembly_parser.py
│   │   │   ├── personal_training_plan_agent.py
│   │   │   ├── teaching_resource_parser.py
│   │   │   └── teaching_resource_content_agent.py
│   │   ├── services/            # 业务服务（33 个服务模块）
│   │   ├── tasks/               # Celery 异步任务（5 个任务模块）
│   │   ├── models/              # SQLAlchemy 模型（18 个模型模块）
│   │   ├── schemas/             # Pydantic 模型（22 个 Schema 模块）
│   │   ├── templates/           # HTML 模板（教学资源课件）
│   │   ├── middleware/          # 鉴权、日志、异常处理
│   │   ├── database/            # 数据库初始化、Redis 客户端、自动迁移
│   │   └── utils/               # 授权判断、数据范围、初始化配置等
│   ├── alembic/                 # 数据库迁移（30 个版本）
│   ├── data/                    # 本地临时文件（.gitignore）
│   ├── tests/
│   ├── main.py                  # 应用入口
│   ├── config.py                # 配置中心
│   ├── logger.py                # Loguru 日志配置
│   ├── migrate.py               # 迁移管理
│   ├── init_data.py             # 种子数据初始化
│   ├── celery_app.py            # Celery 配置
│   ├── requirements.txt
│   └── Dockerfile
├── docs/
│   ├── 训练平台需求报告.html
│   ├── resource-library-feature-design.md
│   ├── AI排课自然语言转规则配置实施报告.md
│   ├── 一期智能体可行性研究与后续安排.md
│   ├── 一期智能体开发任务拆解.md
│   ├── 待实现功能清单.md
│   └── 问题BUG优先级排序.md
├── docker/
│   ├── docker-compose.yaml
│   ├── nginx.conf
│   ├── .env
│   └── Makefile
└── README.md
```

## 架构与分层

### 后端架构

```text
HTTP 请求
  ↓
middleware/         鉴权（JWT Bearer）、请求日志、全局异常处理
  ↓
views/              路由层 — 参数绑定、权限校验、调用 controller
  ↓
controllers/        控制器层 — 编排 service 调用、组装响应
  ↓
services/           业务服务层 — 核心逻辑、事务管理
  ↓
models/ + schemas/  ORM 模型 + Pydantic 校验
  ↓
database/           SQLAlchemy Session（连接池 20 / 溢出 50）、Redis 客户端
```

AI 智能体调用链：

```text
views/ai.py → controllers/ai.py → services/ai.py → tasks/*
                                                       ↓
                                               agents/* (LLM 调用)
                                                       ↓
                                               services/* (结果持久化)
```

### 前端架构

```text
router/             路由守卫（token + 权限 + 角色三重校验）
  ↓
layouts/            MainLayout（侧边栏 + 顶栏 + 移动端抽屉 / 底栏）
  ↓
views/              页面组件（组合式 API）
  ↓
api/                axios 封装（自动 camelCase ↔ snake_case 转换）
  ↓
stores/             Pinia 状态（auth store：登录态、角色、权限）
```

## 运行模式

### 模式一：本地分离开发

适合前后端联调、页面开发和接口调试。

#### 前置要求

- Node.js `^20.19.0` 或 `>=22.12.0`
- pnpm 9+ 或 npm
- Python 3.12
- PostgreSQL
- Redis
- MinIO

如果你要验证以下能力，还需要额外启动 Celery Worker：

- `AI 智能出题`
- `AI 自动组卷`
- `教学资源生成`
- `AI 排课建议`

#### 1. 配置前端环境变量

前端环境文件位于 `frontend/`：

- `frontend/.env.development`
- `frontend/.env.development.local`
- `frontend/.env.production`

注意：

- Vite 会优先读取 `.env.development.local`
- 当前仓库中的 `frontend/.env.development.local` 指向局域网地址，开始本地开发前请先改成你自己的后端地址，或临时删除该文件

示例：

```powershell
VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1
```

#### 2. 安装并启动后端

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python migrate.py upgrade
python init_data.py
python main.py
```

后端默认监听 `http://127.0.0.1:8001`。

#### 3. 可选：启动 Celery Worker

如果需要跑异步 AI 任务，再开一个终端：

```powershell
Set-Location backend
.\.venv\Scripts\Activate.ps1
celery -A celery_app worker --loglevel=info --pool=gevent --concurrency=10
```

#### 4. 安装并启动前端

```powershell
Set-Location ..\frontend
pnpm install
pnpm dev
```

由于 `vite.config.js` 固定了 `base: "/trainingplatform/"`，本地开发默认访问：

- 前端：`http://127.0.0.1:5173/trainingplatform/`
- 后端 Swagger：`http://127.0.0.1:8001/api/v1/docs`
- 后端 OpenAPI：`http://127.0.0.1:8001/api/v1/openapi.json`

### 模式二：Docker Compose 一体化部署

适合完整跑通前端、后端、数据库、Redis、对象存储和 Worker。

部署配置位于 `docker/`：

- `docker/.env`：Compose 环境变量
- `docker/docker-compose.yaml`：服务编排
- `docker/nginx.conf`：前端静态站点和反向代理
- `docker/Makefile`：常用部署命令

启动方式：

```powershell
Set-Location docker
make up
```

或直接使用 Compose：

```powershell
Set-Location docker
docker compose --env-file .env -f docker-compose.yaml up -d --build
```

默认会启动 6 个服务：

| 服务 | 说明 |
| --- | --- |
| `postgres` | PostgreSQL 15 Alpine，持久化存储 |
| `redis` | Redis，AOF 持久化 |
| `minio` | MinIO 对象存储，控制台 9001 端口 |
| `backend` | FastAPI 服务（8001 端口，不对外暴露） |
| `worker` | Celery Worker（gevent，并发 10） |
| `frontend` | Nginx 入口（反代 backend + minio） |

默认对外入口：

- 前端：`http://127.0.0.1:9090/trainingplatform/`
- 后端文档：`http://127.0.0.1:9090/api/v1/docs`
- 后端接口代理：`http://127.0.0.1:9090/api/v1/*`
- MinIO 文件代理：`http://127.0.0.1:9090/minio/*`

说明：

- `docker/.env` 中默认 `FRONTEND_PORT=9090`
- `frontend` 容器本身就是 Nginx 入口，统一反向代理 `backend` 和 `minio`
- Compose 默认不会把后端 `8001` 端口直接暴露到宿主机
- `backend` 容器启动入口会检查数据库状态；空库时会自动执行 `init_data.py` 并 `stamp head`
- 默认 Compose 没有启用 `beat` 服务；如果后续接入周期任务，需要单独加服务或手动启动

## 默认账号

首次执行 `python init_data.py` 后会创建以下种子账号：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `police2025` |
| 教官 | `instructor` | `teach2025` |
| 学员 | `student` | `learn2025` |

额外说明：

- 登录页保留了"快速演示登录"
- 顶部"演示角色切换"只改前端缓存展示，不会修改后端真实权限
- `init_data.py` 同时会同步系统配置模板到数据库

## 关键配置文件

| 文件 | 用途 |
| --- | --- |
| `frontend/.env.development` | 前端开发环境接口地址 |
| `frontend/.env.development.local` | 前端本地覆盖配置，优先级高于 `.env.development` |
| `frontend/.env.production` | 前端生产环境接口地址（相对路径 `/api/v1`） |
| `backend/.env.example` | 后端环境变量模板 |
| `backend/.env` | 本地后端实际配置 |
| `backend/.env.dev` | 可选的本地覆盖配置，启动时会覆盖 `.env` |
| `backend/config.py` | 后端配置中心（数据库、Redis、MinIO、JWT、LLM 等） |
| `backend/logger.py` | Loguru 日志配置（控制台 + 按天轮转文件） |
| `docker/.env` | Docker Compose 部署配置 |

## 文档索引

| 文档 | 用途 |
| --- | --- |
| `README.md` | 仓库级说明（本文件） |
| `frontend/README.md` | 前端维护说明 |
| `backend/README.md` | 后端维护说明 |
| `backend/API_DOCUMENTATION.md` | 后端接口文档（20 个模块） |
| `docs/训练平台需求报告.html` | 需求规格说明 |
| `docs/resource-library-feature-design.md` | 资源中心架构设计 |
| `docs/AI排课自然语言转规则配置实施报告.md` | AI 排课实施报告 |
| `docs/一期智能体可行性研究与后续安排.md` | 一期 AI 智能体可行性研究 |
| `docs/一期智能体开发任务拆解.md` | 一期 AI 智能体任务分解 |
| `docs/待实现功能清单.md` | 功能实现清单与差距分析 |
| `docs/问题BUG优先级排序.md` | 问题 / BUG 优先级排序 |

## 当前实现注意事项

### 外部依赖

- 资源上传依赖 MinIO；如果没有 MinIO，资源上传和文件直链能力不可用
- 培训扫码签到依赖 Redis；Redis 不可用时，二维码签到链路不可用
- AI 智能出题、AI 自动组卷、教学资源生成和 AI 排课建议依赖 Celery Worker；只启动 API 不启动 Worker 时，任务会停留在队列中
- AI 智能出题和 AI 排课自然语言解析读取系统配置组 `ai` 的模型配置；如果 `default_text_model`、`api_base_url`、`api_key` 没配好，出题任务会失败，排课自然语言模式会退化为规则兜底

### 同步 vs 异步

- AI 自动生成试卷、AI 个训方案目前虽然走任务表，但创建任务时仍会同步生成结果，不依赖 Worker
- 其余四条 AI 任务线（智能出题、自动组卷、教学资源生成、排课建议）均为 Celery 异步

### 交互约定

- 智能排课在任务流页面内完成规则确认和课表确认，不再回跳到创建区
- 培训排课规则默认值来自系统配置组 `training_schedule`，培训班级别可再覆盖；AI 排课任务还支持任务级覆盖
- `checkin_closed` 的真实语义是"课程仍在进行中，但签到窗口已结束"，不是"课次已结束"
- 手机验证码登录页会调用外部短信服务发送验证码，但后端 `POST /api/v1/auth/login/phone` 目前只按手机号查用户，不校验验证码真伪

### 数据与迁移

- 后端启动时会先尝试自动迁移，再做关键表结构校验；如果数据库版本号被错误标记为最新但关键字段缺失，服务会直接阻断启动
- 审核策略页会提示谨慎调整规则；如果当前没有启用审核规则，资源提交审核时会自动回退到管理员默认审核

### 前端注意事项

- 请求层自动做 camelCase ↔ snake_case 双向转换，前端代码统一使用 camelCase
- 前端主题色为警务蓝（`#003087`）+ 警徽金（`#c8a84b`），CSS 变量定义在 `frontend/src/assets/styles/variables.css`
- 移动端响应式断点 768px，移动端有底部导航栏和抽屉式侧边栏
- 仓库中仍保留 `frontend/src/mock/` 历史 mock 与少量兜底逻辑，联调请以后端 OpenAPI 和 `backend/API_DOCUMENTATION.md` 为准
