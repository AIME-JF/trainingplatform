<template>
  <div class="exam-manage-page">
    <div class="page-header">
      <div>
        <h2>{{ activeKind === 'admission' ? '准入考试管理' : '培训班考试管理' }}</h2>
        <p class="page-sub">统一题库生成试卷，独立发布准入考试，在培训班内发布随堂测与结课考试</p>
      </div>
      <a-button type="primary" @click="openCreateDrawer">
        <template #icon><PlusOutlined /></template>{{ activeKind === 'admission' ? '发布准入考试' : '发布培训班考试' }}
      </a-button>
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
            {{ purposeLabels[record.purpose] || record.purpose }}
          </template>
          <template v-if="column.key === 'trainingName'">
            {{ record.trainingName || (record.linkedTrainingCount ? `已关联 ${record.linkedTrainingCount} 个培训班` : '-') }}
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColors[record.status]">{{ statusLabels[record.status] }}</a-tag>
          </template>
          <template v-if="column.key === 'time'">
            <div class="time-col">
              <div>{{ formatDateTime(record.startTime) }}</div>
              <div>{{ formatDateTime(record.endTime) }}</div>
            </div>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="openEditDrawer(record)">编辑</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-drawer
      v-model:open="drawerVisible"
      :title="isEdit ? (editingKind === 'admission' ? '编辑准入考试' : '编辑培训班考试') : (activeKind === 'admission' ? '发布准入考试' : '发布培训班考试')"
      width="720"
      @close="resetForm"
    >
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="24">
            <a-form-item :label="activeKind === 'admission' ? '准入考试名称' : '场次名称'" required>
              <a-input v-model:value="form.title" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="试卷名称">
              <a-input v-model:value="form.paperTitle" placeholder="默认同场次名称" />
            </a-form-item>
          </a-col>
          <a-col :span="12" v-if="activeKind === 'training'">
            <a-form-item label="用途">
              <a-select v-model:value="form.purpose">
                <a-select-option value="class_assessment">班内考核</a-select-option>
                <a-select-option value="final_assessment">结业考核</a-select-option>
                <a-select-option value="quiz">随堂测验</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12" v-if="activeKind === 'training'">
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
          <a-col :span="12" v-if="activeKind === 'admission'">
            <a-form-item label="适用范围">
              <a-input v-model:value="form.scope" />
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
              <a-input-number v-model:value="form.duration" :min="10" :max="300" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="及格分">
              <a-input-number v-model:value="form.passingScore" :min="1" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="最大次数">
              <a-input-number v-model:value="form.maxAttempts" :min="1" :max="10" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="6" v-if="activeKind === 'training'">
            <a-form-item label="允许补考">
              <a-switch v-model:checked="form.allowMakeup" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="场次描述">
              <a-textarea v-model:value="form.description" :rows="3" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="试卷题目" required>
              <div class="selected-questions">
                <div class="selected-header">
                  <span>已选 {{ form.questionIds.length }} 题，总分 {{ dynamicTotalScore }} 分</span>
                  <a-button type="primary" size="small" ghost @click="openQuestionPicker">从题库抽题</a-button>
                </div>
                <div v-if="selectedQuestionsCache.length" class="q-cache-list">
                  <div class="q-cache-item" v-for="(item, index) in selectedQuestionsCache" :key="item.id">
                    <span>{{ index + 1 }}.</span>
                    <span>[{{ typeLabels[item.type] || item.type }}]</span>
                    <span class="q-cached-content">{{ item.content }}</span>
                    <span>{{ item.score || 0 }}分</span>
                    <a-button type="link" danger size="small" @click="removeSelectedQ(item.id)">移除</a-button>
                  </div>
                </div>
                <a-empty v-else description="暂未配置题目" />
              </div>
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
      <template #footer>
        <a-space style="float:right">
          <a-button @click="resetForm">取消</a-button>
          <a-button type="primary" :loading="submitting" @click="handleSave">保存</a-button>
        </a-space>
      </template>
    </a-drawer>

    <a-modal
      v-model:open="pickerVisible"
      title="从题库抽取题目"
      width="900px"
      @ok="confirmQuestionPick"
      @cancel="pickerVisible = false"
    >
      <div class="picker-toolbar">
        <a-input-search v-model:value="qpSearch" placeholder="搜索题干" style="width:250px" @search="loadPickerQ" />
        <a-select v-model:value="qpType" style="width:120px" @change="loadPickerQ">
          <a-select-option value="all">所有题型</a-select-option>
          <a-select-option value="single">单选</a-select-option>
          <a-select-option value="multi">多选</a-select-option>
          <a-select-option value="judge">判断</a-select-option>
        </a-select>
      </div>
      <a-table
        :columns="qpColumns"
        :data-source="qpList"
        row-key="id"
        :row-selection="qpRowSelection"
        :pagination="qpPagination"
        :loading="qpLoading"
        @change="handleQpTableChange"
        size="small"
      />
    </a-modal>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useRoute } from 'vue-router'
