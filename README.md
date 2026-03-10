# 🚔 广西公安警务训练平台

<p align="center">
  <b>Police Training Platform</b><br/>
  基于 Vue 3 + Vite + Ant Design Vue 构建的智慧警务训练管理系统
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Vue-3.5-42b883?logo=vue.js&logoColor=white" />
  <img src="https://img.shields.io/badge/Vite-7.3-646cff?logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/Ant%20Design%20Vue-4.x-1677ff?logo=ant-design&logoColor=white" />
  <img src="https://img.shields.io/badge/Pinia-3.x-ffd859?logo=pinia&logoColor=black" />
  <img src="https://img.shields.io/badge/ECharts-6.x-aa344d?logo=apache-echarts&logoColor=white" />
  <img src="https://img.shields.io/badge/License-Private-red" />
</p>

---

## 📖 项目简介

**广西公安警务训练平台** 是一套面向公安机关的一体化训练管理系统，旨在实现警务培训的数字化、智能化管理。平台覆盖从课程学习、考试测评、培训组织到 AI 辅助教学的全流程业务，支持**管理员**、**教官**、**学员**三种角色的差异化操作视图。

### 💡 核心亮点

- 🤖 **AI 智能辅助** — 支持 AI 智能组卷和 AI 教案自动生成
- 👮 **三色角色体系** — 管理员 / 教官 / 学员 三种角色各有专属工作台和功能权限
- 📱 **移动端适配** — 支持移动端底部导航栏及扫码签到功能
- 📚 **资源中心闭环** — 资源上传、审核流转、推荐下载、详情学习一体化
- 📊 **数据可视化** — 基于 ECharts 的数据看板，实时呈现培训数据
- 🎓 **全流程覆盖** — 课程学习 → 培训管理 → 资源中心 → 在线考试 → 结业证书 完整闭环

---

## 🏗️ 技术架构

| 类别 | 技术栈 |
|------|--------|
| **前端框架** | Vue 3 (Composition API + `<script setup>`) |
| **构建工具** | Vite 7 |
| **UI 组件库** | Ant Design Vue 4 |
| **状态管理** | Pinia 3 |
| **路由管理** | Vue Router 4 |
| **图表可视化** | ECharts 6 + vue-echarts 8 |
| **视频播放器** | xgplayer 3 |
| **日期处理** | Day.js |
| **二维码生成** | qrcode |

---

## 📁 项目结构

```
policetrainingplatform/
├── public/                      # 静态资源
├── src/
│   ├── api/                     # Axios API 模块（已对接后端）
│   │   ├── request.js           # 请求封装（camelCase/snake_case 自动转换）
│   │   ├── resource.js          # 资源库接口
│   │   ├── review.js            # 资源审核接口
│   │   ├── recommendation.js    # 推荐与埋点接口
│   │   └── ...
│   ├── assets/                  # 样式、图片等静态资源
│   │   └── styles/              # 全局样式文件
│   ├── layouts/                 # 布局组件
│   │   └── MainLayout.vue       # 主布局（侧边栏 + 顶栏 + 移动端底部导航）
│   ├── mock/                    # 历史 mock 数据（部分页面可能仍保留兜底）
│   ├── router/
│   │   └── index.js             # 路由定义与导航守卫
│   ├── stores/
│   │   └── auth.js              # 认证状态（登录/登出/角色切换）
│   ├── views/
│   │   ├── resource/            # 资源中心
│   │   │   ├── Library.vue      # 资源库
│   │   │   ├── Recommend.vue    # 资源推荐（视频/图片预览，文档下载）
│   │   │   ├── Detail.vue       # 资源详情（左右布局）
│   │   │   ├── Upload.vue       # 上传资源
│   │   │   ├── ReviewQueue.vue  # 审核工作台
│   │   │   ├── PolicyManage.vue # 审核策略
│   │   │   ├── Manage.vue       # 资源管理（管理员）
│   │   │   └── components/ResourceViewer.vue
│   │   ├── ai/
│   │   ├── auth/
│   │   ├── courses/
│   │   ├── dashboard/
│   │   ├── exam/
│   │   ├── instructor/
│   │   ├── mobile/
│   │   ├── profile/
│   │   ├── report/
│   │   ├── talent/
│   │   └── training/
│   ├── App.vue
│   └── main.js
├── backend/                     # FastAPI 后端
├── index.html
├── vite.config.js
└── package.json
```

---

## 🚀 快速开始

### 环境要求

- **Node.js** >= 18.x
- **npm** >= 9.x（或 pnpm / yarn）

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/AIME-JF/trainingplatform.git
cd trainingplatform

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev

# 4. 构建生产版本
npm run build

# 5. 预览生产构建
npm run preview
```

启动后默认访问 `http://localhost:5173`

---

## 👥 角色与权限

平台支持三种角色，每种角色拥有不同的功能权限和工作台视图：

### 🔴 管理员 (Admin)

| 功能 | 说明 |
|------|------|
| 工作台 | 系统公告、近期培训班概览、快速操作入口 |
| 培训管理 | 创建/编辑培训班、培训看板 |
| AI 智能组卷 | 使用 AI 自动生成考试试卷 |
| 题库管理 | 维护考试题库 |
| 人才库 | 管理警务人才信息 |
| 数据看板 | 查看全局培训数据统计 |
| 教官管理 | 管理教官库 |

