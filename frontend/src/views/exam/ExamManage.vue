<template>
  <div class="exam-manage-page">
    <section class="page-hero">
      <div>
        <div class="hero-kicker">Unified Exam Center</div>
        <h2>统一考试管理</h2>
        <p>这里主要用于独立考试管理。培训班考试请前往培训班管理中创建，独立考试支持名单导入和多种考试类型配置。</p>
      </div>
      <div class="hero-actions">
        <a-button type="primary" size="large" @click="openCreateDrawer('standalone')">创建独立考试</a-button>
        <a-button size="large" @click="openTrainingExamGuide">{{ routeTrainingLocked ? '前往培训班管理创建考试' : '创建培训班考试' }}</a-button>
        <a-button size="large" @click="loadAllData">刷新数据</a-button>
      </div>
    </section>

    <section class="dashboard-grid">
      <article class="metric-card">
        <span class="metric-label">考试总量</span>
        <strong>{{ dashboard.totalExams }}</strong>
        <small>统一统计独立考试与培训班考试</small>
      </article>
      <article class="metric-card">
        <span class="metric-label">独立考试</span>
        <strong>{{ dashboard.standaloneExams }}</strong>
        <small>专项考试、准入制考试等独立场景</small>
      </article>
      <article class="metric-card">
        <span class="metric-label">培训班考试</span>
        <strong>{{ dashboard.trainingExams }}</strong>
        <small>培训班内结课考核与测验</small>
      </article>
      <article class="metric-card">
        <span class="metric-label">进行中</span>
        <strong>{{ dashboard.activeExams }}</strong>
        <small>当前正在开放作答</small>
      </article>
      <article class="metric-card">
        <span class="metric-label">近期待开考</span>
        <strong>{{ dashboard.upcomingExams }}</strong>
        <small>已发布但尚未开始的考试</small>
      </article>
    </section>

    <section class="filter-card">
      <div class="filter-row">
        <a-input-search v-model:value="filters.search" placeholder="搜索考试名称、培训班或参试对象摘要" allow-clear class="search-input" @search="handleSearch" />
        <a-select v-model:value="filters.scene" class="filter-select" @change="handleSceneChange">
          <a-select-option value="all">全部考试</a-select-option>
          <a-select-option value="standalone">独立考试</a-select-option>
          <a-select-option value="training">培训班考试</a-select-option>
        </a-select>
        <a-select v-model:value="filters.purpose" allow-clear class="filter-select" placeholder="考试类型" @change="loadExams">
          <a-select-option v-for="item in purposeOptions" :key="item.value" :value="item.value">{{ item.label }}</a-select-option>
        </a-select>
        <a-select v-model:value="filters.status" allow-clear class="filter-select" placeholder="状态" @change="loadExams">
          <a-select-option value="upcoming">未开始</a-select-option>
          <a-select-option value="active">进行中</a-select-option>
          <a-select-option value="ended">已结束</a-select-option>
        </a-select>
        <a-select v-model:value="filters.departmentId" allow-clear show-search option-filter-prop="label" class="filter-select" placeholder="部门" @change="loadExams">
          <a-select-option v-for="item in departmentOptions" :key="item.id" :value="item.id" :label="item.name">{{ item.name }}</a-select-option>
        </a-select>
        <a-select v-model:value="filters.policeTypeId" allow-clear show-search option-filter-prop="label" class="filter-select" placeholder="警种" @change="loadExams">
          <a-select-option v-for="item in policeTypeOptions" :key="item.id" :value="item.id" :label="item.name">{{ item.name }}</a-select-option>
        </a-select>
      </div>
      <div class="filter-hint">
        <span v-if="routeTrainingLocked">当前已锁定到培训班 {{ routeTrainingId }}，如需创建培训班考试，请返回培训班管理页面操作。</span>
        <span v-else>独立考试通过 Excel 名单导入参试对象；培训班考试请前往培训班管理页面创建。</span>
      </div>
    </section>

    <section class="table-card">
      <div class="table-head">
        <div>
          <h3>考试列表</h3>
          <p>同一试卷可关联多场不同类型考试，列表统一展示场景、类型和参试统计。</p>
        </div>
        <a-button danger :disabled="!selectedRowKeys.length" @click="handleBatchDelete">批量删除</a-button>
      </div>
      <a-table row-key="id" :loading="loading" :columns="columns" :data-source="examList" :pagination="pagination" :row-selection="{ selectedRowKeys, onChange: onSelectChange }" @change="handleTableChange">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'title'">
            <div class="title-cell">
              <button class="link-button" @click="openViewDrawer(record)">{{ record.title }}</button>
              <div class="title-meta">
                <a-tag :color="record.scene === 'standalone' ? 'blue' : 'cyan'">{{ sceneLabelMap[record.scene] }}</a-tag>
                <a-tag>{{ purposeLabelMap[record.purpose] || record.purpose || '其他考试' }}</a-tag>
                <a-tag>{{ record.type === 'quiz' ? '测验' : '正式考试' }}</a-tag>
              </div>
            </div>
          </template>
          <template v-else-if="column.key === 'participants'">
            <div class="stat-block"><strong>{{ record.participantCount ?? 0 }}</strong><span>应考</span></div>
            <div class="stat-sub">已交卷 {{ record.submittedCount ?? 0 }} · 缺考 {{ record.absentCount ?? 0 }}</div>
          </template>
          <template v-else-if="column.key === 'training'">
            <span>{{ record.trainingName || (record.scene === 'training' ? '未选择培训班' : '-') }}</span>
          </template>
          <template v-else-if="column.key === 'target'">
            <div class="target-list">
              <span>{{ record.participantSummary || (record.scene === 'standalone' ? '待导入名单' : '培训班已报名学员') }}</span>
              <small v-if="record.departmentNames?.length">部门：{{ record.departmentNames.join('、') }}</small>
              <small v-if="record.policeTypeNames?.length">警种：{{ record.policeTypeNames.join('、') }}</small>
            </div>
          </template>
          <template v-else-if="column.key === 'time'">
            <div class="time-cell"><span>{{ formatDateTime(record.startTime) }}</span><span>{{ formatDateTime(record.endTime) }}</span></div>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="statusColorMap[record.status] || 'default'">{{ statusLabelMap[record.status] || record.status || '未设置' }}</a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space wrap>
              <a-button type="link" @click="openEditDrawer(record)">编辑</a-button>
              <a-button type="link" @click="openViewDrawer(record)">详情</a-button>
              <a-button type="link" @click="goToScores(record)">考试情况</a-button>
              <a-button v-if="record.scene === 'standalone'" type="link" @click="openImportModal(record)">导入名单</a-button>
              <a-button type="link" danger @click="handleDelete(record)">删除</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </section>

    <a-drawer :open="drawerVisible" :title="isViewOnly ? '考试详情' : (isEdit ? '编辑考试' : '创建独立考试')" :width="860" @close="closeDrawer">
      <a-form layout="vertical">
        <div class="drawer-grid">
          <section class="drawer-panel">
            <h4>基础信息</h4>
            <a-form-item label="考试名称" required>
              <a-input v-model:value="form.title" :disabled="isViewOnly" placeholder="请输入考试场次名称" />
            </a-form-item>
            <a-row :gutter="12">
              <a-col :span="12">
                <a-form-item label="考试场景" required>
                  <a-select v-model:value="form.scene" :disabled="true" @change="handleFormSceneChange">
                    <a-select-option value="standalone">独立考试</a-select-option>
                    <a-select-option v-if="isEdit || isViewOnly" value="training">培训班考试</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="考试类型" required>
                  <a-select v-model:value="form.purpose" :disabled="isViewOnly">
                    <a-select-option v-for="item in purposeOptions" :key="item.value" :value="item.value">{{ item.label }}</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>
            <a-form-item v-if="form.scene === 'training'" label="所属培训班" required>
              <a-select v-model:value="form.trainingId" show-search option-filter-prop="label" :disabled="isViewOnly || routeTrainingLocked" :options="trainingOptions.map(item => ({ value: item.id, label: item.name }))" placeholder="请选择培训班" />
            </a-form-item>
            <a-form-item label="关联试卷" required>
              <a-select v-model:value="form.paperId" :disabled="isEdit || isViewOnly" show-search option-filter-prop="label" :options="availablePaperOptions.map(item => ({ value: item.id, label: item.title }))" placeholder="请选择已发布试卷" @change="handlePaperChange" />
            </a-form-item>
            <a-form-item label="关联课程">
              <a-select v-model:value="form.courseIds" mode="multiple" :disabled="isViewOnly" allow-clear show-search option-filter-prop="label" placeholder="可选，支持一个考试关联多个课程">
                <a-select-option v-for="item in courseOptions" :key="item.id" :value="item.id" :label="item.title">{{ item.title }}</a-select-option>
              </a-select>
            </a-form-item>
            <template v-if="form.scene === 'standalone'">
              <a-form-item label="目标部门">
                <a-select v-model:value="form.departmentIds" mode="multiple" :disabled="isViewOnly" allow-clear show-search option-filter-prop="label" placeholder="可选，作为统计维度">
                  <a-select-option v-for="item in departmentOptions" :key="item.id" :value="item.id" :label="item.name">{{ item.name }}</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="目标警种">
                <a-select v-model:value="form.policeTypeIds" mode="multiple" :disabled="isViewOnly" allow-clear show-search option-filter-prop="label" placeholder="可选，作为统计维度">
                  <a-select-option v-for="item in policeTypeOptions" :key="item.id" :value="item.id" :label="item.name">{{ item.name }}</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="参试对象摘要">
                <a-input v-model:value="form.participantSummary" :disabled="isViewOnly" placeholder="例如：射击理论考试（支队民警）" />
              </a-form-item>
              <div class="standalone-tip">独立考试创建后，请在列表中点击“导入名单”，上传 Excel 名单完成参试对象分配。</div>
            </template>
          </section>

          <section class="drawer-panel">
            <h4>发布设置</h4>
            <a-row :gutter="12">
              <a-col :span="12">
                <a-form-item label="状态">
                  <a-select v-model:value="form.status" :disabled="isViewOnly">
                    <a-select-option value="upcoming">未开始</a-select-option>
                    <a-select-option value="active">进行中</a-select-option>
                    <a-select-option value="ended">已结束</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="展示类型">
                  <a-select v-model:value="form.type" :disabled="isViewOnly">
                    <a-select-option value="formal">正式考试</a-select-option>
                    <a-select-option value="quiz">测验</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>
            <a-form-item label="考试时间">
              <a-range-picker v-model:value="dateRange" :disabled="isViewOnly" show-time format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" style="width: 100%" />
            </a-form-item>
            <a-row :gutter="12">
              <a-col :span="8">
                <a-form-item label="考试时长">
                  <a-input-number v-model:value="form.duration" :min="10" :max="300" :disabled="isViewOnly" style="width: 100%" />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="及格分">
                  <a-input-number v-model:value="form.passingScore" :min="1" :disabled="isViewOnly" style="width: 100%" />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="最大次数">
                  <a-input-number v-model:value="form.maxAttempts" :min="1" :max="10" :disabled="isViewOnly" style="width: 100%" />
                </a-form-item>
              </a-col>
            </a-row>
            <a-form-item label="考试说明">
              <a-textarea v-model:value="form.description" :disabled="isViewOnly" :rows="4" placeholder="可填写考试说明、补考规则等" />
            </a-form-item>
            <div class="paper-preview">
              <div class="paper-preview__head">
                <span>试卷预览</span>
                <small>考试创建后不可更换试卷</small>
              </div>
              <template v-if="selectedPaperDetail">
                <strong>{{ selectedPaperDetail.title }}</strong>
                <div class="paper-preview__meta">
                  <span>{{ selectedPaperDetail.questionCount || 0 }} 题</span>
                  <span>满分 {{ selectedPaperDetail.totalScore || 0 }} 分</span>
                  <span>建议时长 {{ selectedPaperDetail.duration || 60 }} 分钟</span>
                </div>
              </template>
              <a-empty v-else description="请选择试卷后查看预览" />
            </div>
          </section>
        </div>
      </a-form>
      <template #footer>
        <a-space style="float: right">
          <a-button @click="closeDrawer">{{ isViewOnly ? '关闭' : '取消' }}</a-button>
          <a-button v-if="!isViewOnly" type="primary" :loading="submitting" @click="handleSave">保存</a-button>
        </a-space>
      </template>
    </a-drawer>

    <a-modal :open="importModalVisible" width="1100px" title="独立考试名单导入" :footer="null" @cancel="closeImportModal">
      <div v-if="importExam" class="import-layout">
        <div class="import-side">
          <div class="import-card">
            <div class="import-card__title">考试信息</div>
            <div class="import-meta">{{ importExam.title }}</div>
            <div class="import-meta">考试类型：{{ purposeLabelMap[importExam.purpose] || importExam.purpose || '其他考试' }}</div>
            <div class="import-meta">当前已导入 {{ importParticipants.length }} 人</div>
          </div>
          <div class="import-card">
            <div class="import-card__title">Excel 名单导入</div>
            <a-space direction="vertical" style="width: 100%">
              <a-button block @click="handleDownloadTemplate">下载导入模板</a-button>
              <a-upload-dragger :before-upload="beforeImportUpload" :file-list="importFileList" :multiple="false" :max-count="1">
                <p class="ant-upload-text">点击或拖拽上传名单 Excel</p>
                <p class="ant-upload-hint">支持 `.xlsx` / `.xls`，按模板填写警号、手机号或身份证号。</p>
              </a-upload-dragger>
              <a-button type="primary" block :loading="importPreviewLoading" @click="handlePreviewImport">预检名单</a-button>
            </a-space>
          </div>
          <div class="import-card">
            <div class="import-card__title">已导入名单</div>
            <a-table size="small" row-key="id" :data-source="importParticipants" :columns="participantColumns" :pagination="{ pageSize: 5 }" />
          </div>
        </div>

        <div class="import-main">
          <div class="import-card">
            <div class="import-card__title">预检结果</div>
            <div v-if="importPreview" class="preview-summary">
              <a-tag color="blue">总行数 {{ importPreview.summary?.totalRows || 0 }}</a-tag>
              <a-tag color="green">已匹配 {{ importPreview.summary?.matchedCount || 0 }}</a-tag>
              <a-tag color="gold">将创建账号 {{ importPreview.summary?.createdCount || 0 }}</a-tag>
              <a-tag color="red">失败 {{ importPreview.summary?.failedCount || 0 }}</a-tag>
            </div>
            <a-empty v-else description="上传并预检 Excel 后，在这里查看匹配结果" />
          </div>
          <div v-if="importPreview" class="preview-grid">
            <div class="import-card">
              <div class="import-card__title">已匹配现有账号</div>
              <a-table size="small" row-key="rowNo" :data-source="importPreview.matchedRows || []" :columns="previewColumns" :pagination="{ pageSize: 5 }" />
            </div>
            <div class="import-card">
              <div class="import-card__title">将自动创建账号</div>
              <a-table size="small" row-key="rowNo" :data-source="importPreview.createdRows || []" :columns="previewColumns" :pagination="{ pageSize: 5 }" />
            </div>
            <div class="import-card import-card--danger">
              <div class="import-card__title">导入失败 / 冲突</div>
              <a-table size="small" row-key="rowNo" :data-source="importPreview.failedRows || []" :columns="failedColumns" :pagination="{ pageSize: 5 }" />
            </div>
          </div>
          <div class="modal-footer">
            <a-button @click="closeImportModal">关闭</a-button>
            <a-button v-if="importPreview?.batchId" :disabled="!(importPreview.failedRows || []).length" @click="handleExportImportResult">导出失败结果</a-button>
            <a-button v-if="importPreview?.batchId" type="primary" :loading="importConfirmLoading" :disabled="(importPreview.summary?.totalRows || 0) === 0" @click="handleConfirmImport">确认导入名单</a-button>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import dayjs from 'dayjs'
