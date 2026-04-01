<template>
  <div class="exam-page">
    <main class="main-body">
      <div class="max-w-[1600px] mx-auto w-full">

        <!-- 统一的大边框容器 -->
        <div class="bg-white border border-slate-200 rounded-[24px] shadow-sm overflow-hidden flex flex-col min-h-[600px]">

          <!-- 第一层：操作与核心过滤行 -->
          <div class="px-8 py-6 border-b border-slate-100 flex flex-wrap gap-4 items-center justify-between">
            <div class="flex items-center gap-3">
              <button class="add-btn" @click="openCreateDrawer">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/></svg>
                添加考试
              </button>
              <div class="relative w-64">
                <svg class="absolute left-3 top-2.5 h-4 w-4 text-slate-400 pointer-events-none" style="z-index:1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                <a-input-search v-model:value="searchText" placeholder="请输入关键字搜索..." allow-clear @search="handleSearch" style="width: 100%" />
              </div>
            </div>

            <div class="flex items-center gap-3">
              <a-select v-model:value="filterExamType" placeholder="考试类型" allow-clear style="width: 128px">
                <a-select-option value="admission">准入考试</a-select-option>
                <a-select-option value="training">培训班考试</a-select-option>
              </a-select>
              <a-select v-model:value="filterCategory" placeholder="考试分类 (全部)" allow-clear style="width: 128px">
                <a-select-option value="default">默认分类</a-select-option>
              </a-select>
              <a-select v-model:value="filterStatusSelect" placeholder="全部" allow-clear style="width: 96px">
                <a-select-option value="upcoming">未开始</a-select-option>
                <a-select-option value="active">进行中</a-select-option>
                <a-select-option value="ended">已结束</a-select-option>
              </a-select>
              <a-select v-model:value="filterVisibility" placeholder="可见范围" allow-clear style="width: 128px">
                <a-select-option value="all">全部</a-select-option>
                <a-select-option value="department">本部门</a-select-option>
                <a-select-option value="role">本角色</a-select-option>
              </a-select>
            </div>
          </div>

          <!-- 第二层：状态与评分统计切换 -->
          <div class="px-8 py-3 border-b border-slate-50 flex items-center justify-between bg-slate-50/20">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold text-slate-400 mr-2 uppercase tracking-tight">状态:</span>
              <div class="flex bg-slate-100/50 p-1 rounded-lg border border-slate-200">
                <span v-for="tab in statusTabs" :key="tab.value" :class="['status-tab', { active: currentStatusTab === tab.value }]" @click="switchStatusTab(tab.value)">{{ tab.label }}</span>
              </div>
            </div>
            <div class="flex items-center gap-6">
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold text-slate-400 uppercase tracking-tight">评分:</span>
                <div class="flex gap-4">
                  <span class="text-xs font-medium text-slate-600 hover:text-blue-600 cursor-pointer">待阅卷</span>
                  <span class="text-xs font-medium text-slate-600 hover:text-blue-600 cursor-pointer">待发布成绩</span>
                </div>
              </div>
              <label class="flex items-center gap-2 cursor-pointer group">
                <a-checkbox v-model:checked="onlyMine"></a-checkbox>
                <span class="text-xs font-medium text-slate-500 group-hover:text-slate-800 transition">只看我发布的</span>
              </label>
            </div>
          </div>

          <!-- 第三层：表格数据 -->
          <div class="flex-1 overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-slate-50/50 border-b border-slate-100">
                  <th class="pl-8 pr-4 py-4 w-10">
                    <a-checkbox v-model:checked="selectAll" @change="handleSelectAll" />
                  </th>
                  <th class="px-4 py-4 w-12 text-[10px] font-bold text-slate-400 uppercase">序号</th>
                  <th class="px-4 py-4 min-w-[280px] text-[10px] font-bold text-slate-400 uppercase">考试名称</th>
                  <th class="px-4 py-4 text-[10px] font-bold text-slate-400 uppercase text-center">考试人员</th>
                  <th class="px-4 py-4 text-[10px] font-bold text-slate-400 uppercase text-center">考试开放时间</th>
                  <th class="px-4 py-4 text-[10px] font-bold text-slate-400 uppercase text-center">状态</th>
                  <th class="px-4 py-4 text-[10px] font-bold text-slate-400 uppercase">所用试卷</th>
                  <th class="px-4 py-4 text-[10px] font-bold text-slate-400 uppercase text-center">类型</th>
                  <th class="px-4 py-4 text-[10px] font-bold text-slate-400 uppercase text-center">分类</th>
                  <th class="pr-8 pl-4 py-4 text-[10px] font-bold text-slate-400 uppercase text-right">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-50">
                <tr v-for="(exam, idx) in examList" :key="exam.id" class="table-row group">
                  <td class="pl-8 pr-4 py-5"><a-checkbox :checked="selectedIds.includes(exam.id)" @change="toggleSelect(exam.id, $event)" /></td>
                  <td class="px-4 py-5 text-sm text-slate-400">{{ (pagination.current - 1) * pagination.pageSize + idx + 1 }}</td>
                  <td class="px-4 py-5">
                    <div class="flex items-center gap-2">
                      <span class="text-sm font-semibold text-slate-700 hover:text-blue-600 cursor-pointer transition" @click="openEditDrawer(exam)">{{ exam.title }}</span>
                      <svg v-if="exam.relatedTrainingId" class="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>
                    </div>
                  </td>
                  <td class="px-4 py-5 text-center">
                    <span class="text-sm font-bold" :class="exam.actualCount > 0 ? 'text-red-500' : 'text-slate-400'">{{ exam.actualCount ?? 0 }}</span>
                    <span class="text-slate-300 mx-0.5">/</span>
                    <span class="text-sm text-slate-400">{{ exam.expectedCount ?? '-' }}</span>
                  </td>
                  <td class="px-4 py-5 text-center">
                    <div v-if="exam.startTime && exam.endTime" class="text-[10px] text-slate-400 leading-tight">
                      <div>{{ formatDateTime(exam.startTime) }}</div>
                      <div>{{ formatDateTime(exam.endTime) }}</div>
                    </div>
                    <div v-else class="text-[10px] text-slate-400">~</div>
                  </td>
                  <td class="px-4 py-5 text-center">
                    <span class="status-pill" :class="getStatusPillClass(exam.status)">{{ statusLabels[exam.status] || exam.status }}</span>
                  </td>
                  <td class="px-4 py-5 text-xs text-red-500 font-medium hover:underline cursor-pointer" @click="goToPaperDetail(exam.paperId)">{{ exam.paperTitle || '-' }}</td>
                  <td class="px-4 py-5 text-center text-sm text-slate-600">{{ exam.type === 'formal' ? '线上' : '测验' }}</td>
                  <td class="px-4 py-5 text-center text-sm text-slate-600">{{ exam.courseName || '默认分类' }}</td>
                  <td class="pr-8 pl-4 py-5 text-right">
                    <button class="text-slate-300 hover:text-slate-800 transition" @click.stop="openEditDrawer(exam)">
                      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 12h.01M12 12h.01M19 12h.01"/></svg>
                    </button>
                  </td>
                </tr>

                <!-- 空状态 -->
                <tr v-if="!loading && examList.length === 0">
                  <td colspan="10" class="text-center py-20">
                    <div class="flex flex-col items-center gap-3 text-slate-400">
                      <svg class="w-12 h-12 text-slate-200" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
                      <span class="text-sm">暂无考试记录</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 第四层：批量操作与分页 -->
          <div class="px-8 py-5 border-t border-slate-100 flex items-center justify-between bg-white shrink-0">
            <div class="flex items-center gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <a-checkbox v-model:checked="selectAll" @change="handleSelectAll" />
                <span class="text-sm font-medium text-slate-600">全选</span>
              </label>
              <div class="h-4 w-px bg-slate-200 mx-2"></div>
              <div class="flex items-center gap-3" v-if="selectedIds.length > 0">
                <span class="text-sm text-slate-400">批量操作 <span class="font-bold text-slate-800">{{ selectedIds.length }}</span> 场考试:</span>
                <button class="text-xs font-bold text-blue-600 hover:bg-blue-50 px-2 py-1 rounded transition" @click="handleBatchExport">导出成绩</button>
                <button class="text-xs font-bold text-red-500 hover:bg-red-50 px-2 py-1 rounded transition" @click="handleBatchDelete">删除</button>
              </div>
              <span v-else class="text-sm text-slate-400">请选择要操作的考试</span>
            </div>

            <div class="flex items-center gap-6">
              <div class="text-xs text-slate-400 uppercase font-bold tracking-widest">
                <span class="text-blue-600">{{ pagination.current }}</span> / {{ totalPages }}
                <span class="mx-3 text-slate-200">|</span>
                共 {{ pagination.total }} 条记录
              </div>
              <div class="flex items-center gap-2">
                <div class="flex items-center gap-1">
                  <span class="text-xs text-slate-400">每页</span>
                  <a-select v-model:value="pagination.pageSize" style="width: 80px" @change="handlePageSizeChange">
                    <a-select-option :value="15">15 条</a-select-option>
                    <a-select-option :value="30">30 条</a-select-option>
                    <a-select-option :value="50">50 条</a-select-option>
                  </a-select>
                </div>
                <div class="flex gap-1 ml-4">
                  <button class="w-8 h-8 rounded border border-slate-200 flex items-center justify-center transition" :class="pagination.current === 1 ? 'text-slate-300 cursor-not-allowed' : 'text-slate-400 hover:bg-slate-50'" :disabled="pagination.current === 1" @click="handlePageChange(pagination.current - 1)">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/></svg>
                  </button>
                  <button v-for="page in visiblePages" :key="page" class="w-8 h-8 rounded text-xs font-bold" :class="page === pagination.current ? 'bg-blue-600 text-white border border-blue-600 shadow-sm' : 'border border-slate-200 text-slate-400 hover:bg-slate-50'" @click="handlePageChange(page)">{{ page }}</button>
                  <button class="w-8 h-8 rounded border border-slate-200 flex items-center justify-center text-slate-400 hover:bg-slate-50 transition" :class="pagination.current === totalPages ? 'text-slate-300 cursor-not-allowed' : ''" :disabled="pagination.current === totalPages" @click="handlePageChange(pagination.current + 1)">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/></svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

        </div>

        <!-- 说明信息 -->
        <div class="mt-6 flex items-start gap-2 text-xs text-slate-400 leading-relaxed max-w-3xl px-2">
          <svg class="w-4 h-4 text-red-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>
          <p>说明：此图标表示该考试为关联培训或关联课程考试，培训或课程中添加的考试，请在培训或课程中进行修改或删除操作。</p>
        </div>

        <div class="h-10"></div>
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
              <div class="flex justify-between items-center mt-1">
                <span class="text-xs text-slate-400">考试只能选择已发布试卷；考试创建后不能再更换试卷</span>
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
                  <div class="flex justify-between items-start gap-4 mb-3">
                    <div>
                      <div class="text-sm font-semibold text-slate-800">{{ selectedPaperDetail.title }}</div>
                      <div class="text-xs text-slate-400 mt-0.5">{{ paperStatusLabels[selectedPaperDetail.status] }} · {{ selectedPaperDetail.questionCount || 0 }} 题 · {{ selectedPaperDetail.totalScore || 0 }} 分</div>
                    </div>
                    <div class="flex gap-4 text-xs text-slate-500 shrink-0">
                      <span>时长 {{ selectedPaperDetail.duration || 60 }} 分钟</span>
                      <span>及格 {{ selectedPaperDetail.passingScore || 60 }} 分</span>
                    </div>
                  </div>
                  <div v-if="selectedPaperDetail.questions?.length" class="max-h-64 overflow-y-auto space-y-2">
                    <div v-for="(item, qi) in selectedPaperDetail.questions.slice(0, 20)" :key="item.id || qi" class="flex items-center gap-2 text-xs p-2 bg-white border border-slate-100 rounded">
                      <span class="text-slate-400 shrink-0">{{ qi + 1 }}.</span>
                      <span class="text-blue-600 shrink-0">[{{ questionTypeLabels[item.type] || item.type }}]</span>
                      <span class="flex-1 text-slate-600 truncate">{{ item.content }}</span>
                      <span class="text-slate-400 shrink-0">{{ item.score || 0 }}分</span>
                    </div>
                    <div v-if="selectedPaperDetail.questions.length > 20" class="text-xs text-center text-slate-400 py-1">还有 {{ selectedPaperDetail.questions.length - 20 }} 道题目...</div>
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
  getExamDetail, getExamPaperDetail, getExamPapers, getExams,
  getAdmissionExamDetail, getAdmissionExams,
  updateExam, updateAdmissionExam,
} from '@/api/exam'
import AdmissionScopeSelector from './components/AdmissionScopeSelector.vue'