import {
  createAdmissionExam,
  createExam,
  getAdmissionExamDetail,
  getAdmissionExams,
  getExamDetail,
  getExams,
  updateAdmissionExam,
  updateExam,
} from '@/api/exam'
import { getQuestions } from '@/api/question'
import { getTrainings } from '@/api/training'

const route = useRoute()
const statusLabels = { upcoming: '即将开始', active: '进行中', ended: '已结束' }
const statusColors = { upcoming: 'orange', active: 'green', ended: 'default' }
const purposeLabels = {
  admission: '准入考试',
  class_assessment: '班内考核',
  final_assessment: '结业考核',
  quiz: '随堂测验',
}
const typeLabels = { single: '单选', multi: '多选', judge: '判断' }

const searchText = ref('')
const filterStatus = ref('all')
const filterPurpose = ref('all')
const activeKind = ref('admission')
const loading = ref(false)
const submitting = ref(false)
const examList = ref([])
const trainingOptions = ref([])
const drawerVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const editingKind = ref('training')
const dateRange = ref(null)
const handledQuickCreateKey = ref('')

const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

const columns = [
  { title: '场次名称', dataIndex: 'title', key: 'title' },
  { title: '用途', key: 'purpose', width: 100 },
  { title: '培训班', dataIndex: 'trainingName', key: 'trainingName', width: 180 },
  { title: '状态', key: 'status', width: 100 },
  { title: '题目数', dataIndex: 'questionCount', key: 'questionCount', width: 80 },
  { title: '时间', key: 'time', width: 180 },
  { title: '操作', key: 'action', width: 100 },
]

const form = reactive({
  title: '',
  paperTitle: '',
  description: '',
  purpose: 'class_assessment',
  trainingId: undefined,
  type: 'formal',
  status: 'upcoming',
  scope: '全体人员',
  duration: 60,
  passingScore: 60,
  maxAttempts: 1,
  allowMakeup: false,
  questionIds: [],
})

const selectedQuestionsCache = ref([])
const dynamicTotalScore = computed(() => selectedQuestionsCache.value.reduce((sum, item) => sum + (item.score || 0), 0))
const routeKind = computed(() => {
  const raw = Array.isArray(route.query.kind) ? route.query.kind[0] : route.query.kind
  return raw === 'training' || raw === 'admission' ? raw : null
})
const routeTrainingId = computed(() => {
  const raw = Array.isArray(route.query.trainingId) ? route.query.trainingId[0] : route.query.trainingId
  const parsed = Number(raw)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : undefined
})

function resetForm() {
  Object.assign(form, {
    title: '',
    paperTitle: '',
    description: '',
    purpose: 'class_assessment',
    trainingId: undefined,
    type: 'formal',
    status: 'upcoming',
    scope: '全体人员',
    duration: 60,
    passingScore: 60,
    maxAttempts: 1,
    allowMakeup: false,
    questionIds: [],
  })
  drawerVisible.value = false
  isEdit.value = false
  editingId.value = null
  editingKind.value = activeKind.value
  dateRange.value = null
  selectedQuestionsCache.value = []
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

function handleTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadExams()
}

function openCreateDrawer() {
  resetForm()
  editingKind.value = activeKind.value
  applyRouteTrainingContext()
  drawerVisible.value = true
}

