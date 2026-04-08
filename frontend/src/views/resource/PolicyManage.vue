<template>
  <div class="policy-manage-page">
    <div class="page-header">
      <h2>审核策略管理</h2>
      <permissions-tooltip
        :allowed="canManagePolicy"
        tips="需要 MANAGE_REVIEW_POLICY 或 VIEW_RESOURCE_ALL 权限"
        v-slot="{ disabled }"
      >
        <a-button type="primary" :disabled="disabled" @click="openCreate">新建策略</a-button>
      </permissions-tooltip>
    </div>

    <a-alert type="info" show-icon style="margin-bottom: 16px;">
      <template #message>策略如何生效</template>
      <template #description>
        <div class="hint-list">
          <div>1. 资源提交审核时，系统会按优先级从小到大选择第一条“已启用且命中”的策略。</div>
          <div>2. 作用域决定这条策略管哪些资源，上传者约束决定这条策略只针对哪些上传人。</div>
          <div>3. 审核阶段顺序必须从 1 开始连续递增，否则工作流无法推进。</div>
          <div>4. 每一级会按你选定的用户、角色或部门分派审核任务，达到最小通过数后才进入下一级。</div>
        </div>
      </template>
    </a-alert>

    <a-alert type="warning" show-icon style="margin-bottom: 16px;">
      <template #message>使用提醒</template>
      <template #description>
        <div class="hint-list">
          <div>1. 如果当前没有启用的审核规则，系统会回退到“管理员默认审核”。</div>
          <div>2. 如现有流程已经满足使用需要，建议优先沿用当前规则；非明确业务变更场景下，不必频繁新增或调整策略。</div>
          <div>3. 策略调整只影响后续新提交的资源，不会自动改写已经在途的审核任务。</div>
        </div>
      </template>
    </a-alert>

    <a-tabs v-model:activeKey="activeBusinessType" @change="onBusinessTypeChange" style="margin-bottom: 16px;">
      <a-tab-pane key="resource" tab="资源审核" />
      <!-- <a-tab-pane key="training" tab="培训审核" /> -->
      <!-- <a-tab-pane key="exam" tab="考试审核" /> -->
    </a-tabs>

    <a-card :bordered="false">
      <a-table :data-source="policies" :columns="columns" row-key="id" :pagination="false" :scroll="{ x: 1180 }">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'priority'">
            <a-tag color="blue">P{{ record.priority }}</a-tag>
          </template>
          <template v-if="column.key === 'scope'">
            <div class="cell-main">{{ formatScopeSummary(record) }}</div>
          </template>
          <template v-if="column.key === 'uploaderConstraint'">
            <div class="cell-main">{{ formatUploaderConstraintSummary(record) }}</div>
          </template>
          <template v-if="column.key === 'stages'">
            <div class="stage-cell">
              <div class="cell-main">{{ (record.stages || []).length }} 级审核</div>
              <div v-for="line in formatStageSummary(record.stages)" :key="line" class="cell-sub">{{ line }}</div>
            </div>
          </template>
          <template v-if="column.key === 'enabled'">
            <a-tag :color="record.enabled ? 'green' : 'default'">{{ record.enabled ? '启用' : '停用' }}</a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <permissions-tooltip
              :allowed="canManagePolicy"
              tips="需要 MANAGE_REVIEW_POLICY 或 VIEW_RESOURCE_ALL 权限"
              v-slot="{ disabled }"
            >
              <a-space>
                <a-button size="small" :disabled="disabled" @click="openEdit(record)">编辑</a-button>
                <a-button size="small" @click="openFlowPreview(record)">流程</a-button>
              </a-space>
            </permissions-tooltip>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="visible"
      :title="editing ? '编辑策略' : '新建策略'"
      :confirm-loading="saving"
      :ok-text="editing ? '保存策略' : '创建策略'"
      cancel-text="取消"
      width="900px"
      @ok="save"
    >
      <a-form layout="vertical">
        <a-alert type="warning" show-icon style="margin-bottom: 16px;">
          <template #message>配置前请确认</template>
          <template #description>
            策略一旦命中，资源会按当前配置自动生成审核任务。若当前没有启用策略，系统会回退到管理员默认审核；如无明确业务变更，建议优先沿用现有规则，避免频繁新增或调整。
          </template>
        </a-alert>

        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="策略名称" required>
              <a-input v-model:value="form.name" placeholder="例：市局全局两级审核" />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="优先级">
              <a-input-number v-model:value="form.priority" :min="1" :max="999" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="启用状态">
              <a-switch v-model:checked="form.enabled" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="12">
          <a-col :span="8">
            <a-form-item label="作用域">
              <a-select v-model:value="form.scopeType" style="width:100%" @change="onScopeTypeChange">
                <a-select-option value="global">全局</a-select-option>
                <a-select-option value="department">单部门</a-select-option>
                <a-select-option value="department_tree">部门树</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="16">
            <a-form-item label="作用部门">
              <a-select
                v-model:value="form.scopeDepartmentId"
                :disabled="form.scopeType === 'global'"
                :options="scopeDepartmentOptions"
                show-search
                option-filter-prop="label"
                allow-clear
                :loading="reviewerOptionsLoading"
                style="width:100%"
                placeholder="全局策略无需选择；部门策略必须指定部门"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <div class="form-tip">{{ scopeTypeTip }}</div>

        <a-row :gutter="12" style="margin-top: 12px;">
          <a-col :span="8">
            <a-form-item label="上传者约束">
              <a-select v-model:value="form.uploaderConstraint" style="width:100%" @change="onUploaderConstraintChange">
                <a-select-option value="all">全部上传者</a-select-option>
                <a-select-option value="specific_role">指定角色上传者</a-select-option>
                <a-select-option value="specific_department">指定部门上传者</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="16">
            <a-form-item label="约束对象">
              <a-select
                v-model:value="form.constraintRefId"
                :disabled="form.uploaderConstraint === 'all'"
                :options="constraintOptions"
                show-search
                option-filter-prop="label"
                allow-clear
                :loading="reviewerOptionsLoading"
                style="width:100%"
                :placeholder="constraintPlaceholder"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <div class="form-tip">{{ uploaderConstraintTip }}</div>

        <div class="preview-card">
          <div class="preview-title">当前策略预览</div>
          <a-descriptions :column="2" size="small" bordered>
            <a-descriptions-item label="命中范围">{{ formatScopeSummary(form) }}</a-descriptions-item>
            <a-descriptions-item label="上传者条件">{{ formatUploaderConstraintSummary(form) }}</a-descriptions-item>
            <a-descriptions-item label="优先级">P{{ form.priority || 100 }}</a-descriptions-item>
            <a-descriptions-item label="状态">{{ form.enabled ? '启用中' : '已停用' }}</a-descriptions-item>
            <a-descriptions-item label="审核路径" :span="2">
              {{ previewStageSummaryText }}
            </a-descriptions-item>
          </a-descriptions>
        </div>

        <a-divider orientation="left">审核阶段</a-divider>

        <a-alert type="info" show-icon style="margin-bottom: 12px;">
          <template #message>阶段配置说明</template>
          <template #description>
            <div class="hint-list">
              <div>阶段顺序必须是 `1, 2, 3...` 连续编号。</div>
              <div>按用户审核时，最小通过数只能是 1。</div>
              <div>如果审核对象已经失效，页面会保留旧 ID 并提示你尽快修正。</div>
            </div>
          </template>
        </a-alert>

        <a-row :gutter="8" class="stage-header">
          <a-col :span="3">阶段顺序</a-col>
          <a-col :span="5">审核人类型</a-col>
          <a-col :span="6">审核对象</a-col>
          <a-col :span="4">最小通过数</a-col>
          <a-col :span="3">允许自审</a-col>
          <a-col :span="3">操作</a-col>
        </a-row>

        <div v-for="(stage, idx) in form.stages" :key="idx" class="stage-row">
          <a-row :gutter="8" align="middle">
            <a-col :span="3">
              <a-input-number v-model:value="stage.stageOrder" :min="1" style="width:100%" placeholder="如 1" />
            </a-col>
            <a-col :span="5">
              <a-select
                v-model:value="stage.reviewerType"
                style="width:100%"
                placeholder="选择类型"
                @change="onReviewerTypeChange(stage)"
              >
                <a-select-option value="user">用户</a-select-option>
                <a-select-option value="role">角色</a-select-option>
                <a-select-option value="department">部门</a-select-option>
              </a-select>
            </a-col>
            <a-col :span="6">
              <a-select
                v-model:value="stage.reviewerRefId"
                :options="getReviewerOptions(stage)"
                show-search
                option-filter-prop="label"
                allow-clear
                :loading="reviewerOptionsLoading"
                style="width:100%"
                :placeholder="getReviewerPlaceholder(stage.reviewerType)"
              />
            </a-col>
            <a-col :span="4">
              <a-input-number v-model:value="stage.minApprovals" :min="1" style="width:100%" placeholder="至少 1" />
            </a-col>
            <a-col :span="3">
              <a-switch v-model:checked="stage.allowSelfReview" />
            </a-col>
            <a-col :span="3">
              <permissions-tooltip
                :allowed="canManagePolicy"
                tips="需要 MANAGE_REVIEW_POLICY 或 VIEW_RESOURCE_ALL 权限"
                v-slot="{ disabled }"
              >
                <a-button type="link" danger :disabled="disabled" @click="removeStage(idx)">删除</a-button>
              </permissions-tooltip>
            </a-col>
          </a-row>
          <div class="stage-tip">
            {{ formatSingleStageLine(stage, idx) }}
          </div>
        </div>
        <permissions-tooltip
          :allowed="canManagePolicy"
          tips="需要 MANAGE_REVIEW_POLICY 或 VIEW_RESOURCE_ALL 权限"
          block
          v-slot="{ disabled }"
        >
          <a-button type="dashed" block :disabled="disabled" @click="addStage">添加阶段</a-button>
        </permissions-tooltip>

        <a-divider orientation="left">流程预览</a-divider>
        <ReviewFlowChart
          :stages="form.stages"
          :reviewer-type-labels="reviewerTypeLabels"
          :get-reviewer-label="getFlowReviewerLabel"
        />
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="flowVisible"
      :title="flowPolicy ? `审核流程 — ${flowPolicy.name}` : '审核流程'"
      :footer="null"
      width="800px"
    >
      <ReviewFlowChart
        v-if="flowPolicy"
        :stages="flowPolicy.stages || []"
        :reviewer-type-labels="reviewerTypeLabels"
        :get-reviewer-label="getFlowReviewerLabel"
      />
    </a-modal>
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getReviewPolicies, createReviewPolicy, updateReviewPolicy } from '@/api/review'
import { getUsers } from '@/api/user'
import { getRoleList } from '@/api/role'
import { getDepartmentList } from '@/api/department'
import { useAuthStore } from '@/stores/auth'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'
import ReviewFlowChart from '@/components/common/ReviewFlowChart.vue'