const router = useRouter()
const authStore = useAuthStore()

const statusLabels = { upcoming: '未开始', active: '进行中', ended: '已结束', draft: '草稿' }
const paperStatusLabels = { draft: '草稿', published: '已发布', archived: '已归档' }
const questionTypeLabels = { single: '单选', multi: '多选', judge: '判断' }

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
const filterExamType = ref(undefined)
const filterCategory = ref(undefined)
const filterStatusSelect = ref(undefined)
const filterVisibility = ref(undefined)
const currentStatusTab = ref('all')
const onlyMine = ref(false)
const examList = ref([])
const selectedIds = ref([])
const paperOptions = ref([])
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
  filterStatusSelect.value = tab === 'all' ? undefined : tab
  pagination.current = 1
  loadExams()
}

function handleSearch() { pagination.current = 1; loadExams() }
function handlePageChange(page) { if (page < 1 || page > totalPages.value) return; pagination.current = page; loadExams() }
function handlePageSizeChange() { pagination.current = 1; loadExams() }

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
    const params = { page: pagination.current, size: pagination.pageSize, search: searchText.value || undefined, status: filterStatusSelect.value !== 'all' ? filterStatusSelect.value : undefined }
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
function openCreateDrawer() { resetForm(); drawerVisible.value = true }

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
      filterExamType.value === 'admission' ? await createAdmissionExam(payload) : await createExam(payload)
      message.success('考试已添加')
    }
    resetForm(); loadExams()
  } catch (e) { message.error(e.message || '保存失败') }
  finally { submitting.value = false }
}