import {
  confirmExamParticipantImport,
  createExam,
  deleteExam,
  downloadExamParticipantImportTemplate,
  exportExamParticipantImportResult,
  getExamDashboard,
  getExamDetail,
  getExamPaperDetail,
  getExamPapers,
  getExamParticipants,
  getExams,
  previewExamParticipantImport,
  updateExam,
} from '@/api/exam'
import { getCourses } from '@/api/course'
import { getTrainings } from '@/api/training'
import { getDepartmentList } from '@/api/department'
import { getPoliceTypes } from '@/api/user'

const router = useRouter()
const route = useRoute()

const purposeOptions = [
  { value: 'admission', label: '准入制考试' },
  { value: 'completion', label: '结课考试' },
  { value: 'quiz', label: '测试' },
  { value: 'makeup', label: '补考' },
  { value: 'special', label: '专项考试' },
  { value: 'other', label: '其他考试' },
]
const purposeLabelMap = Object.fromEntries(purposeOptions.map(item => [item.value, item.label]))
const sceneLabelMap = { standalone: '独立考试', training: '培训班考试' }
const statusLabelMap = { upcoming: '未开始', active: '进行中', ended: '已结束' }
const statusColorMap = { upcoming: 'gold', active: 'green', ended: 'default' }

const columns = [
  { title: '考试名称', key: 'title', width: 260 },
  { title: '参试统计', key: 'participants', width: 150 },
  { title: '考试时间', key: 'time', width: 180 },
  { title: '考试类型 / 对象', key: 'target' },
  { title: '关联培训班', key: 'training', width: 180 },
  { title: '状态', key: 'status', width: 100 },
  { title: '操作', key: 'actions', width: 260, fixed: 'right' },
]

