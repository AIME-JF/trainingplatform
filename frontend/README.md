# 警务训练平台前端

本文档面向 `frontend/` 目录的前端开发与维护，描述当前目录结构、环境变量、启动方式、构建方式和页面约定。

## 目录定位

前端基于 Vue 3 + Vite，负责：

- 登录、工作台、个人中心
- 课程资源、培训管理、考试系统、资源中心
- 系统管理、数据看板、人才库
- AI 任务页：出题、组卷、生成试卷、排课建议、个训方案
- 与后端 `/api/v1` 接口联调

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
│   ├── assets/                  # 本地资源与全局样式
│   ├── components/              # 通用组件
│   │   └── common/              # 权限提示等基础组件
│   ├── constants/               # 页面权限常量
│   ├── layouts/                 # 主布局、认证布局、菜单配置
│   ├── router/                  # 路由定义与守卫
│   ├── stores/                  # Pinia 状态
│   ├── utils/                   # 前端工具函数
│   ├── views/                   # 页面模块
│   └── mock/                    # 历史 mock 与少量兜底逻辑
├── .env.development             # 开发环境变量
├── .env.development.local       # 开发环境本地覆盖
├── .env.production              # 生产环境变量
├── package.json                 # 依赖与脚本
├── pnpm-lock.yaml               # 锁文件
├── vite.config.js               # Vite 配置
└── Dockerfile                   # 前端镜像构建文件
```

## 可用脚本

当前 `package.json` 只提供以下脚本：

```powershell
pnpm dev
pnpm build
pnpm preview
```

没有额外的 lint、test、type-check 脚本。

## 环境变量

当前使用的环境文件：

- `frontend/.env.development`
- `frontend/.env.development.local`
- `frontend/.env.production`

核心变量：

| 变量 | 说明 |
| --- | --- |
| `VITE_API_BASE_URL` | 后端 API 基地址 |

注意：

- Vite 会优先读取 `.env.development.local`
- 当前仓库中的 `.env.development.local` 指向局域网地址，开始本地开发前请先检查并改成自己的后端地址
- 生产环境默认使用相对路径 `/api/v1`

本地联调常见配置：

```powershell
VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1
```

## 本地开发

以下命令以 PowerShell 7 为例。

前置要求：

- Node.js `^20.19.0` 或 `>=22.12.0`（与当前 `Vite 7.3.1` 一致）
- pnpm 9+ 或 npm

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
- 请求层会自动处理 `camelCase <-> snake_case` 转换
- 标准响应会自动解包 `{ code, message, data }`
- 文件下载会保留 `blob / arraybuffer`
- 课程详情学习页离开页面时，会用原生 `fetch(..., { keepalive: true })` 兜底提交学习进度

接口能力以 `backend/API_DOCUMENTATION.md` 和后端 OpenAPI 为准。

## 关键页面与入口

### 登录与基础框架

- 登录页：`frontend/src/views/auth/Login.vue`
- 主布局：`frontend/src/layouts/MainLayout.vue`
- 路由：`frontend/src/router/index.js`
- 菜单配置：`frontend/src/layouts/menuConfig.js`
- 页面权限常量：`frontend/src/constants/pagePermissions.js`

当前基础框架特性：

- 桌面端使用固定侧边栏、固定顶部栏、内容区独立滚动
- 移动端使用抽屉菜单和底部导航
- 侧边栏和主要菜单入口已切换为权限驱动

### 课程域

- 课程列表：`frontend/src/views/courses/List.vue`
- 课程详情：`frontend/src/views/courses/Detail.vue`
- 课程创建 / 编辑：`frontend/src/views/courses/components/CourseEditorModal.vue`

当前前端已覆盖的课程能力：

- 标签远程搜索与即时新建
- 可见范围选择
- 章节引用当前用户已发布资源，并可选择资源内具体 `文件1 / 文件2 ...`
- 学习进度保存与恢复
- 课程详情支持视频、文档、图片三类资源预览
- 学习情况标签页
- 课程资源绑定

### 考试域

- 考试管理：`frontend/src/views/exam/ExamManage.vue`
- 在线考试列表：`frontend/src/views/exam/ExamList.vue`
- 在线作答：`frontend/src/views/exam/Exam.vue`
- 成绩管理：`frontend/src/views/exam/Scores.vue`
- 试卷仓库：`frontend/src/views/exam/PaperManage.vue`
- 试卷详情：`frontend/src/views/exam/PaperDetail.vue`
- 题目仓库：`frontend/src/views/exam/QuestionBank.vue`
- 知识点管理：`frontend/src/views/exam/KnowledgePointManage.vue`

AI 任务页：

- AI 智能出题：`frontend/src/views/exam/AiQuestionTask.vue`
- AI 自动组卷：`frontend/src/views/exam/AiAssemblePaperTask.vue`
- AI 自动生成试卷：`frontend/src/views/exam/AiGeneratePaperTask.vue`

共用组件：

- `frontend/src/views/exam/components/AiTaskTabsLayout.vue`
- `frontend/src/views/exam/components/AiTaskTimeline.vue`
- `frontend/src/views/exam/components/PaperDraftEditor.vue`
- `frontend/src/views/exam/components/QuestionFormModal.vue`

当前前端已覆盖的考试能力：

- 题目支持多知识点选择、搜索与即时创建
- “题库管理 / 知识点管理” 已拆成独立菜单入口
- AI 智能出题结果会带知识点列表，确认入库时自动关联知识点
- AI 自动组卷页会展示解析结果、选题放宽记录和试卷草稿
- AI 智能出题、AI 自动组卷、AI 自动生成试卷的知识点选择已改成远程搜索，默认展示前 20 条，输入关键词后按远程结果刷新
- AI 自动组卷、AI 自动生成试卷的题型配置已改成带字段名、分值小计和总量汇总的编辑器；允许单项数量为 `0`，但不能全部为 `0`

### 培训域

- 培训列表：`frontend/src/views/training/List.vue`
- 培训基地：`frontend/src/views/training/Base.vue`
- 周训练计划：`frontend/src/views/training/Schedule.vue`
- AI 排课建议：`frontend/src/views/training/AiScheduleTask.vue`
- 培训看板：`frontend/src/views/training/Board.vue`
- 培训班详情：`frontend/src/views/training/Detail.vue`
- 扫码签到：`frontend/src/views/training/Checkin.vue`
- 签退评课：`frontend/src/views/training/Checkout.vue`
- 培训训历：`frontend/src/views/training/History.vue`
- AI 个训方案：`frontend/src/views/training/AiPersonalTrainingTask.vue`

当前培训详情页已覆盖：

- 班级概览
- 课程安排
- 排课规则
- 考试安排
- 学员名单
- 课程变更记录
- 公告、快捷操作、签到统计

#### AI 排课建议页当前行为

当前 AI 排课建议页不是单纯的结果展示页，而是完整任务流页面：

- 创建区分为“智能排课”和“手动排课”两个标签
- 智能排课先输入自然语言要求，再创建异步任务
- 任务列表里展示解析规则、确认规则、生成课表和确认应用的阶段
- 规则确认直接在任务详情内完成，不再回跳到创建区
- 课表生成后可查看主方案、备选方案、冲突清单和周历预览
- 支持是否覆盖当前课表
- 支持保存修改、删除任务、删除任务中的课次
- 页面权限已经与培训班管理权限对齐

### 资源域

- 资源上传弹窗：`frontend/src/views/resource/components/ResourceUploadModal.vue`
- 资源库：`frontend/src/views/resource/Library.vue`
- 资源推荐：`frontend/src/views/resource/Recommend.vue`
- 资源详情：`frontend/src/views/resource/Detail.vue`
- 我的资源：`frontend/src/views/resource/MyResources.vue`
- 资源管理：`frontend/src/views/resource/Manage.vue`
- 审核工作台：`frontend/src/views/resource/ReviewQueue.vue`
- 审核策略：`frontend/src/views/resource/PolicyManage.vue`
- 教学资源生成：`frontend/src/views/resource/TeachingResourceGenerationTask.vue`

当前资源域前端已覆盖：

- 资源库和我的资源通过弹窗上传资源，标签输入与课程标签交互一致，支持远程搜索已有标签并回车创建新标签
- 我的资源提供“教学资源生成”入口，路由为 `/resource/teaching-generate`；旧 `/resource/ai-generate` 仅保留兼容跳转
- 教学资源生成页当前只在创建阶段填写自然语言要求；生成预览后再补资源摘要、标签和可见范围，标题由系统自动生成
- 资源标签逻辑已抽成公共组合式工具，课程和资源共用一套“可搜索、可创建”标签交互
- 审核策略页支持作用域、上传者约束、审核路径预览和更完整的前端校验
- 审核策略页会明确提示：空规则时系统回退到管理员默认审核；如无明确业务变更，建议优先沿用现有规则

### 系统与其他

- 用户管理：`frontend/src/views/system/UserManage.vue`
- 角色管理：`frontend/src/views/system/RoleManage.vue`
- 部门管理：`frontend/src/views/system/DepartmentManage.vue`
- 配置管理：`frontend/src/views/system/ConfigManage.vue`
- 人才库：`frontend/src/views/talent/Index.vue`
- 数据看板：`frontend/src/views/report/Dashboard.vue`
- 结业证书：`frontend/src/views/certificate/Index.vue`

## Docker 构建

前端镜像构建文件位于：

- `frontend/Dockerfile`

当前镜像构建过程：

1. 在 Node 22 Alpine 镜像中安装依赖并执行 `pnpm build`
2. 把 `dist/` 发布到 Nginx
3. 复用仓库根目录下的 `docker/nginx.conf`

如果你使用根目录下的 `docker/docker-compose.yaml`：

- `frontend` 服务使用仓库根目录作为构建上下文
- Dockerfile 路径为 `frontend/Dockerfile`
- 最终统一通过 `http://<host>:9090/trainingplatform/` 对外访问

