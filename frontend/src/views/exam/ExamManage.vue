<template>
  <div class="exam-manage-page">
    <!-- 内容滚动区 -->
    <div class="content-wrapper">
      <div class="max-w-[1600px] mx-auto w-full">

        <!-- 页面标题 -->
        <div class="page-title-section">
          <div>
            <h1 class="page-title">考试管理</h1>
            <p class="page-subtitle">考试场次已按所属课程进行归档，点击课程行可快速查看该课程下的所有考试记录</p>
          </div>
          <permissions-tooltip
            :allowed="canManageExam"
            tips="需要 CREATE_EXAM 权限"
            v-slot="{ disabled }"
          >
            <a-button
              type="primary"
              :disabled="disabled"
              @click="openCreateDrawer"
              class="publish-btn"
            >
              <template #icon><PlusOutlined /></template>
              发布新考试
            </a-button>
          </permissions-tooltip>
        </div>

        <!-- 统一的大边框容器 -->
        <div class="main-container">

          <!-- 第一部分：数据汇总 -->
          <div class="stats-bar">
            <div class="stat-item">
              <div class="stat-label">活跃课程</div>
              <div class="stat-value">{{ statsData.activeCourses }} <span class="stat-unit">门</span></div>
            </div>
            <div class="stat-item stat-divider">
              <div class="stat-label stat-label-green">进行中考试</div>
              <div class="stat-value stat-value-green">{{ statsData.ongoingExams }} <span class="stat-unit">场次</span></div>
            </div>
            <div class="stat-item stat-divider">
              <div class="stat-label stat-label-blue">今日参考人数</div>
              <div class="stat-value stat-value-blue">{{ statsData.todayParticipants }} <span class="stat-unit">人</span></div>
            </div>
            <div class="stat-item">
              <div class="stat-label stat-label-amber">待批改试卷</div>
              <div class="stat-value stat-value-amber">{{ statsData.pendingGrading }} <span class="stat-unit">份</span></div>
            </div>
          </div>

          <!-- 第二部分：过滤条 -->
          <div class="filter-bar">
            <div class="filter-left">
              <a-input-search
                v-model:value="searchText"
                placeholder="搜索考试场次名称..."
                allow-clear
                @search="handleSearch"
                class="search-input"
              />
              <a-select
                v-model:value="filterStatus"
                style="width: 160px"
                @change="handleSearch"
                class="status-select"
              >
                <a-select-option value="all">全部状态</a-select-option>
                <a-select-option value="upcoming">即将开始</a-select-option>
                <a-select-option value="active">进行中</a-select-option>
                <a-select-option value="ended">已结束</a-select-option>
              </a-select>
            </div>
            <div class="filter-right">
              <a-tabs v-model:activeKey="activeKind" @change="handleKindChange" class="kind-tabs">
                <a-tab-pane key="admission" tab="准入考试" />
                <a-tab-pane key="training" tab="培训班考试" />
              </a-tabs>
            </div>
          </div>

          <!-- 第三部分：列表主体 -->
          <div class="list-container">

            <!-- 列表头 -->
            <div class="list-header">
              <div class="col-course">所属课程 / 场次名称</div>
              <div class="col-paper">关联试卷</div>
              <div class="col-status text-center">状态</div>
              <div class="col-count text-center">实考/应考</div>
              <div class="col-time">有效时间范围</div>
              <div class="col-action text-right">操作</div>
            </div>

            <!-- 课程分组列表 -->
            <div v-for="course in groupedExamList" :key="course.id" class="course-group">
              <!-- 课程行 -->
              <div
                class="course-row"
                :class="{ 'is-collapsed': collapsedCourses.includes(course.id) }"
                @click="toggleCourse(course.id)"
              >
                <div class="col-course">
                  <svg class="chevron-icon" :class="{ 'rotated': collapsedCourses.includes(course.id) }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"/>
                  </svg>
                  <svg class="course-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                  </svg>
                  <span class="course-name">{{ course.name }}</span>
                </div>
                <div class="col-paper flex-1 text-xs text-slate-400 font-medium italic">
                  当前课程下共有 {{ course.exams.length }} 场考试任务
                </div>
                <div class="col-status"></div>
                <div class="col-count"></div>
                <div class="col-time"></div>
                <div class="col-action text-right">
                  <span class="course-detail-hint">查看课程详情</span>
                </div>
              </div>

              <!-- 场次列表 -->
              <div class="exam-items" :class="{ 'is-collapsed': collapsedCourses.includes(course.id) }">
                <div
                  v-for="exam in course.exams"
                  :key="exam.id"
                  class="exam-row"
                >
                  <div class="col-course pl-7">
                    <span class="exam-title">{{ exam.title }}</span>
                    <span class="exam-id">ID: {{ exam.code }}</span>
                  </div>
                  <div class="col-paper flex flex-col">
                    <span class="text-sm text-slate-600">{{ exam.paperTitle || '-' }}</span>
                    <span v-if="exam.paperStatus" class="paper-status-badge" :class="'paper-status-' + exam.paperStatus">
                      {{ paperStatusLabels[exam.paperStatus] || exam.paperStatus }}
                    </span>
                  </div>
                  <div class="col-status flex justify-center">
                    <span class="status-pill" :class="'status-' + exam.status">
                      {{ statusLabels[exam.status] }}
                    </span>
                  </div>
                  <div class="col-count text-center">
                    <span class="font-bold text-slate-700">{{ exam.actualCount }}</span>
                    <span class="text-slate-300 mx-0.5">/</span>
                    <span class="text-slate-400">{{ exam.expectedCount }}</span>
                  </div>
                  <div class="col-time flex flex-col justify-center">
                    <span class="text-[11px] font-medium text-slate-600">{{ formatDateTime(exam.startTime) }}</span>
                    <span class="text-[11px] text-slate-400">{{ formatDateTime(exam.endTime) }}</span>
                  </div>
                  <div class="col-action text-right flex justify-end gap-4">
                    <permissions-tooltip
                      :allowed="canManageExam"
                      tips="需要 CREATE_EXAM 权限"
                      v-slot="{ disabled }"
                    >
                      <a-button
                        type="link"
                        size="small"
                        :disabled="disabled"
                        @click.stop="openEditDrawer(exam)"
                        class="action-btn"
                      >
                        {{ exam.status === 'active' ? '监考' : (exam.status === 'ended' ? '成绩' : '编辑') }}
                      </a-button>
                    </permissions-tooltip>
                    <a-button
                      type="link"
                      size="small"
                      @click.stop="openEditDrawer(exam)"
                      class="action-btn-secondary"
                    >
                      {{ exam.status === 'ended' ? '归档' : '统计' }}
                    </a-button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 空状态 -->
            <div v-if="groupedExamList.length === 0 && !loading" class="empty-state">
              <svg class="empty-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
              </svg>
              <p>暂无考试记录</p>
            </div>
          </div>

          <!-- 分页 -->
          <div class="pagination-bar">
            <div class="pagination-info">
              Showing {{ ((pagination.current - 1) * pagination.pageSize) + 1 }} to {{ Math.min(pagination.current * pagination.pageSize, pagination.total) }} of {{ pagination.total }} Courses
            </div>
            <div class="pagination-controls">
              <a-button
                class="page-btn"
                :disabled="pagination.current === 1"
                @click="handlePageChange(pagination.current - 1)"
              >
                <LeftOutlined />
              </a-button>
              <a-button
                v-for="page in visiblePages"
                :key="page"
                :class="['page-btn', { 'page-btn-active': page === pagination.current }]"
                @click="handlePageChange(page)"
              >
                {{ page }}
              </a-button>
              <a-button
                class="page-btn"
                :disabled="pagination.current === totalPages"
                @click="handlePageChange(pagination.current + 1)"
              >
                <RightOutlined />
              </a-button>
            </div>
          </div>

        </div>

        <!-- 辅助脚部 -->
        <div class="footer-bar">
          <span>© 2024 警务训练指挥平台 | 考试管理模块</span>
          <div class="flex items-center gap-2">
            <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
            数据连接已就绪
          </div>
        </div>

      </div>
    </div>

    <!-- 创建/编辑抽屉 -->
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
import { PlusOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons-vue'
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
const collapsedCourses = ref([])

const pagination = reactive({ current: 1, pageSize: 10, total: 0 })
const statsData = reactive({
  activeCourses: 0,
  ongoingExams: 0,
  todayParticipants: 0,
  pendingGrading: 0
})

// 按课程分组的考试列表
const groupedExamList = computed(() => {
  const groups = {}
  examList.value.forEach(exam => {
    const courseId = exam.courseId || 0
    const courseName = exam.courseName || '未分类'
    if (!groups[courseId]) {
      groups[courseId] = {
        id: courseId,
        name: courseName,
        exams: []
      }
    }
    groups[courseId].exams.push(exam)
  })
  return Object.values(groups)
})

const totalPages = computed(() => Math.ceil(pagination.total / pagination.pageSize))
const visiblePages = computed(() => {
  const pages = []
  const total = totalPages.value
  const current = pagination.current
  let start = Math.max(1, current - 2)
  let end = Math.min(total, start + 4)
  if (end - start < 4) {
    start = Math.max(1, end - 4)
  }
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

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

function toggleCourse(courseId) {
  const index = collapsedCourses.value.indexOf(courseId)
  if (index > -1) {
    collapsedCourses.value.splice(index, 1)
  } else {
    collapsedCourses.value.push(courseId)
  }
}

function handleSearch() {
  pagination.current = 1
  loadExams()
}

function handlePageChange(page) {
  pagination.current = page
  loadExams()
}

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
    })

    // 转换数据以适配新布局
    examList.value = (result.items || []).map(item => ({
      ...item,
      code: item.code || `EXAM-${String(item.id).padStart(4, '0')}`,
      actualCount: item.actualCount ?? item.joinedCount ?? 0,
      expectedCount: item.expectedCount ?? item.totalCount ?? item.maxParticipants ?? '-',
      courseId: item.courseId,
      courseName: item.courseName
    }))

    pagination.total = result.total || 0

    // 计算统计数据
    statsData.activeCourses = new Set(examList.value.map(e => e.courseId)).size || 1
    statsData.ongoingExams = examList.value.filter(e => e.status === 'active').length
    statsData.todayParticipants = examList.value.reduce((sum, e) => sum + (e.actualCount || 0), 0)
    statsData.pendingGrading = 15 // 这个可能需要从后端获取
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

function openCreateDrawer() {
  if (!canManageExam.value) return
  resetForm()
  editingKind.value = activeKind.value
  if (activeKind.value === 'training' && routeTrainingId.value) {
    form.trainingId = routeTrainingId.value
  }
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
      form.passingScore = resolvePassingScoreSuggestion(detail)
    }
  } catch (error) {
    selectedPaperDetail.value = null
  }
}

