# 警务训练平台前端 v2（教官 / 学员端）

本文档面向 `frontend-v2/` 目录的前端开发与维护，描述当前目录结构、设计规范、环境变量、启动方式和页面约定。

## 目录定位

面向**教官和学员**的 Vue 3 + TypeScript 前端，不包含管理员功能。负责：

- 登录、工作台、个人中心
- 班级（培训班）列表与详情
- 培训班、排课、签到签退、报名
- 在线考试（参加、作答、成绩）
- 资源库浏览、我的资源
- 移动端适配（底部导航栏）

## 技术栈

| 类别 | 技术 | 版本 |
| --- | --- | --- |
| 框架 | Vue 3 | 3.5 |
| 语言 | TypeScript | 5.9 |
| 构建工具 | Vite | 8.0 |
| UI 组件库 | Ant Design Vue | 4.2 |
| 状态管理 | Pinia | 3.0 |
| 路由 | Vue Router | 4.6 |
| HTTP | axios | 1.14 |
| API 生成 | Orval | 8.6 |
| 日期 | dayjs | 1.11 |
| 图标 | @ant-design/icons-vue | 7.0 |

## 目录结构

```text
frontend-v2/
├── orval.config.ts              # Orval API 生成配置
├── vite.config.ts               # Vite 配置（proxy、alias）
├── tsconfig.json
├── tsconfig.app.json
├── package.json
├── .env.development             # 开发环境 API 地址
├── .env.production              # 生产环境 API 地址
├── index.html
└── src/
    ├── main.ts                  # 入口：Pinia + Router + Antd + dayjs 中文
    ├── App.vue                  # ConfigProvider（主题 + 中文 locale）
    ├── env.d.ts                 # Vite 环境变量类型声明
    ├── api/
    │   ├── custom-instance.ts   # Orval mutator（Bearer token + 信封解包 + 401）
    │   └── generated/           # Orval 自动生成（按 tag 拆文件 + model/）
    ├── router/
    │   ├── index.ts             # createRouter + beforeEach 守卫
    │   └── routes.ts            # 路由表（仅教官/学员）
    ├── stores/
    │   └── auth.ts              # 认证状态（login / logout / 权限判断）
    ├── layouts/
    │   ├── MobileLayout.vue     # 主布局：图标侧栏 + 内容 + 底部导航
    │   └── AuthLayout.vue       # 登录页布局
    ├── composables/
    │   ├── useAuth.ts           # 权限快捷方法
    │   └── useMobile.ts         # 响应式 isMobile（768px 断点）
    ├── styles/
    │   ├── variables.css        # 全局 CSS 变量（设计 token）
    │   ├── theme.ts             # Ant Design Vue 主题 token 配置
    │   ├── global.css           # 全局基础样式
    │   └── mobile.css           # 移动优先响应式样式
    ├── constants/
    │   └── permissions.ts       # 页面权限常量
    ├── components/              # 公共组件
    └── views/                   # 页面组件
        ├── auth/Login.vue       # 登录页
        ├── dashboard/Index.vue  # 工作台
        └── classes/
            ├── List.vue         # 班级列表（卡片网格，调用 GET /trainings）
            └── Detail.vue       # 班级详情（调用 GET /trainings/:id）
```

## 可用脚本

```bash
pnpm dev            # 启动开发服务器
pnpm build          # 生产构建
pnpm preview        # 预览构建产物
pnpm api:generate   # 从后端 OpenAPI 生成 API 客户端（需后端运行）
```

## 环境变量

| 文件 | 说明 |
| --- | --- |
| `.env.development` | 开发环境，默认 `http://127.0.0.1:8001/api/v1` |
| `.env.production` | 生产环境，默认相对路径 `/api/v1` |

核心变量：

| 变量 | 说明 |
| --- | --- |
| `VITE_API_BASE_URL` | 后端 API 基地址 |

## 本地开发

前置要求：Node.js >= 20、pnpm 9+

```bash
cd frontend-v2
pnpm install
pnpm dev
```

默认访问地址：`http://127.0.0.1:5173/`

Vite 已配置 `/api/v1` 代理到 `http://127.0.0.1:8001`，开发时无需 CORS。

### Orval API 同步

后端运行时执行：

```bash
pnpm api:generate
```

生成的文件位于 `src/api/generated/`，按后端 tag 拆分。生成的类型使用 snake_case（与后端一致），前端代码直接使用 snake_case 字段名，不做运行时转换。

## 设计规范

以下规范提取自设计稿，所有新页面必须遵循。

### 整体风格

- **现代扁平化**：大圆角（8-16px）、轻阴影、无重边框
- **留白充分**：内容区 padding 24-32px，卡片间距 16px
- **色彩柔和**：封面使用淡色渐变，不使用纯色块