const participantColumns = [
  { title: '姓名', dataIndex: 'name', key: 'name', width: 100 },
  { title: '账号', dataIndex: 'username', key: 'username', width: 120 },
  { title: '警号', dataIndex: 'policeId', key: 'policeId', width: 120 },
  { title: '手机号', dataIndex: 'phone', key: 'phone', width: 120 },
  { title: '匹配状态', dataIndex: 'matchStatus', key: 'matchStatus', width: 100 },
  { title: '参与状态', dataIndex: 'participationStatus', key: 'participationStatus', width: 100 },
]

const previewColumns = [
  { title: '行号', dataIndex: 'rowNo', key: 'rowNo', width: 70 },
  { title: '姓名', dataIndex: 'name', key: 'name', width: 100 },
  { title: '警号', dataIndex: 'policeId', key: 'policeId', width: 120 },
  { title: '手机号', dataIndex: 'phone', key: 'phone', width: 120 },
  { title: '账号', dataIndex: 'username', key: 'username', width: 120 },
  { title: '说明', dataIndex: 'message', key: 'message' },
]

const failedColumns = [
  { title: '行号', dataIndex: 'rowNo', key: 'rowNo', width: 70 },
  { title: '姓名', dataIndex: 'name', key: 'name', width: 100 },
  { title: '警号', dataIndex: 'policeId', key: 'policeId', width: 120 },
  { title: '手机号', dataIndex: 'phone', key: 'phone', width: 120 },
  { title: '失败原因', dataIndex: 'message', key: 'message' },
]

