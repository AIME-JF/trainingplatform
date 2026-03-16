# 警务训练平台

警务训练平台是一个前后端分离的警务教育训练系统，覆盖课程学习、培训组织、在线考试、资源中心、AI 任务辅助出题组卷、数据看板和系统管理等业务域。

本仓库同时包含：

- `frontend/` 前端应用
- `backend/` FastAPI 后端服务
- `docker/` Docker Compose 部署编排

## 项目概览

### 业务模块

- 工作台：按管理员、教官、学员展示不同首页数据
- 课程学习：课程列表、详情、章节进度、课程笔记、课程答疑
- 考试系统：统一题库、试卷管理、试卷快照、独立准入考试、培训班内考试、成绩管理、考试分析
- 培训管理：培训班详情、流程步骤条、培训基地、报名审核、名单锁定、当前课程、课次签到 / 签退、培训资源绑定、考试安排
- 资源中心：资源库、上传、推荐流、审核工作台、审核策略
- AI 能力：AI 智能出题、AI 自动组卷、AI 自动生成试卷
- 系统管理：用户、角色、部门、权限、警种、培训基地、数据范围
- 其他：公告、个人中心、结业证书、人才库、数据看板

### 最近已落地的业务调整

- 考试系统已拆成两条线：
  - `试卷管理`：独立维护试卷草稿、发布、归档，题目快照固化在试卷层
  - `准入考试`：独立维护，不直接隶属培训班
  - `培训班内考试`：必须关联 `training_id`，用于随堂测、班内考核、结业考试、补考
- 考试管理页不再直接从题库抽题，而是只允许选择“已发布试卷”创建考试；试卷发布后不可再修改题目，考试创建后不可更换试卷。
- 准入考试的适用范围已改为结构化限制：
  - `all`：全部学员
  - `user`：指定学员
  - `department`：指定部门
  - `role`：指定角色
- 准入考试现在会在后端按适用范围做真实拦截；只有范围内学员才能看到、进入和提交该考试。
- 培训班可通过 `admission_exam_id` 绑定准入考试；学员报名时如果该培训班配置了准入考试，则必须先通过该考试。
- 培训班已新增“报名是否需要申请”开关：
  - `true`：学员报名后进入待审核列表
  - `false`：学员报名后直接通过
- 培训班详情页的“学员名单”标签已内嵌申请管理弹层，班主任和管理员可直接在详情页审核报名申请，并在拒绝时填写理由。
- AI 能力已统一改成任务流，入口收敛为：
  - `题库管理 -> AI 智能出题`
  - `卷库管理 -> AI 自动组卷`
  - `卷库管理 -> AI 自动生成试卷`
- 3 条 AI 任务统一流程为：
  - 填写信息
  - 创建任务
  - 后端模拟生成结果
  - 查看任务
  - 可选编辑题目 / 试卷
  - 确认入库
  - 完成
- 培训基地已独立成表和管理页面；培训班支持维护 `department_id`、`police_type_id`、`training_base_id`，选择培训基地时会自动带出地点，并优先继承基地部门。
- 题库题目已支持可选 `police_type_id`，为后续按警种做题库隔离和数据域控制提供基础。
- 角色管理已支持配置数据范围：
  - `all`
  - `department`
  - `department_and_sub`
  - `police_type`
  - `self`
- 用户、培训班、培训基地、题库当前已接入对象级数据域控制；资源库尚未接入这一轮的数据范围规则。
- 试卷仓库和培训班考试列表 / 详情也已接入数据范围控制：
  - 试卷会按试题归属警种和创建人范围过滤
  - 培训班考试会按所属培训班的部门、警种、班主任 / 创建人范围过滤
- 试卷仓库已新增独立试卷详情页，详情接口返回题目标准答案；前端按题目维度折叠展示题干、选项、答案和解析。
- 培训详情页已围绕“步骤条 + 详情页操作”组织，而不是把重操作堆在列表页。
- 培训班流程已改成严格顺序：
  - 发布招生
  - 锁定名单
  - 开班
  - 结班
- 如果提前点击“锁定名单”或“开班”，前端会弹窗确认是否跳过前置环节；后端也会校验顺序，只有显式传入 `skip_steps` 才会自动补齐并锁定被跳过环节。
- 课程签到已改成课次状态流：
  - 开始签到
  - 结束签到
  - 开始签退
  - 结束签退
  - 跳过课次
- 课次状态当前按后端真实枚举流转：
  - `pending`：未开始
  - `checkin_open`：签到中
  - `checkin_closed`：课程进行中，签到窗口已结束
  - `checkout_open`：签退中
  - `completed / skipped / missed`
- 权限边界按当前实现收敛为：
  - 管理员：全部可操作
  - 班主任：当前培训班全部可操作
  - 主讲 / 带教教官：仅自己课次可操作
  - 学员：只能查看和操作自己的报名、签到、训历等数据
  - 数据范围控制：在功能权限之外，用户 / 培训班 / 培训基地 / 题库还会额外按部门、警种、本人范围过滤
- 权限补齐和内置角色默认数据范围修正现在统一通过 Alembic 数据迁移下发，不再依赖应用启动时做运行时补丁
- 前端侧边栏、移动端菜单和页面访问控制已从角色硬编码切换为权限驱动：
  - 菜单通过 `hasAnyPermission` 过滤
  - 父菜单在没有任何可见子菜单时自动隐藏
  - 路由也按权限集合校验，不再仅依赖 `admin / instructor / student` 角色分支

### 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite 7、Ant Design Vue 4、Pinia、Vue Router 4、ECharts 6、xgplayer |
| 后端 | FastAPI、SQLAlchemy 2、Alembic、Pydantic 2 |
| 数据与中间件 | PostgreSQL、Redis、MinIO、Celery |
| AI | OpenAI 兼容 SDK，当前默认对接 DeepSeek |
| 部署 | Docker Compose、Nginx |