### 色彩体系

| Token | 值 | 用途 |
| --- | --- | --- |
| `--v2-primary` | `#4B6EF5` | 主色（选中态、按钮、链接） |
| `--v2-primary-hover` | `#3B5DE0` | 主色 hover |
| `--v2-primary-light` | `#EEF2FF` | 主色浅底（选中背景、标签底色） |
| `--v2-success` | `#34C759` | 成功/在线 |
| `--v2-warning` | `#FF9500` | 警告 |
| `--v2-danger` | `#FF3B30` | 错误/删除 |
| `--v2-info` | `#5AC8FA` | 信息 |
| `--v2-bg` | `#F5F6FA` | 页面背景 |
| `--v2-bg-card` | `#FFFFFF` | 卡片/容器背景 |
| `--v2-text-primary` | `#1D1D1F` | 主文字 |
| `--v2-text-secondary` | `#6E6E73` | 次要文字 |
| `--v2-text-muted` | `#AEAEB2` | 辅助/占位文字 |
| `--v2-border` | `#E5E5EA` | 边框 |
| `--v2-border-light` | `#F2F2F7` | 轻边框/分隔线 |

### 卡片封面渐变预设

课程卡片封面使用 8 种淡色渐变轮换，居中显示半透明白色图标：

| Token | 色系 |
| --- | --- |
| `--v2-cover-blue` | 蓝色 `#DBEAFE → #BFDBFE` |
| `--v2-cover-green` | 绿色 `#D1FAE5 → #A7F3D0` |
| `--v2-cover-pink` | 粉色 `#FCE7F3 → #FBCFE8` |
| `--v2-cover-purple` | 紫色 `#EDE9FE → #DDD6FE` |
| `--v2-cover-yellow` | 黄色 `#FEF3C7 → #FDE68A` |
| `--v2-cover-orange` | 橙色 `#FFEDD5 → #FED7AA` |
| `--v2-cover-teal` | 青色 `#CCFBF1 → #99F6E4` |
| `--v2-cover-rose` | 玫红 `#FFE4E6 → #FECDD3` |

### 工具图标色

详情页教学工具图标使用纯色圆角方块（28x28px, border-radius 6px），图标白色：

| Token | 值 | 用途 |
| --- | --- | --- |
| `--v2-icon-red` | `#FF3B30` | 课程管理、发布通知、直播等 |
| `--v2-icon-orange` | `#FF9500` | 成绩设置、发布作业等 |
| `--v2-icon-green` | `#34C759` | 资源库、备课、教室授课等 |
| `--v2-icon-blue` | `#007AFF` | OBE管理、学习资源等 |
| `--v2-icon-teal` | `#5AC8FA` | 课堂回放、学情数据等 |
| `--v2-icon-purple` | `#AF52DE` | 备用 |

### 圆角

| Token | 值 | 用途 |
| --- | --- | --- |
| `--v2-radius-xs` | `4px` | 标签、小元素 |
| `--v2-radius-sm` | `8px` | 按钮、输入框、小卡片 |
| `--v2-radius` | `12px` | 主卡片、容器 |
| `--v2-radius-lg` | `16px` | 大面板、弹窗 |
| `--v2-radius-xl` | `20px` | 特殊装饰 |
| `--v2-radius-full` | `9999px` | 胶囊按钮、标签 |

### 阴影

| Token | 值 | 用途 |
| --- | --- | --- |
| `--v2-shadow-sm` | `0 1px 3px rgba(0,0,0,0.04)` | 默认卡片 |
| `--v2-shadow` | `0 2px 8px rgba(0,0,0,0.06)` | hover 状态 |
| `--v2-shadow-lg` | `0 8px 24px rgba(0,0,0,0.08)` | 弹出层、悬浮卡片 |

### 字体

```
-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif
```

### 布局规范

#### 图标侧栏（桌面端）

- 宽度：72px，白色背景，右侧 1px 轻边框
- 顶部：品牌图标（36x36 渐变蓝圆角方块）
- 导航项：56x56px 热区，上方 20px 图标 + 下方 10px 文字（首页、日历、班级、学习资源）
- 选中态：浅蓝背景 `--v2-primary-light` + 蓝色文字/图标
- 未选中态：`--v2-text-muted` 灰色
- 底部固定：用户头像（32px 蓝色圆形，首字母）+ 用户名（10px, muted, 最多 60px 截断）

#### 底部导航栏（移动端）

- 高度：64px，白色背景，顶部 1px 轻边框 + 轻阴影
- 导航项：22px 图标 + 10px 文字，等分宽度
- 选中态：`--v2-primary` 蓝色
- 4 个 tab：首页 / 班级 / 资源 / 我的

#### 页面头部横幅（详情页）

