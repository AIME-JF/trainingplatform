<template>
  <div class="exam-manage-page">
    <!-- 主体内容 -->
    <main class="main-content">
      <div class="content-wrapper">

        <!-- 1. 二级导航与快捷操作入口 -->
        <div class="sub-nav-bar">
          <div class="sub-nav-left">
            <span :class="['sub-nav-item', { active: activeNav === 'exam' }]" @click="activeNav = 'exam'">考试中心</span>
          </div>
        </div>

        <!-- 2. 统一的大边框容器 -->
        <div class="main-container">

          <!-- 第一层：操作与搜索过滤 -->
          <div class="toolbar-row">
            <div class="toolbar-left">
              <a-dropdown>
                <button class="btn-primary">
                  {{ createExamType === 'admission' ? '添加准入考试' : '添加培训班考试' }}
                  <svg style="width:12px;height:12px;margin-left:4px" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"/></svg>
                </button>
                <template #overlay>
                  <a-menu @click="({ key }) => { createExamType = key; openCreateDrawer() }">
                    <a-menu-item key="admission">添加准入考试</a-menu-item>
                    <a-menu-item key="training">添加培训班考试</a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
              <div class="search-wrapper">
                <svg class="search-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                <a-input-search v-model:value="searchText" placeholder="请输入关键字搜索..." allow-clear @search="handleSearch" class="search-input" />
              </div>
            </div>

            <div class="toolbar-right">
              <select v-model="filterExamType" class="input-minimal filter-select">
                <option value="admission">准入考试</option>
                <option value="training">培训班考试</option>
              </select>
              <select v-model="filterStatusSelect" class="input-minimal filter-select-sm">
                <option value="">全部</option>
                <option value="upcoming">未开始</option>
                <option value="active">进行中</option>
                <option value="ended">已结束</option>
                <option value="draft">草稿</option>
              </select>
            </div>
          </div>

          <!-- 第二层：状态与评分切换 -->
          <div class="filter-row">
            <div class="filter-left">
              <span class="filter-label">状态:</span>
              <div class="status-tabs">
                <span v-for="tab in statusTabs" :key="tab.value" :class="['status-tab', { active: currentStatusTab === tab.value }]" @click="switchStatusTab(tab.value)">{{ tab.label }}</span>
              </div>
            </div>
          </div>

          <!-- 第三层：表格数据 -->
          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th class="col-check">
                    <a-checkbox v-model:checked="selectAll" @change="handleSelectAll" />
                  </th>
                  <th class="col-index">序号</th>
                  <th class="col-name">考试名称</th>
                  <th class="col-count text-center">考试人员</th>
                  <th class="col-time text-center">考试开放时间</th>
                  <th class="col-status text-center">状态</th>
                  <th class="col-paper">所用试卷</th>
                  <th class="col-type text-center">类型</th>
                  <th class="col-category text-center">分类</th>
                  <th class="col-training text-center">关联班级</th>
                  <th class="col-action text-right">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-50">
                <tr v-for="(exam, idx) in examList" :key="exam.id" class="table-row">
                  <td class="col-check">
                    <a-checkbox :checked="selectedIds.includes(exam.id)" @change="toggleSelect(exam.id, $event)" />
                  </td>
                  <td class="col-index text-slate-400">{{ (pagination.current - 1) * pagination.pageSize + idx + 1 }}</td>
                  <td class="col-name">
                    <div class="name-cell">
                      <span class="name-text" @click="openEditDrawer(exam)">{{ exam.title }}</span>
                      <svg v-if="exam.relatedTrainingId" class="link-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>
                    </div>
                  </td>
                  <td class="col-count text-center">
                    <span class="count-actual" :class="{ 'has-data': exam.actualCount > 0 }">{{ exam.actualCount ?? 0 }}</span>
                    <span class="count-sep">/</span>
                    <span class="count-total">{{ exam.expectedCount ?? '-' }}</span>
                  </td>
                  <td class="col-time text-center">
                    <div v-if="exam.startTime && exam.endTime" class="time-cell">
                      <div class="time-text">{{ formatDateTime(exam.startTime) }}</div>
                      <div class="time-text">{{ formatDateTime(exam.endTime) }}</div>
                    </div>
                    <div v-else class="time-placeholder">~</div>
                  </td>
                  <td class="col-status text-center">
                    <span class="status-pill" :class="getStatusPillClass(exam.status)">{{ statusLabels[exam.status] || exam.status }}</span>
                  </td>
                  <td class="col-paper">
                    <span class="paper-link" @click="goToPaperDetail(exam.paperId)">{{ exam.paperTitle || '-' }}</span>
                  </td>
                  <td class="col-type text-center text-slate-600">{{ exam.type === 'formal' ? '线上' : '测验' }}</td>
                  <td class="col-category text-center text-slate-600">{{ exam.courseNames?.length ? exam.courseNames.join('、') : (exam.courseName || '默认分类') }}</td>
                  <td class="col-training text-center text-slate-600">{{ exam.training_name || '-' }}</td>
                  <td class="col-action text-right">
                    <button class="btn-action" @click.stop="openEditDrawer(exam)">
                      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 12h.01M12 12h.01M19 12h.01"/></svg>
                    </button>
                  </td>
                </tr>

                <!-- 空状态 -->
                <tr v-if="!loading && examList.length === 0">
                  <td colspan="11" class="empty-cell">
                    <div class="empty-content">
                      <svg class="empty-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
                      <span class="empty-text">暂无考试记录</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 第四层：说明与批量操作 -->
          <div class="footer-area">
            <!-- 说明文字 -->
            <div class="notice-area">
              <svg class="notice-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>
              <div class="notice-text">
                <p>说明：此图标表示该考试为关联培训或关联课程考试，培训或课程中添加的考试，请在培训或课程中进行修改或删除操作。</p>
              </div>
            </div>

            <div class="footer-divider"></div>

            <!-- 批量操作与分页 -->
            <div class="footer-actions">
              <div class="footer-left">
                <label class="checkbox-label">
                  <a-checkbox v-model:checked="selectAll" @change="handleSelectAll" />
                  <span>全选</span>
                </label>
                <div class="batch-ops">
                  <span class="batch-label">批量操作:</span>
                  <button class="btn-batch btn-batch-danger" @click="handleBatchDelete">删除</button>
                </div>
              </div>

              <div class="footer-right">
                <div class="page-info">
                  共 {{ pagination.total }} 条记录 <span class="page-sep">|</span> 每页 {{ pagination.pageSize }} 条
                </div>
                <div class="pagination-btns">
                  <button class="page-btn" :class="{ disabled: pagination.current === 1 }" :disabled="pagination.current === 1" @click="handlePageChange(pagination.current - 1)">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/></svg>
                  </button>
                  <button v-for="page in visiblePages" :key="page" class="page-btn" :class="{ 'page-btn-active': page === pagination.current }" @click="handlePageChange(page)">{{ page }}</button>
                  <button class="page-btn" :class="{ disabled: pagination.current === totalPages }" :disabled="pagination.current === totalPages" @click="handlePageChange(pagination.current + 1)">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/></svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

        </div>

      </div>
    </main>

    <!-- 抽屉 -->
    <a-drawer v-model:open="drawerVisible" :title="drawerTitle" width="760" @close="resetForm">
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="24">
            <a-form-item label="场次名称" required>
              <a-input v-model:value="form.title" placeholder="请输入考试场次名称" />
            </a-form-item>
          </a-col>
          <a-col :span="18">
            <a-form-item label="关联试卷" required>
              <a-select v-model:value="form.paperId" placeholder="请选择已发布试卷" :disabled="isEdit" show-search option-filter-prop="label" @change="handlePaperChange" :options="availablePaperOptions.map(p => ({ value: p.id, label: p.title }))" />
              <div class="paper-hint">
                <span class="hint-text">考试只能选择已发布试卷；考试创建后不能再更换试卷</span>
                <a-button type="link" size="small" @click="goToPaperManage">去试卷管理创建试卷</a-button>
              </div>
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
                <a-select-option value="upcoming">未开始</a-select-option>
                <a-select-option value="active">进行中</a-select-option>
                <a-select-option value="ended">已结束</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="适用范围">
              <AdmissionScopeSelector v-model:scope-type="form.scopeType" v-model:scope-target-ids="form.scopeTargetIds" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="考试时间">
              <a-range-picker v-model:value="dateRange" show-time format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="考试时长（分钟）">
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
          <a-col :span="24">
            <a-form-item label="考试说明">
              <a-textarea v-model:value="form.description" :rows="3" placeholder="选填" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="试卷预览">
              <div class="paper-preview">
                <template v-if="selectedPaperDetail">
                  <div class="preview-header">
                    <div>
                      <div class="preview-title">{{ selectedPaperDetail.title }}</div>
                      <div class="preview-meta">{{ paperStatusLabels[selectedPaperDetail.status] }} · {{ selectedPaperDetail.questionCount || 0 }} 题 · {{ selectedPaperDetail.totalScore || 0 }} 分</div>
                    </div>
                    <div class="preview-stats">
                      <span>时长 {{ selectedPaperDetail.duration || 60 }} 分钟</span>
                      <span>及格 {{ selectedPaperDetail.passingScore || 60 }} 分</span>
                    </div>
                  </div>
                  <div v-if="selectedPaperDetail.questions?.length" class="preview-questions">
                    <div v-for="(item, qi) in selectedPaperDetail.questions.slice(0, 20)" :key="item.id || qi" class="question-item">
                      <span class="question-num">{{ qi + 1 }}.</span>
                      <span class="question-type">[{{ questionTypeLabels[item.type] || item.type }}]</span>
                      <span class="question-content">{{ item.content }}</span>
                      <span class="question-score">{{ item.score || 0 }}分</span>
                    </div>
                    <div v-if="selectedPaperDetail.questions.length > 20" class="more-questions">还有 {{ selectedPaperDetail.questions.length - 20 }} 道题目...</div>
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
          <a-button type="primary" :loading="submitting" @click="handleSave">保存</a-button>
        </a-space>
      </template>
    </a-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  createExam, createAdmissionExam,
  deleteAdmissionExam, deleteExam,
  getExamDetail, getExamPaperDetail, getExamPapers, getExams,
  getAdmissionExamDetail, getAdmissionExams,
  updateExam, updateAdmissionExam,
} from '@/api/exam'
import { getCourses } from '@/api/course'
import AdmissionScopeSelector from './components/AdmissionScopeSelector.vue'

