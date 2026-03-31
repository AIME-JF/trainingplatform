<template>
  <div class="enroll-manage">
    <div class="page-header" v-if="training">
      <div>
        <h2>报名管理</h2>
        <p class="page-sub">{{ training.name }}</p>
      </div>
      <a-space>
        <a-button @click="$router.back()">返回</a-button>
        <permissions-tooltip
          :allowed="canManageRoster"
          :disabled="training.isLocked"
          :tips="trainingManageTooltip"
          v-slot="{ disabled }"
        >
          <a-button type="primary" danger ghost :disabled="disabled" @click="handleLock">
            {{ training.isLocked ? '名单已锁定' : '锁定名单' }}
          </a-button>
        </permissions-tooltip>
        <permissions-tooltip
          :allowed="canManageRoster"
          :tips="trainingManageTooltip"
          v-slot="{ disabled }"
        >
          <a-button type="primary" :disabled="disabled" @click="saveRosterAssignments">保存编组</a-button>
        </permissions-tooltip>
      </a-space>
    </div>

    <a-row :gutter="16" style="margin-bottom:20px" v-if="training">
      <a-col :span="6"><a-card :bordered="false" class="kpi-card"><div class="kpi-value">{{ training.capacity || 0 }}</div><div class="kpi-label">总名额</div></a-card></a-col>
      <a-col :span="6"><a-card :bordered="false" class="kpi-card"><div class="kpi-value">{{ approvedList.length }}</div><div class="kpi-label">已录取</div></a-card></a-col>
      <a-col :span="6"><a-card :bordered="false" class="kpi-card"><div class="kpi-value">{{ pendingList.length }}</div><div class="kpi-label">待审核</div></a-card></a-col>
      <a-col :span="6"><a-card :bordered="false" class="kpi-card"><div class="kpi-value">{{ training.isLocked ? '是' : '否' }}</div><div class="kpi-label">名单锁定</div></a-card></a-col>
    </a-row>

    <a-card :bordered="false">
      <div class="toolbar">
        <a-input-search v-model:value="searchText" placeholder="搜索姓名/身份证号/单位" style="width:240px" allow-clear />
        <a-radio-group v-model:value="statusFilter">
          <a-radio-button value="all">全部</a-radio-button>
          <a-radio-button value="pending">待审核</a-radio-button>
          <a-radio-button value="approved">已录取</a-radio-button>
          <a-radio-button value="rejected">已拒绝</a-radio-button>
        </a-radio-group>
      </div>

      <a-table :columns="columns" :data-source="filteredList" row-key="id" :pagination="{ pageSize: 10 }">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'departments'">
            {{ (record.departments || []).join(' / ') }}
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColors[record.status]">{{ statusLabels[record.status] }}</a-tag>
          </template>
          <template v-if="column.key === 'groupName'">
            <a-input
              v-if="record.status === 'approved'"
              v-model:value="record.groupName"
              size="small"
              placeholder="编组名称"
              :disabled="training?.isLocked || !canManageRoster"
            />
            <span v-else>-</span>
          </template>
          <template v-if="column.key === 'cadreRole'">
            <a-select
              v-if="record.status === 'approved'"
              v-model:value="record.cadreRole"
              size="small"
              allow-clear
              placeholder="班干部"
              :disabled="training?.isLocked || !canManageRoster"
              style="width:120px"
            >
              <a-select-option value="班长">班长</a-select-option>
              <a-select-option value="副班长">副班长</a-select-option>
              <a-select-option value="学习委员">学习委员</a-select-option>
              <a-select-option value="纪律委员">纪律委员</a-select-option>
            </a-select>
            <span v-else>-</span>
          </template>
          <template v-if="column.key === 'action'">
            <a-space v-if="record.status === 'pending'">
              <permissions-tooltip
                :allowed="canApproveEnrollment"
                :tips="approveTooltip"
                v-slot="{ disabled }"
              >
                <a-button type="primary" size="small" :disabled="disabled" @click="approve(record)">通过</a-button>
              </permissions-tooltip>
              <permissions-tooltip
                :allowed="canRejectEnrollment"
                :tips="rejectTooltip"
                v-slot="{ disabled }"
              >
                <a-button danger size="small" :disabled="disabled" @click="reject(record)">拒绝</a-button>
              </permissions-tooltip>
            </a-space>
            <span v-else class="handled-text">已处理</span>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="rejectModalOpen"
      title="拒绝报名申请"
      ok-text="确认拒绝"
      cancel-text="取消"
      width="520px"
      @ok="submitReject"
      @cancel="resetRejectModal"
    >
      <a-form layout="vertical">
        <a-form-item label="拒绝理由" required>
          <a-textarea
            v-model:value="rejectNote"
            :rows="4"
            placeholder="请输入拒绝理由，学员会在报名结果中看到该说明"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import {
  approveEnrollment,
  getEnrollments,
  getTraining,
  lockTraining,
  rejectEnrollment,
  updateTrainingRoster,
} from '@/api/training'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

const route = useRoute()
const authStore = useAuthStore()
const trainingId = route.params.id

const training = ref(null)
const enrollments = ref([])
const searchText = ref('')
const statusFilter = ref('all')
const rejectModalOpen = ref(false)
const rejectTarget = ref(null)
const rejectNote = ref('')

const statusLabels = { pending: '待审核', approved: '已录取', rejected: '已拒绝' }
const statusColors = { pending: 'orange', approved: 'green', rejected: 'red' }