const authStore = useAuthStore()
const policies = ref([])
const visible = ref(false)
const editing = ref(null)
const saving = ref(false)
const canManagePolicy = computed(() => authStore.hasAnyPermission(['MANAGE_REVIEW_POLICY', 'VIEW_RESOURCE_ALL']))
const flowVisible = ref(false)
const flowPolicy = ref(null)
const activeBusinessType = ref('resource')

const businessTypeLabels = {
  resource: '资源审核',
  // training: '培训审核',
  // exam: '考试审核',
}

const userReviewerOptions = ref([])
const roleReviewerOptions = ref([])
const departmentReviewerOptions = ref([])
const reviewerOptionsLoading = ref(false)
const reviewerOptionsLoaded = ref(false)

const reviewerTypeLabels = {
  user: '用户',
  role: '角色',
  department: '部门',
}

const columns = [
  { title: '名称', dataIndex: 'name', key: 'name', width: 180 },
  { title: '优先级', dataIndex: 'priority', key: 'priority', width: 90 },
  { title: '作用范围', key: 'scope', width: 220 },
  { title: '上传者约束', key: 'uploaderConstraint', width: 220 },
  { title: '审核路径', key: 'stages', width: 320 },
  { title: '状态', key: 'enabled', width: 100 },
  { title: '操作', key: 'action', width: 150, fixed: 'right' },
]