const router = useRouter()
const authStore = useAuthStore()

const statusLabels = { upcoming: '未开始', active: '进行中', ended: '已结束', draft: '草稿' }
const paperStatusLabels = { draft: '草稿', published: '已发布', archived: '已归档' }
const questionTypeLabels = { single: '单选', multi: '多选', judge: '判断' }

const activeNav = ref('exam')

const statusTabs = [
  { label: '全部', value: 'all' },
  { label: '进行中', value: 'active' },
  { label: '未开始', value: 'upcoming' },
  { label: '已结束', value: 'ended' },
  { label: '草稿', value: 'draft' },
]

const loading = ref(false)
const submitting = ref(false)
const searchText = ref('')
const filterExamType = ref('admission')
const createExamType = ref('admission')
const filterStatusSelect = ref('')
const currentStatusTab = ref('all')
const examList = ref([])
const selectedIds = ref([])
const paperOptions = ref([])
const courseOptions = ref([])
const selectedPaperDetail = ref(null)
const drawerVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const dateRange = ref(null)
const selectAll = ref(false)

const pagination = reactive({ current: 1, pageSize: 15, total: 0 })

const form = reactive({
  title: '', paperId: undefined, description: '',
  type: 'formal', status: 'upcoming',
  scopeType: 'all', scopeTargetIds: [],
  duration: 60, passingScore: 60, maxAttempts: 1,
})