function resolvePassingScoreSuggestion(detail) {
  const totalScore = Number(detail?.totalScore || 0)
  if (!Number.isFinite(totalScore) || totalScore <= 0) {
    return 0
  }
  const configuredPassingScore = Number(detail?.passingScore)
  if (Number.isFinite(configuredPassingScore) && configuredPassingScore > 0 && configuredPassingScore <= totalScore) {
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
  resetForm()
  loadExams()
}

onMounted(() => {
  loadExams()
  loadTrainingOptions()
  loadPaperOptions()
})
</script>

<style scoped>
.exam-manage-page {
  min-height: 100vh;
  background-color: #F8FAFC;
  display: flex;
  flex-direction: column;
}

.content-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 32px 40px 0;
}

.page-title-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 32px;
  gap: 16px;
}

.page-title {
  font-size: 30px;
  font-weight: 600;
  color: #1E293B;
  margin: 0;
  letter-spacing: -0.02em;
}

.page-subtitle {
  margin: 8px 0 0;
  font-size: 14px;
  color: #64748B;
  line-height: 1.6;
}

.publish-btn {
  height: 40px;
  padding: 0 24px;
  font-weight: 500;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.main-container {
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 32px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 数据汇总条 */
.stats-bar {
  display: flex;
  align-items: center;
  padding: 40px 48px;
  border-bottom: 1px solid #F1F5F9;
  background: linear-gradient(to bottom, #F8FAFC, white);
}

.stat-item {
  flex: 1;
  padding: 0 8px;
}

.stat-divider {
  border-left: 1px solid #F1F5F9;
}

.stat-label {
  font-size: 10px;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 4px;
}

.stat-label-green { color: #22C55E; }
.stat-label-blue { color: #3B82F6; }
.stat-label-amber { color: #F59E0B; }

.stat-value {
  font-size: 36px;
  font-weight: 700;
  color: #1E293B;
}

.stat-value-green { color: #16A34A; }
.stat-value-blue { color: #2563EB; }
.stat-value-amber { color: #D97706; }

.stat-unit {
  font-size: 12px;
  font-weight: 400;
  color: #CBD5E1;
  margin-left: 4px;
}

/* 过滤条 */
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 48px;
  border-bottom: 1px solid #F1F5F9;
}

.filter-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.search-input {
  width: 320px;
}

.status-select {
  width: 160px;
}

.kind-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 0;
}

.kind-tabs :deep(.ant-tabs-tab) {
  padding: 8px 0;
  font-size: 14px;
  font-weight: 500;
}

/* 列表容器 */
.list-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* 列表头 */
.list-header {
  display: flex;
  align-items: center;
  padding: 12px 48px;
  background: #F8FAFC;
  border-bottom: 1px solid #F1F5F9;
  font-size: 10px;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.col-course { width: 288px; }
.col-paper { flex: 1; }
.col-status { width: 112px; }
.col-count { width: 96px; }
.col-time { width: 192px; }
.col-action { width: 128px; }

/* 课程分组 */
.course-group {
  border-bottom: 1px solid #F1F5F9;
}

.course-row {
  display: flex;
  align-items: center;
  padding: 20px 48px;
  background: white;
  cursor: pointer;
  transition: background-color 0.15s;
}

.course-row:hover {
  background: #F8FAFC;
}

.course-row > div {
  display: flex;
  align-items: center;
}

.chevron-icon {
  width: 16px;
  height: 16px;
  color: #CBD5E1;
  margin-right: 12px;
  transition: transform 0.3s ease;
}

.chevron-icon.rotated {
  transform: rotate(-90deg);
}

.course-row:hover .chevron-icon {
  color: #3B82F6;
}

.course-icon {
  width: 16px;
  height: 16px;
  color: #3B82F6;
  margin-right: 8px;
}

.course-name {
  font-size: 14px;
  font-weight: 700;
  color: #334155;
}

.course-detail-hint {
  font-size: 10px;
  font-weight: 600;
  color: #3B82F6;
  background: #EFF6FF;
  padding: 2px 8px;
  border-radius: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.course-row:hover .course-detail-hint {
  opacity: 1;
}

/* 考试场次列表 */
.exam-items {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 2000px;
  opacity: 1;
  overflow: hidden;
}

.exam-items.is-collapsed {
  max-height: 0;
  opacity: 0;
}

.exam-row {
  display: flex;
  align-items: center;
  padding: 20px 48px;
  border-top: 1px solid #FAFAFA;
  transition: background-color 0.15s;
}

.exam-row:hover {
  background: #F8FAFC;
}

.exam-row > div {
  display: flex;
  align-items: center;
}

.exam-title {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.exam-id {
  font-size: 10px;
  color: #94A3B8;
  font-family: monospace;
  margin-top: 2px;
}

.paper-status-badge {
  font-size: 10px;
  font-weight: 600;
  color: #3B82F6;
  background: #EFF6FF;
  padding: 1px 4px;
  border-radius: 2px;
  margin-top: 4px;
  width: fit-content;
}

/* 状态标签 */
.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-upcoming,
.status-pending {
  background: #FEF3C7;
  color: #92400E;
}

.status-active,
.status-ongoing {
  background: #DCFCE7;
  color: #166534;
}

.status-ended {
  background: #F1F5F9;
  color: #64748B;
}

/* 操作按钮 */
.action-btn {
  padding: 0;
  height: auto;
  font-size: 14px;
  font-weight: 600;
}

.action-btn-secondary {
  padding: 0;
  height: auto;
  font-size: 14px;
  color: #CBD5E1;
}

.action-btn-secondary:hover {
  color: #64748B;
}

/* 空状态 */
.empty-state {
  padding: 80px 0;
  text-align: center;
  color: #94A3B8;
}

.empty-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
}

/* 分页 */
.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 48px;
  border-top: 1px solid #F1F5F9;
  background: white;
}

.pagination-info {
  font-size: 10px;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.page-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #64748B;
  background: white;
}

.page-btn:hover:not(:disabled) {
  background: #F8FAFC;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-btn-active {
  background: #2563EB !important;
  color: white !important;
  border-color: #2563EB !important;
}

/* 脚部 */
.footer-bar {
  margin-top: 32px;
  padding: 0 16px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 10px;
  font-weight: 500;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* 抽屉内样式 */
.paper-action-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
}

.paper-action-tip {
  font-size: 12px;
  color: #8c8c8c;
}

.passing-score-field {
  display: flex;
  align-items: center;
  gap: 10px;
}

.passing-score-total {
  flex-shrink: 0;
  font-size: 12px;
  color: #8c8c8c;
  white-space: nowrap;
}

.paper-preview-card {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 12px;
  background: #fafafa;
}

.preview-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
}

.preview-title {
  font-size: 15px;
  font-weight: 600;
  color: #001234;
}

.preview-sub {
  margin-top: 4px;
  font-size: 12px;
  color: #8c8c8c;
}

.preview-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #666;
}

.preview-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 320px;
  overflow-y: auto;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
}

.preview-content {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