const form = reactive({
  name: '',
  businessType: 'resource',
  enabled: true,
  scopeType: 'global',
  scopeDepartmentId: null,
  uploaderConstraint: 'all',
  constraintRefId: null,
  priority: 100,
  stages: [],
})

const scopeDepartmentOptions = computed(() => appendMissingOption(
  departmentReviewerOptions.value,
  form.scopeDepartmentId,
  `已失效部门（ID: ${form.scopeDepartmentId}）`,
))

const constraintOptions = computed(() => {
  if (form.uploaderConstraint === 'specific_role') {
    return appendMissingOption(roleReviewerOptions.value, form.constraintRefId, `已失效角色（ID: ${form.constraintRefId}）`)
  }
  if (form.uploaderConstraint === 'specific_department') {
    return appendMissingOption(departmentReviewerOptions.value, form.constraintRefId, `已失效部门（ID: ${form.constraintRefId}）`)
  }
  return []
})

const constraintPlaceholder = computed(() => {
  if (form.uploaderConstraint === 'specific_role') return '请选择可触发该策略的上传者角色'
  if (form.uploaderConstraint === 'specific_department') return '请选择可触发该策略的上传者部门'
  return '全部上传者无需指定对象'
})

const scopeTypeTip = computed(() => {
  if (form.scopeType === 'global') {
    return '全局策略会匹配所有资源。只有当它的优先级高于其他命中策略时，才会先被选中。'
  }
  if (form.scopeType === 'department_tree') {
    return '部门树策略会匹配所选部门及其所有下级部门归属的资源。'
  }
  return '单部门策略只匹配资源归属部门与所选部门完全一致的资源。'
})

