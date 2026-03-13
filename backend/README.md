# 警务训练平台后端

本文档面向后端开发与运维，描述 `backend/` 服务的真实结构、启动流程、环境变量和维护方式。

## 服务定位

后端服务基于 FastAPI，负责以下能力：

- JWT 登录鉴权与权限解析
- 用户、角色、部门、权限、警种管理
- 课程、考试、培训、证书、公告、个人中心
- 资源上传、资源库、推荐流、审核工作流
- 报表导出、人才库、AI 组卷与 AI 教案生成
- PostgreSQL、Redis、MinIO、Celery 的集成

## 技术栈

| 类别 | 技术 |
| --- | --- |
| Web 框架 | FastAPI |
| ORM | SQLAlchemy 2 |
| 配置 | pydantic-settings + python-dotenv |
| 数据库 | PostgreSQL |
| 迁移 | Alembic |
| 缓存 / 队列 | Redis、Celery |
| 文件存储 | MinIO |
| 鉴权 | python-jose JWT |
| 密码加密 | passlib[bcrypt] |
| 日志 | Loguru |
| Excel 导入导出 | openpyxl |
| AI | OpenAI 兼容客户端 |

## 目录结构

```text
backend/
├── app/
│   ├── __init__.py              # FastAPI 应用实例、startup/shutdown
│   ├── views/                   # 路由层
│   ├── controllers/             # 控制器层
│   ├── services/                # 业务层
│   ├── models/                  # SQLAlchemy 模型
│   ├── schemas/                 # Pydantic 模型
│   ├── middleware/              # 鉴权、日志、异常处理
│   ├── database/                # 数据库、Redis、自动迁移
│   ├── tasks/                   # Celery 任务
│   ├── utils/                   # 工具函数与权限分组
│   └── runtime_sync.py          # 运行时兼容修复与额外权限同步
├── alembic/                     # 数据库迁移版本
├── data/                        # 本地数据目录
├── docker/                      # 容器启动脚本
├── tests/                       # 现有测试脚本
├── main.py                      # uvicorn 启动入口
├── config.py                    # Settings 定义
├── migrate.py                   # 迁移管理脚本
├── init_data.py                 # 种子数据初始化
└── celery_app.py                # Celery 实例
```

## 路由组成

已注册业务路由来自 `app/views/*.py`，当前包括：

- `auth`
- `dashboard`
- `courses`
- `exams`
- `questions`
- `trainings`
- `certificates`
- `profile`
- `report`
- `ai`
- `talent`
- `police-types`
- `media`
- `users`
- `notices`
- `roles`
- `departments`
- `permissions`
- `resources`
- `reviews`
- `resources/recommendations`

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

1. 如果 `AUTO_MIGRATE_ON_STARTUP=True`，调用 `app.database.auto_migrate.run_auto_migration()`
2. 调用 `init_db()`，用 `Base.metadata.create_all()` 补齐仍缺失的表
3. 调用 `sync_runtime_state()`，同步额外权限和兼容性修复
4. 测试 Redis 连接

注意：

- 这些步骤不会执行 `init_data.py`
- 首次初始化种子数据仍需手动运行 `python init_data.py`

## 环境变量

推荐从 `backend/.env.example` 复制为 `backend/.env` 后再修改。

### 核心配置

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `PROJECT_NAME` | 项目名称 | `警务训练平台` |
| `VERSION` | 应用版本 | `1.0.0` |
| `DEBUG` | 调试模式 | `true` |
| `API_V1_STR` | API 前缀 | `/api/v1` |
| `AUTO_MIGRATE_ON_STARTUP` | 启动时自动检查迁移 | `true` |

### 数据库配置

| 变量 | 说明 |
| --- | --- |
| `DATABASE_URL` | PostgreSQL 连接串 |
| `DATABASE_ECHO` | 是否打印 SQL |

### Redis 配置

| 变量 | 说明 |
| --- | --- |
| `REDIS_HOST` | Redis 主机 |
| `REDIS_PORT` | Redis 端口 |
| `REDIS_PASSWORD` | Redis 密码，可为空 |
| `REDIS_DB` | Redis DB 编号 |

### MinIO 配置

| 变量 | 说明 |
| --- | --- |
| `MINIO_PUBLIC_URL` | 对外访问文件的基础地址 |
| `MINIO_ENDPOINT` | MinIO 内部连接地址 |
| `MINIO_ACCESS_KEY` | MinIO 账号 |
| `MINIO_SECRET_KEY` | MinIO 密码 |
| `MINIO_SECURE` | 是否启用 HTTPS |
| `MINIO_BUCKET` | 存储桶名称 |

### Celery 配置

