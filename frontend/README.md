# 警务训练平台前端

本文档面向 `frontend/` 目录的前端开发与维护，描述当前目录结构、环境变量、启动方式、构建方式和页面约定。

## 目录定位

前端基于 Vue 3 + Vite，负责：

- 登录、工作台、个人中心
- 课程资源、培训管理、考试系统、资源中心
- 系统管理、数据看板、人员档案（学员 / 教官 / 人才库 / 结业证书）
- AI 任务页：出题、组卷、生成试卷、教学资源生成、排课建议、个训方案
- 移动端扫码签到
- 与后端 `/api/v1` 接口联调

## 技术栈

| 类别 | 技术 | 版本 |
| --- | --- | --- |
| 框架 | Vue 3 | 3.5.25 |
| 构建工具 | Vite | 7.3.1 |
| UI 组件库 | Ant Design Vue | 4.2.6 |
| 状态管理 | Pinia | 3.0.4 |
| 路由 | Vue Router | 4.6.4 |
| HTTP | axios | 1.13.6 |
| 图表 | ECharts 6 + vue-echarts 8 | — |
| 播放器 | xgplayer | 3.0.23 |
| 二维码 | qrcode | 1.5.4 |
| 日期 | dayjs | 1.11.19 |

## 目录结构

```text
frontend/
├── public/                          # 静态资源
├── src/
│   ├── api/                         # 请求封装与接口模块（24 个模块 + request 基础层）
│   │   ├── request.js               # axios 实例（拦截器、camelCase ↔ snake_case 转换）
│   │   ├── auth.js                  # 登录鉴权
│   │   ├── user.js                  # 用户管理
│   │   ├── role.js                  # 角色管理
│   │   ├── department.js            # 部门管理
│   │   ├── permission.js            # 权限管理
│   │   ├── course.js                # 课程资源
│   │   ├── training.js              # 培训管理
│   │   ├── exam.js                  # 考试管理
│   │   ├── question.js              # 题库管理
│   │   ├── knowledgePoint.js        # 知识点管理
│   │   ├── resource.js              # 资源库
│   │   ├── review.js                # 审核工作流
│   │   ├── recommendation.js        # 推荐流
│   │   ├── ai.js                    # AI 任务流（6 条任务线）
│   │   ├── media.js                 # 文件上传（支持进度回调）
│   │   ├── dashboard.js             # 工作台
│   │   ├── profile.js               # 个人中心
│   │   ├── report.js                # 数据看板
│   │   ├── certificate.js           # 结业证书
│   │   ├── talent.js                # 人才库
│   │   ├── notice.js                # 公告
│   │   ├── system.js                # 系统配置
│   │   └── index.js                 # 模块聚合导出
│   ├── assets/
│   │   ├── logo.png
│   │   └── styles/
│   │       ├── variables.css        # CSS 变量（警务蓝 + 警徽金主题）
│   │       ├── global.css           # 全局样式与 Ant Design 覆盖
│   │       └── mobile.css           # 移动端适配（≤768px）
│   ├── components/
│   │   └── common/
│   │       └── PermissionsTooltip.vue   # 权限控制容器组件
│   ├── constants/
│   │   └── pagePermissions.js       # 页面权限常量（25+ 权限类别）
│   ├── layouts/
│   │   ├── MainLayout.vue           # 主布局（侧边栏 + 顶栏 + 移动端适配）
│   │   ├── AuthLayout.vue           # 登录布局
│   │   └── menuConfig.js            # 导航菜单结构（权限驱动）
│   ├── router/
│   │   └── index.js                 # 路由定义与守卫（40+ 路由）
│   ├── stores/
│   │   └── auth.js                  # Pinia 认证状态（登录态 / 角色 / 权限）
│   ├── utils/
│   │   ├── permissions.js           # 权限判断工具
│   │   ├── datetime.js              # 日期格式化
│   │   ├── download.js              # 文件下载
│   │   └── creatableTagSelect.js    # 可搜索可创建标签交互（课程 / 资源共用）
│   ├── views/                       # 页面模块（15 个业务域）
│   │   ├── auth/                    # 登录
│   │   ├── dashboard/               # 工作台
│   │   ├── courses/                 # 课程资源
│   │   ├── training/                # 培训管理
│   │   ├── exam/                    # 考试 / 试卷 / 题库 / 知识点
│   │   ├── resource/                # 资源中心
│   │   ├── instructor/              # 教官档案
│   │   ├── trainee/                 # 学员档案
│   │   ├── talent/                  # 人才库
│   │   ├── certificate/             # 结业证书
│   │   ├── report/                  # 数据看板
│   │   ├── system/                  # 系统管理
│   │   ├── profile/                 # 个人中心
│   │   ├── mobile/                  # 移动端（扫码签到）
│   │   └── ai/                      # AI（占位）
│   └── mock/                        # 历史 mock 与少量兜底逻辑
├── index.html                       # SPA 入口（标题：智慧教育训练平台）
├── .env.development                 # 开发环境变量
├── .env.development.local           # 开发环境本地覆盖
├── .env.production                  # 生产环境变量
├── package.json                     # 依赖与脚本
├── pnpm-lock.yaml                   # 锁文件
├── vite.config.js                   # Vite 配置（base: /trainingplatform/）
└── Dockerfile                       # 前端镜像构建文件
```

