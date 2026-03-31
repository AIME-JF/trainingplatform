<template>
  <div class="exam-manage-page">
    <div class="page-header">
      <div>
        <h2>{{ activeKind === 'admission' ? '准入考试管理' : '培训班考试管理' }}</h2>
        <p class="page-sub">考试只关联已发布试卷，题目配置统一收口到试卷管理</p>
      </div>
      <permissions-tooltip
        :allowed="canManageExam"
        tips="需要 CREATE_EXAM 权限"
        v-slot="{ disabled }"
      >
        <a-button type="primary" :disabled="disabled" @click="openCreateDrawer">
          <template #icon><PlusOutlined /></template>{{ activeKind === 'admission' ? '发布准入考试' : '发布培训班考试' }}
        </a-button>
      </permissions-tooltip>
    </div>

    <a-card :bordered="false" style="margin-bottom:16px">
      <a-tabs v-model:activeKey="activeKind" @change="handleKindChange">
        <a-tab-pane key="admission" tab="准入考试" />
        <a-tab-pane key="training" tab="培训班考试" />
      </a-tabs>
    </a-card>

    <a-card :bordered="false" style="margin-bottom:16px">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-input-search v-model:value="searchText" placeholder="搜索考试名称..." allow-clear @search="loadExams" />
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filterStatus" style="width:100%" @change="loadExams">
            <a-select-option value="all">全部状态</a-select-option>
            <a-select-option value="upcoming">即将开始</a-select-option>
            <a-select-option value="active">进行中</a-select-option>
            <a-select-option value="ended">已结束</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4" v-if="activeKind === 'training'">
          <a-select v-model:value="filterPurpose" style="width:100%" @change="loadExams">
            <a-select-option value="all">全部用途</a-select-option>
            <a-select-option value="class_assessment">班内考核</a-select-option>
            <a-select-option value="final_assessment">结业考核</a-select-option>
            <a-select-option value="quiz">随堂测验</a-select-option>
            <a-select-option value="makeup">补考</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </a-card>

    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data-source="examList"
        row-key="id"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'purpose'">
            {{ purposeLabels[record.purpose] || record.purpose || '-' }}
          </template>
          <template v-else-if="column.key === 'paperTitle'">
            <div class="paper-col">
              <div>{{ record.paperTitle || '-' }}</div>
              <div class="paper-meta">{{ paperStatusLabels[record.paperStatus] || '' }}</div>
            </div>
          </template>
          <template v-else-if="column.key === 'trainingName'">
            {{ record.trainingName || (record.linkedTrainingCount ? `已关联 ${record.linkedTrainingCount} 个培训班` : '-') }}
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="statusColors[record.status]">{{ statusLabels[record.status] }}</a-tag>
          </template>
          <template v-else-if="column.key === 'time'">
            <div class="time-col">
              <div>{{ formatDateTime(record.startTime) }}</div>
              <div>{{ formatDateTime(record.endTime) }}</div>
            </div>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <permissions-tooltip
                :allowed="canManageExam"
                tips="需要 CREATE_EXAM 权限"
                v-slot="{ disabled }"
              >
                <a-button type="link" size="small" :disabled="disabled" @click="openEditDrawer(record)">编辑</a-button>
              </permissions-tooltip>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-drawer
      v-model:open="drawerVisible"
      :title="drawerTitle"
      width="760"
      @close="resetForm"
    >
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="24">
            <a-form-item :label="editingKind === 'admission' ? '准入考试名称' : '场次名称'" required>
              <a-input v-model:value="form.title" />
            </a-form-item>
          </a-col>
          <a-col :span="18">
            <a-form-item label="关联试卷" required>
              <a-select
                v-model:value="form.paperId"
                placeholder="请选择已发布试卷"
                :disabled="isEdit"
                show-search
                option-filter-prop="label"
                @change="handlePaperChange"
              >
                <a-select-option
                  v-for="paper in availablePaperOptions"
                  :key="paper.id"
                  :value="paper.id"
                  :label="paper.title"
                >
                  {{ paper.title }}（{{ paper.questionCount || 0 }}题 / {{ paper.totalScore || 0 }}分）
                </a-select-option>
              </a-select>
              <div class="paper-action-row">
                <span class="paper-action-tip">考试只能选择已发布试卷；考试创建后不能再更换试卷</span>
                <a-button type="link" @click="goToPaperManage">去试卷管理创建试卷</a-button>
              </div>
            </a-form-item>
          </a-col>
          <a-col :span="6" v-if="editingKind === 'training'">
            <a-form-item label="用途">
              <a-select v-model:value="form.purpose">
                <a-select-option value="class_assessment">班内考核</a-select-option>
                <a-select-option value="final_assessment">结业考核</a-select-option>
                <a-select-option value="quiz">随堂测验</a-select-option>
                <a-select-option value="makeup">补考</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12" v-if="editingKind === 'training'">
            <a-form-item label="关联培训班">
              <a-select v-model:value="form.trainingId" placeholder="培训班内考试必须关联培训班">
                <a-select-option v-for="training in trainingOptions" :key="training.id" :value="training.id">
                  {{ training.name }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="展示类型">
              <a-select v-model:value="form.type">
                <a-select-option value="formal">正式考核</a-select-option>
                <a-select-option value="quiz">测验</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="状态">
              <a-select v-model:value="form.status">
                <a-select-option value="upcoming">即将开始</a-select-option>
                <a-select-option value="active">进行中</a-select-option>
                <a-select-option value="ended">已结束</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12" v-if="editingKind === 'admission'">
            <a-form-item label="适用范围">
              <AdmissionScopeSelector
                v-model:scope-type="form.scopeType"
                v-model:scope-target-ids="form.scopeTargetIds"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="考试时间">
              <a-range-picker
                v-model:value="dateRange"
                show-time
                format="YYYY-MM-DD HH:mm:ss"
                value-format="YYYY-MM-DD HH:mm:ss"
                style="width:100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="考试时长">
              <a-input-number
                v-model:value="form.duration"
                :min="10"
                :max="EXAM_DURATION_LIMIT"
                style="width:100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="及格分">
              <div class="passing-score-field">
                <a-input-number
                  v-model:value="form.passingScore"
                  :min="1"
                  style="width:100%"
                />
                <span class="passing-score-total">
                  满分 {{ currentPaperTotalScore > 0 ? currentPaperTotalScore : '--' }} 分
                </span>
              </div>
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="最大次数">
              <a-input-number v-model:value="form.maxAttempts" :min="1" :max="10" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="6" v-if="editingKind === 'training'">
            <a-form-item label="允许补考">
              <a-switch v-model:checked="form.allowMakeup" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="考试说明">
              <a-textarea v-model:value="form.description" :rows="3" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="试卷预览">
              <div class="paper-preview-card">
                <template v-if="selectedPaperDetail">
                  <div class="preview-head">
                    <div>
                      <div class="preview-title">{{ selectedPaperDetail.title }}</div>
                      <div class="preview-sub">
                        {{ paperStatusLabels[selectedPaperDetail.status] || '' }} · {{ selectedPaperDetail.questionCount || 0 }} 题 · {{ selectedPaperDetail.totalScore || 0 }} 分
                      </div>
                    </div>
                    <div class="preview-meta">
                      <span>时长 {{ selectedPaperDetail.duration || 60 }} 分钟</span>
                      <span>及格 {{ selectedPaperDetail.passingScore || 60 }} 分</span>
                    </div>
                  </div>
                  <div v-if="selectedPaperDetail.questions?.length" class="preview-list">
                    <div class="preview-item" v-for="(item, index) in selectedPaperDetail.questions" :key="item.id">
                      <span>{{ index + 1 }}.</span>
                      <span>[{{ questionTypeLabels[item.type] || item.type }}]</span>
                      <span class="preview-content">{{ item.content }}</span>
                      <span>{{ item.score || 0 }}分</span>
                    </div>
                  </div>
                  <a-empty v-else description="试卷暂无题目快照" />
                </template>
                <a-empty v-else description="请选择试卷" />
              </div>
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
      <template #footer>
        <a-space style="float:right">
          <a-button @click="resetForm">取消</a-button>
          <permissions-tooltip
            :allowed="canManageExam"
            tips="需要 CREATE_EXAM 权限"
            v-slot="{ disabled }"
          >
            <a-button type="primary" :loading="submitting" :disabled="disabled" @click="handleSave">保存</a-button>
          </permissions-tooltip>
        </a-space>
      </template>
    </a-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  createAdmissionExam,
  createExam,
  getAdmissionExamDetail,
  getAdmissionExams,
  getExamDetail,
  getExamPaperDetail,
  getExamPapers,
  getExams,
  updateAdmissionExam,
  updateExam,
} from '@/api/exam'
import { getTrainings } from '@/api/training'
import AdmissionScopeSelector from './components/AdmissionScopeSelector.vue'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const statusLabels = { upcoming: '即将开始', active: '进行中', ended: '已结束' }
const statusColors = { upcoming: 'orange', active: 'green', ended: 'default' }
const paperStatusLabels = { draft: '草稿', published: '已发布', archived: '已归档' }
const purposeLabels = {
  class_assessment: '班内考核',
  final_assessment: '结业考核',
  quiz: '随堂测验',
  makeup: '补考',
}
const questionTypeLabels = { single: '单选', multi: '多选', judge: '判断' }
const EXAM_DURATION_LIMIT = 300
const DEFAULT_EXAM_DURATION = 60
const DEFAULT_PASSING_RATIO = 0.6