| 变量 | 说明 |
| --- | --- |
| `CELERY_BROKER_URL` | Broker 地址 |
| `CELERY_RESULT_BACKEND` | 结果存储地址 |

### 鉴权与 AI 配置

| 变量 | 说明 |
| --- | --- |
| `SECRET_KEY` | JWT 签名密钥 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间，默认 30 天 |
| `LLM_BASE_URL` | 大模型服务地址 |
| `LLM_API_KEY` | 大模型密钥 |
| `LLM_MODEL` | 使用的大模型名称 |

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

然后根据本机环境修改：

- `DATABASE_URL`
- `REDIS_*`
- `MINIO_*`
- `SECRET_KEY`
- `LLM_*`

### 3. 迁移数据库

```powershell
python migrate.py upgrade
```

### 4. 初始化种子数据

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

- Docker 镜像统一通过 `backend/docker/entrypoint.sh` 接收 `api`、`worker`、`beat` 三种模式
- 当前代码仓库内已有 `app/tasks/recommendation.py`，但大部分业务仍以同步 API 为主

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

当前已提交迁移包括：

- 培训主模型
- 用户与警种/单位拆分
- 媒体文件与章节文件关联
- 课程笔记、课程答疑
- 资源库、审核流、推荐流
- 权限 `group` 字段

## 认证与权限

### 认证方式

- 登录接口：`POST /api/v1/auth/login`
- 手机登录接口：`POST /api/v1/auth/login/phone`
- 受保护接口统一使用 `Authorization: Bearer <token>`

### 统一响应

除下载流和文件直链外，接口通常返回：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {}
}
```

分页数据结构：

```json
{
  "page": 1,
  "size": 10,
  "total": 100,
  "items": []
}
```

### 权限模型

- 用户权限由角色权限与部门权限共同决定
- `admin` 角色会在运行时自动补齐所有激活权限
- 权限表带有 `group` 字段，缺失时会根据路由自动推断
- 运行时额外补充的权限定义位于 `app/runtime_sync.py`

### 受保护对象

后端已明确保护以下对象：

- `admin` 角色不可编辑、不可删除、不可重分配权限
- `admin` 用户不可修改角色
- 用户删除采用软删除：`is_active=False`

## 文件上传与对象存储

资源和媒体相关能力依赖 MinIO：

- 上传接口：`POST /api/v1/media/upload`
- 取文件接口：`GET /api/v1/media/files/{file_id}`

实现特性：

- 上传时按 SHA-256 秒传去重
- 文件写入 MinIO
- 数据库保留文件元数据
- 历史本地文件仍支持兼容读取
- `GET /media/files/{id}` 可能直接返回文件，也可能 307 跳转到 MinIO 直链

## 批量导入

后端提供三类 Excel 导入：

- 全员底库导入：`POST /api/v1/users/import/police-base`
- 培训学员导入：`POST /api/v1/trainings/{training_id}/import/students`
- 培训教官导入：`POST /api/v1/trainings/{training_id}/import/instructors`
- 培训课表导入：`POST /api/v1/trainings/{training_id}/import/schedule`

导入特点：

- 基于 `openpyxl` 解析 `.xlsx`
- 自动识别中英文表头别名
- 缺失部门与警种会自动创建
- 新建账号默认密码为 `Police@123456`

## Docker 运行说明

`backend/Dockerfile` 会构建 API 与 Worker 共用镜像。

容器内启动入口：

- `api`：`python main.py`
- `worker`：`celery -A celery_app worker --loglevel=info --pool=gevent ...`
- `beat`：`celery -A celery_app beat --loglevel=info`

完整部署建议从仓库根目录下的 `docker/` 目录操作，而不是单独运行后端镜像。

## 种子数据

`python init_data.py` 会初始化：

- 权限
- 根部门 `ROOT`
- 基础警种
- `admin` / `instructor` / `student` 三个默认角色
- 三个示例用户

默认账号：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `police2025` |
| 教官 | `instructor` | `teach2025` |
| 学员 | `student` | `learn2025` |

## 已知行为与注意事项

- `POST /api/v1/auth/login/phone` 目前尚未校验验证码内容，只根据手机号查用户并发 token。
- 后端启动不会自动执行 `init_data.py`，首次建库必须手动运行。
- 当前同时保留了 Alembic 迁移与 `Base.metadata.create_all()` 补表逻辑，后者主要用于兼容旧库或开发环境缺表。
- 某些系统管理接口同时提供 REST 风格和兼容旧前端的 `/create`、`/update`、`/delete` 别名。

## 进一步阅读

- 接口明细：`backend/API_DOCUMENTATION.md`
- 前后端整体说明：仓库根目录 `README.md`