## 可用脚本

```powershell
pnpm dev       # 启动开发服务器
pnpm build     # 生产构建（输出到 dist/）
pnpm preview   # 预览构建产物
```

没有额外的 lint、test、type-check 脚本。

## 环境变量

| 文件 | 说明 |
| --- | --- |
| `.env.development` | 开发环境，默认 `http://localhost:8001/api/v1` |
| `.env.development.local` | 本地覆盖（优先级高于 `.env.development`） |
| `.env.production` | 生产环境，默认相对路径 `/api/v1` |

核心变量：

| 变量 | 说明 |
| --- | --- |
| `VITE_API_BASE_URL` | 后端 API 基地址 |

注意：

- Vite 会优先读取 `.env.development.local`
- 当前仓库中的 `.env.development.local` 指向局域网地址，开始本地开发前请先检查并改成自己的后端地址

本地联调常见配置：

```powershell
VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1
```

## 本地开发

前置要求：

- Node.js `^20.19.0` 或 `>=22.12.0`（与当前 Vite 7.3.1 一致）
- pnpm 9+ 或 npm

```powershell
Set-Location frontend
pnpm install
pnpm dev
```

默认访问地址：`http://127.0.0.1:5173/trainingplatform/`

说明：

- `vite.config.js` 固定了 `base: "/trainingplatform/"`
- `server.host` 已配置为 `0.0.0.0`
- 前端请求后端时会使用 `VITE_API_BASE_URL`

## 请求与数据格式约定

- 请求封装入口：`src/api/request.js`
- 前端内部统一使用 `camelCase`
- 请求层会自动处理 `camelCase ↔ snake_case` 转换
- 标准响应会自动解包 `{ code, message, data }`
- 401 响应自动跳转登录页
- 文件下载会保留 `blob / arraybuffer`
- 请求超时：15 秒
- 课程详情学习页离开页面时，会用原生 `fetch(..., { keepalive: true })` 兜底提交学习进度

接口能力以 `backend/API_DOCUMENTATION.md` 和后端 OpenAPI 为准。

## 主题与样式

| 变量 | 值 | 用途 |
| --- | --- | --- |
| `--primary-color` | `#003087` | 警务蓝（主色调） |
| `--secondary-color` | `#1a4fa0` | 浅蓝色 |
| `--accent-color` | `#c8a84b` | 警徽金（强调色） |
| `--sidebar-bg` | `#001849` | 侧边栏背景 |
| `--text-primary` | `#1a1a2e` | 主文字色 |

完整 CSS 变量定义在 `src/assets/styles/variables.css`。

移动端响应式断点：768px。移动端使用抽屉菜单和底部导航栏（工作台 / 培训 / 考试 / 我的）。

## 导航菜单结构

菜单定义在 `src/layouts/menuConfig.js`，按权限过滤：

```text
工作台
资源中心
  ├── 课程资源
  ├── 资源库
  ├── 资源推荐
  ├── 我的资源
  ├── 资源管理
  ├── 审核工作台
  └── 审核策略
培训管理
  ├── 培训班列表
  ├── 培训基地
  ├── 周训练计划
  └── 培训看板
考试中心
  ├── 考试管理
  └── 参加考试
题库管理
  ├── 试题仓库
  ├── 知识点管理
  └── AI 智能出题
卷库管理
  ├── 试卷仓库
  ├── AI 自动组卷
  └── AI 自动生成试卷
人员档案
  ├── 学员库
  ├── 教官库
  ├── 人才库
  └── 结业证书
数据看板
系统管理
  ├── 用户管理
  ├── 角色管理
  ├── 部门管理
  └── 配置管理（仅 admin）
```