const filters = reactive({
  search: '',
  scene: 'all',
  purpose: undefined,
  status: undefined,
  departmentId: undefined,
  policeTypeId: undefined,
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
})

const dashboard = reactive({
  totalExams: 0,
  standaloneExams: 0,
  trainingExams: 0,
  activeExams: 0,
  upcomingExams: 0,
})

const loading = ref(false)
const submitting = ref(false)
const examList = ref([])
const selectedRowKeys = ref([])
const paperOptions = ref([])
const courseOptions = ref([])
const trainingOptions = ref([])
const departmentOptions = ref([])
const policeTypeOptions = ref([])
const selectedPaperDetail = ref(null)
const availablePaperOptions = computed(() => (
  isEdit.value || isViewOnly.value
    ? paperOptions.value
    : paperOptions.value.filter(item => item.status === 'published')
))

const drawerVisible = ref(false)
const isEdit = ref(false)
const isViewOnly = ref(false)
const editingId = ref(null)
const dateRange = ref(null)

const form = reactive({
  title: '',
  scene: 'standalone',
  purpose: 'special',
  paperId: undefined,
  trainingId: undefined,
  courseIds: [],
  departmentIds: [],
  policeTypeIds: [],
  participantSummary: '',
  status: 'upcoming',
  type: 'formal',
  duration: 60,
  passingScore: 60,
  maxAttempts: 1,
  description: '',
})

