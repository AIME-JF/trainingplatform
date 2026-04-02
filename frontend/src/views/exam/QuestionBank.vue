<template>
  <div class="question-bank-page">
    <!-- 主体内容 -->
    <main class="main-content">
      <div class="content-wrapper">

        <!-- 1. 二级导航与快捷操作入口 -->
        <div class="sub-nav-bar">
          <div class="sub-nav-left">
            <span
              v-if="canManageQuestionBank"
              :class="['sub-nav-item', { active: activeNav === 'bank' }]"
              @click="switchNav('bank')"
            >
              题库中心
            </span>
            <span
              v-if="canManageKnowledgePoints"
              :class="['sub-nav-item', { active: activeNav === 'knowledge' }]"
              @click="switchNav('knowledge')"
            >
              知识点
            </span>
          </div>
        </div>

        <!-- 2. 统一的大边框容器 -->
        <div class="main-container">
          <template v-if="activeNav === 'bank'">

          <!-- 第一层：操作与搜索过滤 -->
          <div class="toolbar-row">
            <template v-if="selectedFolderId">
              <div class="toolbar-left">
                <button class="btn-aux" @click="handleBackToFolders">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
                  返回题库列表
                </button>
                <span class="toolbar-title">{{ selectedFolderName }}（共 {{ questionList.length }} 道题目）</span>
              </div>
              <div class="toolbar-right">
                <!-- 筛选控件 -->
                <a-input-search v-model:value="pickerSearch" placeholder="搜索题干" style="width:180px" allow-clear />
                <a-select v-model:value="pickerKpName" allow-clear show-search placeholder="按知识点" :options="kpSelectOptions" style="width:160px" />
                <a-select v-model:value="pickerType" style="width:120px">
                  <a-select-option value="all">全部题型</a-select-option>
                  <a-select-option value="single">单选题</a-select-option>
                  <a-select-option value="multi">多选题</a-select-option>
                  <a-select-option value="judge">判断题</a-select-option>
                </a-select>
                <div class="divider-v"></div>
                <button v-if="!pickMode" class="btn-primary" @click="enterPickMode">
                  从题库选题
                </button>
                <template v-else>
                  <span class="pick-hint">已选 {{ pickSelectedKeys.length }} 道</span>
                  <button class="btn-aux" @click="exitPickMode">取消</button>
                  <button class="btn-primary" :disabled="pickSelectedKeys.length === 0" @click="confirmPick">加入试卷</button>
                </template>
              </div>
            </template>
            <template v-else>
              <div class="toolbar-left">
                <button class="btn-primary" @click="openCreateFolderModal">
                添加题库
                </button>
                <button v-if="canUseAiQuestion" class="btn-aux" @click="goToAiQuestion">
                  智能出题
                </button>
                <div class="search-wrapper">
                  <svg class="search-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                  <input type="text" class="input-minimal" v-model="searchText" placeholder="请输入关键字搜索..." @input="handleSearch">
                </div>
              </div>
              <div class="toolbar-right">
                <select class="input-minimal filter-select" v-model="filterCategory">
                  <option value="">题库分类 (全部)</option>
                  <option value="default">默认分类</option>
                </select>
                <div class="divider-v"></div>
                <label class="checkbox-label">
                  <input type="checkbox" v-model="filterMyOnly" class="custom-checkbox">
                  <span>只看我发布的</span>
                </label>
              </div>
            </template>
          </div>

          <!-- 第二层：表格数据 -->
          <div class="table-wrapper">
            <!-- 文件夹列表视图 -->
            <table v-if="!selectedFolderId" class="data-table">
              <thead>
                <tr>
                  <th class="col-check">
                    <input type="checkbox" class="custom-checkbox" :checked="isAllSelected" @change="toggleSelectAll">
                  </th>
                  <th class="col-index">序号</th>
                  <th class="col-name">题库名称</th>
                  <th class="col-publisher">发布人</th>
                  <th class="col-category text-center">题库分类</th>
                  <th class="col-paper text-center">试卷数</th>
                  <th class="col-exercise text-center">课后练习数</th>
                  <th class="col-questions text-center">题目数量</th>
                  <th class="col-status text-center">状态</th>
                  <th class="col-time">添加时间</th>
                  <th class="col-action text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in displayedList" :key="item.id" class="table-row">
                  <td class="col-check">
                    <input type="checkbox" class="custom-checkbox" :checked="selectedIds.includes(item.id)" @change="toggleSelect(item.id)">
                  </td>
                  <td class="col-index">{{ (pagination.current - 1) * pagination.pageSize + index + 1 }}</td>
                  <td class="col-name">
                    <span class="name-text" :class="{ 'is-system': item.isSystem }">{{ item.displayName || item.name }}</span>
                    <span v-if="item.isSystem" class="badge-system">System</span>
                  </td>
                  <td class="col-publisher">{{ item.creatorName || '-' }}</td>
                  <td class="col-category text-center">{{ item.category }}</td>
                  <td class="col-paper text-center">{{ item.paperCount }}</td>
                  <td class="col-exercise text-center">{{ item.exerciseCount }}</td>
                  <td class="col-questions text-center">
                    <button class="question-count-btn" @click.stop="handleViewQuestions(item)">{{ item.questionCount }} 题</button>
                  </td>
                  <td class="col-status text-center">
                    <span class="status-text">{{ item.statusText }}</span>
                  </td>
                  <td class="col-time">{{ item.createdAt }}</td>
                  <td class="col-action text-right">
                    <div class="action-btns">
                      <button class="btn-link" @click="handleViewQuestions(item)">查看题目</button>
                      <button class="btn-link" @click="openEditFolderModal(item)" :disabled="item.isSystem">编辑</button>
                      <button class="btn-link btn-link-danger" @click="handleDeleteFolder(item)" :disabled="item.isSystem">删除</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="displayedList.length === 0">
                  <td colspan="11" class="empty-row">暂无数据</td>
                </tr>
              </tbody>
            </table>

            <!-- 文件夹内题目列表视图 -->
            <table v-else class="data-table">
              <thead>
                <tr>
                  <th v-if="pickMode" class="col-check">
                    <input type="checkbox" class="custom-checkbox" :checked="isAllPickSelected" @change="togglePickSelectAll">
                  </th>
                  <th class="col-index">序号</th>
                  <th class="col-type text-center">题型</th>
                  <th class="col-content">题干</th>
                  <th class="col-answer">答案</th>
                  <th class="col-difficulty text-center">难度</th>
                  <th class="col-kp">知识点</th>
                  <th class="col-time">添加时间</th>
                  <th class="col-action text-center">操作</th>
                </tr>
              </thead>
              <tbody v-if="questionLoading">
                <tr>
                  <td :colspan="pickMode ? 9 : 8" class="empty-row">加载中...</td>
                </tr>
              </tbody>
              <tbody v-else>
                <tr v-for="(q, index) in displayedQuestionList" :key="q.id" class="table-row">
                  <td v-if="pickMode" class="col-check">
                    <input type="checkbox" class="custom-checkbox" :checked="pickSelectedKeys.includes(q.id)" @change="togglePickSelect(q.id)">
                  </td>
                  <td class="col-index">{{ (questionPagination.current - 1) * questionPagination.pageSize + index + 1 }}</td>
                  <td class="col-type text-center">
                    <span :class="['tag-pill', typeTagColors[q.type]]">{{ typeLabels[q.type] }}</span>
                  </td>
                  <td class="col-content">
                    <span class="name-text">{{ q.content }}</span>
                    <div v-if="q.options && q.options.length > 0" class="options-preview">
                      <span v-for="opt in q.options.slice(0,4)" :key="opt.key" class="option-tag">{{ opt.key }}. {{ opt.text }}</span>
                    </div>
                  </td>
                  <td class="col-answer">
                    <span class="answer-text">{{ formatAnswer(q) }}</span>
                  </td>
                  <td class="col-difficulty text-center">
                    <span class="difficulty-badge">{{ q.difficulty || 1 }}</span>
                  </td>
                  <td class="col-kp">
                    <span class="kp-text">{{ formatKps(q.knowledgePointNames) }}</span>
                  </td>
                  <td class="col-time">{{ q.createdAt || '-' }}</td>
                  <td class="col-action text-center">
                    <div class="action-btns">
                      <button class="btn-link" @click="handleEditQuestion(q)">编辑</button>
                      <button class="btn-link" @click="handleMoveQuestion(q)">移动</button>
                      <button class="btn-link btn-link-danger" @click="handleDeleteQuestion(q)">删除</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="questionList.length === 0">
                  <td :colspan="pickMode ? 9 : 8" class="empty-row">该题库暂无题目</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 第三层：说明与批量操作 -->
          <div class="footer-area">
            <!-- 说明文字 -->
            <div class="notice-area">
              <svg class="notice-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              <div class="notice-text">
                <p>说明：1.综合题库为默认题库，不支持编辑、删除和导出等操作，请谨慎使用</p>
                <p class="mt-4">2.被用于试卷的题库和关联课后练习的题库不能删除</p>
              </div>
            </div>

            <div class="footer-divider"></div>

            <!-- 批量操作与分页 -->
            <div class="footer-actions">
              <!-- 题库列表视图 -->
              <template v-if="!selectedFolderId">
                <div class="footer-left">
                  <label class="checkbox-label">
                    <input type="checkbox" class="custom-checkbox" :checked="isAllSelected" @change="toggleSelectAll">
                    <span>全选</span>
                  </label>
                  <div class="divider-v"></div>
                  <div class="batch-ops">
                    <span class="batch-label">批量操作:</span>
                    <button class="btn-batch btn-batch-danger" @click="handleBatchDelete">批量删除</button>
                  </div>
                </div>

                <div class="footer-right">
                  <div class="page-size-selector">
                    <span class="page-size-label">每页显示：</span>
                    <select class="page-size-select" :value="pagination.pageSize" @change="handlePageSizeChange(Number($event.target.value))">
                      <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}条</option>
                    </select>
                  </div>
                  <div class="page-info">
                    共 {{ pagination.total }} 条记录
                  </div>
                  <div class="pagination-btns">
                    <button class="page-btn" :disabled="pagination.current <= 1" @click="changePage(pagination.current - 1)">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/></svg>
                    </button>
                    <button v-for="page in visiblePages" :key="page" class="page-btn" :class="{ 'page-btn-active': page === pagination.current }" @click="changePage(page)">{{ page }}</button>
                    <button class="page-btn" :disabled="pagination.current >= totalPages" @click="changePage(pagination.current + 1)">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/></svg>
                    </button>
                  </div>
                </div>
              </template>

              <!-- 题目列表视图 -->
              <template v-else>
                <div class="footer-left">
                  <!-- 空白占位 -->
                </div>

                <div class="footer-right">
                  <div class="page-size-selector">
                    <span class="page-size-label">每页显示：</span>
                    <select class="page-size-select" :value="questionPagination.pageSize" @change="handleQuestionPageSizeChange(Number($event.target.value))">
                      <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}条</option>
                    </select>
                  </div>
                  <div class="page-info">
                    共 {{ questionPagination.total }} 道题目
                  </div>
                  <div class="pagination-btns">
                    <button class="page-btn" :disabled="questionPagination.current <= 1" @click="changeQuestionPage(questionPagination.current - 1)">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/></svg>
                    </button>
                    <button v-for="page in questionVisiblePages" :key="page" class="page-btn" :class="{ 'page-btn-active': page === questionPagination.current }" @click="changeQuestionPage(page)">{{ page }}</button>
                    <button class="page-btn" :disabled="questionPagination.current >= questionTotalPages" @click="changeQuestionPage(questionPagination.current + 1)">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/></svg>
                    </button>
                  </div>
                </div>
              </template>
            </div>
          </div>
          </template>
          <knowledge-point-panel v-else />

        </div>
      </div>
    </main>

    <!-- 新建/编辑题库弹窗 -->
    <a-modal
      v-model:open="folderFormModalVisible"
      :title="editingFolderId ? '编辑题库' : '添加题库'"
      @ok="handleFolderSubmit"
      @cancel="resetFolderFormModal"
      width="520px"
    >
      <a-form :model="folderForm" layout="vertical">
        <a-form-item label="题库名称" :rules="[{ required: true, message: '请输入题库名称' }]">
          <a-input v-model:value="folderForm.name" placeholder="请输入题库名称" :maxlength="100" />
        </a-form-item>
        <a-form-item label="题库分类">
          <a-select v-model:value="folderForm.category" placeholder="请选择分类">
            <a-select-option value="default">默认分类</a-select-option>
            <a-select-option value="criminal">刑事类</a-select-option>
            <a-select-option value="public_security">治安类</a-select-option>
            <a-select-option value="traffic">交通类</a-select-option>
            <a-select-option value="comprehensive">综合类</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="editingFolderId" label="移动到">
          <a-tree-select
            v-model:value="folderForm.parentId"
            :tree-data="folderTreeData"
            placeholder="根目录（不移动）"
            allow-clear
            tree-default-expand-all
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 移动单个题目弹窗 -->
    <a-modal
      v-model:open="moveQuestionModalVisible"
      title="移动题目"
      @ok="handleMoveQuestionConfirm"
    >
      <a-form layout="vertical">
        <a-form-item label="选择目标文件夹">
          <a-select v-model:value="moveQuestionTargetFolderId" placeholder="请选择目标文件夹">
            <a-select-option :value="null">根目录（移出文件夹）</a-select-option>
            <a-select-option v-for="folder in allFolderList" :key="folder.id" :value="folder.id">
              {{ folder.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 新增/编辑题目弹窗 -->
    <question-form-modal
      v-model:open="modalOpen"
      :title="editingQuestion ? '编辑题目' : '新增题目'"
      :question="editingQuestion"
      :police-type-options="policeTypeOptions"
      @submit="handleSubmitQuestion"
    />

  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import { AI_QUESTION_PAGE_PERMISSIONS, KNOWLEDGE_POINT_PAGE_PERMISSIONS, QUESTION_BANK_PAGE_PERMISSIONS } from '@/constants/pagePermissions'
import {
  createQuestion,
  createQuestionFolder,
  deleteQuestion,
  deleteQuestionFolder,
  getQuestions,
  getQuestionFolders,
  moveQuestionToFolder,
  updateQuestion,
  updateQuestionFolder,
} from '@/api/question'
import { getPoliceTypes } from '@/api/user'
import { getKnowledgePoints } from '@/api/knowledgePoint'
import QuestionFormModal from './components/QuestionFormModal.vue'
import KnowledgePointPanel from './components/KnowledgePointPanel.vue'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

// ============ 导航 ============
const activeNav = computed(() => (route.path.startsWith('/question/knowledge-points') ? 'knowledge' : 'bank'))

// ============ 搜索与筛选 ============
const searchText = ref('')
const filterCategory = ref('')
const filterDifficulty = ref('')
const filterMyOnly = ref(false)

const typeLabels = { single: '单选题', multi: '多选题', judge: '判断题', gap: '填空题' }
const typeTagColors = { single: 'tag-blue', multi: 'tag-purple', judge: 'tag-orange', gap: 'tag-cyan' }
const canUseAiQuestion = computed(() => authStore.hasAnyPermission(AI_QUESTION_PAGE_PERMISSIONS))
const canManageQuestionBank = computed(() => authStore.hasAnyPermission([...QUESTION_BANK_PAGE_PERMISSIONS, ...AI_QUESTION_PAGE_PERMISSIONS]))
const canManageKnowledgePoints = computed(() => authStore.hasAnyPermission(KNOWLEDGE_POINT_PAGE_PERMISSIONS))

// ============ 题库列表数据 ============
const loading = ref(false)
const folderList = ref([])
const selectedIds = ref([])

// 文件夹内题目查看模式
const selectedFolderId = ref(null)
const selectedFolderName = ref('')
const questionList = ref([])
const questionLoading = ref(false)

// 题目筛选与选题模式
const pickerSearch = ref('')
const pickerKpName = ref(null)
const pickerType = ref('all')
const kpSelectOptions = ref([])
const pickMode = ref(false)
const pickSelectedKeys = ref([])

// ============ 分页 ============
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })
const pageSizeOptions = [10, 20, 50]
const questionPagination = reactive({ current: 1, pageSize: 20, total: 0 })

