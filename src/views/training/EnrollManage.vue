<template>
  <div class="enroll-manage">
    <!-- 页头 -->
    <div class="page-header-bar" v-if="training">
      <div>
        <h2 class="page-h2">报名管理</h2>
        <div class="page-sub">{{ training.name }}</div>
      </div>
      <div class="header-actions">
        <a-button @click="$router.back()"><ArrowLeftOutlined /> 返回</a-button>
        <a-button type="primary" ghost @click="message.success('名单已导出')"><DownloadOutlined /> 导出名单</a-button>
      </div>
    </div>

    <!-- 名额统计卡 -->
    <div class="quota-cards" v-if="training">
      <div class="qcard">
        <div class="qcard-num total">{{ training.capacity }}</div>
        <div class="qcard-label">总名额</div>
      </div>
      <div class="qcard">
        <div class="qcard-num approved">{{ approvedList.length }}</div>
        <div class="qcard-label">已录取</div>
        <a-progress :percent="Math.round((approvedList.length / training.capacity) * 100) || 0" :show-info="false" stroke-color="#52c41a" size="small" />
      </div>
      <div class="qcard">
        <div class="qcard-num pending">{{ pendingList.length }}</div>
        <div class="qcard-label">待审核</div>
      </div>
      <div class="qcard">
        <div class="qcard-num remain">{{ Math.max(0, training.capacity - approvedList.length) }}</div>
        <div class="qcard-label">剩余名额</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <a-input-search v-model:value="searchText" placeholder="搜索姓名/警号/单位" style="width:240px" allow-clear />
      <a-radio-group v-model:value="statusFilter" button-style="solid">
        <a-radio-button value="all">全部 ({{ enrollments.length }})</a-radio-button>
        <a-radio-button value="pending">待审核 ({{ pendingList.length }})</a-radio-button>
        <a-radio-button value="approved">已录取 ({{ approvedList.length }})</a-radio-button>
        <a-radio-button value="rejected">已拒绝 ({{ rejectedList.length }})</a-radio-button>
      </a-radio-group>
      <a-button type="primary" :disabled="selectedRows.length === 0" @click="batchApprove">
        批量通过 ({{ selectedRows.length }})
      </a-button>
    </div>

    <!-- 报名列表表格 -->
    <div class="table-card">
      <a-table
        :columns="columns"
        :data-source="filteredList"
        :row-selection="{ selectedRowKeys: selectedRowKeys, onChange: onSelectChange }"
        row-key="id"
        :pagination="{ pageSize: 10 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space v-if="record.status === 'pending'">
              <a-button type="primary" size="small" @click="approve(record)">通过</a-button>
              <a-button danger size="small" @click="reject(record)">拒绝</a-button>
            </a-space>
            <span v-else class="handled-text">已处理</span>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { ArrowLeftOutlined, DownloadOutlined } from '@ant-design/icons-vue'
import { MOCK_ENROLLMENTS } from '@/mock/enrollments.js'
import { MOCK_TRAININGS } from '@/mock/trainings.js'

const route = useRoute()
const trainingId = route.params.id
// 使用 reactive 包装，以便在修改 enrolled / students 数量后页面能响应式更新
const training = reactive(MOCK_TRAININGS.find(t => t.id === trainingId) || {})

const searchText = ref('')
const statusFilter = ref('all')
const selectedRowKeys = ref([])
const selectedRows = ref([])

// 直接引用全局数据，从而真实改变 mock 状态
const enrollments = ref(MOCK_ENROLLMENTS.filter(e => e.trainingId === trainingId))

const pendingList = computed(() => enrollments.value.filter(e => e.status === 'pending'))
const approvedList = computed(() => enrollments.value.filter(e => e.status === 'approved'))
const rejectedList = computed(() => enrollments.value.filter(e => e.status === 'rejected'))

const filteredList = computed(() => {
  let list = enrollments.value
  if (statusFilter.value !== 'all') list = list.filter(e => e.status === statusFilter.value)
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(e => e.name.includes(q) || e.policeId.toLowerCase().includes(q) || e.unit.includes(q))
  }
  return list
})

const columns = [
  { title: '姓名', dataIndex: 'name', key: 'name', width: 80 },
  { title: '警号', dataIndex: 'policeId', key: 'policeId', width: 120 },
  { title: '所属单位', dataIndex: 'unit', key: 'unit' },
  { title: '联系电话', dataIndex: 'phone', key: 'phone', width: 120 },
  { title: '报名时间', dataIndex: 'enrollTime', key: 'enrollTime', width: 160 },
  { title: '状态', key: 'status', width: 90 },
  { title: '操作', key: 'action', width: 140, fixed: 'right' },
]

function statusColor(s) { return { approved: 'green', pending: 'orange', rejected: 'red' }[s] || 'default' }
function statusLabel(s) { return { approved: '已录取', pending: '待审核', rejected: '已拒绝' }[s] || s }

function onSelectChange(keys, rows) {
  selectedRowKeys.value = keys
  selectedRows.value = rows
}

function approve(record) {
  if (training.students.length >= training.capacity) {
    message.error('名额已满，无法通过更多学员')
    return
  }
  record.status = 'approved'
  if (!training.students.includes(record.userId)) {
    training.students.push(record.userId)
    training.enrolled = training.students.length
  }
  message.success(`已通过 ${record.name} 的报名申请`)
}

function reject(record) {
  record.status = 'rejected'
  record.note = '名额限制，暂无资格'
  message.warning(`已拒绝 ${record.name} 的报名申请`)
}

function batchApprove() {
  const pendingCount = selectedRows.value.filter(r => r.status === 'pending').length
  const remain = training.capacity - training.students.length
  if (pendingCount > remain) {
    message.error(`批量通过失败：剩余名额不足（仅剩 ${remain} 人）`)
    return
  }

  selectedRows.value.forEach(r => { 
    if (r.status === 'pending') {
      r.status = 'approved'
      if (!training.students.includes(r.userId)) {
        training.students.push(r.userId)
      }
    }
  })
  training.enrolled = training.students.length
  message.success(`已批量通过审核`)
  selectedRowKeys.value = []
  selectedRows.value = []
}
</script>

<style scoped>
.enroll-manage { }
.page-header-bar { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.page-h2 { font-size: 20px; font-weight: 700; color: #001234; margin: 0 0 4px; }
.page-sub { font-size: 13px; color: #8c8c8c; }
.header-actions { display: flex; gap: 8px; }
.quota-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.qcard { background: white; border-radius: 8px; padding: 16px 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.qcard-num { font-size: 32px; font-weight: 700; margin-bottom: 4px; }
.qcard-num.total { color: #595959; }
.qcard-num.approved { color: #52c41a; }
.qcard-num.pending { color: #fa8c16; }
.qcard-num.remain { color: #003087; }
.qcard-label { font-size: 12px; color: #8c8c8c; margin-bottom: 8px; }
.filter-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.table-card { background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden; }
:deep(.ant-table) { border-radius: 8px; }
.handled-text { color: #8c8c8c; font-size: 12px; }
</style>