const searchText = ref('')
const filterStatus = ref('all')
const filterPurpose = ref('all')
const activeKind = ref('admission')
const loading = ref(false)
const submitting = ref(false)
const examList = ref([])
const trainingOptions = ref([])
const paperOptions = ref([])
const selectedPaperDetail = ref(null)
const drawerVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const editingKind = ref('admission')
const dateRange = ref(null)
const handledQuickCreateKey = ref('')

const pagination = reactive({ current: 1, pageSize: 10, total: 0 })
const columns = [
  { title: '场次名称', dataIndex: 'title', key: 'title' },
  { title: '试卷', key: 'paperTitle', width: 220 },
  { title: '用途', key: 'purpose', width: 100 },
  { title: '培训班', dataIndex: 'trainingName', key: 'trainingName', width: 180 },
  { title: '状态', key: 'status', width: 100 },
  { title: '题目数', dataIndex: 'questionCount', key: 'questionCount', width: 80 },
  { title: '时间', key: 'time', width: 180 },
  { title: '操作', key: 'action', width: 100 },
]

const form = reactive({
  title: '',
  paperId: undefined,
  description: '',
  purpose: 'class_assessment',
  trainingId: undefined,
  type: 'formal',
  status: 'upcoming',
  scopeType: 'all',
  scopeTargetIds: [],
  duration: 60,
  passingScore: 60,
  maxAttempts: 1,
  allowMakeup: false,
})

