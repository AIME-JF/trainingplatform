# 警务训练平台新增“资源库 + UGC审核 + 推荐 + 分区权限”实现方案

## 1. 目标与范围

本文基于当前项目实际代码结构（Vue3 + FastAPI + SQLAlchemy + Alembic + Redis + Celery + MinIO）给出可落地的实现方案，覆盖以下能力：

1. 视音频/图文资源作为独立模块存在，不再绑定课程。
2. 普通用户可自由上传 UGC 资源，且必须经过多级人工审核后才能对外可见。
3. 根据用户浏览行为 + 警种身份做个性化推荐。
4. 支持按部门/层级划分审核和访问权限，满足多层级组织独立把关。

不在本次范围：

1. 复杂机器学习模型训练平台（先用规则+轻量召回排序）。
2. 完整舆情/违规检测AI（可预留接口，人工审核为主）。

---

## 2. 当前项目现状（和新增需求的关系）

## 2.1 已有能力

1. 文件存储已存在：`media_files` + MinIO 上传下载（`/api/v1/media/*`）。
2. 课程章节可绑定文件：`chapters.file_id -> media_files.id`。
3. 有 RBAC + 部门 + 警种模型：`roles / permissions / departments / police_types`。
4. 已有 Redis、Celery worker 基础设施，可承载推荐计算、审核队列任务。

## 2.2 当前短板

1. “文件”是技术对象，不是“资源内容对象”：缺少标题、摘要、标签、可见范围、审核状态、发布状态等业务字段。
2. 缺少独立“资源库”域模型，课程只能直接上传章节文件，无法复用同一资源到多课程/多培训班。
3. 缺少审核流模型（审核策略、多级节点、审核任务、审核记录）。
4. 权限控制主要是接口级，没有资源行级数据权限（按部门/层级/警种/可见域）。
5. 没有行为埋点和推荐服务。

结论：当前基础可复用，但必须新增“资源域模型 + 审核域模型 + 行为与推荐域模型”。

---

## 3. 总体架构方案

## 3.1 分层设计

在现有 `models / schemas / services / controllers / views` 结构内新增 3 个领域：

1. `resource`：资源内容管理与课程/培训引用。
2. `review`：多级人工审核工作流。
3. `recommendation`：行为采集、召回排序、推荐接口。

## 3.2 关键原则

1. **向后兼容**：保留 `chapters.file_id`，逐步迁移到“章节引用资源”。
2. **状态驱动**：资源可见性由状态机驱动（草稿/待审/审核中/已发布/驳回/下线）。
3. **策略与实例分离**：审核规则是“策略”，具体审核过程是“实例+任务”。
4. **接口鉴权 + 数据域过滤双层控制**：防止越权查看/审核。

---

## 4. 数据模型设计（核心）

以下表建议通过 Alembic 新增，命名沿用当前风格（snake_case）。

## 4.1 资源域

### `resources`

资源主体（业务对象），关键字段：

1. `id`
2. `title`、`summary`、`content_type`（video/image_text/document/mixed）
3. `uploader_id`（FK users）
4. `source_type`（ugc/official/imported）
5. `status`（draft/pending_review/reviewing/published/rejected/offline）
6. `visibility_type`（public/department/police_type/custom）
7. `owner_department_id`（资源归属部门，可空）
8. `publish_at`、`offline_at`
9. `review_policy_id`（命中哪条审核策略）
10. `cover_media_file_id`（封面文件）
11. `view_count`、`like_count`、`favorite_count`（可异步累计）
12. `created_at`、`updated_at`

### `resource_media_links`

资源与底层文件多对多关系：

1. `resource_id`
2. `media_file_id`
3. `media_role`（main/attachment/subtitle）
4. `sort_order`

### `resource_tags` / `resource_tag_relations`

用于检索和推荐。

### `resource_visibility_scopes`

细粒度可见域（可选）：

1. `resource_id`
2. `scope_type`（department/police_type/role/user）
3. `scope_id`

> 若前期简化，可先只做 `department/police_type`。

## 4.2 引用关系域

### `course_resource_refs`

1. `course_id`
2. `resource_id`
3. `usage_type`（required/optional/extension）
4. `sort_order`

### `training_resource_refs`

1. `training_id`
2. `resource_id`
3. `usage_type`
4. `sort_order`

这样实现“课程/培训引用资源”，资源本身独立存在。

## 4.3 审核域（多级人工）

### `review_policies`

审核策略（谁上传走什么流程）：

1. `id`、`name`
2. `enabled`
3. `scope_type`（global/department/department_tree）
4. `scope_department_id`（可空）
5. `uploader_constraint`（all/specific_role/specific_department）
6. `priority`（命中顺序）

### `review_policy_stages`

策略节点（多级）：

1. `policy_id`
2. `stage_order`（1,2,3...）
3. `reviewer_type`（role/department/user）
4. `reviewer_ref_id`
5. `min_approvals`
6. `allow_self_review`（默认 false）

### `resource_review_workflows`

每个资源提交审核生成一条工作流实例：