const uploaderConstraintTip = computed(() => {
  if (form.uploaderConstraint === 'all') {
    return '不限制上传者身份，只要资源作用域命中，这条策略就可能被选中。'
  }
  if (form.uploaderConstraint === 'specific_role') {
    return '只有拥有所选角色的上传者提交资源时，这条策略才会命中。'
  }
  return '只有属于所选部门的上传者提交资源时，这条策略才会命中。'
})

const previewStageSummaryText = computed(() => {
  const lines = formatStageSummary(form.stages)
  return lines.length ? lines.join('；') : '尚未配置审核阶段'
})

onMounted(() => {
  fetchPolicies()
  ensureReviewerOptionsLoaded().catch(() => {})
})

let reviewerOptionsPromise = null

function createStage(stageOrder = 1) {
  return {
    stageOrder,
    reviewerType: 'role',
    reviewerRefId: null,
    minApprovals: 1,
    allowSelfReview: false,
  }
}

function mapToOptions(items, labelGetter, prefix) {
  return (items || []).map((item) => ({
    value: item.id,
    label: labelGetter(item) || `${prefix}#${item.id}`,
  }))
}

function normalizeId(value) {
  if (value === null || value === undefined || value === '') {
    return null
  }
  const normalized = Number(value)
  return Number.isInteger(normalized) && normalized > 0 ? normalized : null
}

function appendMissingOption(options, value, label) {
  const normalizedValue = normalizeId(value)
  if (!normalizedValue) {
    return options
  }
  const exists = (options || []).some((item) => Number(item.value) === normalizedValue)
  if (exists) {
    return options
  }
  return [...(options || []), { value: normalizedValue, label }]
}

