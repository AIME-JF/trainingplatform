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

    <a-card :bordered="false">
      <a-table :data-source="policies" :columns="columns" row-key="id" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'enabled'">
            <a-tag :color="record.enabled ? 'green' : 'default'">{{ record.enabled ? '启用' : '停用' }}</a-tag>
          </template>
          <template v-if="column.key === 'stages'">
            {{ (record.stages || []).length }} 级
          </template>
          <template v-if="column.key === 'action'">
            <permissions-tooltip
              :allowed="canManagePolicy"
              tips="需要 MANAGE_REVIEW_POLICY 或 VIEW_RESOURCE_ALL 权限"
              v-slot="{ disabled }"
            >
              <a-button size="small" :disabled="disabled" @click="openEdit(record)">编辑</a-button>
            </permissions-tooltip>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal v-model:open="visible" :title="editing ? '编辑策略' : '新建策略'" @ok="save" width="760px">
      <a-form layout="vertical">
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="策略名称" required>
              <a-input v-model:value="form.name" />
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

        <a-form-item label="作用域">
          <a-select v-model:value="form.scopeType" style="width:220px">
            <a-select-option value="global">全局</a-select-option>
            <a-select-option value="department">部门</a-select-option>
            <a-select-option value="department_tree">部门树</a-select-option>
          </a-select>
        </a-form-item>

        <a-divider orientation="left">审核阶段</a-divider>

        <a-row :gutter="8" class="stage-header">
          <a-col :span="4">阶段顺序</a-col>
          <a-col :span="6">审核人类型</a-col>
          <a-col :span="6">审核对象</a-col>
          <a-col :span="4">最小通过数</a-col>
          <a-col :span="3">允许自审</a-col>
          <a-col :span="1">操作</a-col>
        </a-row>

        <div v-for="(stage, idx) in form.stages" :key="idx" class="stage-row">
          <a-row :gutter="8" align="middle">
            <a-col :span="4">
              <a-input-number v-model:value="stage.stageOrder" :min="1" style="width:100%" placeholder="如 1" />
            </a-col>
            <a-col :span="6">
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
            <a-col :span="3"><a-switch v-model:checked="stage.allowSelfReview" /></a-col>
            <a-col :span="1">
              <permissions-tooltip
                :allowed="canManagePolicy"
                tips="需要 MANAGE_REVIEW_POLICY 或 VIEW_RESOURCE_ALL 权限"
                v-slot="{ disabled }"
              >
                <a-button type="link" danger :disabled="disabled" @click="removeStage(idx)">删</a-button>
              </permissions-tooltip>
            </a-col>
          </a-row>
        </div>
        <permissions-tooltip
          :allowed="canManagePolicy"
          tips="需要 MANAGE_REVIEW_POLICY 或 VIEW_RESOURCE_ALL 权限"
          block
          v-slot="{ disabled }"
        >
          <a-button type="dashed" block :disabled="disabled" @click="addStage">添加阶段</a-button>
        </permissions-tooltip>
      </a-form>
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

const authStore = useAuthStore()
const policies = ref([])
const visible = ref(false)
const editing = ref(null)
const canManagePolicy = computed(() => authStore.hasAnyPermission(['MANAGE_REVIEW_POLICY', 'VIEW_RESOURCE_ALL']))

const userReviewerOptions = ref([])
const roleReviewerOptions = ref([])
const departmentReviewerOptions = ref([])
const reviewerOptionsLoading = ref(false)
const reviewerOptionsLoaded = ref(false)

const columns = [
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '优先级', dataIndex: 'priority', key: 'priority', width: 100 },
  { title: '作用域', dataIndex: 'scopeType', key: 'scopeType', width: 120 },
  { title: '阶段数', key: 'stages', width: 100 },
  { title: '状态', key: 'enabled', width: 120 },
  { title: '操作', key: 'action', width: 100 },
]

const form = reactive({
  name: '',
  enabled: true,
  scopeType: 'global',
  scopeDepartmentId: null,
  uploaderConstraint: 'all',
  constraintRefId: null,
  priority: 100,
  stages: [],
})

onMounted(fetchPolicies)

let reviewerOptionsPromise = null

function mapToOptions(items, labelGetter, prefix) {
  return (items || []).map(item => ({
    value: item.id,
    label: labelGetter(item) || `${prefix}#${item.id}`,
  }))
}

function getBaseReviewerOptions(type) {
  if (type === 'user') return userReviewerOptions.value
  if (type === 'department') return departmentReviewerOptions.value
  return roleReviewerOptions.value
}