1. `resource_id`
2. `policy_id`
3. `current_stage`
4. `status`（pending/reviewing/approved/rejected/cancelled）
5. `started_at`、`finished_at`

### `resource_review_tasks`

每一级审核任务：

1. `workflow_id`
2. `stage_order`
3. `assignee_user_id`（或 reviewer_pool_key）
4. `status`（pending/approved/rejected/skipped）
5. `comment`
6. `reviewed_at`

### `resource_review_logs`

审计日志（不可篡改业务日志）：

1. `resource_id`、`workflow_id`、`actor_id`
2. `action`（submit/approve/reject/revoke/reassign）
3. `detail_json`
4. `created_at`

## 4.4 推荐域

### `resource_behavior_events`

埋点事件（浏览、停留、点赞、收藏、分享等）：

1. `user_id`
2. `resource_id`
3. `event_type`（impression/click/play/complete/like/favorite）
4. `watch_seconds`（视频）
5. `event_time`
6. `context_json`（来源页面、推荐位、设备）

### `resource_recommend_scores`（可选缓存表）

离线预计算用户-资源分值缓存，提升接口速度。

---

## 5. 状态机与业务流程

## 5.1 UGC 上传与发布流程

1. 用户上传文件（复用现有 `/media/upload`）并创建 `resource`（状态 `draft`）。
2. 用户点击“提交审核” -> 根据归属部门/上传者身份匹配 `review_policy`，创建 workflow + stage1 tasks。
3. 各级审核人处理任务：
   - 通过：进入下一阶段；最后一级通过则资源 `published`。
   - 驳回：workflow `rejected`，资源 `rejected`，填写驳回原因。
4. 作者修改后可再次提交，形成新 workflow（保留历史）。

## 5.2 多级审核判定规则

1. 阶段通过条件：该阶段 `approved_count >= min_approvals`。
2. 阶段驳回条件：任一“强驳回节点”驳回或超过最大容错。
3. 作者不能审核自己上传的资源（`allow_self_review=false`）。

---

## 6. 权限与分区管理方案

## 6.1 新增权限码（示例）

在 `init_data.py` 增加并同步到角色：

1. `CREATE_RESOURCE`
2. `UPDATE_RESOURCE`
3. `SUBMIT_RESOURCE_REVIEW`
4. `VIEW_RESOURCE_ALL`
5. `VIEW_RESOURCE_DEPARTMENT`
6. `REVIEW_RESOURCE_STAGE1` / `REVIEW_RESOURCE_STAGE2` ...
7. `MANAGE_REVIEW_POLICY`
8. `MANAGE_RESOURCE_VISIBILITY`

## 6.2 数据域过滤（核心）

列表查询必须叠加数据域条件：

1. 普通用户：仅可见 `published` 且命中可见范围的资源。
2. 上传者：可看到自己全部资源（含草稿/驳回）。
3. 审核人：可看到分配给自己的审核任务相关资源。
4. 管理员：按权限可跨部门查看。

部门层级可复用现有 `Department.parent_id` 与 `inherit_sub_permissions` 逻辑，新增“部门树可见”判断函数。

---

## 7. 个性化推荐设计（先易后难）

## 7.1 推荐信号

1. 用户画像：`police_types`、`departments`、角色。
2. 行为信号：点击、播放时长、完播、点赞、收藏、近期活跃度。
3. 内容信号：标签、内容类型、来源部门、热度、发布时间。

## 7.2 召回层（多路召回）

1. 警种召回：资源标签/分类匹配用户警种。
2. 部门召回：优先同部门/上级部门发布资源。
3. 行为相似召回：用户最近高互动资源的相似标签扩展。
4. 热门兜底：近期高质量高互动资源。

## 7.3 排序层（规则版）

`score = w1*police_type_match + w2*dept_match + w3*interest_match + w4*freshness + w5*quality + w6*popularity`

初期权重可配置化（系统配置表），后续迭代可接入学习排序。

## 7.4 计算与服务方式

1. 在线实时：轻量规则计算（小流量可直接 SQL + Python）。
2. 离线预计算：Celery 周期任务写入 `resource_recommend_scores`。
3. API：`GET /resources/recommendations/feed`，支持分页和场景位参数。

---

## 8. 接口设计建议（FastAPI）

## 8.1 资源库接口

1. `POST /api/v1/resources` 创建资源（草稿）
2. `PUT /api/v1/resources/{id}` 更新资源
3. `POST /api/v1/resources/{id}/submit` 提交审核
4. `GET /api/v1/resources` 资源列表（按状态/标签/类型/部门筛选）
5. `GET /api/v1/resources/{id}` 资源详情
6. `POST /api/v1/resources/{id}/publish` 管理员强制发布（可选）
7. `POST /api/v1/resources/{id}/offline` 下线
8. `POST /api/v1/resources/{id}/events` 行为埋点

## 8.2 审核接口

1. `GET /api/v1/reviews/tasks` 我的待审任务
2. `POST /api/v1/reviews/tasks/{task_id}/approve`
3. `POST /api/v1/reviews/tasks/{task_id}/reject`
4. `GET /api/v1/reviews/workflows/{resource_id}` 审核轨迹