const importModalVisible = ref(false)
const importExam = ref(null)
const importParticipants = ref([])
const importFile = ref(null)
const importFileList = ref([])
const importPreview = ref(null)
const importPreviewLoading = ref(false)
const importConfirmLoading = ref(false)

const routeTrainingId = computed(() => {
  const value = Number(route.query.trainingId)
  return Number.isInteger(value) && value > 0 ? value : undefined
})
const routeTrainingLocked = computed(() => !!routeTrainingId.value)

function formatDateTime(value) {
  return value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '未设置'
}

function handleSearch() {
  pagination.current = 1
  loadExams()
}

function handleSceneChange(nextScene) {
  if (routeTrainingLocked.value && nextScene !== 'training') {
    filters.scene = 'training'
    return
  }
  pagination.current = 1
  loadExams()
}

function onSelectChange(keys) {
  selectedRowKeys.value = keys
}

function handleTableChange(nextPagination) {
  pagination.current = nextPagination.current
  pagination.pageSize = nextPagination.pageSize
  loadExams()
}

function goToScores(record) {
  router.push({ name: 'ExamScores', query: { examId: record.id } })
}

function normalizeScene(value) {
  return value === 'training' ? 'training' : 'standalone'
}

function resetForm(scene = 'standalone') {
  Object.assign(form, {
    title: '',
    scene,
    purpose: scene === 'training' ? 'completion' : 'special',
    paperId: undefined,
    trainingId: routeTrainingId.value,
    courseIds: [],
    departmentIds: [],
    policeTypeIds: [],
    participantSummary: '',
    status: 'upcoming',
    type: 'formal',
    duration: 60,
    passingScore: 60,
    maxAttempts: 1,
    description: '',
  })
  dateRange.value = null
  selectedPaperDetail.value = null
}

function closeDrawer() {
  drawerVisible.value = false
  isEdit.value = false
  isViewOnly.value = false
  editingId.value = null
}

function downloadBlob(blob, fileName) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  link.click()
  URL.revokeObjectURL(url)
}

async function loadDashboard() {
  try {
    const data = await getExamDashboard(routeTrainingLocked.value ? { trainingId: routeTrainingId.value } : undefined)
    dashboard.totalExams = data?.kpi?.totalExams || 0
    dashboard.standaloneExams = data?.kpi?.standaloneExams || 0
    dashboard.trainingExams = data?.kpi?.trainingExams || 0
    dashboard.activeExams = data?.kpi?.activeExams || 0
    dashboard.upcomingExams = data?.kpi?.upcomingExams || 0
  } catch {
    Object.assign(dashboard, { totalExams: 0, standaloneExams: 0, trainingExams: 0, activeExams: 0, upcomingExams: 0 })
  }
}

