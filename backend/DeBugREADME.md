# 智慧教育训练平台 - 缺陷修复追踪文档（DeBug README）

> 更新时间：2026-03-07
> 说明：本次仅更新文档，不修改任何业务代码。本文基于当前仓库代码现状，对原始 4 大章节 19 个缺陷逐项给出状态、现状说明与证据位置。

---

## 0. 缺陷修复总览

- 总项数：**19**
- 已修复：**6**
- 部分修复：**4**
- 未修复：**9**

| 章节 | 总项 | 已修复 | 部分修复 | 未修复 |
|---|---:|---:|---:|---:|
| 一、培训班管理列表及详情 | 5 | 5 | 0 | 0 |
| 二、签到打卡与数据对齐 | 2 | 0 | 2 | 0 |
| 三、周训练计划交互展示 | 4 | 1 | 2 | 1 |
| 四、培训数据看板与报表 | 8 | 0 | 0 | 8 |

### 状态定义
- **已修复**：代码已实现且与缺陷目标一致。
- **部分修复**：已做改动，但仍存在关键口径/链路缺口。
- **未修复**：当前实现仍不满足缺陷要求。

---

## 一、培训班管理列表及详情缺陷

### 1. 培训班状态与日期不同步
- **当前状态：已修复**
- **现状说明：** 后端已按当前日期动态计算 `upcoming/active/ended`，列表与详情均复用该结果。
- **关键证据：**
  - `backend/app/services/training.py:447`
  - `backend/app/services/training.py:50`
  - `backend/app/services/training.py:407`

### 2. 进度条标签计算不合理
- **当前状态：已修复**
- **现状说明：** 进度百分比已基于培训起止日期按天数动态计算，非仅 0/100。
- **关键证据：**
  - `backend/app/services/training.py:457`
  - `backend/app/services/training.py:467`
  - `backend/app/services/training.py:471`

### 3. 主责教官信息渲染错误
- **当前状态：已修复**
- **现状说明：** 新建/编辑时可选择 `instructorId`，后端按 `instructor_id` 持久化并回传 `instructor_name`。
- **关键证据：**
  - `src/views/training/List.vue:166`
  - `backend/app/services/training.py:96`
  - `backend/app/services/training.py:419`

### 4. 课程与学员配置无持久化
- **当前状态：已修复**
- **现状说明：** `courses` 与 `student_ids` 已纳入更新契约并落库；详情页课程/学员增删会调用 `updateTraining`。
- **关键证据：**
  - `backend/app/models/training.py:35`
  - `backend/app/models/training.py:51`
  - `backend/app/schemas/training.py:69`
  - `backend/app/services/training.py:145`
  - `backend/app/services/training.py:159`
  - `src/views/training/Detail.vue:796`
  - `src/views/training/Detail.vue:648`
  - `src/api/training.js:15`
  - `src/api/request.js:37`

### 5. 学员详情页路由跳转失效
- **当前状态：已修复**
- **现状说明：** 详情页学员姓名可点击并跳转 `TraineeDetail` 路由。
- **关键证据：**
  - `src/views/training/Detail.vue:101`
  - `src/views/training/Detail.vue:604`
  - `src/router/index.js:126`

---

## 二、签到打卡与数据对齐问题

### 1. 签到动作无动态反馈
- **当前状态：部分修复**
- **现状说明：** 页面已有提示与圆环展示，但前端未真正调用 `checkin` 接口写入记录，统计更新仍主要停留在前端演示逻辑。
- **关键证据：**
  - `src/views/training/Checkin.vue:63`
  - `src/views/training/Checkin.vue:316`
  - `src/views/training/Checkin.vue:383`
  - `src/views/training/Checkin.vue:220`
  - `src/views/training/Checkin.vue:376`
  - `backend/app/views/training.py:187`
  - `backend/app/services/training.py:336`

### 2. 详情页签到统计信息不真实且逻辑割裂
- **当前状态：部分修复**
- **现状说明：** 详情页已开始拉取后端签到记录；但口径仍不满足要求：
  - 开班签到率分母按“已有记录数”而非应签到人数；
  - 课程总签到率无记录时使用随机值兜底，仍非真实统计。