const columns = [
  { title: '姓名', dataIndex: 'userNickname', key: 'userNickname', width: 120 },
  { title: '身份证号', dataIndex: 'idCardNumber', key: 'idCardNumber', width: 180 },
  { title: '单位', key: 'departments' },
  { title: '电话', dataIndex: 'contactPhone', key: 'contactPhone', width: 140 },
  { title: '住宿', dataIndex: 'needAccommodation', key: 'needAccommodation', width: 80, customRender: ({ text }) => text ? '需要' : '无需' },
  { title: '状态', key: 'status', width: 90 },
  { title: '编组', key: 'groupName', width: 140 },
  { title: '班干部', key: 'cadreRole', width: 140 },
  { title: '操作', key: 'action', width: 140 },
]

const pendingList = computed(() => enrollments.value.filter(item => item.status === 'pending'))
const approvedList = computed(() => enrollments.value.filter(item => item.status === 'approved'))
const canManageRoster = computed(() => !!training.value?.canManageAll)
const canApproveEnrollment = computed(() => !!training.value?.canReviewEnrollments && authStore.hasPermission('APPROVE_ENROLLMENT'))
const canRejectEnrollment = computed(() => !!training.value?.canReviewEnrollments && authStore.hasPermission('REJECT_ENROLLMENT'))
const trainingManageTooltip = computed(() => {
  if (authStore.hasPermission('MANAGE_TRAINING')) return '当前培训班不在可管理范围内'
  if (authStore.hasPermission('UPDATE_TRAINING')) return '仅培训班班主任可执行该操作'
  return '需要 MANAGE_TRAINING，或具备 UPDATE_TRAINING 且为班主任'
})
const approveTooltip = computed(() => (
  !authStore.hasPermission('APPROVE_ENROLLMENT')
    ? '需要 APPROVE_ENROLLMENT 权限'
    : trainingManageTooltip.value
))
const rejectTooltip = computed(() => (
  !authStore.hasPermission('REJECT_ENROLLMENT')
    ? '需要 REJECT_ENROLLMENT 权限'
    : trainingManageTooltip.value
))

const filteredList = computed(() => {
  let rows = [...enrollments.value]
  if (statusFilter.value !== 'all') {
    rows = rows.filter(item => item.status === statusFilter.value)
  }
  if (searchText.value) {
    const keyword = searchText.value.toLowerCase()
    rows = rows.filter(item => {
      const name = (item.userNickname || item.userName || '').toLowerCase()
      const idCardNumber = (item.idCardNumber || '').toLowerCase()
      const departments = (item.departments || []).join(' ').toLowerCase()
      return name.includes(keyword) || idCardNumber.includes(keyword) || departments.includes(keyword)
    })
  }
  return rows
})

async function loadData() {
  try {
    const [trainingDetail, enrollmentResult] = await Promise.all([
      getTraining(trainingId),
      getEnrollments(trainingId, { size: -1 }),
    ])
    training.value = trainingDetail
    enrollments.value = enrollmentResult.items || []
  } catch (error) {
    message.error(error.message || '加载报名数据失败')
  }
}

async function approve(record) {
  if (!canApproveEnrollment.value) return
  try {
    await approveEnrollment(trainingId, record.id)
    record.status = 'approved'
    message.success('已通过报名申请')
  } catch (error) {
    message.error(error.message || '操作失败')
  }
}

async function reject(record) {
  if (!canRejectEnrollment.value) return
  rejectTarget.value = record
  rejectNote.value = record?.note || ''
  rejectModalOpen.value = true
}

function resetRejectModal() {
  rejectModalOpen.value = false
  rejectTarget.value = null
  rejectNote.value = ''
}

async function submitReject() {
  if (!rejectTarget.value) return
  if (!rejectNote.value.trim()) {
    message.warning('请输入拒绝理由')
    return
  }
  try {
    await rejectEnrollment(trainingId, rejectTarget.value.id, rejectNote.value.trim())
    rejectTarget.value.status = 'rejected'
    rejectTarget.value.note = rejectNote.value.trim()
    message.success('已拒绝报名申请')
    resetRejectModal()
  } catch (error) {
    message.error(error.message || '操作失败')
  }
}

async function saveRosterAssignments() {
  if (!canManageRoster.value) return
  const payload = approvedList.value.map(item => ({
    enrollmentId: item.id,
    groupName: item.groupName || undefined,
    cadreRole: item.cadreRole || undefined,
  }))
  try {
    const result = await updateTrainingRoster(trainingId, payload)
    enrollments.value = result
    message.success('编组信息已保存')
  } catch (error) {
    message.error(error.message || '保存失败')
  }
}

function handleLock() {
  if (!canManageRoster.value || training.value?.isLocked) return
  Modal.confirm({
    title: '确认锁定名单？',
    content: '锁定后将不再接受新报名，待审核记录会自动关闭。',
    okType: 'danger',
    onOk: async () => {
      try {
        await lockTraining(trainingId)
        message.success('名单已锁定')
        loadData()
      } catch (error) {
        message.error(error.message || '锁定失败')
      }
    },
  })
}

onMounted(loadData)
</script>

<style scoped>
.enroll-manage { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 12px; }
.page-header h2 { margin: 0; color: #001234; }
.page-sub { margin: 6px 0 0; font-size: 13px; color: #8c8c8c; }
.kpi-card { text-align: center; }
.kpi-value { font-size: 30px; font-weight: 700; color: #003087; }
.kpi-label { font-size: 12px; color: #8c8c8c; }
.toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.handled-text { color: #8c8c8c; font-size: 12px; }
</style>