function getReviewerOptions(stage) {
  const options = getBaseReviewerOptions(stage?.reviewerType || 'role')
  const reviewerRefId = stage?.reviewerRefId
  if (reviewerRefId === null || reviewerRefId === undefined || reviewerRefId === '') return options

  const exists = options.some(option => Number(option.value) === Number(reviewerRefId))
  if (exists) return options

  return [...options, { value: reviewerRefId, label: `已失效对象（ID: ${reviewerRefId}）` }]
}

function getReviewerPlaceholder(type) {
  if (type === 'user') return '请选择用户'
  if (type === 'department') return '请选择部门'
  return '请选择角色'
}

function onReviewerTypeChange(stage) {
  stage.reviewerRefId = null
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

    userReviewerOptions.value = mapToOptions(users, item => item.nickname || item.username, '用户')
    roleReviewerOptions.value = mapToOptions(roles, item => item.name || item.code, '角色')
    departmentReviewerOptions.value = mapToOptions(departments, item => item.name || item.code, '部门')

    if (!usersRes || !rolesRes || !departmentsRes) {
      message.warning('审核对象数据加载不完整，部分选项不可用')
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
  form.enabled = true
  form.scopeType = 'global'
  form.scopeDepartmentId = null
  form.uploaderConstraint = 'all'
  form.constraintRefId = null
  form.priority = 100
  form.stages = [{ stageOrder: 1, reviewerType: 'role', reviewerRefId: null, minApprovals: 1, allowSelfReview: false }]
}

async function fetchPolicies() {
  try {
    policies.value = await getReviewPolicies() || []
  } catch (e) {
    message.error(e.message || '加载策略失败')
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
  form.enabled = policy.enabled
  form.scopeType = policy.scopeType
  form.scopeDepartmentId = policy.scopeDepartmentId
  form.uploaderConstraint = policy.uploaderConstraint
  form.constraintRefId = policy.constraintRefId
  form.priority = policy.priority
  form.stages = (policy.stages || []).map(s => ({
    stageOrder: s.stageOrder,
    reviewerType: s.reviewerType,
    reviewerRefId: s.reviewerRefId,
    minApprovals: s.minApprovals,
    allowSelfReview: s.allowSelfReview,
  }))
  if (!form.stages.length) addStage()
  await ensureReviewerOptionsLoaded()
  visible.value = true
}

function addStage() {
  if (!canManagePolicy.value) return
  const maxOrder = form.stages.reduce((m, s) => Math.max(m, Number(s.stageOrder || 0)), 0)
  form.stages.push({ stageOrder: maxOrder + 1, reviewerType: 'role', reviewerRefId: null, minApprovals: 1, allowSelfReview: false })
}

function removeStage(idx) {
  if (!canManagePolicy.value) return
  form.stages.splice(idx, 1)
  if (!form.stages.length) addStage()
}

async function save() {
  if (!canManagePolicy.value) return
  if (!form.name.trim()) return message.warning('请输入策略名称')
  if (!form.stages.length) return message.warning('请至少配置一个审核阶段')

  for (let i = 0; i < form.stages.length; i++) {
    const stage = form.stages[i]
    if (!stage.reviewerType) return message.warning(`第 ${i + 1} 级缺少审核人类型`)
    if (stage.reviewerRefId === null || stage.reviewerRefId === undefined || stage.reviewerRefId === '') {
      return message.warning(`第 ${i + 1} 级缺少审核对象`)
    }
  }

  const payload = {
    name: form.name,
    enabled: form.enabled,
    scopeType: form.scopeType,
    scopeDepartmentId: form.scopeDepartmentId,
    uploaderConstraint: form.uploaderConstraint,
    constraintRefId: form.constraintRefId,
    priority: form.priority,
    stages: form.stages.map(s => ({
      stageOrder: s.stageOrder,
      reviewerType: s.reviewerType,
      reviewerRefId: s.reviewerRefId,
      minApprovals: s.minApprovals,
      allowSelfReview: s.allowSelfReview,
    })),
  }

  try {
    if (editing.value) {
      await updateReviewPolicy(editing.value.id, payload)
      message.success('策略已更新')
    } else {
      await createReviewPolicy(payload)
      message.success('策略已创建')
    }
    visible.value = false
    fetchPolicies()
  } catch (e) {
    message.error(e.message || '保存失败')
  }
}
</script>

<style scoped>
.policy-manage-page { padding: 0; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.stage-header {
  margin-bottom: 8px;
  padding: 0 8px;
  color: #666;
  font-size: 12px;
}
.stage-row { margin-bottom:10px; padding:8px; background:#fafafa; border-radius:6px; }
</style>