async function handleBatchExport() { if (!selectedIds.value.length) return; message.info(`导出 ${selectedIds.value.length} 场考试（功能开发中）`) }
async function handleBatchDelete() {
  if (!selectedIds.value.length) return
  Modal.confirm({ title: `确定删除选中的 ${selectedIds.value.length} 场考试吗？`, okText: '确定删除', okType: 'danger', onOk() { message.info('功能开发中'); selectedIds.value = [] } })
}

function goToPaperManage() { router.push({ path: '/paper/repository' }) }
function goToPaperDetail(id) { if (id) router.push({ path: `/paper/repository/${id}` }) }
function formatDateTime(v) { return v ? String(v).replace('T', ' ').slice(0, 16) : '未设置' }

watch(filterExamType, () => { pagination.current = 1; loadExams() })
watch(filterStatusSelect, val => { currentStatusTab.value = val || 'all' })
onMounted(() => { loadExams(); loadPaperOptions() })
</script>

<style scoped>
.exam-page {
  min-height: 100vh;
  background-color: #F8FAFC;
  display: flex;
  flex-direction: column;
  width: 100%;
}

/* 主体 */
.main-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  width: 100%;
}

/* 状态切换标签 */
.status-tab {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #64748B;
  border-radius: 0.375rem;
  transition: all 0.2s;
  cursor: pointer;
  user-select: none;
}
.status-tab:hover { background-color: #F1F5F9; color: #1E293B; }
.status-tab.active {
  background-color: #FFFFFF;
  color: #2563EB;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  border: 1px solid #E2E8F0;
}

/* 表格行 */
.table-row {
  transition: background-color 0.2s;
}
.table-row:hover { background-color: #F8FAFC; }

/* 状态 Pill */
.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.125rem 0.625rem;
  border-radius: 9999px;
  font-size: 0.7rem;
  font-weight: 600;
}
.status-ongoing { background-color: #DCFCE7; color: #166534; }
.status-pending { background-color: #FEF3C7; color: #92400E; }
.status-ended { background-color: #F1F5F9; color: #64748B; }

/* 添加按钮 */
.add-btn {
  background: #2563EB;
  color: white;
  font-size: 14px;
  font-weight: 700;
  padding: 8px 20px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.2s;
}
.add-btn:hover { background: #1D4ED8; }
.add-btn:active { transform: scale(0.98); }

/* 试卷预览 */
.paper-preview {
  border: 1px solid #EBEBEB;
  border-radius: 0.5rem;
  padding: 0.75rem;
  background: #FAFAFA;
}

/* 搜索框样式覆盖 */
:deep(.ant-input-search) {
  padding-left: 2.25rem;
}
:deep(.ant-input-search .ant-input-group-addon) {
  left: 0;
}
:deep(.ant-input-search .ant-input) {
  border-radius: 0.5rem;
  border-color: #E2E8F0;
  height: 36px;
  font-size: 0.875rem;
}
:deep(.ant-input-search .ant-input:hover),
:deep(.ant-input-search .ant-input:focus) {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Select 下拉框宽度 */
:deep(.ant-select) {
  font-size: 0.875rem;
}
:deep(.ant-select:not(.ant-select-disabled):hover .ant-select-selector) {
  border-color: #CBD5E1;
}
:deep(.ant-select-focused .ant-select-selector) {
  border-color: #3B82F6 !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}
</style>