## 8.3 策略管理接口

1. `GET /api/v1/review-policies`
2. `POST /api/v1/review-policies`
3. `PUT /api/v1/review-policies/{id}`
4. `POST /api/v1/review-policies/{id}/stages`

## 8.4 引用关系接口

1. `POST /api/v1/courses/{course_id}/resources` 课程绑定资源
2. `DELETE /api/v1/courses/{course_id}/resources/{resource_id}`
3. `POST /api/v1/trainings/{training_id}/resources`

---

## 9. 前端改造方案（Vue）

## 9.1 新增页面与路由

1. `src/views/resource/Library.vue` 资源库首页（检索 + 推荐）
2. `src/views/resource/Upload.vue` UGC 上传与编辑
3. `src/views/resource/MyResources.vue` 我的资源（草稿/待审/驳回/已发布）
4. `src/views/resource/ReviewQueue.vue` 审核工作台
5. `src/views/resource/PolicyManage.vue` 审核策略管理（管理员）

并在 `src/router/index.js` 与 `src/layouts/MainLayout.vue` 增加菜单入口。

## 9.2 现有页面衔接

1. 课程编辑页（`courses/List.vue`, `courses/Detail.vue`）新增“从资源库选择”能力。
2. 培训详情页新增“引用资源”区块。
3. 保留当前“直接上传章节文件”作为兼容模式，逐步引导到资源库。

## 9.3 前端 API 模块

新增：

1. `src/api/resource.js`
2. `src/api/review.js`
3. `src/api/recommendation.js`

沿用当前 `request.js` 的 snake_case/camelCase 自动转换。

---

## 10. 后端代码落点（建议文件）

## 10.1 模型与迁移

1. `backend/app/models/resource.py`（新增）
2. `backend/app/models/review.py`（新增）
3. `backend/app/models/recommendation.py`（新增）
4. `backend/alembic/versions/*_add_resource_review_recommend_tables.py`
5. `backend/app/models/__init__.py` 注册新模型

## 10.2 Schema / Service / Controller / View

1. `backend/app/schemas/resource.py`
2. `backend/app/schemas/review.py`
3. `backend/app/services/resource.py`
4. `backend/app/services/review.py`
5. `backend/app/services/recommendation.py`
6. `backend/app/views/resource.py`
7. `backend/app/views/review.py`
8. `backend/app/views/recommendation.py`
9. `backend/app/views/__init__.py` 注册路由

## 10.3 权限与初始化

1. `backend/init_data.py` 增加权限码与角色默认授权。
2. 若需要，新增策略初始化脚本（如全局默认两级审核策略）。

---

## 11. 分阶段落地计划（推荐）

## Phase 1：资源库最小闭环（1-2 周）

1. 建 `resources + resource_media_links + course_resource_refs`。
2. 完成资源创建/编辑/列表/详情。
3. 课程可引用资源。
4. 无审核，先仅管理员可发布（快速验证数据模型）。

## Phase 2：多级人工审核（2 周）

1. 建 `review_policies + review_policy_stages + workflows + tasks + logs`。
2. 打通提交审核与审核工作台。
3. 资源可见性与审核状态绑定。
4. 部门策略命中与层级审核。

## Phase 3：推荐系统（1-2 周）

1. 行为埋点接口和事件表。
2. 规则召回+排序服务。
3. 首页推荐流 + “为你推荐”区块。
4. Celery 定时预计算（可选）。

## Phase 4：治理与优化（持续）

1. 审核 SLA、超时提醒、催办。
2. 风险内容自动初筛（可选接入）。
3. 指标看板：通过率、驳回率、发布时延、推荐点击率。

---

## 12. 测试与验收标准

## 12.1 后端测试（新增）

在 `backend/tests/` 增加：

1. 资源 CRUD 与可见性过滤用例。
2. 多级审核状态流转用例（通过/驳回/重提）。
3. 审核权限与越权访问用例。
4. 推荐接口基础可用性与排序稳定性用例。

## 12.2 前端验收

1. 普通用户能上传资源但不可直接发布。
2. 审核员仅看到自己部门/阶段任务。
3. 通过后全站可见；驳回后仅作者可见并可修改重提。
4. 课程页可引用资源并正常播放/查看。
5. 推荐流可根据警种和行为变化。

---

## 13. 关键风险与应对

1. **审核策略复杂度过高**：先做“线性多级 + 最小审批人数”，避免并行会签复杂度。
2. **权限误配导致越权**：接口鉴权外，必须做 SQL 级数据域过滤；关键接口加审计日志。
3. **推荐效果冷启动差**：优先警种+部门+热门混排，逐步引入行为权重。
4. **历史数据迁移成本**：保留 `chapter.file_id` 兼容，按批次回填 `resource`。

---

## 14. 建议优先实现顺序（结合当前项目）

1. 先把“文件”升级为“资源对象”（这是所有能力的基础）。
2. 再实现审核策略与任务流。
3. 然后接入课程/培训引用。
4. 最后上线推荐。

按这个顺序改造，对现有项目改动最可控，且每一步都能独立交付和验收。