// ============ 文件夹管理弹窗 ============
const folderFormModalVisible = ref(false)
const editingFolderId = ref(null)
const folderForm = reactive({ name: '', category: '', parentId: null })
const moveQuestionModalVisible = ref(false)
const moveQuestionTargetFolderId = ref(null)
const currentMovingQuestion = ref(null)

// ============ 题目弹窗 ============
const modalOpen = ref(false)
const editingQuestion = ref(null)
const policeTypeOptions = ref([])

// ============ 计算属性 ============

// 过滤后的题库列表
const filteredList = computed(() => {
  let list = [...folderList.value]

  // 关键字搜索
  if (searchText.value) {
    const keyword = searchText.value.toLowerCase()
    list = list.filter(item => item.name.toLowerCase().includes(keyword) || (item.creatorName || '').toLowerCase().includes(keyword))
  }

  // 只看我发布的
  if (filterMyOnly.value) {
    const currentUserId = authStore.currentUser?.id
    list = list.filter(item => item.createdBy === currentUserId)
  }

  return list
})

// 分页后的展示列表
const displayedList = computed(() => {
  const start = (pagination.current - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return filteredList.value.slice(start, end)
})

// 总页数
const totalPages = computed(() => Math.ceil(pagination.total / pagination.pageSize) || 1)

const visiblePages = computed(() => {
  const pages = [], total = totalPages.value, cur = pagination.current
  let start = Math.max(1, cur - 2), end = Math.min(total, start + 4)
  if (end - start < 4) start = Math.max(1, end - 4)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

// 全选状态
const isAllSelected = computed(() => {
  if (displayedList.value.length === 0) return false
  return displayedList.value.every(item => selectedIds.value.includes(item.id))
})

const allFolderList = computed(() => [...folderList.value])

// 文件夹树形数据（用于选择父文件夹）
const folderTreeData = computed(() => {
  const convert = (folders) => {
    return folders
      .filter(f => f.id !== editingFolderId.value)
      .map(f => ({
        value: f.id,
        label: f.name,
        children: f.children ? convert(f.children) : []
      }))
  }
  return convert(folderList.value)
})

// ============ 方法 ============

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  const pad = n => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function formatAnswer(q) {
  if (q.answer === null || q.answer === undefined) return '-'
  // 判断题答案
  if (q.type === 'judge') {
    return q.answer === true || q.answer === 'true' || q.answer === 1 ? '正确' : '错误'
  }
  // 单选/多选题答案
  if (Array.isArray(q.answer)) {
    return q.answer.join('、')
  }
  return String(q.answer)
}

function flattenFolderTree(folders, depth = 0) {
  let result = []
  for (const folder of folders || []) {
    result.push({ folder, depth })
    if (folder.children && folder.children.length > 0) {
      result = result.concat(flattenFolderTree(folder.children, depth + 1))
    }
  }
  return result
}

function buildBankList(folders) {
  const flattened = flattenFolderTree(folders)
  return flattened.map(({ folder, depth }) => {
    const indent = depth > 0 ? `${'　'.repeat(depth)}└ ` : ''
    const creatorName = folder.created_by_name ?? folder.createdByName
    const category = folder.category ?? '默认分类'
    const paperCount = folder.paper_count ?? folder.paperCount ?? 0
    const exerciseCount = folder.exercise_count ?? folder.exerciseCount ?? 0
    const questionCount = folder.question_count ?? folder.questionCount ?? 0
    const status = folder.status ?? folder.statusText ?? '未使用'
    const createdAt = folder.created_at ?? folder.createdAt
    const createdBy = folder.created_by ?? folder.createdBy
    const parentId = folder.parent_id ?? folder.parentId ?? null

    return {
      id: folder.id,
      name: folder.name,
      displayName: `${indent}${folder.name}`,
      parentId,
      isSystem: folder.name === '综合题库' || folder.is_system,
      creatorName: creatorName || '-',
      category,
      paperCount,
      exerciseCount,
      questionCount,
      statusText: status,
      createdAt: formatDate(createdAt),
      createdBy,
    }
  })
}

async function loadData() {
  loading.value = true
  try {
    const folders = await getQuestionFolders()
    const bankList = buildBankList(folders || [])
    folderList.value = bankList.map(b => ({ ...b, children: [] }))
    pagination.total = bankList.length
  } catch (error) {
    message.error(error.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.current = 1
}

function changePage(page) {
  if (page < 1 || page > totalPages.value) return
  pagination.current = page
}

function changeQuestionPage(page) {
  const total = Math.ceil(questionPagination.total / questionPagination.pageSize) || 1
  if (page < 1 || page > total) return
  questionPagination.current = page
}

function handlePageSizeChange(size) {
  pagination.pageSize = size
  pagination.current = 1
}

function handleQuestionPageSizeChange(size) {
  questionPagination.pageSize = size
  questionPagination.current = 1
}

// 题目列表分页后的展示列表（应用筛选）
const displayedQuestionList = computed(() => {
  let list = questionList.value
  // 搜索题干
  if (pickerSearch.value) {
    const kw = pickerSearch.value.toLowerCase()
    list = list.filter(q => q.content?.toLowerCase().includes(kw))
  }
  // 知识点筛选
  if (pickerKpName.value) {
    list = list.filter(q => {
      const kps = q.knowledgePointNames || []
      return kps.some(kp => String(kp).includes(pickerKpName.value))
    })
  }
  // 题型筛选
  if (pickerType.value !== 'all') {
    list = list.filter(q => q.type === pickerType.value)
  }
  questionPagination.total = list.length
  const start = (questionPagination.current - 1) * questionPagination.pageSize
  const end = start + questionPagination.pageSize
  return list.slice(start, end)
})

const isAllPickSelected = computed(() => {
  return questionList.value.length > 0 && questionList.value.every(q => pickSelectedKeys.value.includes(q.id))
})

// 题目总页数
const questionTotalPages = computed(() => Math.ceil(questionPagination.total / questionPagination.pageSize) || 1)

const questionVisiblePages = computed(() => {
  const pages = [], total = questionTotalPages.value, cur = questionPagination.current
  let start = Math.max(1, cur - 2), end = Math.min(total, start + 4)
  if (end - start < 4) start = Math.max(1, end - 4)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx > -1) {
    selectedIds.value.splice(idx, 1)
  } else {
    selectedIds.value.push(id)
  }
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedIds.value = selectedIds.value.filter(id => !displayedList.value.some(item => item.id === id))
  } else {
    const pageIds = displayedList.value.map(item => item.id)
    const merged = new Set([...selectedIds.value, ...pageIds])
    selectedIds.value = Array.from(merged)
  }
}

function openCreateFolderModal() {
  editingFolderId.value = null
  folderForm.name = ''
  folderForm.category = ''
  folderForm.parentId = null
  folderFormModalVisible.value = true
}

function goToAiQuestion() {
  router.push({ path: '/question/ai' })
}

function switchNav(target) {
  if (target === activeNav.value) return
  if (target === 'knowledge') {
    router.push({ path: '/question/knowledge-points' })
    return
  }
  router.push({ path: '/question/repository' })
}

function openEditFolderModal(folder) {
  editingFolderId.value = folder.id
  folderForm.name = folder.name
  folderForm.category = folder.category === '默认分类' ? '' : folder.category
  folderForm.parentId = folder.parentId
  folderFormModalVisible.value = true
}

function resetFolderFormModal() {
  editingFolderId.value = null
  folderForm.name = ''
  folderForm.category = ''
  folderForm.parentId = null
  folderFormModalVisible.value = false
}

async function handleFolderSubmit() {
  if (!folderForm.name?.trim()) {
    message.warning('请输入题库名称')
    return
  }
  try {
    const payload = {
      name: folderForm.name,
      category: folderForm.category || null,
      parentId: folderForm.parentId,
    }
    if (editingFolderId.value) {
      await updateQuestionFolder(editingFolderId.value, payload)
      message.success('题库已更新')
    } else {
      await createQuestionFolder(payload)
      message.success('题库已创建')
    }
    resetFolderFormModal()
    await loadData()
  } catch (error) {
    message.error(error.message || '操作失败')
  }
}

function handleDeleteFolder(folder) {
  if (folder.isSystem) {
    message.warning('系统题库不能删除')
    return
  }
  Modal.confirm({
    title: '确认删除题库',
    content: `删除后无法恢复，是否删除题库「${folder.name}」？`,
    okType: 'danger',
    async onOk() {
      try {
        await deleteQuestionFolder(folder.id)
        message.success('题库已删除')
        await loadData()
      } catch (error) {
        message.error(error.message || '删除失败')
      }
    },
  })
}

function handleViewQuestions(item) {
  if (item.isSystem) {
    message.info('系统题库暂无题目')
    return
  }
  selectedFolderId.value = item.id
  selectedFolderName.value = item.name
  pickMode.value = false
  pickSelectedKeys.value = []
  pickerSearch.value = ''
  pickerKpName.value = null
  pickerType.value = 'all'
  router.replace({ path: '/question/repository', query: { folderId: item.id } })
  loadQuestionsForFolder(item.id)
  loadKpOptionsForPicker()
}

async function loadQuestionsForFolder(folderId) {
  questionLoading.value = true
  questionList.value = []
  questionPagination.current = 1
  pickerSearch.value = ''
  pickerKpName.value = null
  pickerType.value = 'all'
  try {
    const result = await getQuestions({ folder_id: folderId, recursive: true, size: -1 })
    questionList.value = result.items || result || []
    questionPagination.total = questionList.value.length
  } catch (error) {
    message.error(error.message || '加载题目失败')
  } finally {
    questionLoading.value = false
  }
}

async function loadKpOptionsForPicker() {
  try {
    const result = await getKnowledgePoints({ size: -1 })
    kpSelectOptions.value = (result.items || []).map(kp => ({ label: kp.name, value: kp.name }))
  } catch { kpSelectOptions.value = [] }
}

function enterPickMode() {
  pickMode.value = true
  pickSelectedKeys.value = []
}

function exitPickMode() {
  pickMode.value = false
  pickSelectedKeys.value = []
}

function togglePickSelect(id) {
  const idx = pickSelectedKeys.value.indexOf(id)
  if (idx >= 0) {
    pickSelectedKeys.value.splice(idx, 1)
  } else {
    pickSelectedKeys.value.push(id)
  }
}

function togglePickSelectAll() {
  if (isAllPickSelected.value) {
    pickSelectedKeys.value = []
  } else {
    pickSelectedKeys.value = questionList.value.map(q => q.id)
  }
}

function confirmPick() {
  if (!pickSelectedKeys.value.length) return
  const ids = pickSelectedKeys.value.join(',')
  router.push({ path: '/paper/repository', query: { pickQuestions: ids } })
  exitPickMode()
}

function formatKps(kps = []) {
  if (!Array.isArray(kps)) return '-'
  return kps.length > 0 ? kps.join('、') : '-'
}

function handleBackToFolders() {
  selectedFolderId.value = null
  selectedFolderName.value = ''
  questionList.value = []
  pickMode.value = false
  pickSelectedKeys.value = []
  pickerSearch.value = ''
  pickerKpName.value = null
  pickerType.value = 'all'
  router.replace({ path: '/question/repository' })
}

function handleBatchDelete() {
  if (selectedIds.value.length === 0) {
    message.warning('请先选择要删除的题库')
    return
  }
  Modal.confirm({
    title: '确认批量删除',
    content: `确定要删除选中的 ${selectedIds.value.length} 个题库吗？`,
    okType: 'danger',
    async onOk() {
      try {
        for (const id of selectedIds.value) {
          await deleteQuestionFolder(id)
        }
        message.success('批量删除成功')
        selectedIds.value = []
        await loadData()
      } catch (error) {
        message.error(error.message || '批量删除失败')
      }
    },
  })
}

// 单个题目操作
function handleEditQuestion(q) {
  editingQuestion.value = q
  modalOpen.value = true
}

function handleMoveQuestion(q) {
  currentMovingQuestion.value = q
  moveQuestionTargetFolderId.value = null
  moveQuestionModalVisible.value = true
}

async function handleMoveQuestionConfirm() {
  if (moveQuestionTargetFolderId.value === null && moveQuestionTargetFolderId.value !== 0) {
    message.warning('请选择目标文件夹')
    return
  }
  try {
    await moveQuestionToFolder(currentMovingQuestion.value.id, moveQuestionTargetFolderId.value)
    message.success('题目已移动')
    moveQuestionModalVisible.value = false
    currentMovingQuestion.value = null
    await loadQuestionsForFolder(selectedFolderId.value)
  } catch (error) {
    message.error(error.message || '移动失败')
  }
}

function handleDeleteQuestion(q) {
  Modal.confirm({
    title: '确认删除题目',
    content: `删除后无法恢复，是否删除该题目？`,
    okType: 'danger',
    async onOk() {
      try {
        await deleteQuestion(q.id)
        message.success('题目已删除')
        await loadQuestionsForFolder(selectedFolderId.value)
      } catch (error) {
        message.error(error.message || '删除失败')
      }
    },
  })
}

// 题目相关
async function handleSubmitQuestion(payload) {
  try {
    if (editingQuestion.value?.id) {
      await updateQuestion(editingQuestion.value.id, payload)
      message.success('题目已更新')
    } else {
      await createQuestion(payload)
      message.success('题目已创建')
    }
    modalOpen.value = false
    editingQuestion.value = null
    await loadData()
  } catch (error) {
    message.error(error.message || '保存失败')
  }
}

async function loadPoliceTypeOptions() {
  try {
    const result = await getPoliceTypes()
    policeTypeOptions.value = result.items || result || []
  } catch {
    policeTypeOptions.value = []
  }
}

function clearQuestionSelection() {
  selectedFolderId.value = null
  selectedFolderName.value = ''
  questionList.value = []
  questionPagination.total = 0
  questionPagination.current = 1
}

function ensureActiveViewAccess() {
  if (activeNav.value === 'knowledge' && !canManageKnowledgePoints.value && canManageQuestionBank.value) {
    router.replace({ path: '/question/repository' })
    return false
  }
  if (activeNav.value === 'bank' && !canManageQuestionBank.value && canManageKnowledgePoints.value) {
    router.replace({ path: '/question/knowledge-points' })
    return false
  }
  return true
}

async function syncFolderState(folderId) {
  if (activeNav.value !== 'bank') {
    clearQuestionSelection()
    return
  }

  if (!folderId) {
    clearQuestionSelection()
    return
  }

  const folder = folderList.value.find((item) => String(item.id) === String(folderId))
  if (!folder) {
    clearQuestionSelection()
    return
  }

  selectedFolderId.value = folder.id
  selectedFolderName.value = folder.name
  await loadQuestionsForFolder(folder.id)
}

onMounted(async () => {
  if (canManageQuestionBank.value) {
    await loadData()
    await loadPoliceTypeOptions()
  }
  if (!ensureActiveViewAccess()) return
  await syncFolderState(route.query.folderId)
})

watch(() => route.path, () => {
  if (!ensureActiveViewAccess()) return
  syncFolderState(route.query.folderId)
})

watch(() => route.query.folderId, (newVal) => {
  if (!ensureActiveViewAccess()) return
  syncFolderState(newVal)
})

watch([pickerSearch, pickerKpName, pickerType], () => {
  questionPagination.current = 1
})

onUnmounted(() => {
  const mainLayout = document.querySelector('.main-layout')
  if (mainLayout) {
    mainLayout.classList.remove('question-bank-fullscreen')
  }
})
</script>

<style scoped>
/* ============ 页面布局 ============ */
.question-bank-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #F8FAFC;
  color: #334155;
  margin: 0;
  padding: 0;
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

/* ============ 二级导航 ============ */
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
  color: #94A3B8;
  padding-bottom: 8px;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  cursor: pointer;
}

.sub-nav-item:hover {
  color: #64748B;
}

.sub-nav-item.active {
  color: #1E293B;
  border-color: #2563EB;
}

.sub-nav-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-aux {
  font-size: 12px;
  font-weight: 600;
  color: #64748B;
  padding: 6px 12px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  background-color: #FFFFFF;
  transition: all 0.2s;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-aux:hover {
  border-color: #CBD5E1;
  background-color: #F8FAFC;
  color: #1E293B;
}

/* ============ 主容器 ============ */
.main-container {
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 640px;
}

/* ============ 工具栏 ============ */
.toolbar-row {
  padding: 24px 32px;
  border-bottom: 1px solid #F1F5F9;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  justify-content: space-between;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.btn-primary {
  background: #2563EB;
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
  background: #1D4ED8;
  transform: scale(0.98);
}

.search-wrapper {
  position: relative;
  width: 256px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 10px;
  width: 16px;
  height: 16px;
  color: #94A3B8;
  pointer-events: none;
}

.input-minimal {
  background-color: transparent;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 14px;
  color: #1E293B;
  transition: all 0.2s;
  outline: none;
  height: 36px;
}

.input-minimal:hover {
  border-color: #CBD5E1;
}

.input-minimal:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-wrapper .input-minimal {
  padding-left: 36px;
  width: 100%;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-title {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
}

.pick-hint {
  font-size: 13px;
  color: #2563EB;
  font-weight: 600;
  padding: 0 8px;
}

.filter-select {
  width: 160px;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20width%3D%2220%22%20height%3D%2220%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpath%20d%3D%22M5%207l5%205%205-5%22%20stroke%3D%22%2394A3B8%22%20stroke-width%3D%221.5%22%20fill%3D%22none%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  font-size: 12px;
  font-weight: 500;
  color: #64748B;
  cursor: pointer;
}

.filter-select-sm {
  width: 128px;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20width%3D%2220%22%20height%3D%2220%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpath%20d%3D%22M5%207l5%205%205-5%22%20stroke%3D%22%2394A3B8%22%20stroke-width%3D%221.5%22%20fill%3D%22none%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  font-size: 12px;
  font-weight: 500;
  color: #64748B;
  cursor: pointer;
}

.divider-v {
  width: 1px;
  height: 16px;
  background: #E2E8F0;
  margin: 0 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  color: #64748B;
  transition: color 0.2s;
}

.checkbox-label:hover {
  color: #1E293B;
}

.custom-checkbox {
  width: 14px;
  height: 14px;
  border-radius: 4px;
  border: 1px solid #CBD5E1;
  accent-color: #2563EB;
  cursor: pointer;
}

/* ============ 表格 ============ */
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
  background: #F8FAFC;
  border-bottom: 1px solid #F1F5F9;
}

.data-table th {
  padding: 16px;
  font-size: 10px;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  white-space: nowrap;
}

.text-center {
  text-align: center;
}

.text-right {
  text-align: right;
}

.col-check {
  padding-left: 32px !important;
  padding-right: 16px !important;
  width: 48px;
}

.col-index {
  width: 60px;
  text-align: center;
}

.col-name {
  width: 200px;
}

.col-publisher {
  width: 80px;
}

.col-category {
  width: 100px;
}

.col-paper {
  width: 80px;
}

.col-exercise {
  width: 100px;
}

.col-questions {
  width: 80px;
}

.col-status {
  width: 80px;
}

.col-time {
  width: 120px;
}

.col-action {
  width: 140px;
  padding-right: 32px !important;
  padding-left: 16px !important;
}

.col-type {
  width: 80px;
}

.col-content {
  min-width: 200px;
}

.col-answer {
  width: 100px;
}

.answer-text {
  font-size: 13px;
  font-weight: 600;
  color: #059669;
}

.ml-2 {
  margin-left: 8px;
}

.col-difficulty {
  width: 60px;
}

.col-kp {
  max-width: 180px;
}

.kp-text {
  font-size: 12px;
  color: #64748B;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.options-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.option-tag {
  font-size: 11px;
  color: #64748B;
  background: #F1F5F9;
  padding: 1px 6px;
  border-radius: 3px;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.difficulty-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #F1F5F9;
  color: #64748B;
  font-size: 11px;
  font-weight: 600;
}

.table-row {
  transition: background-color 0.2s;
  border-bottom: 1px solid #F8FAFC;
}

.table-row:hover {
  background-color: #F8FAFC;
}

.data-table td {
  padding: 20px 16px;
  vertical-align: middle;
}

.name-text {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  transition: color 0.2s;
}

.name-text:hover {
  color: #2563EB;
}

.name-text.is-system {
  color: #334155;
}

.badge-system {
  margin-left: 8px;
  font-size: 9px;
  font-weight: 700;
  color: #3B82F6;
  background: #EFF6FF;
  padding: 2px 4px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: -0.02em;
}

.question-count {
  font-weight: 700;
  color: #2563EB;
}

.question-count-btn {
  background: none;
  border: none;
  color: #2563EB;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}

.question-count-btn:hover {
  color: #1D4ED8;
  text-decoration: underline;
}

.status-text {
  font-size: 12px;
  font-weight: 500;
  color: #94A3B8;
  font-style: italic;
}

.col-time {
  font-size: 12px;
  color: #94A3B8;
  font-family: monospace;
}

.action-btns {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn-link {
  background: none;
  border: none;
  color: #2563EB;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 0;
  transition: color 0.2s;
}

.btn-link:hover:not(:disabled) {
  color: #1D4ED8;
  text-decoration: underline;
}

.btn-link:disabled {
  color: #CBD5E1;
  cursor: not-allowed;
}

.btn-link-danger {
  color: #EF4444;
}

.btn-link-danger:hover:not(:disabled) {
  color: #DC2626;
}

.empty-row {
  text-align: center;
  padding: 40px;
  color: #94A3B8;
  font-size: 14px;
}

/* ============ 底部区域 ============ */
.footer-area {
  padding: 20px 32px;
  border-top: 1px solid #F1F5F9;
  background: rgba(248, 250, 252, 0.1);
  flex-shrink: 0;
}

.notice-area {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 11px;
  color: #94A3B8;
  line-height: 1.6;
  max-width: 800px;
}

.notice-icon {
  width: 16px;
  height: 16px;
  color: #CBD5E1;
  flex-shrink: 0;
  margin-top: 2px;
}

.notice-text {
  margin: 0;
}

.notice-text p {
  margin: 0;
}

.notice-text .mt-4 {
  margin-top: 4px;
}

.footer-divider {
  width: 100%;
  height: 1px;
  background: #F1F5F9;
  margin: 16px 0;
}

.footer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.batch-ops {
  display: flex;
  align-items: center;
  gap: 12px;
}

.batch-label {
  font-size: 12px;
  color: #94A3B8;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: -0.02em;
}

.btn-batch {
  font-size: 12px;
  font-weight: 700;
  color: #64748B;
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid transparent;
  background: none;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-batch:hover {
  background: #F1F5F9;
  border-color: #E2E8F0;
}

.btn-batch-danger {
  color: #EF4444;
}

.btn-batch-danger:hover {
  background: #FEF2F2;
  border-color: #FECACA;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.page-info {
  font-size: 11px;
  color: #94A3B8;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.page-sep {
  margin: 0 12px;
  color: #E2E8F0;
}

.pagination-btns {
  display: flex;
  gap: 4px;
}

.page-btn {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  border: 1px solid #E2E8F0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 10px;
  font-weight: 700;
  color: #64748B;
}

.page-btn:hover:not(:disabled) {
  background: #F1F5F9;
}

.page-btn:disabled {
  color: #CBD5E1;
  cursor: not-allowed;
}

.page-btn-active {
  background: #1E293B;
  color: white;
  border-color: #1E293B;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* ============ 分页大小选择 ============ */
.page-size-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-size-label {
  font-size: 11px;
  color: #94A3B8;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.page-size-select {
  font-size: 12px;
  color: #64748B;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  padding: 4px 24px 4px 8px;
  background: white;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20width%3D%2220%22%20height%3D%2220%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpath%20d%3D%22M5%207l5%205%205-5%22%20stroke%3D%22%2394A3B8%22%20stroke-width%3D%221.5%22%20fill%3D%22none%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 4px center;
  background-size: 16px;
  transition: all 0.2s;
}

.page-size-select:hover {
  border-color: #CBD5E1;
}

.page-size-select:focus {
  outline: none;
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* ============ 答案展开区域 ============ */
.answer-section {
  margin-top: 12px;
  padding: 12px 16px;
  background: #F0F9FF;
  border-radius: 8px;
  border: 1px solid #E0F2FE;
}

.answer-label {
  font-size: 12px;
  font-weight: 700;
  color: #0369A1;
  margin-bottom: 4px;
}

.answer-content {
  font-size: 14px;
  font-weight: 700;
  color: #0C4A6E;
}

.answer-explanation {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #BAE6FD;
}

.answer-explanation .answer-label {
  color: #7C3AED;
}

.answer-explanation div:last-child {
  font-size: 13px;
  color: #4C1D95;
  line-height: 1.6;
}

/* ============ 文件夹管理弹窗 ============ */
.folder-manager {
  padding: 8px 0;
}

.folder-manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.folder-manager-list {
  max-height: 400px;
  overflow-y: auto;
}

.folder-manager-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 8px;
  border-bottom: 1px solid #F1F5F9;
}

.folder-manager-item:hover {
  background: #F8FAFC;
}

.folder-manager-item-left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #334155;
}

.folder-manager-item-actions {
  display: flex;
  gap: 8px;
}

/* ============ 滚动条 ============ */
::-webkit-scrollbar {
  width: 5px;
}

::-webkit-scrollbar-thumb {
  background: #E2E8F0;
  border-radius: 10px;
}
</style>