const drawerTitle = computed(() => {
  if (isEdit.value) {
    return editingKind.value === 'admission' ? '编辑准入考试' : '编辑培训班考试'
  }
  return activeKind.value === 'admission' ? '发布准入考试' : '发布培训班考试'
})

const routeKind = computed(() => {
  const raw = Array.isArray(route.query.kind) ? route.query.kind[0] : route.query.kind
  return raw === 'training' || raw === 'admission' ? raw : null
})

const routeTrainingId = computed(() => {
  const raw = Array.isArray(route.query.trainingId) ? route.query.trainingId[0] : route.query.trainingId
  const parsed = Number(raw)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : undefined
})

const availablePaperOptions = computed(() => {
  if (isEdit.value) {
    return paperOptions.value
  }
  return paperOptions.value.filter(item => item.status === 'published')
})
const canManageExam = computed(() => authStore.hasPermission('CREATE_EXAM'))
const currentPaperTotalScore = computed(() => {
  const totalScore = Number(selectedPaperDetail.value?.totalScore || 0)
  return Number.isFinite(totalScore) ? totalScore : 0
})
const passingScoreSuggestion = computed(() => resolvePassingScoreSuggestion(selectedPaperDetail.value))

function resetForm() {
  Object.assign(form, {
    title: '',
    paperId: undefined,
    description: '',
    purpose: 'class_assessment',
    trainingId: undefined,
    type: 'formal',
    status: 'upcoming',
    scopeType: 'all',
    scopeTargetIds: [],
    duration: 60,
    passingScore: 60,
    maxAttempts: 1,
    allowMakeup: false,
  })
  selectedPaperDetail.value = null
  drawerVisible.value = false
  isEdit.value = false
  editingId.value = null
  editingKind.value = activeKind.value
  dateRange.value = null
}

function resolvePassingScoreSuggestion(detail) {
  const totalScore = Number(detail?.totalScore || 0)
  if (!Number.isFinite(totalScore) || totalScore <= 0) {
    return 0
  }
  const configuredPassingScore = Number(detail?.passingScore)
  if (
    Number.isFinite(configuredPassingScore) &&
    configuredPassingScore > 0 &&
    configuredPassingScore <= totalScore
  ) {
    return configuredPassingScore
  }
  return Math.max(1, Math.ceil(totalScore * DEFAULT_PASSING_RATIO))
}

function resolveDefaultDuration(value) {
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue) || numericValue <= 0) {
    return DEFAULT_EXAM_DURATION
  }
  return Math.min(EXAM_DURATION_LIMIT, Math.max(10, Math.floor(numericValue)))
}

function applyRouteKindContext() {
  if (routeKind.value && activeKind.value !== routeKind.value) {
    activeKind.value = routeKind.value
  }
}