### 🟡 教官 (Instructor)

| 功能 | 说明 |
|------|------|
| 工作台 | 本周课程安排、待处理事项、学员学习进度 |
| AI 智能组卷 | 使用 AI 自动生成考试试卷 |
| AI 教案生成 | 使用 AI 生成教学教案 |
| 题库管理 | 维护考试题库 |
| 培训管理 | 管理所属培训班 |
| 成绩管理 | 查看/管理学员考试成绩 |
| 报名审核 | 审核培训班报名申请 |

### 🟢 学员 (Student)

| 功能 | 说明 |
|------|------|
| 工作台 | 待完成任务、最近学习进度、本月训练完成度 |
| 课程学习 | 在线学习课程内容 |
| 在线考试 | 参加考试并查看成绩 |
| 培训报名 | 报名参加培训班 |
| 扫码签到 | 通过二维码进行培训签到 |
| 结业证书 | 查看/下载结业证书 |
| 个人中心 | 管理个人信息 |

---

## 📋 功能模块详解

### 🏠 工作台 (Dashboard)
智能化的首页仪表盘，根据当前用户角色自动展示不同内容：
- **统计卡片**：关键数据指标一目了然
- **待办事项**：紧急任务高亮提醒
- **快速操作**：常用功能一键直达

### 📚 课程学习 (Courses)
在线课程学习系统，支持课程列表浏览和详情查看，实时追踪学习进度。

### 📝 考试系统 (Exam)
完整的在线考试流程：
- **题库管理**：管理考试题目（管理员/教官）
- **在线考试**：全屏模式答题体验
- **考试结果**：成绩查询与分析
- **成绩管理**：批量管理学员成绩

### 🤖 AI 智能辅助
- **AI 智能组卷**：根据指定条件自动生成试卷
- **AI 教案生成**：辅助教官快速生成标准化教案

### 🏫 培训管理 (Training)
全流程培训管理：
- **培训班管理**：创建、编辑、查看培训班
- **周训练计划**：可视化训练日程安排
- **培训看板**：管理员全局培训数据监控
- **报名管理**：学员报名 + 管理员/教官审核
- **签到管理**：二维码扫码签到

### 📚 资源中心 (Resource)
- **资源库**：按标题/状态/类型检索与筛选资源
- **资源推荐**：推荐流支持视频播放器、图片直显，文档类型提供下载按钮
- **资源详情**：左侧媒体区 + 右侧资源信息区
- **上传与发布**：支持视频 / 图片 / 文档类型上传，资源说明统一填写在资源简介
- **资源管理（管理员）**：支持按条件搜索资源，并可执行下线、删除等管理操作
- **审核流**：提交审核、审核任务、审核策略管理

### 👮 教官管理 (Instructor)
教官信息库、教官详情查看。

### ⭐ 人才库 (Talent)
管理员专属的警务人才信息管理。

### 📊 数据看板 (Report)
基于 ECharts 的数据可视化大屏，全面展示培训相关数据。

### 🎓 结业证书 (Certificate)
培训结业证书管理与查看。

### 📱 移动端签到
独立的移动端签到页面，支持通过扫描二维码快速签到。

---

## 🔐 认证系统

平台支持两种登录方式：

1. **账号密码登录** — 使用预设的 Mock 用户账号
2. **手机号验证码登录** — 通过短信验证码登录（接入火山引擎 SMS API）

登录状态通过 Pinia + localStorage 持久化，刷新页面自动恢复。

> 💡 **Demo 模式**：登录后可通过顶部导航栏的「演示角色切换」快速切换不同角色体验。

---

## 🛠️ 开发指南

### 路由配置
路由配置位于 `src/router/index.js`，使用 Vue Router 4 的动态导入实现懒加载。路由 `meta` 字段支持：
- `title` — 页面标题
- `icon` — 菜单图标
- `roles` — 允许访问的角色数组
- `requiresAuth` — 是否需要登录
- `fullscreen` — 全屏模式（如考试页面）

### 状态管理
使用 Pinia 进行状态管理，认证状态定义在 `src/stores/auth.js`，支持：
- 用户登录/登出
- 角色判断（isAdmin / isInstructor / isStudent）
- 角色动态切换
- 登录状态持久化

### 数据层
当前版本以前后端 API 联调为主（`src/api/*`），请求与响应字段会在 `src/api/request.js` 中自动完成 `camelCase <-> snake_case` 转换。

> 说明：`src/mock/` 目录仍保留历史数据与少量页面兜底逻辑。

---

## 📄 License

本项目为内部使用项目，未经授权不得用于商业用途。

---

<p align="center">
  <sub>Made with ❤️ for 广西公安</sub>
</p>

## 系统管理（新增）

近期已新增完整的系统管理能力，包含：

- 角色管理：支持角色列表、创建、编辑、删除、启停、权限分配。
- 部门管理：支持部门树、创建、编辑、删除、启停、权限分配、添加子部门。
- 用户管理：保留用户增删改查、角色分配、部门分配、警种分配；已移除“输入部门名自动创建部门”能力。

前端路由（管理员可见）：

- `/system/users` 用户管理
- `/system/roles` 角色管理
- `/system/departments` 部门管理

后端对应接口分组：

- 角色管理：`/api/v1/roles/*`
- 部门管理：`/api/v1/departments/*`
- 权限管理：`/api/v1/permissions/*`