function getOptionLabel(options, value, fallbackPrefix) {
  const normalizedValue = normalizeId(value)
  if (!normalizedValue) {
    return '未指定'
  }
  const option = (options || []).find((item) => Number(item.value) === normalizedValue)
  return option?.label || `${fallbackPrefix}#${normalizedValue}`
}

function getBaseReviewerOptions(type) {
  if (type === 'user') return userReviewerOptions.value
  if (type === 'department') return departmentReviewerOptions.value
  return roleReviewerOptions.value
}

function getReviewerOptions(stage) {
  const type = stage?.reviewerType || 'role'
  const fallbackPrefix = reviewerTypeLabels[type] || '对象'
  return appendMissingOption(
    getBaseReviewerOptions(type),
    stage?.reviewerRefId,
    `已失效${fallbackPrefix}（ID: ${stage?.reviewerRefId}）`,
  )
}

function getReviewerPlaceholder(type) {
  if (type === 'user') return '请选择用户'
  if (type === 'department') return '请选择部门'
  return '请选择角色'
}

function openFlowPreview(record) {
  flowPolicy.value = record
  flowVisible.value = true
}

function getFlowReviewerLabel(stage) {
  const type = stage?.reviewerType || 'role'
  return getOptionLabel(getBaseReviewerOptions(type), stage?.reviewerRefId, reviewerTypeLabels[type] || '对象')
}

function onReviewerTypeChange(stage) {
  stage.reviewerRefId = null
  stage.minApprovals = 1
}

function onScopeTypeChange(value) {
  if (value === 'global') {
    form.scopeDepartmentId = null
  }
}

function onUploaderConstraintChange(value) {
  form.constraintRefId = null
}

async function ensureReviewerOptionsLoaded() {
  if (reviewerOptionsLoaded.value) return
  if (reviewerOptionsPromise) return reviewerOptionsPromise

  reviewerOptionsLoading.value = true
  reviewerOptionsPromise = Promise.all([
    getUsers({ size: -1 }).catch(() => null),
    getRoleList({ size: -1 }).catch(() => null),
    getDepartmentList({ size: -1 }).catch(() => null),
  ]).then(([usersRes, rolesRes, departmentsRes]) => {
    const users = usersRes?.items || []
    const roles = rolesRes?.items || []
    const departments = departmentsRes?.items || []

    userReviewerOptions.value = mapToOptions(users, (item) => item.nickname || item.username, '用户')
    roleReviewerOptions.value = mapToOptions(roles, (item) => item.name || item.code, '角色')
    departmentReviewerOptions.value = mapToOptions(departments, (item) => item.name || item.code, '部门')

    if (!usersRes || !rolesRes || !departmentsRes) {
      message.warning('审核对象数据加载不完整，部分选项可能无法正常显示')
    }

    reviewerOptionsLoaded.value = true
  }).finally(() => {
    reviewerOptionsLoading.value = false
    reviewerOptionsPromise = null
  })

  return reviewerOptionsPromise
}

function resetForm() {
  form.name = ''
  form.businessType = activeBusinessType.value
  form.enabled = true
  form.scopeType = 'global'
  form.scopeDepartmentId = null
  form.uploaderConstraint = 'all'
  form.constraintRefId = null
  form.priority = 100
  form.stages = [createStage(1)]
}

function onBusinessTypeChange() {
  fetchPolicies()
}

async function fetchPolicies() {
  try {
    policies.value = await getReviewPolicies({ businessType: activeBusinessType.value }) || []
  } catch (error) {
    message.error(error.message || '加载策略失败')
  }
}

async function openCreate() {
  if (!canManagePolicy.value) return
  editing.value = null
  resetForm()
  await ensureReviewerOptionsLoaded()
  visible.value = true
}