父菜单在没有任何可见子菜单时自动隐藏。

## 路由守卫

路由守卫定义在 `src/router/index.js`，支持三种权限校验：

| meta 字段 | 说明 |
| --- | --- |
| `anyPermissions` | 至少拥有其中一个权限 |
| `allPermissions` | 必须拥有全部权限 |
| `roles` | 指定角色（如 `['admin']`、`['student']`） |

守卫逻辑：

1. 检查 `requiresAuth`：无 token 则跳转 `/login`
2. 检查 `anyPermissions` / `allPermissions`：无权限则跳转 `/`
3. 检查 `roles`：角色不匹配则跳转 `/`

仍有少量页面使用角色限制而不是权限限制：

- `system/configs`：`roles: ['admin']`
- `training/:id/enroll`：`roles: ['student']`

## 状态管理

`src/stores/auth.js`（Pinia store）：

**State：** `currentUser`（id、username、name、role、roleCodes、permissions、policeId、unit 等）

**Computed：** `isLoggedIn`、`role`、`permissions`、`isAdmin`、`isInstructor`、`isStudent`

**Methods：**

| 方法 | 说明 |
| --- | --- |
| `loginWithCredentials(username, password)` | 用户名密码登录 |
| `loginByPhone(phone, code)` | 手机验证码登录 |
| `logout()` | 登出并清理 localStorage |
| `restoreFromStorage()` | 从 localStorage 恢复或请求后端 |
| `switchRole(roleKey)` | 演示角色切换（仅改前端缓存） |
| `hasPermission(code)` | 单权限判断 |
| `hasAnyPermission(list)` | 任一权限判断 |
| `hasAllPermissions(list)` | 全部权限判断 |

## 关键页面与入口

### 登录与基础框架

| 文件 | 说明 |
| --- | --- |
| `src/views/auth/Login.vue` | 登录页（用户名密码 / 手机验证码双模式） |
| `src/layouts/MainLayout.vue` | 主布局（固定侧边栏 220px / 折叠 80px / 移动端隐藏） |
| `src/layouts/AuthLayout.vue` | 登录布局 |
| `src/layouts/menuConfig.js` | 菜单配置（权限驱动） |
| `src/router/index.js` | 路由定义与守卫 |
| `src/constants/pagePermissions.js` | 页面权限常量 |

### 课程域

| 文件 | 说明 |
| --- | --- |
| `src/views/courses/List.vue` | 课程列表（网格布局、筛选、搜索、排序） |
| `src/views/courses/Detail.vue` | 课程详情（章节、资源预览、笔记、问答、学习情况） |
| `src/views/courses/components/CourseEditorModal.vue` | 课程创建 / 编辑弹窗 |
| `src/views/courses/components/CourseChapterResourceSelector.vue` | 章节资源绑定 |

当前已覆盖的课程能力：

- 标签远程搜索与即时新建
- 可见范围选择（不是 `all` 时至少选择一个目标）
- 章节引用当前用户已发布资源，并可选择资源内具体文件
- 学习进度保存与恢复（视频记忆播放位置，离开页面时提交进度）
- 课程详情支持视频、文档、图片三类资源预览
- 学习情况标签页
- 课程资源绑定

### 考试域

| 文件 | 说明 |
| --- | --- |
| `src/views/exam/ExamManage.vue` | 考试管理 |
| `src/views/exam/ExamList.vue` | 在线考试列表 |
| `src/views/exam/Exam.vue` | 在线作答（全屏） |
| `src/views/exam/Result.vue` | 考试结果 |
| `src/views/exam/Scores.vue` | 成绩管理与分析 |
| `src/views/exam/PaperManage.vue` | 试卷仓库 |
| `src/views/exam/PaperDetail.vue` | 试卷详情 |
| `src/views/exam/QuestionBank.vue` | 题目仓库 |
| `src/views/exam/KnowledgePointManage.vue` | 知识点管理 |

AI 任务页：

| 文件 | 说明 |
| --- | --- |
| `src/views/exam/AiQuestionTask.vue` | AI 智能出题 |
| `src/views/exam/AiAssemblePaperTask.vue` | AI 自动组卷 |
| `src/views/exam/AiGeneratePaperTask.vue` | AI 自动生成试卷 |

共用组件：