async function openEditDrawer(record) {
  resetForm()
  isEdit.value = true
  editingId.value = record.id
  editingKind.value = record.kind || activeKind.value
  try {
    const detail = editingKind.value === 'admission'
      ? await getAdmissionExamDetail(record.id)
      : await getExamDetail(record.id)
    form.title = detail.title
    form.paperTitle = detail.paperTitle || ''
    form.description = detail.description || ''
    form.purpose = detail.purpose || 'class_assessment'
    form.trainingId = detail.trainingId
    form.type = detail.type || 'formal'
    form.status = detail.status || 'upcoming'
    form.scope = editingKind.value === 'admission' ? (detail.scope || '全体人员') : '全体人员'
    form.duration = detail.duration || 60
    form.passingScore = detail.passingScore || 60
    form.maxAttempts = detail.maxAttempts || 1
    form.allowMakeup = !!detail.allowMakeup
    form.questionIds = (detail.questions || []).map(item => item.id)
    selectedQuestionsCache.value = detail.questions || []
    dateRange.value = detail.startTime && detail.endTime ? [detail.startTime, detail.endTime] : null
    drawerVisible.value = true
  } catch (error) {
    message.error(error.message || '加载考试详情失败')
  }
}

function removeSelectedQ(id) {
  form.questionIds = form.questionIds.filter(item => item !== id)
  selectedQuestionsCache.value = selectedQuestionsCache.value.filter(item => item.id !== id)
}

async function handleSave() {
  if (!form.title) {
    message.warning('请输入场次名称')
    return
  }
  if (!form.questionIds.length) {
    message.warning('请至少选择一道题目')
    return
  }
  if (editingKind.value === 'training' && !form.trainingId) {
    message.warning('请选择关联培训班')
    return
  }

  const payload = {
    title: form.title,
    paperTitle: form.paperTitle || undefined,
    description: form.description || undefined,
    type: form.type,
    status: form.status,
    duration: form.duration,
    passingScore: form.passingScore,
    totalScore: dynamicTotalScore.value,
    startTime: dateRange.value?.[0],
    endTime: dateRange.value?.[1],
    questionIds: form.questionIds,
  }
  if (editingKind.value === 'training') {
    payload.purpose = form.purpose
    payload.trainingId = form.trainingId
    payload.maxAttempts = form.maxAttempts
    payload.allowMakeup = form.allowMakeup
  } else {
    payload.scope = form.scope || undefined
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

const pickerVisible = ref(false)
const qpSearch = ref('')
const qpType = ref('all')
const qpLoading = ref(false)
const qpList = ref([])
const qpPagination = reactive({ current: 1, pageSize: 10, total: 0 })
const tempSelectedRowKeys = ref([])
const tempSelectedRowsMap = ref(new Map())

const qpColumns = [
  { title: '题干', dataIndex: 'content', key: 'content' },
  { title: '题型', dataIndex: 'type', key: 'type', width: 80 },
  { title: '分值', dataIndex: 'score', key: 'score', width: 80 },
]

const qpRowSelection = computed(() => ({
  selectedRowKeys: tempSelectedRowKeys.value,
  onChange: (keys, rows) => {
    tempSelectedRowKeys.value = keys
    rows.forEach(item => tempSelectedRowsMap.value.set(item.id, item))
  },
}))

async function loadPickerQ() {
  qpLoading.value = true
  try {
    const result = await getQuestions({
      page: qpPagination.current,
      size: qpPagination.pageSize,
      search: qpSearch.value || undefined,
      type: qpType.value !== 'all' ? qpType.value : undefined,
    })
    qpList.value = result.items || []
    qpPagination.total = result.total || 0
  } catch (error) {
    message.error(error.message || '加载题库失败')
  } finally {
    qpLoading.value = false
  }
}

function openQuestionPicker() {
  qpPagination.current = 1
  tempSelectedRowKeys.value = [...form.questionIds]
  tempSelectedRowsMap.value = new Map(selectedQuestionsCache.value.map(item => [item.id, item]))
  pickerVisible.value = true
  loadPickerQ()
}

function handleQpTableChange(pag) {
  qpPagination.current = pag.current
  qpPagination.pageSize = pag.pageSize
  loadPickerQ()
}

function confirmQuestionPick() {
  form.questionIds = [...tempSelectedRowKeys.value]
  selectedQuestionsCache.value = form.questionIds.map(id => tempSelectedRowsMap.value.get(id)).filter(Boolean)
  pickerVisible.value = false
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
  await Promise.all([loadExams(), loadTrainingOptions()])
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
.selected-questions { border: 1px solid #e8e8e8; border-radius: 8px; padding: 12px; background: #fafafa; }
.selected-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.q-cache-list { display: flex; flex-direction: column; gap: 8px; max-height: 360px; overflow-y: auto; }
.q-cache-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #fff; border: 1px solid #f0f0f0; border-radius: 6px; }
.q-cached-content { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.picker-toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
</style>