async function openEdit(policy) {
  if (!canManagePolicy.value) return
  editing.value = policy
  form.name = policy.name
  form.businessType = policy.businessType || activeBusinessType.value
  form.enabled = !!policy.enabled
  form.scopeType = policy.scopeType || 'global'
  form.scopeDepartmentId = normalizeId(policy.scopeDepartmentId)
  form.uploaderConstraint = policy.uploaderConstraint || 'all'
  form.constraintRefId = normalizeId(policy.constraintRefId)
  form.priority = Number(policy.priority || 100)
  form.stages = (policy.stages || []).map((stage) => ({
    stageOrder: Number(stage.stageOrder || 1),
    reviewerType: stage.reviewerType || 'role',
    reviewerRefId: normalizeId(stage.reviewerRefId),
    minApprovals: Number(stage.minApprovals || 1),
    allowSelfReview: !!stage.allowSelfReview,
  }))
  if (!form.stages.length) {
    form.stages = [createStage(1)]
  }
  await ensureReviewerOptionsLoaded()
  visible.value = true
}

function addStage() {
  if (!canManagePolicy.value) return
  const maxOrder = form.stages.reduce((maxValue, stage) => Math.max(maxValue, Number(stage.stageOrder || 0)), 0)
  form.stages.push(createStage(maxOrder + 1))
}

function removeStage(index) {
  if (!canManagePolicy.value) return
  form.stages.splice(index, 1)
  if (!form.stages.length) {
    form.stages = [createStage(1)]
  }
}

function formatScopeSummary(target) {
  const scopeType = target?.scopeType || 'global'
  const departmentLabel = getOptionLabel(departmentReviewerOptions.value, target?.scopeDepartmentId, '部门')
  if (scopeType === 'department') {
    return `单部门：${departmentLabel}`
  }
  if (scopeType === 'department_tree') {
    return `部门树：${departmentLabel}（含下级）`
  }
  return '全局资源'
}

function formatUploaderConstraintSummary(target) {
  const constraintType = target?.uploaderConstraint || 'all'
  if (constraintType === 'specific_role') {
    return `仅角色：${getOptionLabel(roleReviewerOptions.value, target?.constraintRefId, '角色')}`
  }
  if (constraintType === 'specific_department') {
    return `仅部门：${getOptionLabel(departmentReviewerOptions.value, target?.constraintRefId, '部门')}`
  }
  return '全部上传者'
}

function formatStageSummary(stages = []) {
  return (stages || [])
    .slice()
    .sort((left, right) => Number(left.stageOrder || 0) - Number(right.stageOrder || 0))
    .map((stage, index) => formatSingleStageLine(stage, index))
}

function formatSingleStageLine(stage, index = 0) {
  const reviewerType = stage?.reviewerType || 'role'
  const typeLabel = reviewerTypeLabels[reviewerType] || reviewerType
  const reviewerLabel = getOptionLabel(getBaseReviewerOptions(reviewerType), stage?.reviewerRefId, typeLabel)
  const order = Number(stage?.stageOrder || index + 1)
  const parts = [`第 ${order} 级`, `${typeLabel}：${reviewerLabel}`, `至少 ${Number(stage?.minApprovals || 1)} 人通过`]
  if (stage?.allowSelfReview) {
    parts.push('允许自审')
  }
  return parts.join('，')
}