function applyRouteTrainingContext() {
  if (activeKind.value === 'training' && routeTrainingId.value) {
    form.trainingId = routeTrainingId.value
  }
}

function syncQuickCreateFromRoute() {
  const raw = Array.isArray(route.query.quickCreate) ? route.query.quickCreate[0] : route.query.quickCreate
  if (String(raw || '') !== '1') {
    handledQuickCreateKey.value = ''
    return
  }

  const routeKey = `${routeKind.value || activeKind.value}:${routeTrainingId.value || ''}:${raw}`
  if (handledQuickCreateKey.value === routeKey) {
    return
  }

  openCreateDrawer()
  handledQuickCreateKey.value = routeKey
}

async function loadExams() {
  loading.value = true
  try {
    const loader = activeKind.value === 'admission' ? getAdmissionExams : getExams
    const result = await loader({
      page: pagination.current,
      size: pagination.pageSize,
      search: searchText.value || undefined,
      status: filterStatus.value !== 'all' ? filterStatus.value : undefined,
      trainingId: activeKind.value === 'training' ? routeTrainingId.value : undefined,
      purpose: activeKind.value === 'training' && filterPurpose.value !== 'all' ? filterPurpose.value : undefined,
    })
    examList.value = result.items || []
    pagination.total = result.total || 0
  } catch (error) {
    message.error(error.message || '加载考试列表失败')
  } finally {
    loading.value = false
  }
}

async function loadTrainingOptions() {
  try {
    const result = await getTrainings({ size: -1 })
    trainingOptions.value = result.items || []
  } catch {
    trainingOptions.value = []
  }
}

async function loadPaperOptions() {
  try {
    const result = await getExamPapers({ size: -1 })
    paperOptions.value = result.items || []
  } catch {
    paperOptions.value = []
  }
}

function handleTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadExams()
}

function openCreateDrawer() {
  if (!canManageExam.value) return
  resetForm()
  editingKind.value = activeKind.value
  applyRouteTrainingContext()
  drawerVisible.value = true
}

async function setPaperPreview(paperId, applyDefaults = false) {
  if (!paperId) {
    selectedPaperDetail.value = null
    return
  }
  try {
    const detail = await getExamPaperDetail(paperId)
    selectedPaperDetail.value = detail
    if (applyDefaults) {
      form.type = detail.type || 'formal'
      form.duration = resolveDefaultDuration(detail.duration)
      form.passingScore = passingScoreSuggestion.value || form.passingScore
    }
  } catch (error) {
    selectedPaperDetail.value = null
    message.error(error.message || '加载试卷详情失败')
  }
}

function handlePaperChange(value) {
  setPaperPreview(value, !isEdit.value)
}

async function openEditDrawer(record) {
  if (!canManageExam.value) return
  resetForm()
  isEdit.value = true
  editingId.value = record.id
  editingKind.value = record.kind || activeKind.value
  try {
    const detail = editingKind.value === 'admission'
      ? await getAdmissionExamDetail(record.id)
      : await getExamDetail(record.id)
    form.title = detail.title
    form.paperId = detail.paperId
    form.description = detail.description || ''
    form.purpose = detail.purpose || 'class_assessment'
    form.trainingId = detail.trainingId
    form.type = detail.type || 'formal'
    form.status = detail.status || 'upcoming'
    form.scopeType = editingKind.value === 'admission' ? (detail.scopeType || 'all') : 'all'
    form.scopeTargetIds = editingKind.value === 'admission' ? [...(detail.scopeTargetIds || [])] : []
    form.duration = detail.duration || 60
    form.passingScore = detail.passingScore || 60
    form.maxAttempts = detail.maxAttempts || 1
    form.allowMakeup = !!detail.allowMakeup
    dateRange.value = detail.startTime && detail.endTime ? [detail.startTime, detail.endTime] : null
    selectedPaperDetail.value = {
      id: detail.paperId,
      title: detail.paperTitle || '未命名试卷',
      status: detail.paperStatus,
      duration: detail.duration,
      totalScore: detail.totalScore,
      passingScore: detail.passingScore,
      questionCount: detail.questionCount,
      questions: detail.questions || [],
    }
    drawerVisible.value = true
  } catch (error) {
    message.error(error.message || '加载考试详情失败')
  }
}

function goToPaperManage() {
  router.push({ path: '/paper/repository', query: { quickCreate: '1' } })
}