- **关键证据：**
  - `src/views/training/Detail.vue:451`
  - `src/views/training/Detail.vue:506`
  - `src/views/training/Detail.vue:513`
  - `src/views/training/Checkin.vue:281`

---

## 三、周训练计划（日程表）交互展示异常

### 1. 由培训班至日程表的关联跳转失效
- **当前状态：已修复**
- **现状说明：** 详情页/列表页均可跳转至 `training/schedule/:id`，路由存在。
- **关键证据：**
  - `src/views/training/Detail.vue:159`
  - `src/views/training/List.vue:355`
  - `src/router/index.js:82`

### 2. 班级内课程数据多端未打通
- **当前状态：部分修复**
- **现状说明：** 课程排课在详情页可维护并持久化，但日程页读取的是培训列表接口；列表响应不含 `courses`，导致日程页经常回退 Mock。
- **关键证据：**
  - `src/views/training/Schedule.vue:128`
  - `src/views/training/Schedule.vue:215`
  - `src/views/training/Schedule.vue:258`
  - `backend/app/schemas/training.py:97`
  - `backend/app/services/training.py:57`
  - `backend/app/services/training.py:425`

### 3. 排表周期时间轴展示畸形（应为周一至周日）
- **当前状态：未修复**
- **现状说明：** 当前周视图以培训开始日为基准滚动，且仅渲染 5 天，不是固定“周一至周日”7 天轴。
- **关键证据：**
  - `src/views/training/Schedule.vue:175`
  - `src/views/training/Schedule.vue:183`
  - `src/views/training/Schedule.vue:204`

### 4. 课程缺少动态交互（拖拽排版）
- **当前状态：部分修复**
- **现状说明：** 已具备前端拖拽交互，但落点更新只改本地对象，未持久化到后端；刷新后不可保证保留。
- **关键证据：**
  - `src/views/training/Schedule.vue:55`
  - `src/views/training/Schedule.vue:272`
  - `src/views/training/Schedule.vue:294`
  - `src/views/training/Schedule.vue:299`

---

## 四、培训数据看板指标统计及接口调用异常

> 说明：当前“培训看板”页面仍以前端 Mock 为主（`src/views/training/Board.vue`），与要求的 trainings/enrollments/checkin/report 真实口径尚未对齐。

### 1. “进行中的班级”指标
- **当前状态：未修复**
- **现状说明：** 看板按 Mock `status==='active'` 统计并叠加倍率，未按“当前时间落在起止日期区间”计算。
- **关键证据：**
  - `src/views/training/Board.vue:114`
  - `src/views/training/Board.vue:124`
  - `backend/app/services/report.py:35`

### 2. “本月参训人数”指标
- **当前状态：未修复**
- **现状说明：** 看板值为前端公式拼装，未基于本月真实参训学员去重聚合。
- **关键证据：**
  - `src/views/training/Board.vue:130`
  - `backend/app/services/report.py:23`

### 3. “本月培训完成率”指标
- **当前状态：未修复**
- **现状说明：** 看板完成率为固定常量，未按“当月完成培训样本”计算。
- **关键证据：**
  - `src/views/training/Board.vue:136`
  - `backend/app/services/report.py:31`

### 4. “待审核学员”指标
- **当前状态：未修复**
- **现状说明：** 看板取值仍来自 Mock enrollments，后端 report 服务未提供待审核工单聚合。
- **关键证据：**
  - `src/views/training/Board.vue:116`
  - `src/views/training/Board.vue:142`
  - `backend/app/services/report.py:8`

### 5. “各市局本月参训人数统计图”
- **当前状态：未修复**
- **现状说明：** 图表数据仍来自 Mock 城市数组；现有 report API 未提供“本月参训人数按地市聚合”接口。
- **关键证据：**
  - `src/views/training/Board.vue:155`
  - `src/views/training/Board.vue:160`
  - `backend/app/views/report.py:41`
  - `src/api/report.js:11`