| 文件 | 说明 |
| --- | --- |
| `components/AiTaskTabsLayout.vue` | AI 任务标签页布局 |
| `components/AiTaskTimeline.vue` | AI 任务时间线 |
| `components/PaperDraftEditor.vue` | 试卷草稿编辑器 |
| `components/PaperTypeConfigEditor.vue` | 题型配置编辑器（字段名 + 分值小计 + 总量汇总） |
| `components/QuestionFormModal.vue` | 题目编辑弹窗 |
| `components/AdmissionScopeSelector.vue` | 准入考试范围选择 |

工具函数（`src/views/exam/utils/`）：

| 文件 | 说明 |
| --- | --- |
| `knowledgePointRemoteSelect.js` | 知识点远程搜索（默认前 20 条） |
| `paperTypeConfig.js` | 题型配置标准化 |
| `questionSort.js` | 题目排序 |

当前已覆盖的考试能力：

- 题目支持多知识点选择、搜索与即时创建
- "题库管理 / 知识点管理" 已拆成独立菜单入口
- AI 智能出题结果带知识点列表，确认入库时自动关联
- AI 自动组卷页展示解析结果、选题放宽记录和试卷草稿
- 知识点选择已统一为远程搜索，不再全量加载
- 题型配置允许单项数量为 `0`，但不能全部为 `0`

### 培训域

| 文件 | 说明 |
| --- | --- |
| `src/views/training/List.vue` | 培训列表（卡片式） |
| `src/views/training/Detail.vue` | 培训详情（步骤条 + 多标签页） |
| `src/views/training/Base.vue` | 培训基地管理 |
| `src/views/training/Schedule.vue` | 周训练计划 |
| `src/views/training/AiScheduleTask.vue` | AI 排课建议（完整任务流） |
| `src/views/training/AiPersonalTrainingTask.vue` | AI 个训方案 |
| `src/views/training/Board.vue` | 培训看板 |
| `src/views/training/Enroll.vue` | 学员报名 |
| `src/views/training/EnrollManage.vue` | 报名审核 |
| `src/views/training/Checkin.vue` | 扫码签到 |
| `src/views/training/Checkout.vue` | 签退评课 |
| `src/views/training/History.vue` | 培训训历 |

培训详情页内容组件（`src/views/training/components/`）：

| 组件 | 说明 |
| --- | --- |
| `TrainingOverviewContent.vue` | 班级概览 |
| `TrainingScheduleContent.vue` | 课程安排 |
| `TrainingScheduleRuleContent.vue` | 排课规则 |
| `TrainingExamsContent.vue` | 考试安排 |
| `TrainingStudentsContent.vue` | 学员名单 |
| `TrainingCourseChangeLogsContent.vue` | 课程变更记录 |
| `TrainingNoticeCard.vue` | 公告卡片 |
| `TrainingQuickOpsCard.vue` | 快捷操作卡片 |
| `TrainingAttendanceStatsCard.vue` | 签到统计卡片 |
| `TrainingNextActionCard.vue` | 下一步操作卡片 |
| `ScheduleStructuredTaskForm.vue` | 手动排课表单 |

#### AI 排课建议页当前行为

AI 排课建议页是完整任务流页面：

- 创建区分为"智能排课"和"手动排课"两个标签
- 智能排课先输入自然语言要求，再创建异步任务
- 任务列表里展示解析规则、确认规则、生成课表和确认应用的阶段
- 规则确认直接在任务详情内完成，不再回跳到创建区
- 课表生成后可查看主方案、备选方案、冲突清单和周历预览
- 支持是否覆盖当前课表
- 支持保存修改、删除任务、删除任务中的课次
- 页面权限已与培训班管理权限对齐

### 资源域

| 文件 | 说明 |
| --- | --- |
| `src/views/resource/Library.vue` | 资源库（搜索 + 推荐） |
| `src/views/resource/Detail.vue` | 资源详情 |
| `src/views/resource/Recommend.vue` | 资源推荐（沉浸式全屏） |
| `src/views/resource/MyResources.vue` | 我的资源 |
| `src/views/resource/Manage.vue` | 资源管理 |
| `src/views/resource/ReviewQueue.vue` | 审核工作台 |
| `src/views/resource/PolicyManage.vue` | 审核策略 |
| `src/views/resource/TeachingResourceGenerationTask.vue` | 教学资源生成 |

资源组件：

| 文件 | 说明 |
| --- | --- |
| `components/ResourceUploadModal.vue` | 资源上传弹窗 |
| `components/ResourceViewer.vue` | 媒体查看器（视频 / 文档） |

