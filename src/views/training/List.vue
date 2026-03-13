<template>
  <div class="training-list-page">
    <div class="page-header">
      <div>
        <h2>{{ authStore.isStudent ? '我的培训' : '培训班管理' }}</h2>
        <p class="page-sub">支持发布挂网、准入考试绑定、名单锁定和训历归档</p>
      </div>
      <a-button type="primary" v-if="authStore.isAdmin || authStore.isInstructor" @click="openCreateModal">
        <template #icon><PlusOutlined /></template>新建培训班
      </a-button>
    </div>

    <a-row :gutter="16" style="margin-bottom:20px">
      <a-col :span="6" v-for="stat in stats" :key="stat.label">
        <a-card :bordered="false" class="stat-card">
          <div class="stat-value" :style="{ color: stat.color }">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </a-card>
      </a-col>
    </a-row>

    <a-card :bordered="false" style="margin-bottom:16px">
      <a-space wrap>
        <a-select v-model:value="filterStatus" style="width:120px">
          <a-select-option value="all">全部状态</a-select-option>
          <a-select-option value="active">进行中</a-select-option>
          <a-select-option value="upcoming">未开始</a-select-option>
          <a-select-option value="ended">已结束</a-select-option>
        </a-select>
        <a-select v-model:value="filterPublish" style="width:140px">
          <a-select-option value="all">全部发布状态</a-select-option>
          <a-select-option value="published">已发布</a-select-option>
          <a-select-option value="draft">草稿</a-select-option>
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

    <div class="training-cards">
      <div v-for="training in filteredTrainings" :key="training.id" class="training-card">
        <div class="card-top">
          <div class="card-status">
            <a-tag :color="statusColors[training.status]">{{ statusLabels[training.status] }}</a-tag>
            <a-tag :color="training.publishStatus === 'published' ? 'blue' : 'default'">
              {{ training.publishStatus === 'published' ? '已发布' : '草稿' }}
            </a-tag>
            <a-tag v-if="training.isLocked" color="red">名单已锁定</a-tag>
          </div>
          <a-tag>{{ typeLabels[training.type] || training.type }}</a-tag>
        </div>

        <div class="card-title">{{ training.name }}</div>
        <div class="card-desc">{{ training.description || '暂无培训简介' }}</div>

        <div class="card-grid">
          <div class="grid-item"><CalendarOutlined /> {{ training.startDate || '待定' }} 至 {{ training.endDate || '待定' }}</div>
          <div class="grid-item"><TeamOutlined /> {{ training.enrolledCount || 0 }}/{{ training.capacity || 0 }} 人</div>
          <div class="grid-item"><UserOutlined /> {{ training.instructorName || '未指定' }}</div>
          <div class="grid-item"><EnvironmentOutlined /> {{ training.location || '未设置地点' }}</div>
        </div>

        <div class="extra-info">
          <div>报名窗口：{{ formatWindow(training.enrollmentStartAt, training.enrollmentEndAt) }}</div>
          <div>准入考试：{{ training.admissionExamTitle || '无' }}</div>
        </div>

        <a-progress :percent="Number.isFinite(training.progressPercent) ? training.progressPercent : 0" size="small" style="margin:12px 0 16px" />

        <div class="card-actions">
          <a-button size="small" type="primary" @click="goDetail(training)">进入培训班</a-button>
          <a-button size="small" @click="goHistory(training)">训历</a-button>

          <template v-if="authStore.isStudent && !isMyTraining(training)">
            <a-button
              v-if="training.status !== 'ended' && training.publishStatus === 'published'"
              size="small"
              :disabled="training.isLocked"
              @click="goEnroll(training)"
            >
              {{ training.isLocked ? '名单已锁定' : '报名申请' }}
            </a-button>
          </template>
        </div>
      </div>
    </div>

    <a-empty v-if="filteredTrainings.length === 0" description="暂无符合条件的培训班" style="margin-top:60px" />

    <a-modal
      v-model:open="showCreateModal"
      :title="editingTraining ? '编辑培训班' : '新建培训班'"
      width="760px"
      @ok="handleSubmitTraining"
      @cancel="resetForm"
      ok-text="确认保存"
      cancel-text="取消"
    >
      <a-form :model="trainingForm" layout="vertical" style="margin-top:16px">
        <a-row :gutter="16">
          <a-col :span="24">
            <a-form-item label="培训班名称" required>
              <a-input v-model:value="trainingForm.name" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="培训类型" required>
              <a-select v-model:value="trainingForm.type">
                <a-select-option value="basic">基础训练</a-select-option>
                <a-select-option value="special">专项训练</a-select-option>
                <a-select-option value="promotion">晋升培训</a-select-option>
                <a-select-option value="online">线上培训</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="班级容量" required>
              <a-input-number v-model:value="trainingForm.capacity" :min="5" :max="500" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="班次编号">
              <a-input v-model:value="trainingForm.classCode" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="开始日期" required>
              <a-date-picker v-model:value="trainingFormDates[0]" style="width:100%" format="YYYY-MM-DD" @change="(_, s) => trainingForm.startDate = s" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="结束日期" required>
              <a-date-picker v-model:value="trainingFormDates[1]" style="width:100%" format="YYYY-MM-DD" @change="(_, s) => trainingForm.endDate = s" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="报名窗口">
              <a-range-picker
                v-model:value="enrollmentWindow"
                show-time
                format="YYYY-MM-DD HH:mm:ss"
                value-format="YYYY-MM-DD HH:mm:ss"
                style="width:100%"
                @change="handleWindowChange"
              />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="培训地点" required>
              <a-input v-model:value="trainingForm.location" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="主管教官">
              <a-select
                v-model:value="trainingForm.instructorId"
                show-search
                option-filter-prop="label"
                @change="onInstructorChange"
              >
                <a-select-option
                  v-for="inst in instructorList"
                  :key="inst.userId"
                  :value="inst.userId"
                  :label="inst.name"
                >
                  {{ inst.name }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="准入考试">
              <a-select v-model:value="trainingForm.admissionExamId" allow-clear placeholder="可选，报名需先通过">
                <a-select-option v-for="exam in admissionExamOptions" :key="exam.id" :value="exam.id">
                  {{ exam.title }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="培训简介">
              <a-textarea v-model:value="trainingForm.description" :rows="3" />
            </a-form-item>
          </a-col>
          <a-col :span="24" v-if="!editingTraining">
            <a-form-item label="学员Excel导入（可选）">
              <a-upload :before-upload="handleStudentImportBeforeUpload" :show-upload-list="false" accept=".xlsx">
                <a-button>选择学员名单文件</a-button>
              </a-upload>
              <div v-if="studentImportFileName" class="import-tip">已选择：{{ studentImportFileName }}</div>
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import dayjs from 'dayjs'
import {
  CalendarOutlined,
  EnvironmentOutlined,
  PlusOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import {
  createTraining,
  deleteTraining,
  endTraining,
  getTrainings,
  importTrainingStudents,
  lockTraining,
  publishTraining,
  startTraining,
  updateTraining,
} from '@/api/training'
import { getUsers } from '@/api/user'
import { getAdmissionExams } from '@/api/exam'

const router = useRouter()
const authStore = useAuthStore()

const statusLabels = { active: '进行中', upcoming: '未开始', ended: '已结束' }
const statusColors = { active: 'green', upcoming: 'orange', ended: 'default' }
const typeLabels = { basic: '基础训练', special: '专项训练', promotion: '晋升培训', online: '线上培训' }

const filterStatus = ref('all')
const filterType = ref('all')
const filterPublish = ref('all')
const searchText = ref('')
const trainingList = ref([])
const instructorList = ref([])
const admissionExamOptions = ref([])
const showCreateModal = ref(false)
const editingTraining = ref(null)
const studentImportFile = ref(null)
const studentImportFileName = ref('')
const trainingFormDates = ref([null, null])
const enrollmentWindow = ref([])

const trainingForm = reactive({
  name: '',
  type: 'basic',
  capacity: 30,
  classCode: '',
  startDate: '',
  endDate: '',
  location: '',
  instructorId: null,
  instructorName: '',
  description: '',
  enrollmentStartAt: '',
  enrollmentEndAt: '',
  admissionExamId: undefined,
})

const stats = computed(() => [
  { label: '全部培训班', value: trainingList.value.length, color: '#003087' },
  { label: '已发布', value: trainingList.value.filter(item => item.publishStatus === 'published').length, color: '#1677ff' },
  { label: '进行中', value: trainingList.value.filter(item => item.status === 'active').length, color: '#52c41a' },
  { label: '已锁定', value: trainingList.value.filter(item => item.isLocked).length, color: '#ff4d4f' },
])

const filteredTrainings = computed(() => {
  let list = [...trainingList.value]
  if (authStore.isStudent) {
    list = list.filter(item => item.publishStatus === 'published' && (isMyTraining(item) || item.status !== 'ended'))
  }
  if (filterStatus.value !== 'all') {
    list = list.filter(item => item.status === filterStatus.value)
  }
  if (filterPublish.value !== 'all') {
    list = list.filter(item => item.publishStatus === filterPublish.value)
  }
  if (filterType.value !== 'all') {
    list = list.filter(item => item.type === filterType.value)
  }
  if (searchText.value) {
    list = list.filter(item => item.name.includes(searchText.value))
  }
  return list
})

function getTrainingStudentIds(training) {
  return training?.studentIds || []
}

function isMyTraining(training) {
  return getTrainingStudentIds(training).includes(authStore.currentUser?.id)
}

function formatWindow(start, end) {
  if (!start && !end) return '未设置'
  const startText = start ? String(start).replace('T', ' ').slice(0, 16) : '即时'
  const endText = end ? String(end).replace('T', ' ').slice(0, 16) : '长期'
  return `${startText} ~ ${endText}`
}

function handleWindowChange(_, strings) {
  trainingForm.enrollmentStartAt = strings?.[0] || ''
  trainingForm.enrollmentEndAt = strings?.[1] || ''
}

function onInstructorChange(userId) {
  const instructor = instructorList.value.find(item => item.userId === userId)
  if (instructor) {
    trainingForm.instructorName = instructor.name
  }
}

function handleStudentImportBeforeUpload(file) {
  studentImportFile.value = file
  studentImportFileName.value = file.name
  return false
}

function resetForm() {
  Object.assign(trainingForm, {
    name: '',
    type: 'basic',
    capacity: 30,
    classCode: '',
    startDate: '',
    endDate: '',
    location: '',
    instructorId: null,
    instructorName: '',
    description: '',
    enrollmentStartAt: '',
    enrollmentEndAt: '',
    admissionExamId: undefined,
  })
  trainingFormDates.value = [null, null]
  enrollmentWindow.value = []
  editingTraining.value = null
  studentImportFile.value = null
  studentImportFileName.value = ''
  showCreateModal.value = false
}

function openCreateModal() {
  resetForm()
  showCreateModal.value = true
}

function openEditModal(training) {
  editingTraining.value = training
  Object.assign(trainingForm, {
    name: training.name,
    type: training.type,
    capacity: training.capacity || 30,
    classCode: training.classCode || '',
    startDate: training.startDate || '',
    endDate: training.endDate || '',
    location: training.location || '',
    instructorId: training.instructorId || null,
    instructorName: training.instructorName || '',
    description: training.description || '',
    enrollmentStartAt: training.enrollmentStartAt || '',
    enrollmentEndAt: training.enrollmentEndAt || '',
    admissionExamId: training.admissionExamId,
  })
  trainingFormDates.value = [
    training.startDate ? dayjs(training.startDate) : null,
    training.endDate ? dayjs(training.endDate) : null,
  ]
  enrollmentWindow.value = [
    training.enrollmentStartAt || null,
    training.enrollmentEndAt || null,
  ].filter(Boolean)
  showCreateModal.value = true
}

async function fetchTrainings() {
  try {
    const result = await getTrainings({ size: -1 })
    trainingList.value = result.items || result || []
  } catch (error) {
    message.error(error.message || '加载培训班失败')
  }
}

async function fetchInstructors() {
  try {
    const result = await getUsers({ role: 'instructor', size: -1 })
    instructorList.value = (result.items || []).map(item => ({
      ...item,
      userId: item.id,
      name: item.nickname || item.username,
    }))
  } catch {
    instructorList.value = []
  }
}

async function fetchAdmissionExams() {
  try {
    const result = await getAdmissionExams({ size: 200, status: 'upcoming' })
    const activeResult = await getAdmissionExams({ size: 200, status: 'active' })
    admissionExamOptions.value = [...(result.items || []), ...(activeResult.items || [])]
  } catch {
    admissionExamOptions.value = []
  }
}

async function handleSubmitTraining() {
  if (!trainingForm.name || !trainingForm.startDate || !trainingForm.endDate || !trainingForm.location) {
    message.warning('请填写必填项')
    return
  }

  const payload = {
    name: trainingForm.name,
    type: trainingForm.type,
    capacity: trainingForm.capacity,
    classCode: trainingForm.classCode || undefined,
    startDate: trainingForm.startDate,
    endDate: trainingForm.endDate,
    location: trainingForm.location,
    instructorId: trainingForm.instructorId || undefined,
    description: trainingForm.description || undefined,
    enrollmentStartAt: trainingForm.enrollmentStartAt || undefined,
    enrollmentEndAt: trainingForm.enrollmentEndAt || undefined,
    admissionExamId: trainingForm.admissionExamId || undefined,
  }

  try {
    if (editingTraining.value) {
      await updateTraining(editingTraining.value.id, payload)
      message.success('培训班已更新')
    } else {
      const created = await createTraining(payload)
      if (studentImportFile.value) {
        const importResult = await importTrainingStudents(created.id, studentImportFile.value)
        message.success(`培训班创建成功，导入学员 ${importResult.enrollmentAdded || 0} 人`)
      } else {
        message.success('培训班创建成功')
      }
    }
    resetForm()
    fetchTrainings()
  } catch (error) {
    message.error(error.message || '操作失败')
  }
}

function handleDelete(training) {
  Modal.confirm({
    title: '确认删除培训班？',
    content: training.name,
    okType: 'danger',
    onOk: async () => {
      try {
        await deleteTraining(training.id)
        message.success('已删除')
        fetchTrainings()
      } catch (error) {
        message.error(error.message || '删除失败')
      }
    },
  })
}

async function handlePublish(training) {
  try {
    await publishTraining(training.id)
    message.success('培训班已发布')
    fetchTrainings()
  } catch (error) {
    message.error(error.message || '发布失败')
  }
}

async function handleLock(training) {
  try {
    await lockTraining(training.id)
    message.success('名单已锁定')
    fetchTrainings()
  } catch (error) {
    message.error(error.message || '锁定失败')
  }
}

async function handleStart(training) {
  try {
    await startTraining(training.id)
    message.success('已开班')
    fetchTrainings()
  } catch (error) {
    message.error(error.message || '开班失败')
  }
}

async function handleEnd(training) {
  try {
    await endTraining(training.id)
    message.success('已结班')
    fetchTrainings()
  } catch (error) {
    message.error(error.message || '结班失败')
  }
}

function goDetail(training) {
  router.push({ name: 'TrainingDetail', params: { id: training.id } })
}

function goEnroll(training) {
  router.push({ name: 'Enroll', params: { id: training.id } })
}

function goEnrollManage(training) {
  router.push({ name: 'EnrollManage', params: { id: training.id } })
}

function goCheckin(training) {
  router.push({ name: 'Checkin', params: { id: training.id } })
}

function goCheckout(training) {
  router.push({ name: 'Checkout', params: { id: training.id } })
}

function goHistory(training) {
  router.push({ name: 'TrainingHistory', params: { id: training.id } })
}

onMounted(() => {
  fetchTrainings()
  fetchInstructors()
  fetchAdmissionExams()
})
</script>

<style scoped>
.training-list-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 16px; }
.page-header h2 { margin: 0; font-size: 22px; color: #001234; }
.page-sub { margin: 6px 0 0; color: #8c8c8c; font-size: 13px; }
.stat-card { text-align: center; }
.stat-value { font-size: 30px; font-weight: 700; }
.stat-label { font-size: 12px; color: #8c8c8c; }
.training-cards { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.training-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 10px; padding: 18px; box-shadow: 0 4px 20px rgba(0, 32, 96, 0.06); }
.card-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 10px; }
.card-status { display: flex; flex-wrap: wrap; gap: 4px; }
.card-title { font-size: 16px; font-weight: 700; color: #1f1f1f; margin-bottom: 8px; }
.card-desc { font-size: 13px; color: #666; min-height: 40px; }
.card-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 14px; }
.grid-item { font-size: 12px; color: #555; background: #f7f9fc; border-radius: 6px; padding: 8px 10px; display: flex; align-items: center; gap: 6px; }
.extra-info { display: flex; flex-direction: column; gap: 6px; font-size: 12px; color: #777; margin-top: 12px; }
.card-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.import-tip { margin-top: 8px; color: #666; font-size: 12px; }

@media (max-width: 1200px) {
  .training-cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 768px) {
  .training-cards { grid-template-columns: 1fr; }
  .card-grid { grid-template-columns: 1fr; }
  .page-header { flex-direction: column; }
}
</style>