### 6. “近6月完成培训趋势折线图”
- **当前状态：未修复**
- **现状说明：** 前端直接读取 Mock 趋势；后端现有趋势口径是考试记录，不是培训完成率且未限定近 6 月。
- **关键证据：**
  - `src/views/training/Board.vue:169`
  - `src/views/training/Board.vue:173`
  - `backend/app/services/report.py:49`

### 7. “各地市完成率排名”
- **当前状态：未修复**
- **现状说明：** 前端排名仍为 Mock；后端城市排名当前基于 `User.avg_score`，非培训完成率口径。
- **关键证据：**
  - `src/views/training/Board.vue:182`
  - `backend/app/services/report.py:91`

### 8. “生成报告”按钮未能联动后台
- **当前状态：未修复**
- **现状说明：** 按钮仅本地提示并未请求导出接口；前后端均无 Word/Excel/PDF 导出网关实现。
- **关键证据：**
  - `src/views/training/Board.vue:185`
  - `src/api/report.js:3`
  - `backend/app/views/report.py:19`

---

## 五、后续实施优先级（P0 / P1 / P2）

| 优先级 | 缺陷ID | 目标 | 关键落点 |
|---|---|---|---|
| **P0** | 2.1, 2.2 | 打通签到“操作→落库→统计刷新”闭环 | `Checkin.vue` 接入 `checkin/getCheckinRecords`；`Detail.vue` 统一签到率口径 |
| **P0** | 4.1 ~ 4.8 | 看板从 Mock 切到真实 `report` 口径并补齐导出链路 | `src/views/training/Board.vue`、`src/api/report.js`、`backend/app/services/report.py`、`backend/app/views/report.py` |
| **P0** | 3.2 | 日程与班级课程数据打通 | `Schedule.vue` 改为读取含 `courses/schedules` 的真实数据源 |
| **P1** | 3.3 | 周视图改为固定“周一至周日”7天轴 | `Schedule.vue` 周起点与天数生成逻辑 |
| **P1** | 3.4 | 拖拽结果持久化 | 拖拽落点后调用更新接口并回写 `schedules` |
| **P2** | 全局 | 回归脚本化与口径巡检 | API smoke + 页面冒烟清单长期化 |

---

## 六、回归验证清单（API + 页面）

### 6.1 API 回归（`/api/v1`）
- [ ] `GET /trainings`：`status/progress_percent` 与当前日期一致（upcoming/active/ended）。
- [ ] `GET /trainings/{id}`：返回 `instructor_name/courses/student_ids/enrolled_count` 与数据库一致。
- [ ] `PUT /trainings/{id}`（`courses`）：刷新后课程排课不丢失。
- [ ] `PUT /trainings/{id}`（`student_ids`）：`enrollments` 中 approved/rejected 状态同步正确。
- [ ] `POST /trainings/{id}/checkin`：`session_key` 维度签到可写入并幂等更新。
- [ ] `GET /trainings/{id}/checkin/records`：同一场次统计与详情页展示一致。
- [ ] `GET /report/*`：KPI/趋势/排名均使用真实口径（禁用前端 Mock 混算）。
- [ ] 报告导出接口（待补）：可返回可下载流（Word/Excel/PDF 至少一种）。

### 6.2 页面回归
- [ ] `training/List.vue`：状态标签、进度条、主管教官显示正确。
- [ ] `training/Detail.vue`：课程/学员增删后刷新仍在；学员名可跳转详情。
- [ ] `training/Checkin.vue`：签到后完成率与记录即时更新且刷新不丢失。
- [ ] `training/Schedule.vue`：从详情跳转后看到同一班级课程；周轴为周一~周日。
- [ ] `training/Schedule.vue`：拖拽调整后刷新仍保持新时段。
- [ ] `training/Board.vue`：KPI、柱状图、折线图、排名均来自真实接口。
- [ ] `training/Board.vue`：导出报告按钮可触发后端导出并下载文件。

---

## 七、结论

当前代码对“培训班基础信息与持久化能力”已完成主要修复，但“签到统计口径闭环”和“看板真实报表链路”仍是主风险。建议按本文件 P0→P1 顺序推进实施，并以第六章清单作为每轮发布前的强制回归标准。