function validateStagesBeforeSave() {
  if (!form.stages.length) {
    message.warning('请至少配置一个审核阶段')
    return null
  }

  const normalizedStages = form.stages.map((stage, index) => ({
    stageOrder: Number(stage.stageOrder || 0),
    reviewerType: stage.reviewerType,
    reviewerRefId: normalizeId(stage.reviewerRefId),
    minApprovals: Number(stage.minApprovals || 1),
    allowSelfReview: !!stage.allowSelfReview,
    index,
  }))

  for (const stage of normalizedStages) {
    if (!stage.stageOrder) {
      message.warning(`第 ${stage.index + 1} 行缺少阶段顺序`)
      return null
    }
    if (!stage.reviewerType) {
      message.warning(`第 ${stage.index + 1} 行缺少审核人类型`)
      return null
    }
    if (!stage.reviewerRefId) {
      message.warning(`第 ${stage.index + 1} 行缺少审核对象`)
      return null
    }
    if (stage.minApprovals < 1) {
      message.warning(`第 ${stage.index + 1} 行的最小通过数必须大于 0`)
      return null
    }
    if (stage.reviewerType === 'user' && stage.minApprovals > 1) {
      message.warning(`第 ${stage.index + 1} 行按用户审核时，最小通过数不能超过 1`)
      return null
    }
  }

  const sortedStages = normalizedStages.slice().sort((left, right) => left.stageOrder - right.stageOrder)
  const orders = sortedStages.map((stage) => stage.stageOrder)
  const uniqueOrderCount = new Set(orders).size
  if (uniqueOrderCount !== orders.length) {
    message.warning('审核阶段顺序不能重复')
    return null
  }

  const expectedOrders = Array.from({ length: sortedStages.length }, (_, index) => index + 1)
  if (orders.join(',') !== expectedOrders.join(',')) {
    message.warning('审核阶段顺序必须从 1 开始并连续递增')
    return null
  }

  return sortedStages.map((stage) => ({
    stageOrder: stage.stageOrder,
    reviewerType: stage.reviewerType,
    reviewerRefId: stage.reviewerRefId,
    minApprovals: stage.minApprovals,
    allowSelfReview: stage.allowSelfReview,
  }))
}

async function save() {
  if (!canManagePolicy.value) return
  if (!form.name.trim()) {
    message.warning('请输入策略名称')
    return
  }
  if (form.scopeType !== 'global' && !normalizeId(form.scopeDepartmentId)) {
    message.warning('当前作用域需要指定作用部门')
    return
  }
  if (form.uploaderConstraint !== 'all' && !normalizeId(form.constraintRefId)) {
    message.warning('当前上传者约束需要指定具体对象')
    return
  }

  const stages = validateStagesBeforeSave()
  if (!stages) {
    return
  }

  const payload = {
    name: form.name.trim(),
    businessType: form.businessType || activeBusinessType.value,
    enabled: form.enabled,
    scopeType: form.scopeType,
    scopeDepartmentId: form.scopeType === 'global' ? null : normalizeId(form.scopeDepartmentId),
    uploaderConstraint: form.uploaderConstraint,
    constraintRefId: form.uploaderConstraint === 'all' ? null : normalizeId(form.constraintRefId),
    priority: Number(form.priority || 100),
    stages,
  }

  saving.value = true
  try {
    if (editing.value) {
      await updateReviewPolicy(editing.value.id, payload)
      message.success('策略已更新，后续新提交的资源会按新规则匹配')
    } else {
      await createReviewPolicy(payload)
      message.success('策略已创建，命中后会自动生成审核任务')
    }
    visible.value = false
    await fetchPolicies()
  } catch (error) {
    message.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.policy-manage-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.hint-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cell-main {
  color: #1f1f1f;
  font-weight: 500;
}

.cell-sub {
  color: #8c8c8c;
  font-size: 12px;
  line-height: 1.5;
}

.stage-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.form-tip {
  margin-top: -8px;
  color: #8c8c8c;
  font-size: 12px;
  line-height: 1.6;
}

.preview-card {
  margin-top: 16px;
  margin-bottom: 20px;
  padding: 12px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background: #fafcff;
}

.preview-title {
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 600;
  color: #001234;
}

.stage-header {
  margin-bottom: 8px;
  padding: 0 10px;
  color: #666;
  font-size: 12px;
}

.stage-row {
  margin-bottom: 10px;
  padding: 10px 10px 4px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
}

.stage-tip {
  margin-top: 8px;
  color: #8c8c8c;
  font-size: 12px;
  line-height: 1.5;
}
</style>