async function handleSave() {
  if (!canManageExam.value) return
  if (!form.title) {
    message.warning('请输入场次名称')
    return
  }
  if (!form.paperId) {
    message.warning('请选择试卷')
    return
  }
  if (editingKind.value === 'training' && !form.trainingId) {
    message.warning('请选择关联培训班')
    return
  }
  if (editingKind.value === 'admission' && form.scopeType !== 'all' && !form.scopeTargetIds.length) {
    message.warning('请选择适用范围')
    return
  }
  const duration = Number(form.duration)
  const passingScore = Number(form.passingScore)
  if (!Number.isFinite(duration) || duration < 10) {
    message.warning('考试时长不能少于10分钟')
    return
  }
  if (!Number.isFinite(passingScore) || passingScore < 1) {
    message.warning('及格分不能小于1分')
    return
  }
  if (dateRange.value?.[0] && dateRange.value?.[1]) {
    const startTime = dayjs(dateRange.value[0])
    const endTime = dayjs(dateRange.value[1])
    if (!startTime.isValid() || !endTime.isValid() || !endTime.isAfter(startTime)) {
      message.warning('考试结束时间必须晚于开始时间')
      return
    }
  }
  if (currentPaperTotalScore.value <= 0) {
    message.warning('当前试卷总分无效，请先检查试卷配置')
    return
  }
  if (passingScore > currentPaperTotalScore.value) {
    message.warning(`及格分不能超过试卷满分（${currentPaperTotalScore.value}分）`)
    return
  }

  const payload = {
    title: form.title,
    paperId: form.paperId,
    description: form.description || undefined,
    type: form.type,
    status: form.status,
    duration,
    passingScore,
    startTime: dateRange.value?.[0],
    endTime: dateRange.value?.[1],
  }
  if (editingKind.value === 'training') {
    payload.purpose = form.purpose
    payload.trainingId = form.trainingId
    payload.maxAttempts = form.maxAttempts
    payload.allowMakeup = form.allowMakeup
  } else {
    payload.scopeType = form.scopeType
    payload.scopeTargetIds = form.scopeTargetIds
    payload.maxAttempts = form.maxAttempts
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      if (editingKind.value === 'admission') {
        await updateAdmissionExam(editingId.value, payload)
        message.success('准入考试已更新')
      } else {
        await updateExam(editingId.value, payload)
        message.success('考试场次已更新')
      }
    } else {
      if (activeKind.value === 'admission') {
        await createAdmissionExam(payload)
        message.success('准入考试已发布')
      } else {
        await createExam(payload)
        message.success('考试场次已发布')
      }
    }
    resetForm()
    loadExams()
  } catch (error) {
    message.error(error.message || '保存失败')
  } finally {
    submitting.value = false
  }
}

function formatDateTime(value) {
  if (!value) return '未设置'
  return String(value).replace('T', ' ').slice(0, 16)
}

function handleKindChange() {
  pagination.current = 1
  filterPurpose.value = 'all'
  resetForm()
  loadExams()
}

async function initializeFromRoute() {
  applyRouteKindContext()
  await Promise.all([loadExams(), loadTrainingOptions(), loadPaperOptions()])
  syncQuickCreateFromRoute()
}

onMounted(() => {
  initializeFromRoute()
})

watch(() => route.fullPath, () => {
  pagination.current = 1
  filterPurpose.value = 'all'
  initializeFromRoute()
})
</script>

<style scoped>
.exam-manage-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 16px; }
.page-header h2 { margin: 0; color: #001234; }
.page-sub { margin: 6px 0 0; font-size: 13px; color: #8c8c8c; }
.time-col { font-size: 12px; color: #666; }
.paper-col { display: flex; flex-direction: column; gap: 2px; }
.paper-meta { font-size: 12px; color: #8c8c8c; }
.paper-action-row { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; }
.paper-action-tip { font-size: 12px; color: #8c8c8c; }
.passing-score-field { display: flex; align-items: center; gap: 10px; }
.passing-score-total { flex-shrink: 0; font-size: 12px; color: #8c8c8c; white-space: nowrap; }
.paper-preview-card { border: 1px solid #e8e8e8; border-radius: 8px; padding: 12px; background: #fafafa; }
.preview-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 12px; }
.preview-title { font-size: 15px; font-weight: 600; color: #001234; }
.preview-sub { margin-top: 4px; font-size: 12px; color: #8c8c8c; }
.preview-meta { display: flex; gap: 16px; font-size: 12px; color: #666; }
.preview-list { display: flex; flex-direction: column; gap: 8px; max-height: 320px; overflow-y: auto; }
.preview-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #fff; border: 1px solid #f0f0f0; border-radius: 6px; }
.preview-content { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
