# 警务训练平台前端

本文档面向 `frontend/` 目录的前端开发与维护，描述当前目录结构、环境变量、启动方式、构建方式和关键约定。

## 目录定位

前端基于 Vue 3 + Vite，负责：

- 登录、工作台和个人中心
- 课程学习、培训管理、考试系统、资源中心
- 系统管理、人员档案、数据看板
- 与后端 `/api/v1` 接口联调

前端源码已从仓库根目录迁移到 `frontend/`，后续前端相关说明均以本目录为准。

## 技术栈

| 类别 | 技术 |
| --- | --- |
| 框架 | Vue 3 |
| 构建工具 | Vite 7 |
| UI 组件库 | Ant Design Vue 4 |
| 状态管理 | Pinia |
| 路由 | Vue Router 4 |
| 图表 | ECharts 6、vue-echarts |
| 播放器 | xgplayer |
| HTTP | axios |

## 目录结构

```text
frontend/
├── public/                      # 静态资源
├── src/
│   ├── api/                     # 请求封装与接口模块
│   ├── assets/                  # 本地资源
│   ├── components/              # 通用组件
│   ├── layouts/                 # 主布局与认证布局
│   ├── router/                  # 路由定义
│   ├── stores/                  # Pinia 状态
│   ├── utils/                   # 前端工具函数
│   ├── views/                   # 页面模块
│   └── mock/                    # 历史 mock 与少量兜底逻辑
├── .env.development             # 开发环境变量
├── .env.production              # 生产环境变量
├── package.json                 # 依赖与脚本
├── pnpm-lock.yaml               # 锁文件
├── vite.config.js               # Vite 配置
└── Dockerfile                   # 前端镜像构建文件
```

## 环境变量

当前使用的环境文件：

- `frontend/.env.development`
- `frontend/.env.production`

核心变量：

| 变量 | 说明 |
| --- | --- |
| `VITE_API_BASE_URL` | 后端 API 基地址 |

本地联调常见配置：

```powershell
VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1
```

## 本地开发

以下命令以 PowerShell 7 为例。

### 安装依赖

```powershell
Set-Location frontend
pnpm install
```

### 启动开发服务器

```powershell
Set-Location frontend
pnpm dev
```

默认访问地址：

- 前端：`http://127.0.0.1:5173/trainingplatform/`

说明：

- `vite.config.js` 固定了 `base: "/trainingplatform/"`
- `server.host` 已配置为 `0.0.0.0`
- 前端请求后端时会使用 `VITE_API_BASE_URL`

## 构建与预览

### 生产构建

```powershell
Set-Location frontend
pnpm build
```

构建产物输出到 `frontend/dist/`。

### 本地预览

```powershell
Set-Location frontend
pnpm preview
```

## 请求与数据格式约定

- 请求封装入口：`frontend/src/api/request.js`
- 前端内部统一使用 `camelCase`
- 与后端交互时，请求层会自动处理 `camelCase <-> snake_case` 转换
- 接口能力以 `backend/API_DOCUMENTATION.md` 和后端 OpenAPI 为准

## 关键业务入口

常见维护位置：

- 课程列表 / 详情：`frontend/src/views/courses/List.vue`、`Detail.vue`
- 课程创建 / 编辑弹窗：`frontend/src/views/courses/components/CourseEditorModal.vue`
- 培训管理：`frontend/src/views/training`
- 考试系统：`frontend/src/views/exam`
- 试卷详情页：`frontend/src/views/exam/PaperDetail.vue`
- 准入考试发布页：`frontend/src/views/exam/ExamManage.vue`
- 准入考试适用范围选择：`frontend/src/views/exam/components/AdmissionScopeSelector.vue`
- AI 任务页：`frontend/src/views/exam/AiQuestionTask.vue`、`AiAssemblePaperTask.vue`、`AiGeneratePaperTask.vue`
- 资源中心：`frontend/src/views/resource`
- 系统管理：`frontend/src/views/system`
- 人员档案：`frontend/src/views/trainee`、`frontend/src/views/instructor`、`frontend/src/views/talent`
- 主菜单与侧边栏：`frontend/src/layouts/MainLayout.vue`
- 路由：`frontend/src/router/index.js`

## Docker 构建

前端镜像构建文件位于：

- `frontend/Dockerfile`

该镜像会：

1. 在 Node 镜像中安装依赖并执行 `pnpm build`
2. 将 `dist/` 发布到 Nginx
3. 复用仓库中的 `docker/nginx.conf`

如果你使用仓库根目录下的 `docker/docker-compose.yaml`：

- `frontend` 服务当前使用仓库根目录作为构建上下文
- Dockerfile 路径为 `frontend/Dockerfile`
- Nginx 配置直接从 `docker/nginx.conf` 复制，不需要在 `frontend/` 目录额外维护一份

## 当前注意事项

- 前端仍保留 `frontend/src/mock/` 中的历史 mock 与少量兜底逻辑，真实联调请以后端接口为准
- 登录页保留演示角色切换，但不会改变后端真实权限
- 前端登录后会通过 `/api/v1/auth/me` 获取当前用户角色与权限集合；后端新增权限码和内置角色修正依赖 Alembic 迁移下发，而不是运行时自动补齐
- 侧边栏、移动端抽屉和主要菜单入口已改成权限驱动：
  - 菜单配置位于 `frontend/src/layouts/menuConfig.js`
  - 页面权限常量位于 `frontend/src/constants/pagePermissions.js`
  - 路由守卫会按 `meta.anyPermissions / meta.allPermissions` 校验，不再只看角色
- 培训管理、考试系统、数据范围等页面已按当前后端能力改造，文档优先看仓库根 README 与后端接口文档
- AI 能力已经收敛为 3 个任务页：
  - `AI 智能出题`
  - `AI 自动组卷`
  - `AI 自动生成试卷`
- 3 个 AI 页面都采用 `创建任务 / 任务列表` 标签页切换
- 试卷仓库的“查看”已改成独立详情页，不再使用只读抽屉；详情页会按题目折叠展示选项、标准答案和解析
- 发布准入考试时，适用范围不再是自由输入，而是结构化选择：
  - 全部
  - 指定用户
  - 指定部门
  - 指定角色
- 培训班创建 / 编辑时已支持“报名是否需要申请”：
  - `申请审核`
  - `直接通过`
- 培训班详情页的“学员名单”标签已内嵌“申请管理”弹层，可直接审核报名申请并填写拒绝理由
- 课程创建 / 编辑弹窗已支持课程标签远程搜索：
  - 输入关键字会请求 `/courses/tags`
  - 输入新标签按回车会直接调用 `/courses/tags` 创建
- 视频章节上传后会自动读取视频时长并换算课程时长；文档章节仍由表单手填学习时长
- 课程详情页现在会保存并恢复视频最近播放位置，重新进入课程会跳转到最近学习章节
- 课程详情页已新增“学习情况”标签页，只有后端返回 `canViewLearningStatus=true` 时才展示
- 培训班详情页已新增“课程变更记录”标签页，只有后端返回 `canViewCourseChangeLogs=true` 时才展示
- 培训班状态为 `ended` 时，课程安排区域前端会直接禁用新增、编辑、删除操作
- 学员端在线考试列表现在会同时展示培训班考试和准入考试，并按考试类型自动进入对应作答 / 成绩页