async function loadLookups() {
  const [papers, courses, trainings, departments, policeTypes] = await Promise.allSettled([
    getExamPapers({ size: -1 }),
    getCourses({ size: -1 }),
    getTrainings({ size: -1 }),
    getDepartmentList({ size: -1 }),
    getPoliceTypes(),
  ])
  paperOptions.value = papers.status === 'fulfilled' ? (papers.value.items || []) : []
  courseOptions.value = courses.status === 'fulfilled' ? (courses.value.items || []) : []
  trainingOptions.value = trainings.status === 'fulfilled' ? (trainings.value.items || []) : []
  departmentOptions.value = departments.status === 'fulfilled' ? (departments.value.items || []) : []
  policeTypeOptions.value = policeTypes.status === 'fulfilled' ? (policeTypes.value || []) : []
}

async function loadExams() {
  loading.value = true
  try {
    const result = await getExams({
      page: pagination.current,
      size: pagination.pageSize,
      search: filters.search || undefined,
      scene: filters.scene === 'all' ? undefined : filters.scene,
      purpose: filters.purpose || undefined,
      status: filters.status || undefined,
      departmentId: filters.departmentId || undefined,
      policeTypeId: filters.policeTypeId || undefined,
      trainingId: routeTrainingId.value,
    })
    examList.value = result.items || []
    pagination.total = result.total || 0
    selectedRowKeys.value = []
  } catch (error) {
    message.error(error.message || '加载考试列表失败')
  } finally {
    loading.value = false
  }
}

async function loadAllData() {
  await Promise.all([loadDashboard(), loadExams()])
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
      form.duration = detail.duration || 60
      form.passingScore = detail.passingScore || Math.max(1, Math.ceil((detail.totalScore || 0) * 0.6))
      form.type = detail.type || 'formal'
    }
  } catch {
    selectedPaperDetail.value = null
  }
}

function handleFormSceneChange(nextScene) {
  if (nextScene === 'training') {
    form.purpose = form.purpose === 'special' ? 'completion' : form.purpose
    form.trainingId = routeTrainingId.value || form.trainingId
  } else {
    form.trainingId = undefined
    form.purpose = form.purpose === 'completion' ? 'special' : form.purpose
  }
}

function handlePaperChange(value) {
  setPaperPreview(value, !isEdit.value)
}

function openCreateDrawer(scene = 'standalone') {
  resetForm(scene === 'training' ? 'standalone' : scene)
  isViewOnly.value = false
  isEdit.value = false
  drawerVisible.value = true
}

function openTrainingExamGuide() {
  Modal.confirm({
    title: '培训班考试请前往培训班管理创建',
    content: '培训班考试需要在对应培训班内完成创建和关联，当前页面仅支持独立考试管理。你可以直接前往培训班管理页面继续操作。',
    okText: '跳转到培训班管理',
    cancelText: '知道了',
    onOk() {
      router.push({ name: 'TrainingList' })
    },
  })
}

async function openExamDrawer(record, viewOnly = false) {
  try {
    const detail = await getExamDetail(record.id)
    resetForm(normalizeScene(detail.scene || record.scene))
    isViewOnly.value = viewOnly
    isEdit.value = !viewOnly
    editingId.value = record.id
    form.title = detail.title || ''
    form.scene = normalizeScene(detail.scene)
    form.purpose = detail.purpose || 'completion'
    form.paperId = detail.paperId
    form.trainingId = detail.trainingId
    form.courseIds = [...(detail.courseIds || [])]
    form.departmentIds = [...(detail.departmentIds || [])]
    form.policeTypeIds = [...(detail.policeTypeIds || [])]
    form.participantSummary = detail.participantSummary || ''
    form.status = detail.status || 'upcoming'
    form.type = detail.type || 'formal'
    form.duration = detail.duration || 60
    form.passingScore = detail.passingScore || 60
    form.maxAttempts = detail.maxAttempts || 1
    form.description = detail.description || ''
    dateRange.value = detail.startTime && detail.endTime ? [detail.startTime, detail.endTime] : null
    selectedPaperDetail.value = {
      title: detail.paperTitle || '未命名试卷',
      questionCount: detail.questionCount || 0,
      totalScore: detail.totalScore || 0,
      duration: detail.duration || 60,
      status: detail.paperStatus,
    }
    drawerVisible.value = true
  } catch (error) {
    message.error(error.message || '加载考试详情失败')
  }
}

function openEditDrawer(record) {
  openExamDrawer(record, false)
}

function openViewDrawer(record) {
  openExamDrawer(record, true)
}