- 深色渐变背景：`linear-gradient(135deg, #1A1A2E 0%, #16213E 40%, #0F3460 100%)`
- 白色大标题（28px, bold）、白色半透明元数据（13px）
- 右侧浮动信息卡片（白色背景，圆角 8px）

#### 课程卡片

- 圆角 12px，白色背景
- 封面高度 120px，淡色渐变 + 居中白色图标（48px, 70% 透明度）
- 左下角学期标签：黑色半透明底 + 白色文字（11px）
- 右上角类型标签：白色半透明底 + 灰色文字（11px）
- 卡片体 12px padding，标题 14px bold，教师名 12px muted
- hover：translateY(-2px) + shadow-lg

#### 教学工具面板

- 白色卡片容器，圆角 12px，padding 24px
- 四列等分网格（移动端两列）
- 每列：中文标题 16px bold + 英文副标题 12px muted
- 工具项：28px 彩色圆角图标 + 14px 文字，垂直列表间距 12px

#### 胶囊 Tab 按钮

- 圆角 9999px（胶囊形），padding 6px 18px
- 选中态：蓝色填充 + 白色文字
- 未选中态：白色底 + 灰色边框 + 灰色文字

#### 过滤器按钮组

- 容器：白色底 + 圆角 8px + padding 4px
- 按钮：圆角 8px，padding 6px 16px
- 选中态：浅蓝底 `--v2-primary-light` + 蓝色文字

### 响应式断点

| 断点 | 说明 |
| --- | --- |
| ≤ 768px | 移动端：隐藏侧栏、显示底部导航、课程网格 2 列、工具面板 2 列 |
| ≥ 769px | 桌面端：显示图标侧栏、隐藏底部导航、课程网格 6 列、工具面板 4 列 |

### 交互规范

- **卡片 hover**：上浮 2px + 大阴影过渡
- **导航项过渡**：color 和 background 0.15s
- **触控友好**：所有可点击元素最小 44px 热区
- **文字溢出**：单行 `text-overflow: ellipsis`，不换行

## 请求与数据格式约定

- 请求封装入口：`src/api/custom-instance.ts`
- **不做 camelCase/snake_case 运行时转换**：Orval 生成 snake_case 类型，直接使用
- 标准响应自动解包 `{ code, message, data }`
- 401 响应自动跳转登录页
- Token 存储在 localStorage，通过 `Authorization: Bearer {token}` 发送
- 请求超时：15 秒

## 导航结构

### 图标侧栏（桌面端）

```
AI (品牌图标)
首页
日历
班级 ← 选中高亮
学习资源
───────
用户头像
用户名
```

### 底部导航（移动端）

```
首页 | 班级 | 资源 | 我的
```

## 路由

已注册路由（仅教官/学员）：

| 路径 | 说明 |
| --- | --- |
| `/login` | 登录 |
| `/` | 工作台 |
| `/classes` | 班级列表 |
| `/classes/:id` | 班级详情 |
| `/classes/schedule/:id?` | 周训练计划 |
| `/classes/:id/enroll` | 报名 |
| `/classes/:id/checkin` | 签到 |
| `/classes/:id/checkout` | 签退 |
| `/exam/list` | 在线考试 |
| `/exam/do/:id` | 考试作答 |
| `/exam/result/:id` | 考试结果 |
| `/resource/library` | 资源库 |
| `/resource/recommend` | 资源推荐 |
| `/resource/detail/:id` | 资源详情 |
| `/resource/my` | 我的资源 |
| `/profile` | 个人中心 |

不包含：`/system/*`、`/exam/manage`、`/exam/scores`、`/question/*`、`/paper/*`、`/resource/manage`、`/resource/review`、`/resource/policy`、`/instructor`、`/trainee`、`/talent`、`/report`、`/courses`

## 路由守卫

| meta 字段 | 说明 |
| --- | --- |
| `anyPermissions` | 至少拥有其中一个权限 |
| `allPermissions` | 必须拥有全部权限 |
| `roles` | 指定角色（如 `['student']`） |

## 状态管理

`src/stores/auth.ts`（Pinia store）：

**State：** `currentUser`（id、username、role、role_codes、permissions 等）

**Computed：** `isLoggedIn`、`role`、`permissions`、`isInstructor`、`isStudent`

**Methods：** `loginWithCredentials`、`restoreFromStorage`、`logout`、`hasPermission`、`hasAnyPermission`、`hasAllPermissions`

## 进一步阅读

| 文档 | 用途 |
| --- | --- |
| `README.md`（仓库根目录） | 前后端整体说明 |
| `frontend/README.md` | v1 前端维护说明 |
| `backend/README.md` | 后端维护说明 |
| `backend/API_DOCUMENTATION.md` | 后端接口明细 |
