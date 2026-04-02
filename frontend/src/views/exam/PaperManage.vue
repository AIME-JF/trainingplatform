<template>
  <div class="paper-manage-page">
    <!-- 主体内容 -->
    <main class="main-content">
      <div class="content-wrapper">

        <!-- 统一的大边框容器 -->
        <div class="main-container">

          <!-- 第一层：操作与搜索过滤 -->
          <div class="toolbar-row">
            <div class="toolbar-left">
              <a-dropdown>
                <button class="btn-primary">
                  新建试卷
                  <svg style="width:12px;height:12px;margin-left:4px" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"/></svg>
                </button>
                <template #overlay>
                  <a-menu @click="({ key }) => handleCreateClick(key)">
                    <a-menu-item key="manual">手动选题目</a-menu-item>
                    <a-menu-item key="ai">智能组卷</a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
              <button class="btn-aux" @click="router.push({ path: '/paper/ai-assemble', query: { mode: 'list' } })">
                智能出卷任务
              </button>
              <div class="search-wrapper">
                <svg class="search-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                <input type="text" class="input-minimal" v-model="searchText" placeholder="请输入关键字搜索..." @input="handleSearch">
              </div>
            </div>

            <div class="toolbar-right">
              <!-- 警种筛选 -->
              <a-select
                v-if="currentView === 'policeType'"
                v-model:value="selectedPoliceTypeIds"
                mode="multiple"
                placeholder="请选择警种"
                :options="policeTypeSelectOptions"
                style="min-width: 200px"
                @change="handleFilterChange"
              />
              <!-- 课程筛选 -->
              <a-select
                v-if="currentView === 'course'"
                v-model:value="selectedCourseIds"
                mode="multiple"
                placeholder="请选择课程"
                :loading="courseLoading"
                :options="courseSelectOptions"
                show-search
                :filter-option="false"
                @search="handleCourseSearch"
                @change="handleFilterChange"
                style="min-width: 200px"
              />
              <!-- 知识点筛选 -->
              <a-select
                v-if="currentView === 'knowledgePoint'"
                v-model:value="selectedKpIds"
                mode="multiple"
                placeholder="请选择知识点"
                :loading="kpLoading"
                :options="kpSelectOptions"
                show-search
                :filter-option="false"
                style="min-width: 200px"
                @change="handleFilterChange"
              />
            </div>
          </div>

          <!-- 第二层：表格数据 -->
          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th class="col-index">序号</th>
                  <th class="col-paper-name">试卷名称</th>
                  <th class="col-type text-center">试卷类型</th>
                  <th class="col-folder text-center">试卷分类</th>
                  <th class="col-count text-center">题目数量</th>
                  <th class="col-duration text-center">考试时长</th>
                  <th class="col-score text-center">总分值</th>
                  <th class="col-passing text-center">及格分数</th>
                  <th class="col-count text-center">考试数</th>
                  <th class="col-time">添加时间</th>
                  <th class="col-publisher">发布人</th>
                  <th class="col-action text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(record, index) in displayedPapers" :key="record.id" class="table-row">
                  <td class="col-index">{{ index + 1 }}</td>
                  <td class="col-paper-name">
                    <span class="name-text">{{ record.title }}</span>
                    <p class="desc-text">{{ record.description || '暂无描述' }}</p>
                  </td>
                  <td class="col-type text-center">
                    <span :class="['tag-pill', typeTagColors[record.type]]">{{ typeLabels[record.type] }}</span>
                  </td>
                  <td class="col-folder text-center text-xs text-slate-500">{{ record.folderName || '-' }}</td>
                  <td class="col-count text-center">{{ record.questionCount || 0 }}</td>
                  <td class="col-duration text-center">{{ record.duration || 60 }}分钟</td>
                  <td class="col-score text-center">{{ record.totalScore || 0 }}</td>
                  <td class="col-passing text-center">{{ record.passingScore || 60 }}</td>
                  <td class="col-count text-center">{{ record.usageCount || 0 }}</td>
                  <td class="col-time">{{ formatDate(record.createdAt) }}</td>
                  <td class="col-publisher text-xs">{{ record.creatorName || '-' }}</td>
                  <td class="col-action text-right">
                    <div class="action-btns">
                      <button class="btn-link" @click="openViewDrawer(record)">查看</button>
                      <button v-if="record.status === 'draft'" class="btn-link" @click="openEditDrawer(record)">编辑</button>
                      <button v-if="record.status === 'draft'" class="btn-link" @click="handlePublish(record)">发布</button>
                      <button v-if="record.usageCount === 0" class="btn-link btn-link-danger" @click="handleDelete(record)">删除</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="displayedPapers.length === 0">
                  <td colspan="12" class="empty-row">暂无试卷数据</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 第三层：说明与分页 -->
          <div class="footer-area">
            <div class="footer-divider"></div>
            <div class="footer-actions">
              <div class="footer-left">
                <span class="page-info">共 {{ statsState.total }} 条记录</span>
              </div>
              <div class="footer-right">
                <div class="pagination-btns">
                  <button class="page-btn" :disabled="pagination.current <= 1" @click="handlePrevPage">‹</button>
                  <button v-for="page in visiblePages" :key="page" class="page-btn" :class="{ 'page-btn-active': page === pagination.current }" @click="pagination.current = page">{{ page }}</button>
                  <button class="page-btn" :disabled="pagination.current >= totalPages" @click="handleNextPage">›</button>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </main>

    <!-- 新建/编辑试卷抽屉 -->
    <a-drawer v-model:open="drawerVisible" :title="drawerTitle" width="900px" @close="resetDraft">
      <paper-draft-editor
        v-model="paperDraft"
        :disabled="isViewMode"
        :allow-manual-question="false"
        :allow-question-edit="false"
      />
      <template #footer>
        <a-space style="float:right">
          <a-button @click="resetDraft">关闭</a-button>
          <a-button v-if="!isViewMode" type="primary" :loading="submitting" @click="handleSave">保存</a-button>
        </a-space>
      </template>
    </a-drawer>

    <!-- 管理文件夹弹窗 -->
    <a-modal
      v-model:open="folderModalVisible"
      title="管理目录"
      width="600px"
      @ok="handleFolderSubmit"
      @cancel="resetFolderModal"
    >
      <div class="folder-manager">
        <div class="folder-manager-header">
          <a-input-search v-model:value="folderSearchText" placeholder="搜索文件夹..." allow-clear style="margin-bottom: 12px" />
          <button class="btn-primary" @click="openCreateFolderModal">新建文件夹</button>
        </div>
        <div class="folder-manager-list">
          <div v-for="folder in filteredFolderList" :key="folder.id" class="folder-manager-item">
            <div class="folder-manager-item-left">
              <span>{{ folder.name }}</span>
              <span class="text-xs text-slate-400">({{ folder.paperCount }}份试卷)</span>
            </div>
            <div class="folder-manager-item-actions">
              <button class="btn-link" @click="openEditFolderModal(folder)">编辑</button>
              <button class="btn-link btn-link-danger" @click="handleDeleteFolder(folder)">删除</button>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <a-space style="float:right">
          <a-button @click="folderModalVisible = false">关闭</a-button>
        </a-space>
      </template>
    </a-modal>

    <!-- 新建/编辑文件夹弹窗 -->
    <a-modal
      v-model:open="folderFormModalVisible"
      :title="editingFolderId ? '编辑文件夹' : '新建文件夹'"
      @ok="handleFolderSubmit"
      @cancel="resetFolderFormModal"
    >
      <a-form :model="folderForm" layout="vertical">
        <a-form-item label="文件夹名称" name="name" :rules="[{ required: true, message: '请输入文件夹名称' }]">
          <a-input v-model:value="folderForm.name" placeholder="请输入文件夹名称" :maxlength="100" />
        </a-form-item>
        <a-form-item v-if="editingFolderId" label="移动到">
          <a-tree-select
            v-model:value="folderForm.parentId"
            :treeData="folderTreeData"
            placeholder="根目录（不移动）"
            allow-clear
            tree-default-expand-all
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 批量移动弹窗 -->
    <a-modal
      v-model:open="batchMoveModalVisible"
      title="批量移动试卷"
      @ok="handleBatchMove"
    >
      <a-form layout="vertical">
        <a-form-item label="选择目标文件夹">
          <a-select v-model:value="batchMoveTargetFolderId" placeholder="请选择目标文件夹">
            <a-select-option :value="null">根目录（移出文件夹）</a-select-option>
            <a-select-option v-for="folder in allFolderList" :key="folder.id" :value="folder.id">
              {{ folder.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import {
  archiveExamPaper,
  createExamPaper,
  createPaperFolder,
  deleteExamPaper,
  deletePaperFolder,
  getExamPaperDetail,
  getExamPapers,
  getPaperFolders,
  movePaperToFolder,
  publishExamPaper,
  updateExamPaper,
  updatePaperFolder,
} from '@/api/exam'
import { getPoliceTypes } from '@/api/user'
import { getCourses } from '@/api/course'
import { getKnowledgePoints } from '@/api/knowledgePoint'
import PaperDraftEditor from './components/PaperDraftEditor.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const submitting = ref(false)
const drawerVisible = ref(false)
const drawerMode = ref('create')
const editingId = ref(null)
const handledQuickCreate = ref('')
const paperList = ref([])
const searchText = ref('')

// 统计数据
const statsState = reactive({
  total: 0,
  published: 0,
  draft: 0,
  archived: 0,
})

// 拖拽相关
const draggedPaper = ref(null)
const draggedFromFolder = ref(null)
const dragOverFolderId = ref(null)

// 文件夹相关
const folderList = ref([])
const expandedFolders = ref(new Set())
const folderModalVisible = ref(false)
const folderFormModalVisible = ref(false)
const folderSearchText = ref('')
const editingFolderId = ref(null)
const folderForm = reactive({ name: '', parentId: null })
const batchMoveModalVisible = ref(false)
const batchMoveTargetFolderId = ref(null)
const currentBatchMoveFolderId = ref(null)
const folderModalMode = ref('create')

// 视角切换
const currentView = ref('policeType') // 'policeType' | 'course' | 'knowledgePoint'

// 警种相关
const policeTypeSelectOptions = ref([])
const selectedPoliceTypeIds = ref([])

// 课程相关
const courseList = ref([])
const courseSelectOptions = ref([])
const selectedCourseIds = ref([])
const courseLoading = ref(false)

// 知识点相关
const kpSelectOptions = ref([])
const selectedKpIds = ref([])
const kpLoading = ref(false)

// 分页
const pagination = reactive({ current: 1, pageSize: 50 })

// 每页显示的展开文件夹列表
const expandedFolderList = ref([])

const currentTime = ref('')

const statusLabels = { draft: '草稿', published: '已发布', archived: '已归档' }
const statusTagColors = { draft: 'tag-orange', published: 'tag-green', archived: 'tag-gray' }
const typeLabels = { formal: '正式考核', quiz: '测验' }
const typeTagColors = { formal: 'tag-blue', quiz: 'tag-purple' }

// 扁平试卷列表（用于表格展示）
const displayedPapers = computed(() => paperList.value)

const flatFolderList = computed(() => {
  const result = []
  const flatten = (folders) => {
    folders.forEach(folder => {
      result.push(folder)
      if (folder.children && folder.children.length > 0) {
        flatten(folder.children)
      }
    })
  }
  flatten(folderList.value)
  return result
})

// 所有文件夹列表（扁平，用于批量移动选择）
const allFolderList = computed(() => flatFolderList.value)

// 过滤后的文件夹列表（管理弹窗用）
const filteredFolderList = computed(() => {
  if (!folderSearchText.value) return folderList.value
  return folderList.value.filter(f => f.name.includes(folderSearchText.value))
})

// 文件夹树形数据（用于选择父文件夹）
const folderTreeData = computed(() => {
  const convert = (folders, level = 0) => {
    return folders
      .filter(f => f.id !== editingFolderId.value)
      .map(f => ({
        value: f.id,
        label: f.name,
        children: f.children ? convert(f.children, level + 1) : []
      }))
  }
  return convert(folderList.value)
})

const folderCount = computed(() => folderList.value.length)

const totalPages = computed(() => Math.ceil(statsState.total / pagination.pageSize) || 1)

const visiblePages = computed(() => {
  const pages = [], total = totalPages.value, cur = pagination.current
  let start = Math.max(1, cur - 2), end = Math.min(total, start + 4)
  if (end - start < 4) start = Math.max(1, end - 4)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

const viewLabel = computed(() => {
  const labels = {
    policeType: '警种',
    course: '课程',
    knowledgePoint: '知识点'
  }
  return labels[currentView.value] || '警种'
})

const canManagePaper = computed(() => authStore.hasPermission('CREATE_EXAM'))
const canOpenAiAssembleTask = computed(() => authStore.hasAnyPermission(['GET_AI_PAPER_ASSEMBLY_TASKS', 'CREATE_AI_PAPER_ASSEMBLY_TASK']))

const isViewMode = computed(() => drawerMode.value === 'view')
const drawerTitle = computed(() => {
  if (drawerMode.value === 'edit') return '编辑试卷'
  if (drawerMode.value === 'view') return '查看试卷'
  return '新建试卷'
})

// 带展开状态的文件夹列表
const displayedGroups = computed(() => {
  return expandedFolderList.value.map(folder => ({
    ...folder,
    expanded: expandedFolders.value.has(folder.id),
  }))
})

function updateCurrentTime() {
  const now = new Date()
  currentTime.value = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  const pad = n => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function toggleFolder(folderId) {
  if (expandedFolders.value.has(folderId)) {
    expandedFolders.value.delete(folderId)
  } else {
    expandedFolders.value.add(folderId)
  }
  expandedFolders.value = new Set(expandedFolders.value)
}

// 拖拽相关函数
function handlePaperDragStart(event, paper, folder) {
  draggedPaper.value = paper
  draggedFromFolder.value = folder
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', JSON.stringify({ paperId: paper.id, folderId: folder.id }))
}

function handleDragOver(event, folder) {
  event.preventDefault()
  event.stopPropagation()
  event.dataTransfer.dropEffect = 'move'
  dragOverFolderId.value = folder.id
}

function handleDragLeave(event, folder) {
  event.stopPropagation()
  if (!event.currentTarget.contains(event.relatedTarget)) {
    dragOverFolderId.value = null
  }
}

async function handleDropToFolder(event, targetFolder) {
  event.preventDefault()
  event.stopPropagation()
  dragOverFolderId.value = null

  if (!draggedPaper.value) {
    console.warn('拖拽 paper 为空')
    return
  }

  const paper = draggedPaper.value
  const sourceFolderId = paper.folderId
  const newFolderId = targetFolder.id === 0 ? null : targetFolder.id

  // 如果是同一个文件夹，不做任何操作
  if (sourceFolderId === newFolderId || (sourceFolderId == null && newFolderId == null)) {
    console.log('同文件夹内拖拽，不移动')
    draggedPaper.value = null
    draggedFromFolder.value = null
    return
  }

  console.log('移动试卷:', paper.id, paper.title, '从文件夹', sourceFolderId, '到', newFolderId, targetFolder.name)

  try {
    // 先更新前端状态，乐观响应
    const targetGroup = expandedFolderList.value.find(g => g.id === newFolderId)
    const sourceGroup = expandedFolderList.value.find(g => g.id === sourceFolderId)

    if (targetGroup) {
      // 从原文件夹移除
      if (sourceGroup) {
        sourceGroup.papers = sourceGroup.papers.filter(p => p.id !== paper.id)
        sourceGroup.paperCount = sourceGroup.papers.length
      }
      // 添加到目标文件夹
      const updatedPaper = { ...paper, folderId: newFolderId }
      targetGroup.papers.push(updatedPaper)
      targetGroup.paperCount = targetGroup.papers.length
    }

    // 调用 API 确认移动
    await movePaperToFolder(paper.id, newFolderId)
    message.success(`已将试卷移动到「${targetFolder.name}」`)

    // 确保目标文件夹展开
    if (!expandedFolders.value.has(targetFolder.id)) {
      expandedFolders.value.add(targetFolder.id)
      expandedFolders.value = new Set(expandedFolders.value)
    }

    // 重新加载统计数据
    await loadStats()
  } catch (error) {
    console.error('移动失败:', error)
    message.error(error.message || '移动失败')
    // 失败时重新加载数据恢复状态
    await loadPapers()
  }
  draggedPaper.value = null
  draggedFromFolder.value = null
}

function handleDragEnd() {
  draggedPaper.value = null
  draggedFromFolder.value = null
  dragOverFolderId.value = null
}

async function loadPapers() {
  loading.value = true
  try {
    // 构建基础请求参数
    const params = {
      page: 1,
      size: 1000,
      search: searchText.value || undefined,
    }

    // 如果有筛选条件则传给后端
    if (currentView.value === 'policeType' && selectedPoliceTypeIds.value.length > 0) {
      params.policeTypeIds = selectedPoliceTypeIds.value.join(',')
    } else if (currentView.value === 'course' && selectedCourseIds.value.length > 0) {
      params.courseIds = selectedCourseIds.value.join(',')
    } else if (currentView.value === 'knowledgePoint' && selectedKpIds.value.length > 0) {
      params.knowledgePointIds = selectedKpIds.value.join(',')
    }

    const result = await getExamPapers(params)
    const papers = result.items || []

    // 扩展试卷属性
    const folderMap = new Map(flatFolderList.value.map(f => [f.id, f.name]))
    paperList.value = papers.map(paper => ({
      ...paper,
      folderName: paper.folder_id ? (folderMap.get(paper.folder_id) || paper.folder_name || '-') : (paper.folder_name || '-'),
      creatorName: paper.creator_name || '-',
    }))

    // 根据当前视角分组显示（前端分组）
    if (currentView.value === 'policeType') {
      groupPapersByPoliceType(paperList.value)
    } else if (currentView.value === 'course') {
      groupPapersByCourse(paperList.value)
    } else if (currentView.value === 'knowledgePoint') {
      groupPapersByKnowledgePoint(paperList.value)
    }

    refreshExpandedState()
    pagination.total = result.total || 0
  } catch (error) {
    message.error(error.message || '加载试卷失败')
  } finally {
    loading.value = false
  }
}

function refreshExpandedState() {
  const currentExpanded = new Set(expandedFolders.value)
  expandedFolderList.value.forEach(folder => {
    if (currentExpanded.has(folder.id)) {
      expandedFolders.value.add(folder.id)
    }
  })
  expandedFolders.value = new Set(expandedFolders.value)
}

function groupPapersByFolder(papers) {
  // 构建文件夹Map（扁平结构）
  const folderMap = new Map()
  flatFolderList.value.forEach(folder => {
    folderMap.set(folder.id, { ...folder, papers: [], paperCount: 0 })
  })

  // 将试卷分配到文件夹，同时支持 snake_case 和 camelCase
  papers.forEach(paper => {
    const folderId = paper.folderId || paper.folder_id
    if (folderId && folderMap.has(folderId)) {
      const folderData = folderMap.get(folderId)
      folderData.papers.push(paper)
      folderData.paperCount = folderData.papers.length
    }
  })

  // 未分类的试卷放入"未分类"文件夹
  const uncategorizedPapers = papers.filter(p => {
    const folderId = p.folderId || p.folder_id
    return !folderId || !folderMap.has(folderId)
  })
  if (uncategorizedPapers.length > 0) {
    folderMap.set(0, { id: 0, name: '未分类', paperCount: uncategorizedPapers.length, papers: uncategorizedPapers, children: [], parentId: null, sortOrder: 999 })
  }

  // 更新文件夹列表
  expandedFolderList.value = Array.from(folderMap.values())

  // 调试：输出分组信息
  console.log('[文件夹分组] 共', folderMap.size, '个文件夹', Array.from(folderMap.values()).map(g => ({ name: g.name, count: g.paperCount })))
}

// 按警种分组
function groupPapersByPoliceType(papers) {
  const groupMap = new Map()

  papers.forEach(paper => {
    // 试卷没有直接的警种字段，从知识点间接获取或标记为未分类
    const policeTypeName = paper.policeTypeName || paper.police_type_name || '未分类'
    const policeTypeId = paper.policeTypeId || paper.police_type_id || 0

    if (!groupMap.has(policeTypeId)) {
      groupMap.set(policeTypeId, {
        id: policeTypeId,
        name: policeTypeName,
        papers: [],
        paperCount: 0,
        children: [],
        parentId: null,
        sortOrder: policeTypeId,
      })
    }
    groupMap.get(policeTypeId).papers.push(paper)
    groupMap.get(policeTypeId).paperCount++
  })

  // 排序
  const sortedGroups = Array.from(groupMap.values()).sort((a, b) => {
    if (a.name === '未分类') return 1
    if (b.name === '未分类') return -1
    return a.name.localeCompare(b.name)
  })

  // 默认展开前两个
  expandedFolderList.value = sortedGroups
  if (sortedGroups.length > 0 && expandedFolders.value.size === 0) {
    sortedGroups.slice(0, 2).forEach(g => expandedFolders.value.add(g.id))
    expandedFolders.value = new Set(expandedFolders.value)
  }
}

// 按课程分组
function groupPapersByCourse(papers) {
  const groupMap = new Map()

  papers.forEach(paper => {
    // 试卷没有直接的课程字段，标记为未分类
    const courseName = paper.courseName || paper.course_name || '未分类'
    const courseId = paper.courseId || paper.course_id || 0

    if (!groupMap.has(courseId)) {
      groupMap.set(courseId, {
        id: courseId,
        name: courseName,
        papers: [],
        paperCount: 0,
        children: [],
        parentId: null,
        sortOrder: courseId,
      })
    }
    groupMap.get(courseId).papers.push(paper)
    groupMap.get(courseId).paperCount++
  })

  const sortedGroups = Array.from(groupMap.values()).sort((a, b) => {
    if (a.name === '未分类') return 1
    if (b.name === '未分类') return -1
    return a.name.localeCompare(b.name)
  })

  expandedFolderList.value = sortedGroups
  if (sortedGroups.length > 0 && expandedFolders.value.size === 0) {
    sortedGroups.slice(0, 2).forEach(g => expandedFolders.value.add(g.id))
    expandedFolders.value = new Set(expandedFolders.value)
  }
}

// 按知识点分组
function groupPapersByKnowledgePoint(papers) {
  const groupMap = new Map()

  papers.forEach(paper => {
    // 一张试卷可能有多个知识点，同时支持 snake_case 和 camelCase
    const kpNames = paper.knowledgePointNames || paper.knowledge_point_names || []
    if (kpNames.length === 0) {
      // 没有知识点的试卷归入"未分类"
      const kpId = 0
      if (!groupMap.has(kpId)) {
        groupMap.set(kpId, {
          id: kpId,
          name: '未分类',
          papers: [],
          paperCount: 0,
          children: [],
          parentId: null,
          sortOrder: 999,
        })
      }
      groupMap.get(kpId).papers.push(paper)
      groupMap.get(kpId).paperCount++
    } else {
      kpNames.forEach(kpName => {
        // 使用知识点名称作为key
        if (!groupMap.has(kpName)) {
          groupMap.set(kpName, {
            id: kpName,
            name: kpName,
            papers: [],
            paperCount: 0,
            children: [],
            parentId: null,
            sortOrder: 0,
          })
        }
        groupMap.get(kpName).papers.push(paper)
        groupMap.get(kpName).paperCount++
      })
    }
  })

  const sortedGroups = Array.from(groupMap.values()).sort((a, b) => {
    if (a.name === '未分类') return 1
    if (b.name === '未分类') return -1
    return a.name.localeCompare(b.name)
  })

  expandedFolderList.value = sortedGroups
  if (sortedGroups.length > 0 && expandedFolders.value.size === 0) {
    sortedGroups.slice(0, 2).forEach(g => expandedFolders.value.add(g.id))
    expandedFolders.value = new Set(expandedFolders.value)
  }

  // 调试：输出分组信息
  console.log('[知识点分组] 共', sortedGroups.length, '个分组', sortedGroups.map(g => ({ name: g.name, count: g.paperCount })))
}

async function loadFolders() {
  try {
    const result = await getPaperFolders()
    folderList.value = result || []
    // 默认展开第一个文件夹
    if (folderList.value.length > 0 && expandedFolders.value.size === 0) {
      expandedFolders.value.add(folderList.value[0].id)
      expandedFolders.value = new Set(expandedFolders.value)
    }
  } catch (error) {
    console.error('加载文件夹失败:', error)
    folderList.value = []
  }
}

async function loadStats() {
  try {
    const result = await getExamPapers({ page: 1, size: 1 })
    const allPapers = result.items || []
    statsState.total = result.total || 0
    statsState.published = allPapers.filter(p => p.status === 'published').length || 0
    statsState.draft = allPapers.filter(p => p.status === 'draft').length || 0
    statsState.archived = allPapers.filter(p => p.status === 'archived').length || 0

    // 重新获取完整列表来统计
    const fullResult = await getExamPapers({ page: 1, size: 1000 })
    const papers = fullResult.items || []
    statsState.published = papers.filter(p => p.status === 'published').length
    statsState.draft = papers.filter(p => p.status === 'draft').length
    statsState.archived = papers.filter(p => p.status === 'archived').length
  } catch {
    // ignore
  }
}

function handleSearch() {
  pagination.current = 1
  loadPapers()
}

function handlePrevPage() {
  if (pagination.current > 1) {
    pagination.current--
  }
}

function handleNextPage() {
  if (pagination.current < totalPages.value) {
    pagination.current++
  }
}

// ==================== 多维度视图相关 ====================

function switchView(view) {
  currentView.value = view
  // 切换视角时重置筛选和展开状态
  expandedFolders.value = new Set()
  if (view === 'policeType') {
    selectedPoliceTypeIds.value = []
    selectedCourseIds.value = []
    selectedKpIds.value = []
    loadPapers()
  } else if (view === 'course') {
    selectedPoliceTypeIds.value = []
    selectedCourseIds.value = []
    selectedKpIds.value = []
    loadCourses()
    loadPapers()
  } else if (view === 'knowledgePoint') {
    selectedPoliceTypeIds.value = []
    selectedCourseIds.value = []
    selectedKpIds.value = []
    loadKnowledgePoints()
    loadPapers()
  }
}

function handleFilterChange() {
  loadPapers()
}

async function loadPoliceTypes() {
  try {
    const result = await getPoliceTypes()
    const items = result || []
    policeTypeSelectOptions.value = items.map(c => ({ label: c.name, value: c.id }))
  } catch {
    policeTypeSelectOptions.value = []
  }
}

async function loadCourses(search = '') {
  courseLoading.value = true
  try {
    const result = await getCourses({ search, size: 100 })
    const items = result.items || result || []
    courseList.value = items
    courseSelectOptions.value = items.map(c => ({ label: c.title, value: c.id }))
  } catch {
    courseSelectOptions.value = []
  } finally {
    courseLoading.value = false
  }
}

let courseSearchTimer = null
function handleCourseSearch(search) {
  clearTimeout(courseSearchTimer)
  courseSearchTimer = setTimeout(() => {
    loadCourses(search)
  }, 250)
}

async function loadKnowledgePoints() {
  kpLoading.value = true
  try {
    const result = await getKnowledgePoints({ size: 500 })
    const items = result.items || result || []
    kpSelectOptions.value = items.map(kp => ({
      label: kp.name,
      value: kp.id,
    }))
  } catch {
    kpSelectOptions.value = []
  } finally {
    kpLoading.value = false
  }
}

// ==================== 试卷操作相关 ====================

function createEmptyDraft() {
  return {
    title: '',
    description: '',
    type: 'formal',
    duration: 60,
    passingScore: 60,
    totalScore: 0,
    questions: [],
    folderId: null,
  }
}

const paperDraft = reactive(createEmptyDraft())

function resetDraft() {
  Object.assign(paperDraft, createEmptyDraft())
  drawerVisible.value = false
  drawerMode.value = 'create'
  editingId.value = null
}

function mapPaperQuestion(question) {
  const knowledgePoints = question.knowledgePoints
    || (question.knowledgePoint ? [question.knowledgePoint] : [])
  return {
    tempId: `question-${question.id}`,
    sourceQuestionId: question.id,
    origin: 'existing',
    type: question.type,
    content: question.content,
    options: question.type === 'judge'
      ? [{ key: 'A', text: '正确' }, { key: 'B', text: '错误' }]
      : (question.options || []),
    answer: question.answer,
    explanation: question.explanation,
    difficulty: Number(question.difficulty || 3),
    knowledgePoints,
    knowledgePointNames: [...knowledgePoints],
    policeTypeId: question.policeTypeId,
    score: Number(question.score || 1),
  }
}

function openCreateDrawer() {
  if (!canManagePaper.value) return
  resetDraft()
  paperDraft.folderId = null
  drawerMode.value = 'create'
  drawerVisible.value = true
}

function handleCreateClick(key) {
  if (key === 'manual') {
    openCreateDrawer()
  } else if (key === 'ai') {
    router.push({ path: '/paper/ai-assemble' })
  }
}

async function openPaperDetail(record, mode) {
  if (mode === 'edit' && !canManagePaper.value) return
  resetDraft()
  drawerMode.value = mode
  editingId.value = record.id
  try {
    const detail = await getExamPaperDetail(record.id)
    Object.assign(paperDraft, {
      title: detail.title,
      description: detail.description || '',
      type: detail.type || 'formal',
      duration: detail.duration || 60,
      passingScore: detail.passingScore || 60,
      totalScore: detail.totalScore || 0,
      folderId: detail.folderId,
      questions: (detail.questions || []).map(mapPaperQuestion),
    })
    drawerVisible.value = true
  } catch (error) {
    message.error(error.message || '加载试卷详情失败')
  }
}

function openEditDrawer(record) {
  openPaperDetail(record, 'edit')
}

function openViewDrawer(record) {
  router.push({ name: 'PaperDetail', params: { id: record.id } })
}

async function handleSave() {
  if (!canManagePaper.value) return
  if (!paperDraft.title?.trim()) {
    message.warning('请输入试卷名称')
    return
  }
  if (!paperDraft.questions.length) {
    message.warning('请至少选择一道题目')
    return
  }

  const questionIds = paperDraft.questions.map((item) => item.sourceQuestionId).filter(Boolean)
  if (questionIds.length !== paperDraft.questions.length) {
    message.warning('试卷仓库页面仅支持题库已有题目，请移除非题库题目后再保存')
    return
  }

  const payload = {
    title: paperDraft.title,
    description: paperDraft.description || undefined,
    type: paperDraft.type,
    duration: paperDraft.duration,
    passingScore: paperDraft.passingScore,
    totalScore: paperDraft.totalScore,
    folderId: paperDraft.folderId,
    questionIds,
  }

  submitting.value = true
  try {
    if (drawerMode.value === 'edit') {
      await updateExamPaper(editingId.value, payload)
      message.success('试卷已更新')
    } else {
      await createExamPaper(payload)
      message.success('试卷已创建')
    }
    resetDraft()
    loadPapers()
    loadStats()
  } catch (error) {
    message.error(error.message || '保存失败')
  } finally {
    submitting.value = false
  }
}

function handlePublish(record) {
  if (!canManagePaper.value) return
  Modal.confirm({
    title: '确认发布试卷',
    content: `发布后【${record.title}】将不能再修改题目，是否继续？`,
    async onOk() {
      try {
        await publishExamPaper(record.id)
        message.success('试卷已发布')
        loadPapers()
        loadStats()
      } catch (error) {
        message.error(error.message || '发布失败')
      }
    },
  })
}

function handleArchive(record) {
  if (!canManagePaper.value) return
  Modal.confirm({
    title: '确认归档试卷',
    content: `归档后【${record.title}】将不再用于创建考试，是否继续？`,
    async onOk() {
      try {
        await archiveExamPaper(record.id)
        message.success('试卷已归档')
        loadPapers()
        loadStats()
      } catch (error) {
        message.error(error.message || '归档失败')
      }
    },
  })
}

function handleDelete(record) {
  if (!canManagePaper.value) return
  Modal.confirm({
    title: '确认删除试卷',
    content: `删除后无法恢复，是否删除【${record.title}】？`,
    okType: 'danger',
    async onOk() {
      try {
        await deleteExamPaper(record.id)
        message.success('试卷已删除')
        loadPapers()
        loadStats()
      } catch (error) {
        message.error(error.message || '删除失败')
      }
    },
  })
}

// ==================== 文件夹管理相关 ====================

function openManageFolderModal() {
  folderModalVisible.value = true
}

function openCreateFolderModal() {
  folderModalMode.value = 'create'
  editingFolderId.value = null
  folderForm.name = ''
  folderForm.parentId = null
  folderFormModalVisible.value = true
}

function openEditFolderModal(folder) {
  folderModalMode.value = 'edit'
  editingFolderId.value = folder.id
  folderForm.name = folder.name
  folderForm.parentId = folder.parentId
  folderFormModalVisible.value = true
}

function resetFolderModal() {
  folderForm.name = ''
  folderForm.parentId = null
  editingFolderId.value = null
  folderModalVisible.value = false
}

function resetFolderFormModal() {
  folderForm.name = ''
  folderForm.parentId = null
  editingFolderId.value = null
  folderFormModalVisible.value = false
}

async function handleFolderSubmit() {
  if (!folderForm.name?.trim()) {
    message.warning('请输入文件夹名称')
    return
  }
  try {
    if (editingFolderId.value) {
      await updatePaperFolder(editingFolderId.value, {
        name: folderForm.name,
        parentId: folderForm.parentId,
      })
      message.success('文件夹已更新')
    } else {
      await createPaperFolder({
        name: folderForm.name,
        parentId: folderForm.parentId,
      })
      message.success('文件夹已创建')
    }
    resetFolderFormModal()
    loadFolders()
  } catch (error) {
    message.error(error.message || '操作失败')
  }
}

async function handleDeleteFolder(folder) {
  if (!canManagePaper.value) return
  Modal.confirm({
    title: '确认删除文件夹',
    content: `删除后无法恢复，是否删除文件夹「${folder.name}」？`,
    okType: 'danger',
    async onOk() {
      try {
        await deletePaperFolder(folder.id)
        message.success('文件夹已删除')
        loadFolders()
      } catch (error) {
        message.error(error.message || '删除失败')
      }
    },
  })
}

// ==================== 批量移动相关 ====================

function openBatchMoveModal(folder) {
  currentBatchMoveFolderId.value = folder.id
  batchMoveTargetFolderId.value = null
  batchMoveModalVisible.value = true
}

async function handleBatchMove() {
  if (currentBatchMoveFolderId.value === null) {
    message.warning('请选择目标文件夹')
    return
  }
  try {
    const papersInFolder = expandedFolderList.value.find(f => f.id === currentBatchMoveFolderId.value)?.papers || []
    for (const paper of papersInFolder) {
      await movePaperToFolder(paper.id, batchMoveTargetFolderId.value)
    }
    message.success(`已将 ${papersInFolder.length} 份试卷移动到目标文件夹`)
    batchMoveModalVisible.value = false
    loadPapers()
    loadStats()
  } catch (error) {
    message.error(error.message || '移动失败')
  }
}

function applyQuickCreateFromRoute() {
  const raw = Array.isArray(route.query.quickCreate) ? route.query.quickCreate[0] : route.query.quickCreate
  if (String(raw || '') !== '1') {
    handledQuickCreate.value = ''
    return
  }
  if (handledQuickCreate.value === route.fullPath) {
    return
  }
  openCreateDrawer()
  handledQuickCreate.value = route.fullPath
}

onMounted(async () => {
  await loadFolders()
  await loadPapers()
  loadStats()
  loadPoliceTypes()
  loadCourses()
  loadKnowledgePoints()
  updateCurrentTime()
  applyQuickCreateFromRoute()
})

watch(() => route.fullPath, () => {
  loadPapers()
  applyQuickCreateFromRoute()
})
</script>

<style scoped>
.paper-manage-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #F8FAFC;
  color: #334155;
  margin: 0;
  padding: 0;
}

/* 主体内容 */
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}

.content-wrapper {
  width: 100%;
}


/* ============ 按钮样式 ============ */
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

.btn-aux:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.filter-select {
  min-width: 160px;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20width%3D%2220%22%20height%3D%2220%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpath%20d%3D%22M5%207l5%205%205-5%22%20stroke%3D%22%2394A3B8%22%20stroke-width%3D%221.5%22%20fill%3D%22none%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  font-size: 12px;
  font-weight: 500;
  color: #64748B;
  cursor: pointer;
  padding-right: 28px;
}

.filter-select:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
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

.col-index {
  width: 50px;
  text-align: center;
}

.col-paper-name {
  width: 200px;
}

.col-type {
  width: 100px;
}

.col-folder {
  width: 100px;
}

.col-count {
  width: 80px;
}

.col-duration {
  width: 80px;
}

.col-score {
  width: 80px;
}

.col-passing {
  width: 80px;
}

.col-time {
  width: 150px;
}

.col-publisher {
  width: 80px;
}

.col-action {
  width: 120px;
  padding-right: 32px !important;
}

.group-header-row {
  background: #F8FAFC;
  cursor: pointer;
  transition: background-color 0.2s;
}

.group-header-row:hover {
  background: #F1F5F9;
}

.group-header {
  padding: 14px 32px !important;
  display: flex;
  align-items: center;
  gap: 12px;
}

.group-chevron {
  font-size: 14px;
  color: #CBD5E1;
  transition: color 0.2s;
  letter-spacing: -2px;
}

.group-chevron.expanded {
  color: #2563EB;
}

.group-name {
  font-size: 14px;
  font-weight: 700;
  color: #334155;
}

.group-count {
  font-size: 12px;
  color: #94A3B8;
  margin-left: 8px;
}

.table-row {
  transition: background-color 0.2s;
  border-bottom: 1px solid #F8FAFC;
}

.table-row:hover {
  background-color: #F8FAFC;
}

.data-table td {
  padding: 16px;
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

.desc-text {
  font-size: 12px;
  color: #94A3B8;
  margin: 4px 0 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-btns {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
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

/* ============ 标签样式 ============ */
.tag-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.tag-blue { background: #EFF6FF; color: #2563EB; }
.tag-purple { background: #FAF5FF; color: #9333EA; }
.tag-amber { background: #FFFBEB; color: #D97706; }
.tag-green { background: #F0FDF4; color: #16A34A; }
.tag-cyan { background: #ECFEFF; color: #0891B2; }
.tag-orange { background: #FFF7ED; color: #EA580C; }
.tag-red { background: #FEF2F2; color: #DC2626; }
.tag-gray { background: #F1F5F9; color: #64748B; }

/* ============ 底部区域 ============ */
.footer-area {
  padding: 20px 32px;
}

.footer-divider {
  height: 1px;
  background: #F1F5F9;
  margin-bottom: 20px;
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

.footer-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-info {
  font-size: 12px;
  color: #94A3B8;
  font-weight: 500;
}

.pagination-btns {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 1px solid #E2E8F0;
  background: white;
  color: #64748B;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  border-color: #CBD5E1;
  color: #1E293B;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-btn-active {
  background: #1E293B;
  color: white;
  border-color: #1E293B;
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

/* ============ 通用样式 ============ */
.text-xs { font-size: 12px; }
.text-sm { font-size: 14px; }
.text-slate-400 { color: #94A3B8; }
.text-slate-700 { color: #334155; }
.text-slate-200 { color: #CBD5E1; }
.text-slate-300 { color: #CBD5E1; }
.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }
.rounded-full { border-radius: 9999px; }
.flex { display: flex; }
.items-center { align-items: center; }
.justify-center { justify-content: center; }
.justify-end { justify-content: flex-end; }
.gap-4 { gap: 16px; }
.w-2 { width: 8px; }
.h-2 { height: 8px; }
</style>
