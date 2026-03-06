<template>
  <div class="training-list-page">
    <div class="page-header">
      <h2>{{ authStore.isStudent ? '我的培训' : '培训班管理' }}</h2>
      <a-button type="primary" v-if="authStore.isAdmin || authStore.isInstructor" @click="showCreateModal = true">
        <template #icon><PlusOutlined /></template>新建培训班
      </a-button>
    </div>

    <!-- 统计卡 -->
    <a-row :gutter="16" style="margin-bottom:20px">
      <a-col :span="6" v-for="stat in stats" :key="stat.label">
        <a-card :bordered="false" class="stat-card">
          <div class="stat-icon" :style="{ background: stat.color + '20', color: stat.color }">{{ stat.icon }}</div>
          <div class="stat-num">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 过滤 -->
    <a-card :bordered="false" style="margin-bottom:16px">
      <a-space>
        <a-select v-model:value="filterStatus" style="width:120px">
          <a-select-option value="all">全部状态</a-select-option>
          <a-select-option value="active">进行中</a-select-option>
          <a-select-option value="upcoming">未开始</a-select-option>
          <a-select-option value="ended">已结束</a-select-option>
        </a-select>
        <a-select v-model:value="filterType" style="width:120px">
          <a-select-option value="all">全部类型</a-select-option>
          <a-select-option value="basic">基础训练</a-select-option>
          <a-select-option value="special">专项训练</a-select-option>
          <a-select-option value="promotion">晋升培训</a-select-option>
          <a-select-option value="online">线上培训</a-select-option>
        </a-select>
        <a-input-search v-model:value="searchText" placeholder="搜索培训班..." style="width:240px" allow-clear />
      </a-space>
    </a-card>

    <!-- 培训班列表 -->
    <div class="training-cards">
      <div v-for="t in filteredTrainings" :key="t.id" class="training-card">
        <div class="tc-header" :class="'status-' + t.status">
          <div class="tc-status-dot"></div>
          <span class="tc-status-text">{{ statusLabels[t.status] }}</span>
          <a-tag size="small" style="margin-left:auto;font-size:11px">{{ t.typeLabel }}</a-tag>
        </div>
        <div class="tc-body">
          <div class="tc-title">{{ t.name }}</div>
          <div class="tc-meta">
            <div class="tc-meta-item"><CalendarOutlined /> {{ t.startDate }} ~ {{ t.endDate }}</div>
            <div class="tc-meta-item"><TeamOutlined /> {{ t.enrolled }}/{{ t.capacity }} 人</div>
            <div class="tc-meta-item"><UserOutlined /> {{ t.instructorName }}</div>
            <div class="tc-meta-item"><EnvironmentOutlined /> {{ t.location }}</div>
          </div>
          <a-progress
            :percent="Math.round(t.enrolled / t.capacity * 100)"
            :stroke-color="t.enrolled >= t.capacity ? '#ff4d4f' : '#003087'"
            size="small"
            style="margin-top:12px"
          />
        </div>
        <div class="tc-footer">
          <a-button size="small" @click="goDetail(t)">查看详情</a-button>
          <!-- Admin/Instructor: 开班签到 -->
          <a-button size="small" type="primary" @click="goCheckin(t)" v-if="t.status === 'active' && !authStore.isStudent">
            <template #icon><QrcodeOutlined /></template>开班签到
          </a-button>

          <!-- 学员：已报名且进行中才能扫码 -->
          <a-button size="small" type="primary" @click="goCheckin(t)"
            v-if="t.status === 'active' && authStore.isStudent && t.students.includes(authStore.currentUser?.id)">
            <template #icon><QrcodeOutlined /></template>扫码签到
          </a-button>

          <template v-if="t.status === 'upcoming' && authStore.isStudent">
            <a-button size="small" disabled v-if="t.students.includes(authStore.currentUser?.id)">已报名</a-button>
            <a-button size="small" disabled v-else-if="isPending(t.id)">审核中</a-button>
            <a-button size="small" @click="goEnroll(t)" v-else>报名申请</a-button>
          </template>

          <!-- 学员：已报名的班级可看日程 -->
          <a-button size="small" @click="goSchedule(t)"
            v-if="authStore.isStudent && t.students.includes(authStore.currentUser?.id)">
            查看日程
          </a-button>
          <a-dropdown v-if="authStore.isAdmin || authStore.isInstructor" :trigger="['click']">
            <a-button size="small"><EllipsisOutlined /></a-button>
            <template #overlay>
              <div class="dropdown-menu">
                <div class="dropdown-item" @click="handleEdit(t)">✏️ 编辑</div>
                <div class="dropdown-item" @click="goEnrollManage(t)">📋 报名管理</div>
                <div class="dropdown-item danger" @click="handleDelete(t)">🗑️ 删除</div>
              </div>
            </template>
          </a-dropdown>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <a-empty v-if="filteredTrainings.length === 0" description="暂无符合条件的培训班" style="margin-top:60px" />

    <!-- 新建/编辑培训班弹窗 -->
    <a-modal
      v-model:open="showCreateModal"
      :title="editingTraining ? '编辑培训班' : '新建培训班'"
      width="680px"
      @ok="handleSubmitTraining"
      @cancel="resetForm"
      ok-text="确认保存"
      cancel-text="取消"
    >
      <a-form :model="trainingForm" layout="vertical" style="margin-top:16px">
        <a-row :gutter="16">
          <a-col :span="24">
            <a-form-item label="培训班名称" required>
              <a-input v-model:value="trainingForm.name" placeholder="例：2025年春季刑侦专项训练班（第一期）" :maxlength="50" show-count />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="培训类型" required>
              <a-select v-model:value="trainingForm.type" placeholder="请选择类型">
                <a-select-option value="basic">基础训练</a-select-option>
                <a-select-option value="special">专项训练</a-select-option>
                <a-select-option value="promotion">晋升培训</a-select-option>
                <a-select-option value="online">线上培训</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="班级容量" required>
              <a-input-number v-model:value="trainingForm.capacity" :min="5" :max="500" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="开始日期" required>
              <a-date-picker
                v-model:value="trainingFormDates[0]"
                style="width:100%"
                :format="'YYYY-MM-DD'"
                placeholder="请选择开始日期"
                @change="(_, s) => trainingForm.startDate = s"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="结束日期" required>
              <a-date-picker
                v-model:value="trainingFormDates[1]"
                style="width:100%"
                :format="'YYYY-MM-DD'"
                placeholder="请选择结束日期"
                @change="(_, s) => trainingForm.endDate = s"
              />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="培训地点" required>
              <a-input v-model:value="trainingForm.location" placeholder="例：第三训练楼201教室" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="主管教官">
              <a-select
                v-model:value="trainingForm.instructorId"
                placeholder="从教官库中选择"
                show-search
                option-filter-prop="label"
                style="width:100%"
                @change="onInstructorChange"
              >
                <a-select-option
                  v-for="inst in MOCK_INSTRUCTORS"
                  :key="inst.id"
                  :value="inst.id"
                  :label="inst.name"
                >
                  {{ inst.name }} · {{ inst.title }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="培训简介">
              <a-textarea v-model:value="trainingForm.description" :rows="3" placeholder="请简要描述本次培训的目标和内容..." :maxlength="200" show-count />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, CalendarOutlined, TeamOutlined, UserOutlined, EnvironmentOutlined, QrcodeOutlined, EllipsisOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { MOCK_TRAININGS, TRAINING_TYPES } from '@/mock/trainings'
import { MOCK_ENROLLMENTS } from '@/mock/enrollments'
import { MOCK_INSTRUCTORS } from '@/mock/instructors'

const router = useRouter()
const authStore = useAuthStore()
const filterStatus = ref('all')
const filterType = ref('all')
const searchText = ref('')
const showCreateModal = ref(false)
const editingTraining = ref(null)

const statusLabels = { active: '进行中', upcoming: '未开始', ended: '已结束' }

const typeLabels = { basic: '基础训练', special: '专项训练', promotion: '晋升培训', online: '线上培训' }

const isPending = (trainingId) => {
  return authStore.isStudent && MOCK_ENROLLMENTS.some(e => e.trainingId === trainingId && e.userId === authStore.currentUser?.id && e.status === 'pending')
}

// 本地可修改的培训班列表
const trainingList = ref([...MOCK_TRAININGS])

const filteredTrainings = computed(() => {
  let list = trainingList.value
  // 学员只看自己参与的 + 正在招生的
  if (authStore.isStudent) {
    const myId = authStore.currentUser?.id
    list = list.filter(t =>
      (t.students || []).includes(myId) || t.status === 'upcoming'
    )
  }
  if (filterStatus.value !== 'all') list = list.filter(t => t.status === filterStatus.value)
  if (filterType.value !== 'all') list = list.filter(t => t.type === filterType.value)
  if (searchText.value) list = list.filter(t => t.name.includes(searchText.value))
  return list
})

const stats = computed(() => [
  { icon: '🏫', label: '全部培训班', value: trainingList.value.length, color: '#003087' },
  { icon: '▶', label: '进行中', value: trainingList.value.filter(t => t.status === 'active').length, color: '#52c41a' },
  { icon: '🕐', label: '未开始', value: trainingList.value.filter(t => t.status === 'upcoming').length, color: '#faad14' },
  { icon: '✓', label: '已结束', value: trainingList.value.filter(t => t.status === 'ended').length, color: '#888' },
])

// 表单数据
const trainingFormDates = ref([null, null]) // dayjs values for date-pickers
const trainingForm = reactive({
  name: '',
  type: 'basic',
  capacity: 30,
  startDate: '',
  endDate: '',
  location: '',
  instructorId: null,
  instructorName: '',
  description: '',
})

const onInstructorChange = (id) => {
  const inst = MOCK_INSTRUCTORS.find(i => i.id === id)
  if (inst) trainingForm.instructorName = inst.name
}

const resetForm = () => {
  Object.assign(trainingForm, { name: '', type: 'basic', capacity: 30, startDate: '', endDate: '', location: '', instructorId: null, instructorName: '', description: '' })
  trainingFormDates.value = [null, null]
  editingTraining.value = null
  showCreateModal.value = false
}

const handleEdit = (t) => {
  editingTraining.value = t
  Object.assign(trainingForm, {
    name: t.name,
    type: t.type,
    capacity: t.capacity,
    startDate: t.startDate,
    endDate: t.endDate,
    location: t.location,
    instructorId: t.instructorId || null,
    instructorName: t.instructorName,
    description: t.description,
  })
  showCreateModal.value = true
}

const handleSubmitTraining = () => {
  if (!trainingForm.name || !trainingForm.startDate || !trainingForm.endDate || !trainingForm.location) {
    message.warning('请填写必填项：培训班名称、日期、地点')
    return
  }
  const typeMap = { basic: '基础训练', special: '专项训练', promotion: '晋升培训', online: '线上培训' }
  if (editingTraining.value) {
    // 编辑
    const idx = trainingList.value.findIndex(t => t.id === editingTraining.value.id)
    if (idx !== -1) {
      trainingList.value[idx] = {
        ...trainingList.value[idx],
        name: trainingForm.name,
        type: trainingForm.type,
        typeLabel: typeMap[trainingForm.type],
        capacity: trainingForm.capacity,
        startDate: trainingForm.startDate,
        endDate: trainingForm.endDate,
        location: trainingForm.location,
        instructorId: trainingForm.instructorId,
        instructorName: trainingForm.instructorName,
        description: trainingForm.description,
      }
    }
    message.success('培训班信息已更新')
  } else {
    // 新建
    const newId = `t${String(Date.now()).slice(-4)}`
    trainingList.value.unshift({
      id: newId,
      name: trainingForm.name,
      type: trainingForm.type,
      typeLabel: typeMap[trainingForm.type],
      status: 'upcoming',
      startDate: trainingForm.startDate,
      endDate: trainingForm.endDate,
      location: trainingForm.location,
      instructorName: trainingForm.instructorName,
      capacity: trainingForm.capacity,
      enrolled: 0,
      students: [],
      description: trainingForm.description,
      subjects: [],
      courses: [],
      checkinRecords: [],
    })
    message.success('培训班创建成功')
  }
  resetForm()
}

const handleDelete = (t) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除培训班"${t.name}"吗？此操作不可恢复。`,
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: () => {
      trainingList.value = trainingList.value.filter(item => item.id !== t.id)
      message.success('已删除')
    },
  })
}

const goDetail = (t) => router.push({ name: 'TrainingDetail', params: { id: t.id } })
const goCheckin = (t) => router.push({ name: 'Checkin', params: { id: t.id } })
const goSchedule = (t) => router.push('/training/schedule/' + t.id)
const goEnroll = (t) => router.push(`/training/${t.id}/enroll`)
const goEnrollManage = (t) => router.push(`/training/${t.id}/enroll/manage`)
</script>

<style scoped>
.training-list-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.stat-card { text-align: center; }
.stat-icon { width: 48px; height: 48px; border-radius: 50%; margin: 0 auto 8px; display: flex; align-items: center; justify-content: center; font-size: 22px; }
.stat-num { font-size: 28px; font-weight: 700; color: #1a1a1a; }
.stat-label { font-size: 12px; color: #888; }
.training-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.training-card { background: #fff; border-radius: 8px; border: 1px solid #e8e8e8; overflow: hidden; transition: box-shadow 0.2s; }
.training-card:hover { box-shadow: 0 4px 16px rgba(0,48,135,0.10); }
.tc-header { padding: 8px 16px; display: flex; align-items: center; gap: 8px; }
.tc-header.status-active { background: #f6ffed; }
.tc-header.status-upcoming { background: #fffbe6; }
.tc-header.status-ended { background: #f5f5f5; }
.tc-status-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
.status-active .tc-status-dot { background: #52c41a; }
.status-upcoming .tc-status-dot { background: #faad14; }
.status-ended .tc-status-dot { background: #bbb; }
.tc-status-text { font-size: 12px; font-weight: 600; }
.status-active .tc-status-text { color: #52c41a; }
.status-upcoming .tc-status-text { color: #faad14; }
.status-ended .tc-status-text { color: #888; }
.tc-body { padding: 14px 16px; }
.tc-title { font-size: 15px; font-weight: 600; color: #1a1a1a; margin-bottom: 12px; line-height: 1.4; }
.tc-meta { display: flex; flex-direction: column; gap: 6px; }
.tc-meta-item { font-size: 13px; color: #666; display: flex; align-items: center; gap: 6px; }
.tc-footer { padding: 10px 16px; background: #fafafa; border-top: 1px solid #f0f0f0; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }

@media (max-width: 900px) {
  .training-cards { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .training-cards { grid-template-columns: 1fr !important; }
  .stat-card { padding: 12px; margin-bottom: 8px; }
  .stat-num { font-size: 20px; }
}
.dropdown-menu {
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  padding: 4px 0;
  min-width: 120px;
}
.dropdown-item {
  padding: 8px 16px;
  font-size: 13px;
  cursor: pointer;
  color: #333;
  transition: background 0.15s;
}
.dropdown-item:hover {
  background: #f5f5f5;
}
.dropdown-item.danger {
  color: #ff4d4f;
}
</style>