当前资源域前端已覆盖：

- 资源库和我的资源通过弹窗上传资源，标签输入支持远程搜索 + 回车创建
- 我的资源提供"教学资源生成"入口（路由 `/resource/teaching-generate`；旧 `/resource/ai-generate` 保留兼容跳转）
- 教学资源生成页：创建阶段填写自然语言要求 → 生成预览后补资源摘要、标签和可见范围 → 标题由系统自动生成
- 标签逻辑已抽成公共组合式工具 `src/utils/creatableTagSelect.js`，课程和资源共用
- 审核策略页支持作用域、上传者约束、审核路径预览和前端校验
- 审核策略页会提示空规则时系统回退到管理员默认审核

### 系统与其他

| 文件 | 说明 |
| --- | --- |
| `src/views/system/UserManage.vue` | 用户管理（CRUD、导入导出、角色分配） |
| `src/views/system/RoleManage.vue` | 角色管理（CRUD、权限分配） |
| `src/views/system/DepartmentManage.vue` | 部门管理（树形结构、导入导出） |
| `src/views/system/ConfigManage.vue` | 配置管理（仅 admin） |
| `src/views/dashboard/Index.vue` | 工作台（管理员 / 教官 / 学员三视图） |
| `src/views/profile/Index.vue` | 个人中心 |
| `src/views/report/Dashboard.vue` | 数据看板（KPI / 趋势 / 排名 / 分布） |
| `src/views/trainee/List.vue` / `Detail.vue` | 学员档案 |
| `src/views/instructor/List.vue` / `Detail.vue` | 教官档案 |
| `src/views/talent/Index.vue` | 人才库 |
| `src/views/certificate/Index.vue` | 结业证书 |
| `src/views/mobile/Checkin.vue` | 移动端扫码签到 |

## Docker 构建

前端镜像构建文件：`frontend/Dockerfile`

构建过程：

1. 在 Node 22 Alpine 镜像中安装依赖并执行 `pnpm build`
2. 把 `dist/` 发布到 Nginx
3. 复用仓库根目录下的 `docker/nginx.conf`

如果使用 `docker/docker-compose.yaml`：

- `frontend` 服务使用仓库根目录作为构建上下文
- Dockerfile 路径为 `frontend/Dockerfile`
- 最终统一通过 `http://<host>:9090/trainingplatform/` 对外访问

## 当前约定与注意事项

### 权限与菜单

- 菜单过滤基于 `hasAnyPermission`
- 路由守卫支持 `meta.anyPermissions / meta.allPermissions / meta.roles`
- 父菜单在没有任何可见子菜单时自动隐藏
- 按钮级权限通过 `PermissionsTooltip` 组件控制

### 登录与认证

- 登录页保留"快速演示登录"和顶部"演示角色切换"能力，但不会改变后端真实权限
- 手机验证码登录页会调用外部短信接口发送验证码；后端当前不校验验证码真伪
- Token 存储在 localStorage，通过 `Authorization: Bearer {token}` 发送

### AI 页面行为

- AI 智能出题：创建任务后异步排队
- AI 自动组卷：创建任务后异步排队，任务详情中展示解析条件、选题说明和试卷草稿
- AI 排课建议：创建任务后异步排队，在任务列表中完成规则确认和课表确认
- 教学资源生成：创建任务后异步排队，预览课件后补充资源信息并确认
- AI 自动生成试卷 / AI 个训方案：创建后通常直接拿到结果
- 知识点选择已统一为远程搜索，不再全量加载
- 题型配置允许单项数量为 `0`，但不能全部为 `0`

### 培训页面行为

- 培训详情页可以从"考试安排"直接快捷创建培训班考试
- 培训详情页中的"课程变更记录"等标签依赖后端返回的 `canView...` 标记决定是否展示
- 排课规则默认值来自后端系统配置，培训班级别可覆盖

### 课程页面行为

- 课程创建 / 编辑弹窗支持课程可见范围；不是 `all` 时至少选择一个目标
- 课程详情页会保存并恢复视频最近播放位置，离开页面时主动提交进度

### 其他

- 仓库中仍保留 `src/mock/` 历史 mock 与少量兜底逻辑，联调时以后端接口为准

## 进一步阅读

| 文档 | 用途 |
| --- | --- |
| `README.md`（仓库根目录） | 前后端整体说明 |
| `backend/README.md` | 后端维护说明 |
| `backend/API_DOCUMENTATION.md` | 后端接口明细 |