## 仓库结构

```text
police-training-platform/
├── frontend/                    # Vue 前端
│   ├── src/
│   │   ├── api/                 # 接口封装（自动 camelCase <-> snake_case 转换）
│   │   ├── layouts/             # 主布局与认证布局
│   │   ├── router/              # 前端路由
│   │   ├── stores/              # Pinia 状态
│   │   ├── views/               # 页面模块
│   │   └── mock/                # 历史 mock 数据与兜底逻辑
│   ├── public/                  # 前端静态资源
│   ├── package.json             # 前端依赖与脚本
│   ├── vite.config.js           # Vite 配置
│   └── Dockerfile               # 前端镜像
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── views/               # 路由层
│   │   ├── controllers/         # 控制器层
│   │   ├── services/            # 业务层
│   │   ├── models/              # SQLAlchemy 模型
│   │   ├── schemas/             # Pydantic 模型
│   │   ├── middleware/          # 鉴权、日志、异常处理
│   │   └── database/            # 数据库与 Redis 初始化
│   ├── alembic/                 # 数据库迁移
│   ├── data/                    # 本地数据目录
│   └── tests/                   # 现有后端测试脚本
├── docs/                        # 设计与需求文档
├── docker/                      # Docker Compose、Nginx、部署环境变量
└── backend/Dockerfile           # 后端 / Worker 镜像
```

## 运行模式

### 模式一：本地分离开发

适合前后端联调、页面开发、接口调试。

#### 前置要求

- Node.js 18+
- pnpm 9+ 或 npm
- Python 3.12
- PostgreSQL
- Redis
- MinIO

#### 1. 配置前端环境变量

前端请求基地址来自 `frontend/` 目录下的环境文件：

- `frontend/.env.development`：本地开发使用
- `frontend/.env.production`：生产构建使用

当前仓库中的 `frontend/.env.development` 可能指向局域网地址，开始开发前请改成你自己的后端地址，例如：

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

#### 3. 安装并启动前端

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
- `docker/nginx.conf`：前端静态站点与反向代理配置
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

默认对外入口：

- 前端：`http://127.0.0.1:4001/trainingplatform/`
- 后端文档：`http://127.0.0.1:4001/api/v1/docs`
- 后端接口代理：`http://127.0.0.1:4001/api/v1/*`
- MinIO 文件代理：`http://127.0.0.1:4001/minio/*`

说明：

- Nginx 会把 `/` 重定向到 `/trainingplatform/`
- 前端生产环境通过相对路径 `/api/v1` 调后端
- Compose 默认不会把后端 `8001` 端口直接暴露到宿主机
- 当前前端镜像构建文件位于 `frontend/Dockerfile`，并通过仓库根目录作为构建上下文复用 `docker/nginx.conf`

## 默认账号

首次执行 `python init_data.py` 后会创建以下种子账号：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `police2025` |
| 教官 | `instructor` | `teach2025` |
| 学员 | `student` | `learn2025` |

额外说明：

- 登录页保留了“快速演示登录”和“演示角色切换”能力
- 顶部角色切换仅用于前端演示，不会修改后端真实权限

## 关键配置文件

| 文件 | 用途 |
| --- | --- |
| `frontend/.env.development` | 前端开发环境接口地址 |
| `frontend/.env.production` | 前端生产环境接口地址 |
| `backend/.env.example` | 后端环境变量模板 |
| `backend/.env` | 本地后端实际配置，不建议提交 |
| `docker/.env` | Docker Compose 部署配置 |

## 文档索引

- 仓库级说明：`README.md`
- 前端维护说明：`frontend/README.md`
- 后端维护说明：`backend/README.md`
- 后端接口文档：`backend/API_DOCUMENTATION.md`

## 当前实现注意事项

- 手机验证码登录的前端页面会调用外部短信服务发送验证码，但后端 `POST /api/v1/auth/login/phone` 目前只按手机号查用户，暂未校验验证码真伪。
- 后端启动时会先尝试 Alembic 自动迁移，再做关键表结构校验；如果数据库版本被错误标记为最新但关键字段缺失，服务会直接阻断启动并提示执行 `python migrate.py upgrade`。
- 自动迁移不再对“已有业务表但没有 `alembic_version`”的旧库直接 `stamp head`。如果是历史数据库，请先备份，再手动执行迁移。
- 新增权限码、`admin` 权限回填、内置角色默认 `data_scopes` 修正等兼容性数据，也通过 Alembic 迁移发版；部署新版本时应先执行 `python migrate.py upgrade`。
- 内置角色默认数据范围当前为：
  - `admin`：`all`
  - `instructor`：`department_and_sub + police_type + self`
  - `student`：`department + police_type + self`
- 用户管理、培训班、培训基地、题库这四类对象已经接入数据范围控制；如果角色只有功能权限、没有匹配的数据范围，列表和详情仍可能被过滤。
- 资源上传依赖 MinIO；如果只启动前后端、不提供 MinIO，则资源上传和文件直链能力不可用。
- 培训扫码签到依赖 Redis；Redis 不可用时，二维码签到链路不可用。
- 培训班流程接口现在会校验“发布 -> 锁定名单 -> 开班”的顺序；如果越级调用且未显式确认跳步，后端会直接拒绝。
- `checkin_closed` 的业务语义是“课程仍在进行中，但签到窗口已结束”，不是“课次已结束”。
- 仓库中仍保留 `frontend/src/mock/` 历史数据和少量兜底逻辑；接口能力请以后端 OpenAPI 与 `backend/API_DOCUMENTATION.md` 为准。