function buildPayload() {
  return {
    title: form.title.trim(),
    scene: form.scene,
    participantMode: form.scene === 'training' ? 'training_enrollment' : 'excel_import',
    purpose: form.purpose,
    paperId: form.paperId,
    trainingId: form.scene === 'training' ? form.trainingId : undefined,
    courseIds: form.courseIds,
    departmentIds: form.scene === 'standalone' ? form.departmentIds : [],
    policeTypeIds: form.scene === 'standalone' ? form.policeTypeIds : [],
    participantSummary: form.scene === 'standalone' ? (form.participantSummary || undefined) : undefined,
    status: form.status,
    type: form.type,
    duration: Number(form.duration),
    passingScore: Number(form.passingScore),
    maxAttempts: Number(form.maxAttempts),
    description: form.description || undefined,
    startTime: dateRange.value?.[0] || undefined,
    endTime: dateRange.value?.[1] || undefined,
  }
}

async function handleSave() {
  if (!form.title.trim()) return message.warning('请输入考试名称')
  if (!form.paperId) return message.warning('请选择试卷')
  if (!isEdit.value) {
    form.scene = 'standalone'
  }
  if (form.scene === 'training' && !form.trainingId) return message.warning('请选择培训班')
  if (Number(form.duration) < 10) return message.warning('考试时长不能少于 10 分钟')
  if (selectedPaperDetail.value && Number(form.passingScore) > Number(selectedPaperDetail.value.totalScore || 0)) {
    return message.warning('及格分不能超过试卷满分')
  }
  submitting.value = true
  try {
    const payload = buildPayload()
    if (isEdit.value) {
      await updateExam(editingId.value, payload)
      message.success('考试已更新')
    } else {
      await createExam(payload)
      message.success(form.scene === 'standalone' ? '独立考试已创建，请继续导入名单' : '培训班考试已创建')
    }
    closeDrawer()
    await loadAllData()
  } catch (error) {
    message.error(error.message || '保存失败')
  } finally {
    submitting.value = false
  }
}

function handleDelete(record) {
  Modal.confirm({
    title: `确定删除“${record.title}”吗？`,
    content: '已有作答记录或已关联业务流程的考试不能删除。',
    okType: 'danger',
    async onOk() {
      try {
        await deleteExam(record.id)
        message.success('删除成功')
        await loadAllData()
      } catch (error) {
        message.error(error.message || '删除失败')
      }
    },
  })
}

function handleBatchDelete() {
  if (!selectedRowKeys.value.length) return
  Modal.confirm({
    title: `确定删除选中的 ${selectedRowKeys.value.length} 场考试吗？`,
    content: '删除后不可恢复。',
    okType: 'danger',
    async onOk() {
      let success = 0
      let failed = 0
      for (const examId of selectedRowKeys.value) {
        try {
          await deleteExam(examId)
          success += 1
        } catch {
          failed += 1
        }
      }
      await loadAllData()
      if (failed) message.warning(`成功删除 ${success} 场，${failed} 场删除失败`)
      else message.success(`成功删除 ${success} 场考试`)
    },
  })
}

async function loadImportParticipants(examId) {
  try {
    importParticipants.value = await getExamParticipants(examId)
  } catch {
    importParticipants.value = []
  }
}

function resetImportState() {
  importPreview.value = null
  importFile.value = null
  importFileList.value = []
  importParticipants.value = []
}

async function openImportModal(record) {
  importExam.value = record
  resetImportState()
  importModalVisible.value = true
  await loadImportParticipants(record.id)
}

function closeImportModal() {
  importModalVisible.value = false
  importExam.value = null
  resetImportState()
}

function beforeImportUpload(file) {
  importFile.value = file
  importFileList.value = [file]
  return false
}

async function handleDownloadTemplate() {
  try {
    const blob = await downloadExamParticipantImportTemplate()
    downloadBlob(blob, '独立考试名单导入模板.xlsx')
  } catch (error) {
    message.error(error.message || '模板下载失败')
  }
}

async function handlePreviewImport() {
  if (!importExam.value) return
  if (!importFile.value) return message.warning('请先选择 Excel 文件')
  importPreviewLoading.value = true
  try {
    importPreview.value = await previewExamParticipantImport(importExam.value.id, importFile.value)
    message.success('名单预检完成')
  } catch (error) {
    message.error(error.message || '名单预检失败')
  } finally {
    importPreviewLoading.value = false
  }
}

async function handleConfirmImport() {
  if (!importPreview.value?.batchId) return message.warning('请先完成名单预检')
  importConfirmLoading.value = true
  try {
    importPreview.value = await confirmExamParticipantImport(importPreview.value.batchId)
    await Promise.all([loadImportParticipants(importExam.value.id), loadAllData()])
    message.success('名单导入成功')
  } catch (error) {
    message.error(error.message || '名单导入失败')
  } finally {
    importConfirmLoading.value = false
  }
}

