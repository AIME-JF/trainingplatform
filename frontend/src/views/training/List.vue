<template>
  <div class="training-list-page">
    <div class="page-header">
      <div>
        <h2>{{ authStore.isStudent ? '我的培训' : '培训班管理' }}</h2>
        <p class="page-sub">支持发布挂网、准入考试绑定、名单锁定和训历归档</p>
      </div>
      <permissions-tooltip
        v-if="!authStore.isStudent"
        :allowed="canCreateTraining"
        tips="需要 CREATE_TRAINING 权限"
        v-slot="{ disabled }"
      >
        <a-button type="primary" :disabled="disabled" @click="openCreateModal">
          <template #icon><PlusOutlined /></template>新建培训班
        </a-button>
      </permissions-tooltip>
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
            <a-tag :color="workflowStepColors[getWorkflowStepKey(training)]">
              {{ workflowStepLabels[getWorkflowStepKey(training)] }}
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
          <div>报名方式：{{ training.enrollmentRequiresApproval === false ? '直接通过' : '申请审核' }}</div>
          <div>准入考试：{{ training.admissionExamTitle || '无' }}</div>
          <div>培训基地：{{ training.trainingBaseName || '手动输入地点' }}</div>
          <div>数据域：{{ [training.departmentName, training.policeTypeName].filter(Boolean).join(' / ') || '未设置' }}</div>
        </div>

        <a-progress :percent="Number.isFinite(training.progressPercent) ? training.progressPercent : 0" size="small" style="margin:12px 0 16px" />

        <div class="card-actions">
          <a-button
            size="small"
            type="primary"
            :disabled="authStore.isStudent && !training.canEnterTraining"
            @click="goDetail(training)"
          >
            进入培训班
          </a-button>
          <a-button size="small" @click="goHistory(training)">训历</a-button>

          <template v-if="authStore.isStudent && !isMyTraining(training)">
            <a-button
              v-if="training.currentEnrollmentStatus === 'pending'"
              size="small"
              disabled
            >
              待审核
            </a-button>
            <a-button
              v-else-if="training.currentEnrollmentStatus === 'rejected'"
              size="small"
              disabled
            >
              审核未通过
            </a-button>
            <a-button
              v-else-if="training.status !== 'ended' && training.publishStatus === 'published'"
              size="small"
              :disabled="training.isLocked"
              @click="goEnroll(training)"
            >
              {{ training.isLocked ? '名单已锁定' : (training.enrollmentRequiresApproval === false ? '加入培训班' : '报名申请') }}
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
          <a-col :span="12">
            <a-form-item label="警种">
              <a-select v-model:value="trainingForm.policeTypeId" allow-clear placeholder="可选，仅用于数据域管理">
                <a-select-option v-for="item in policeTypeOptions" :key="item.id" :value="item.id">
                  {{ item.name }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="部门">
              <a-select v-model:value="trainingForm.departmentId" allow-clear placeholder="可选，可被培训基地自动带出">
                <a-select-option v-for="item in departmentOptions" :key="item.id" :value="item.id">
                  {{ item.name }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="地点来源">
              <a-space>
                <a-checkbox :checked="locationSourceMode === 'base'" @change="() => setLocationSourceMode('base')">
                  培训基地
                </a-checkbox>
                <a-checkbox :checked="locationSourceMode === 'manual'" @change="() => setLocationSourceMode('manual')">
                  手动输入
                </a-checkbox>
              </a-space>
            </a-form-item>
          </a-col>
          <a-col :span="24" v-if="locationSourceMode === 'base'">
            <a-form-item label="培训基地" required>
              <a-select
                v-model:value="trainingForm.trainingBaseId"
                allow-clear
                show-search
                option-filter-prop="label"
                placeholder="选择培训基地"
                @change="onTrainingBaseChange"
              >
                <a-select-option
                  v-for="item in trainingBaseOptions"
                  :key="item.id"
                  :value="item.id"
                  :label="`${item.name} ${item.location}`"
                >
                  {{ item.name }} / {{ item.location }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item :label="locationSourceMode === 'base' ? '培训地点（自动带出）' : '培训地点'" required>
              <a-input v-model:value="trainingForm.location" :disabled="locationSourceMode === 'base'" />
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
          <a-col :span="12">
            <a-form-item label="报名方式">
              <a-radio-group v-model:value="trainingForm.enrollmentRequiresApproval">
                <a-radio :value="true">申请审核</a-radio>
                <a-radio :value="false">直接通过</a-radio>
              </a-radio-group>
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
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'
import {
  createTraining,
  deleteTraining,
  endTraining,
  getTrainingBases,
  getTrainings,
  importTrainingStudents,
  lockTraining,
  publishTraining,
  startTraining,
  updateTraining,
} from '@/api/training'
import { getDepartmentList } from '@/api/department'
import { getUsers, getPoliceTypes } from '@/api/user'
import { getAdmissionExams } from '@/api/exam'

const router = useRouter()
const authStore = useAuthStore()

const statusLabels = { active: '进行中', upcoming: '未开始', ended: '已结束' }
const statusColors = { active: 'green', upcoming: 'orange', ended: 'default' }
const workflowStepLabels = {
  draft: '草稿阶段',
  published: '发布招生',
  locked: '名单锁定',
  running: '开班进行中',
  completed: '结班归档',
}
const workflowStepColors = {
  draft: 'default',
  published: 'blue',
  locked: 'orange',
  running: 'processing',
  completed: 'green',
}
const typeLabels = { basic: '基础训练', special: '专项训练', promotion: '晋升培训', online: '线上培训' }

const filterStatus = ref('all')
const filterType = ref('all')
const filterPublish = ref('all')
const searchText = ref('')
const trainingList = ref([])
const instructorList = ref([])
const instructorOptionsLoaded = ref(false)
const instructorOptionsLoading = ref(false)
const admissionExamOptions = ref([])
const trainingBaseOptions = ref([])
const departmentOptions = ref([])
const policeTypeOptions = ref([])
const showCreateModal = ref(false)
const editingTraining = ref(null)
const studentImportFile = ref(null)
const studentImportFileName = ref('')
const trainingFormDates = ref([null, null])
const enrollmentWindow = ref([])
const locationSourceMode = ref('manual')
const canCreateTraining = computed(() => authStore.hasPermission('CREATE_TRAINING'))

const trainingForm = reactive({
  name: '',
  type: 'basic',
  capacity: 30,
  classCode: '',
  startDate: '',
  endDate: '',
  location: '',
  departmentId: undefined,
  policeTypeId: undefined,
  trainingBaseId: undefined,
  instructorId: null,
  instructorName: '',
  description: '',
  enrollmentStartAt: '',
  enrollmentEndAt: '',
  enrollmentRequiresApproval: true,
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
  return !!training.canEnterTraining || getTrainingStudentIds(training).includes(authStore.currentUser?.id)
}

function getWorkflowStepKey(training) {
  if (training?.currentStepKey && workflowStepLabels[training.currentStepKey]) {
    return training.currentStepKey
  }
  if (training?.status === 'ended') {
    return 'completed'
  }
  if (training?.status === 'active') {
    return 'running'
  }
  if (training?.isLocked) {
    return 'locked'
  }
  if (training?.publishStatus === 'published') {
    return 'published'
  }
  return 'draft'
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

function setLocationSourceMode(mode) {
  locationSourceMode.value = mode
  if (mode === 'manual') {
    trainingForm.trainingBaseId = undefined
    return
  }
  if (trainingForm.trainingBaseId) {
    onTrainingBaseChange(trainingForm.trainingBaseId)
  } else {
    trainingForm.location = ''
  }
}

function onTrainingBaseChange(baseId) {
  const base = trainingBaseOptions.value.find(item => item.id === baseId)
  if (!base) {
    trainingForm.location = ''
    return
  }
  trainingForm.location = base.location || ''
  trainingForm.departmentId = base.departmentId || undefined
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
    departmentId: undefined,
    policeTypeId: undefined,
    trainingBaseId: undefined,
    instructorId: null,
    instructorName: '',
    description: '',
    enrollmentStartAt: '',
    enrollmentEndAt: '',
    enrollmentRequiresApproval: true,
    admissionExamId: undefined,
  })
  locationSourceMode.value = 'manual'
  trainingFormDates.value = [null, null]
  enrollmentWindow.value = []
  editingTraining.value = null
  studentImportFile.value = null
  studentImportFileName.value = ''
  showCreateModal.value = false
}

function openCreateModal() {
  if (!canCreateTraining.value) return
  resetForm()
  showCreateModal.value = true
  ensureInstructorOptionsLoaded(true)
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
    departmentId: training.departmentId,
    policeTypeId: training.policeTypeId,
    trainingBaseId: training.trainingBaseId,
    instructorId: training.instructorId || null,
    instructorName: training.instructorName || '',
    description: training.description || '',
    enrollmentStartAt: training.enrollmentStartAt || '',
    enrollmentEndAt: training.enrollmentEndAt || '',
    enrollmentRequiresApproval: training.enrollmentRequiresApproval !== false,
    admissionExamId: training.admissionExamId,
  })
  locationSourceMode.value = training.trainingBaseId ? 'base' : 'manual'
  trainingFormDates.value = [
    training.startDate ? dayjs(training.startDate) : null,
    training.endDate ? dayjs(training.endDate) : null,
  ]
  enrollmentWindow.value = [
    training.enrollmentStartAt || null,
    training.enrollmentEndAt || null,
  ].filter(Boolean)
  showCreateModal.value = true
  ensureInstructorOptionsLoaded(true)
}

async function fetchTrainings() {
  try {
    const result = await getTrainings({ size: -1 })
    trainingList.value = result.items || result || []
  } catch (error) {
    message.error(error.message || '加载培训班失败')
  }
}

async function ensureInstructorOptionsLoaded(force = false) {
  if (instructorOptionsLoading.value) return
  if (instructorOptionsLoaded.value && !force) return

  instructorOptionsLoading.value = true
  try {
    const result = await getUsers({ role: 'instructor', size: -1 })
    instructorList.value = (result.items || []).map(item => ({
      ...item,
      userId: item.id,
      name: item.nickname || item.username,
    }))
    instructorOptionsLoaded.value = true
  } catch (error) {
    instructorList.value = []
    instructorOptionsLoaded.value = false
    if (force) {
      message.warning(error?.message || '暂无权限加载教官候选列表')
    }
  } finally {
    instructorOptionsLoading.value = false
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

async function fetchDepartments() {
  try {
    const result = await getDepartmentList({ size: -1 })
    departmentOptions.value = result.items || []
  } catch {
    departmentOptions.value = []
  }
}

async function fetchPoliceTypeOptions() {
  try {
    const result = await getPoliceTypes()
    policeTypeOptions.value = result.items || []
  } catch {
    policeTypeOptions.value = []
  }
}

async function fetchTrainingBaseOptions() {
  try {
    const result = await getTrainingBases({ size: -1 })
    trainingBaseOptions.value = result.items || []
  } catch {
    trainingBaseOptions.value = []
  }
}

async function handleSubmitTraining() {
  if (!canCreateTraining.value) return
  const hasLocation = locationSourceMode.value === 'base'
    ? Boolean(trainingForm.trainingBaseId && trainingForm.location)
    : Boolean(trainingForm.location)
  if (!trainingForm.name || !trainingForm.startDate || !trainingForm.endDate || !hasLocation) {
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
    departmentId: trainingForm.departmentId || undefined,
    policeTypeId: trainingForm.policeTypeId || undefined,
    trainingBaseId: locationSourceMode.value === 'base' ? (trainingForm.trainingBaseId || undefined) : undefined,
    instructorId: trainingForm.instructorId || undefined,
    description: trainingForm.description || undefined,
    enrollmentStartAt: trainingForm.enrollmentStartAt || undefined,
    enrollmentEndAt: trainingForm.enrollmentEndAt || undefined,
    enrollmentRequiresApproval: trainingForm.enrollmentRequiresApproval,
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
  if (authStore.isStudent && !training.canEnterTraining) {
    message.warning('当前用户尚未被录取到该培训班')
    return
  }
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
  if (!authStore.isStudent && canCreateTraining.value) {
    fetchAdmissionExams()
    fetchDepartments()
    fetchPoliceTypeOptions()
    fetchTrainingBaseOptions()
  }
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