const drawerTitle = computed(() => isEdit.value ? '编辑考试' : '添加考试')
const availablePaperOptions = computed(() => isEdit.value ? paperOptions.value : paperOptions.value.filter(i => i.status === 'published'))
const totalPages = computed(() => Math.max(1, Math.ceil(pagination.total / pagination.pageSize)))
const visiblePages = computed(() => {
  const pages = [], total = totalPages.value, cur = pagination.current
  let start = Math.max(1, cur - 2), end = Math.min(total, start + 4)
  if (end - start < 4) start = Math.max(1, end - 4)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

function getStatusPillClass(status) {
  return { upcoming: 'status-pending', active: 'status-ongoing', ended: 'status-ended', draft: 'status-pending' }[status] || 'status-pending'
}

function switchStatusTab(tab) {
  currentStatusTab.value = tab
  filterStatusSelect.value = tab === 'all' ? '' : tab
  pagination.current = 1
  loadExams()
}

function handleSearch() { pagination.current = 1; loadExams() }
function handlePageChange(page) { if (page < 1 || page > totalPages.value) return; pagination.current = page; loadExams() }

function toggleSelect(id, e) {
  if (e.target.checked) { if (!selectedIds.value.includes(id)) selectedIds.value.push(id) }
  else { selectedIds.value = selectedIds.value.filter(i => i !== id) }
  selectAll.value = selectedIds.value.length === examList.value.length && examList.value.length > 0
}

function handleSelectAll(e) {
  if (e.target.checked) { selectedIds.value = examList.value.map(ex => ex.id); selectAll.value = true }
  else { selectedIds.value = []; selectAll.value = false }
}

async function loadExams() {
  loading.value = true
  try {
    const params = { page: pagination.current, size: pagination.pageSize, search: searchText.value || undefined, status: filterStatusSelect.value || undefined }
    const result = filterExamType.value === 'admission' ? await getAdmissionExams(params) : await getExams(params)
    examList.value = (result.items || []).map(item => ({
      ...item,
      code: item.code || 'EXAM-' + String(item.id).padStart(4, '0'),
      actualCount: item.actualCount ?? item.joinedCount ?? 0,
      expectedCount: item.expectedCount ?? item.totalCount ?? item.maxParticipants ?? '-',
      relatedTrainingId: item.trainingId,
    }))
    pagination.total = result.total || 0
    selectedIds.value = []; selectAll.value = false
  } catch (e) { message.error(e.message || '加载考试列表失败') }
  finally { loading.value = false }
}

async function loadPaperOptions() {
  try { const r = await getExamPapers({ size: -1 }); paperOptions.value = r.items || [] }
  catch { paperOptions.value = [] }
}

async function loadCourseOptions() {
  try {
    const result = await getCourses({ size: -1 })
    courseOptions.value = (result.items || []).map(item => ({
      value: item.id,
      label: item.title,
    }))
  } catch {
    courseOptions.value = []
  }
}

async function setPaperPreview(paperId, applyDefaults = false) {
  if (!paperId) { selectedPaperDetail.value = null; return }
  try {
    const detail = await getExamPaperDetail(paperId)
    selectedPaperDetail.value = detail
    if (applyDefaults) {
      form.type = detail.type || 'formal'
      form.duration = Math.min(300, Math.max(10, Math.floor(Number(detail.duration) || 60)))
      const totalScore = Number(detail?.totalScore || 0)
      const cfg = Number(detail?.passingScore)
      form.passingScore = (Number.isFinite(cfg) && cfg > 0 && cfg <= totalScore) ? cfg : Math.max(1, Math.ceil(totalScore * 0.6))
    }
  } catch { selectedPaperDetail.value = null }
}

function handlePaperChange(val) { setPaperPreview(val, !isEdit.value) }
function openCreateDrawer() {
  resetForm()
  drawerVisible.value = true
}

async function openEditDrawer(record) {
  isEdit.value = true; editingId.value = record.id
  try {
    const detail = (filterExamType.value === 'admission' || record.kind === 'admission')
      ? await getAdmissionExamDetail(record.id) : await getExamDetail(record.id)
    form.title = detail.title
    form.paperId = detail.paperId
    form.description = detail.description || ''
    form.type = detail.type || 'formal'
    form.status = detail.status || 'upcoming'
    form.scopeType = detail.scopeType || 'all'
    form.scopeTargetIds = [...(detail.scopeTargetIds || [])]
    form.courseIds = [...(detail.courseIds || [])]
    form.duration = detail.duration || 60
    form.passingScore = detail.passingScore || 60
    form.maxAttempts = detail.maxAttempts || 1
    dateRange.value = detail.startTime && detail.endTime ? [detail.startTime, detail.endTime] : null
    selectedPaperDetail.value = {
      id: detail.paperId, title: detail.paperTitle || '未命名试卷',
      status: detail.paperStatus, duration: detail.duration, totalScore: detail.totalScore,
      passingScore: detail.passingScore, questionCount: detail.questionCount,
      questions: detail.questions || [],
    }
    drawerVisible.value = true
  } catch (e) { message.error(e.message || '加载详情失败') }
}

function resetForm() {
  Object.assign(form, { title: '', paperId: undefined, description: '', type: 'formal', status: 'upcoming', scopeType: 'all', scopeTargetIds: [], duration: 60, passingScore: 60, maxAttempts: 1 })
  selectedPaperDetail.value = null; drawerVisible.value = false; isEdit.value = false; editingId.value = null; dateRange.value = null
}

async function handleSave() {
  if (!form.title.trim()) { message.warning('请输入场次名称'); return }
  if (!form.paperId) { message.warning('请选择试卷'); return }
  if (form.scopeType !== 'all' && !form.scopeTargetIds.length) { message.warning('请选择适用范围'); return }
  const dur = Number(form.duration), ps = Number(form.passingScore)
  if (!Number.isFinite(dur) || dur < 10) { message.warning('考试时长不能少于10分钟'); return }
  if (!Number.isFinite(ps) || ps < 1) { message.warning('及格分不能小于1分'); return }
  if (selectedPaperDetail.value && ps > selectedPaperDetail.value.totalScore) { message.warning('及格分不能超过试卷满分'); return }
  const payload = { title: form.title, paperId: form.paperId, description: form.description || undefined, type: form.type, status: form.status, duration: dur, passingScore: ps, startTime: dateRange.value?.[0], endTime: dateRange.value?.[1], maxAttempts: form.maxAttempts, scopeType: form.scopeType, scopeTargetIds: form.scopeTargetIds }
  submitting.value = true
  try {
    if (isEdit.value) {
      filterExamType.value === 'admission' ? await updateAdmissionExam(editingId.value, payload) : await updateExam(editingId.value, payload)
      message.success('考试已更新')
    } else {
      createExamType.value === 'admission' ? await createAdmissionExam(payload) : await createExam(payload)
      message.success('考试已添加')
    }
    resetForm(); loadExams()
  } catch (e) { message.error(e.message || '保存失败') }
  finally { submitting.value = false }
}

async function handleBatchDelete() {
  if (!selectedIds.value.length) return
  Modal.confirm({
    title: `确定删除选中的 ${selectedIds.value.length} 场考试吗？`,
    content: '已有作答记录或已关联培训班的考试不能删除。',
    okText: '确定删除',
    okType: 'danger',
    async onOk() {
      let successCount = 0
      let failCount = 0
      for (const id of selectedIds.value) {
        const exam = examList.value.find(item => item.id === id)
        if (!exam) continue
        try {
          if ((exam.kind || filterExamType.value) === 'admission') {
            await deleteAdmissionExam(id)
          } else {
            await deleteExam(id)
          }
          successCount += 1
        } catch {
          failCount += 1
        }
      }
      selectedIds.value = []
      await loadExams()
      if (failCount === 0) {
        message.success(`成功删除 ${successCount} 场考试`)
      } else {
        message.warning(`成功删除 ${successCount} 场，${failCount} 场删除失败`)
      }
    },
  })
}

function goToPaperManage() { router.push({ path: '/paper/repository' }) }
function goToPaperDetail(id) { if (id) router.push({ path: `/paper/repository/${id}` }) }
function formatDateTime(v) { return v ? String(v).replace('T', ' ').slice(0, 16) : '未设置' }

watch(filterExamType, () => { pagination.current = 1; loadExams() })
watch(filterStatusSelect, val => { currentStatusTab.value = val || 'all' })
onMounted(() => { loadExams(); loadPaperOptions() })
</script>

<style scoped>
.exam-manage-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f8fafc;
  color: #334155;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}

.content-wrapper {
  max-width: 100%;
  width: 100%;
}

.sub-nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.sub-nav-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.sub-nav-item {
  font-size: 14px;
  font-weight: 600;
  color: #94a3b8;
  padding-bottom: 8px;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  cursor: pointer;
}

.sub-nav-item:hover {
  color: #64748b;
}

.sub-nav-item.active {
  color: #1e293b;
  border-color: #2563eb;
}

.sub-nav-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-aux {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background-color: #ffffff;
  transition: all 0.2s;
  cursor: pointer;
}

.btn-aux:hover {
  border-color: #cbd5e1;
  background-color: #f8fafc;
  color: #1e293b;
}

.main-container {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 640px;
}

.toolbar-row {
  padding: 24px 32px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  justify-content: space-between;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-primary {
  background: #2563eb;
  color: white;
  font-size: 14px;
  font-weight: 700;
  padding: 8px 24px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 6px rgba(37, 99, 235, 0.1);
}

.btn-primary:hover {
  background: #1d4ed8;
}

.search-wrapper {
  position: relative;
  width: 280px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 10px;
  width: 16px;
  height: 16px;
  color: #94a3b8;
  pointer-events: none;
  z-index: 2;
}

.input-minimal {
  background-color: transparent;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 12px;
  color: #1e293b;
  transition: all 0.2s;
  outline: none;
  height: 36px;
}

.input-minimal:hover {
  border-color: #cbd5e1;
}

.filter-select {
  width: 140px;
}

.filter-select-sm {
  width: 120px;
}

.filter-row {
  padding: 12px 32px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(248, 250, 252, 0.35);
}

.filter-left,
.filter-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-label {
  font-size: 12px;
  font-weight: 700;
  color: #94a3b8;
}

.status-tabs {
  display: flex;
  gap: 4px;
  padding: 2px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
}

.status-tab {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.status-tab:hover {
  color: #334155;
}

.status-tab.active {
  background: white;
  color: #2563eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.grade-filter {
  display: flex;
  align-items: center;
  gap: 10px;
}

.grade-link {
  font-size: 12px;
  color: #64748b;
  cursor: pointer;
}

.grade-link:hover {
  color: #2563eb;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 12px;
  color: #64748b;
}

.table-wrapper {
  flex: 1;
  overflow-x: auto;
}

.data-table {
  width: 100%;
  text-align: left;
  border-collapse: collapse;
  table-layout: fixed;
}

.data-table thead tr {
  background: #f8fafc;
  border-bottom: 1px solid #f1f5f9;
}

.data-table th {
  padding: 16px;
  font-size: 10px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.data-table td {
  padding: 16px;
  vertical-align: middle;
}

.table-row {
  border-bottom: 1px solid #f8fafc;
}

.table-row:hover {
  background-color: #f8fafc;
}

.text-center {
  text-align: center;
}

.text-right {
  text-align: right;
}

.col-check { width: 46px; }
.col-index { width: 56px; }
.col-name { width: 260px; }
.col-count { width: 110px; }
.col-time { width: 160px; }
.col-status { width: 92px; }
.col-paper { width: 180px; }
.col-type { width: 72px; }
.col-category { width: 88px; }
.col-training { width: 100px; }
.col-action { width: 72px; }

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-text {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
}

.name-text:hover {
  color: #2563eb;
}

.link-icon {
  width: 14px;
  height: 14px;
  color: #ef4444;
}

.count-actual { font-size: 13px; color: #94a3b8; font-weight: 700; }
.count-actual.has-data { color: #ef4444; }
.count-sep { margin: 0 4px; color: #cbd5e1; }
.count-total { font-size: 13px; color: #94a3b8; }

.time-cell {
  font-size: 11px;
  color: #94a3b8;
  line-height: 1.4;
}

.time-text { white-space: nowrap; }
.time-placeholder { color: #94a3b8; }

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 600;
}

.status-ongoing { background-color: #dcfce7; color: #166534; }
.status-pending { background-color: #fef3c7; color: #92400e; }
.status-ended { background-color: #f1f5f9; color: #64748b; }

.paper-link {
  color: #ef4444;
  font-size: 12px;
  cursor: pointer;
}

.paper-link:hover {
  text-decoration: underline;
}

.btn-action {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
}

.btn-action:hover {
  color: #334155;
}

.empty-cell {
  text-align: center;
  padding: 64px 0;
}

.empty-content {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.empty-icon {
  width: 44px;
  height: 44px;
  color: #cbd5e1;
}

.empty-text {
  color: #94a3b8;
  font-size: 14px;
}

.footer-area {
  padding: 20px 32px;
  border-top: 1px solid #f1f5f9;
  background: rgba(248, 250, 252, 0.1);
}

.notice-area {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.notice-icon {
  width: 16px;
  height: 16px;
  color: #ef4444;
  margin-top: 2px;
}

.notice-text {
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.6;
}

.footer-divider {
  width: 100%;
  height: 1px;
  background: #f1f5f9;
  margin: 16px 0;
}

.footer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-left,
.footer-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.batch-ops {
  display: flex;
  align-items: center;
  gap: 10px;
}

.batch-label {
  font-size: 12px;
  color: #94a3b8;
}

.btn-batch {
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid transparent;
  background: none;
  cursor: pointer;
}

.btn-batch:hover {
  background: #f1f5f9;
}

.btn-batch-danger {
  color: #ef4444;
}

.btn-batch-danger:hover {
  background: #fef2f2;
}

.page-info {
  font-size: 11px;
  color: #94a3b8;
}

.page-sep {
  margin: 0 8px;
  color: #e2e8f0;
}

.pagination-btns {
  display: flex;
  gap: 4px;
}

.page-btn {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  cursor: pointer;
  color: #64748b;
}

.page-btn:hover:not(:disabled) {
  background: #f1f5f9;
}

.page-btn:disabled,
.page-btn.disabled {
  color: #cbd5e1;
  cursor: not-allowed;
}

.page-btn-active {
  background: #1e293b;
  color: white;
  border-color: #1e293b;
}

.page-footer {
  margin-top: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #94a3b8;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
}

.paper-hint {
  margin-top: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hint-text {
  color: #94a3b8;
  font-size: 12px;
}

.paper-preview {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
  padding: 12px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.preview-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.preview-meta {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
}

.preview-stats {
  font-size: 12px;
  color: #64748b;
  display: flex;
  gap: 12px;
}

.preview-questions {
  max-height: 260px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.question-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #ffffff;
  font-size: 12px;
}

.question-num { color: #94a3b8; }
.question-type { color: #2563eb; white-space: nowrap; }
.question-content {
  flex: 1;
  color: #475569;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.question-score { color: #94a3b8; white-space: nowrap; }
.more-questions {
  font-size: 12px;
  color: #94a3b8;
  text-align: center;
  padding-top: 4px;
}

:deep(.search-input .ant-input-group .ant-input) {
  border-radius: 8px;
  border-color: #e2e8f0;
  padding-left: 36px;
  height: 36px;
}

:deep(.search-input .ant-input-group .ant-input:hover),
:deep(.search-input .ant-input-group .ant-input:focus) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
</style>