async function handleExportImportResult() {
  if (!importPreview.value?.batchId) return
  try {
    const blob = await exportExamParticipantImportResult(importPreview.value.batchId)
    downloadBlob(blob, `${importExam.value?.title || '考试'}_导入结果.xlsx`)
  } catch (error) {
    message.error(error.message || '导出失败结果失败')
  }
}

onMounted(async () => {
  if (routeTrainingLocked.value) filters.scene = 'training'
  else if (route.query.kind === 'training' || route.query.scene === 'training') filters.scene = 'training'
  await loadLookups()
  await loadAllData()
})
</script>

<style scoped>
.exam-manage-page { display: flex; flex-direction: column; gap: 20px; min-height: 100%; padding: 12px 0 24px; }
.page-hero { display: flex; justify-content: space-between; gap: 24px; padding: 28px 32px; border-radius: 24px; background: radial-gradient(circle at top right, rgba(59, 130, 246, 0.22), transparent 34%), linear-gradient(135deg, #0f172a 0%, #13315d 100%); color: #f8fafc; }
.hero-kicker { font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase; color: rgba(191, 219, 254, 0.92); }
.page-hero h2 { margin: 10px 0 8px; font-size: 30px; color: #fff; }
.page-hero p { margin: 0; max-width: 720px; line-height: 1.7; color: rgba(226, 232, 240, 0.92); }
.hero-actions { display: flex; gap: 12px; align-items: flex-start; flex-wrap: wrap; }
.dashboard-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 16px; }
.metric-card, .filter-card, .table-card { border: 1px solid #e2e8f0; border-radius: 20px; background: #fff; box-shadow: 0 14px 30px rgba(15, 23, 42, 0.04); }
.metric-card { padding: 20px; display: flex; flex-direction: column; gap: 8px; }
.metric-label { font-size: 12px; font-weight: 700; letter-spacing: 0.06em; color: #64748b; text-transform: uppercase; }
.metric-card strong { font-size: 28px; color: #0f172a; }
.metric-card small { line-height: 1.6; color: #64748b; }
.filter-card { padding: 20px 24px; }
.filter-row { display: grid; grid-template-columns: minmax(260px, 1.4fr) repeat(5, minmax(140px, 1fr)); gap: 12px; }
.search-input, .filter-select { width: 100%; }
.filter-hint { margin-top: 12px; font-size: 12px; color: #64748b; }
.table-card { padding: 22px 24px 18px; }
.table-head { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 18px; }
.table-head h3 { margin: 0 0 6px; font-size: 20px; color: #0f172a; }
.table-head p { margin: 0; color: #64748b; }
.title-cell { display: flex; flex-direction: column; gap: 8px; }
.link-button { padding: 0; border: none; background: transparent; text-align: left; font-size: 15px; font-weight: 700; color: #0f172a; cursor: pointer; }
.link-button:hover { color: #2563eb; }
.title-meta { display: flex; flex-wrap: wrap; gap: 6px; }
.stat-block { display: flex; align-items: baseline; gap: 8px; }
.stat-block strong { font-size: 20px; color: #0f172a; }
.stat-block span, .stat-sub, .target-list small { color: #64748b; }
.time-cell, .target-list { display: flex; flex-direction: column; gap: 6px; }
.drawer-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.drawer-panel { padding: 18px; border-radius: 18px; background: #f8fafc; border: 1px solid #e2e8f0; }
.drawer-panel h4 { margin: 0 0 16px; font-size: 16px; color: #0f172a; }
.standalone-tip { padding: 12px 14px; border-radius: 12px; background: #eff6ff; color: #1d4ed8; font-size: 12px; line-height: 1.7; }
.paper-preview { padding: 16px; border-radius: 14px; border: 1px solid #dbeafe; background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%); }
.paper-preview__head { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 10px; color: #1e3a8a; font-weight: 600; }
.paper-preview__head small, .paper-preview__meta { color: #64748b; }
.paper-preview__meta { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 12px; }
.import-layout { display: grid; grid-template-columns: 320px minmax(0, 1fr); gap: 16px; }
.import-side, .import-main, .preview-grid { display: flex; flex-direction: column; gap: 16px; }
.import-card { padding: 18px; border-radius: 18px; border: 1px solid #e2e8f0; background: #fff; }
.import-card--danger { border-color: #fecaca; background: #fff7f7; }
.import-card__title { margin-bottom: 14px; font-size: 15px; font-weight: 700; color: #0f172a; }
.import-meta { margin-bottom: 8px; color: #475569; }
.preview-summary { display: flex; flex-wrap: wrap; gap: 8px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; }
@media (max-width: 1400px) { .dashboard-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } .filter-row { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 960px) { .page-hero, .table-head { flex-direction: column; } .dashboard-grid, .filter-row, .drawer-grid, .import-layout { grid-template-columns: 1fr; } }
</style>