## 当前约定与注意事项

- 菜单过滤基于 `hasAnyPermission`
- 路由守卫支持 `meta.anyPermissions / meta.allPermissions / meta.roles`
- 父菜单在没有任何可见子菜单时自动隐藏
- 仍有少量页面使用角色限制而不是权限限制，例如：
  - `system/configs` 使用 `roles: ['admin']`
  - `training/:id/enroll` 使用 `roles: ['student']`
- 登录页保留“快速演示登录”和顶部“演示角色切换”能力，但不会改变后端真实权限
- 手机验证码登录页会调用外部短信接口发送验证码；后端 `POST /auth/login/phone` 当前并不会校验验证码真伪
- AI 页面当前用户可见行为与后端实现保持一致：
  - AI 智能出题：创建任务后异步排队
  - AI 自动组卷：创建任务后异步排队，任务详情中展示解析条件、选题说明和试卷草稿
  - AI 排课建议：创建任务后异步排队，并在任务列表中完成规则确认和课表确认
  - AI 自动生成试卷 / AI 个训方案：创建后通常会直接拿到结果
- 考试域几个 AI 页面中的知识点选择已统一为远程搜索，不再一次性拉取全部知识点。
- AI 自动组卷、AI 自动生成试卷在创建任务前会校验题型配置：可把某个题型数量设为 `0`，但不能把所有题型都设为 `0`。
- 培训详情页可以从“考试安排”直接快捷创建培训班考试，并携带 `trainingId` 跳转到考试管理页
- 培训详情页中的“课程变更记录”与“学习情况”等标签，都会依赖后端返回的 `canView...` 标记再决定是否展示
- 课程创建 / 编辑弹窗支持课程可见范围；如果范围不是 `all`，前端会要求至少选择一个目标
- 课程详情页会保存并恢复视频最近播放位置，离开页面时会主动提交最新进度
- 仓库中仍保留 `frontend/src/mock/` 历史 mock 与少量兜底逻辑，联调时以后端接口为准
