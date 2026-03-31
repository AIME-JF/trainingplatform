<template>
  <div class="question-bank-page">
    <!-- 顶部通栏 -->
    <header class="page-header-bar">
      <div class="header-left">
        <div class="logo-icon">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
        </div>
        <div class="header-title">
          <span class="title-main">试题仓库</span>
          <div class="title-sub">
            <span>考试系统</span>
            <span class="text-slate-200">/</span>
            <span>题库管理</span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <a-button @click="openManageFolderModal">管理目录</a-button>
        <a-button type="primary" @click="openAddModal">
          <template #icon><PlusOutlined /></template>
          新增试题
        </a-button>
      </div>
    </header>

    <!-- 内容区域 -->
    <div class="content-area">
      <div class="content-inner">
        <!-- 标题和搜索 -->
        <div class="page-title-row">
          <div>
            <h1 class="page-title">试题仓库</h1>
            <p class="page-desc">按业务文件夹分类存储，支持点击文件夹快速展开/收起题目</p>
          </div>
          <div class="search-box">
            <a-input-search v-model:value="searchText" placeholder="全库搜索题干..." allow-clear @search="handleSearch" style="width: 288px" />
          </div>
        </div>

        <!-- 统一的大边框容器 -->
        <div class="main-container">
          <!-- 统计数据条 -->
          <div class="stats-bar">
            <div class="stats-content">
              <div class="stat-item">
                <span class="stat-label">目录总数</span>
                <span class="stat-value">{{ folderCount }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">题目总计</span>
                <span class="stat-value">{{ statsState.total }}</span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-legend">
                <span class="legend-item"><i class="w-2 h-2 rounded-full bg-blue-500"></i> 单选 {{ statsState.single }}</span>
                <span class="legend-item"><i class="w-2 h-2 rounded-full bg-purple-500"></i> 多选 {{ statsState.multi }}</span>
                <span class="legend-item"><i class="w-2 h-2 rounded-full bg-amber-500"></i> 判断 {{ statsState.judge }}</span>
              </div>
            </div>
          </div>

          <!-- 列表标题栏 -->
          <div class="list-header">
            <div class="col-folder">所属文件夹</div>
            <div class="col-content">题干描述</div>
            <div class="col-type text-center">题型</div>
            <div class="col-diff text-center">难度</div>
            <div class="col-score text-center">分值</div>
            <div class="col-action text-right">操作</div>
          </div>

          <!-- 文件夹分组区域 -->
          <div class="folder-list">
            <div
              v-for="folder in displayedFolders"
              :key="folder.id"
              :class="['folder-group', { 'folder-collapsed': !folder.expanded }]"
            >
              <!-- 文件夹标题行 -->
              <div
                class="folder-title"
                :class="{ 'folder-drag-over': dragOverFolderId === folder.id }"
                @click="toggleFolder(folder.id)"
                @dragover="handleDragOver($event, folder)"
                @dragleave="handleDragLeave($event, folder)"
                @drop="handleDropToFolder($event, folder)"
              >
                <div class="folder-title-left">
                  <svg :class="['chevron-icon', { 'rotated': folder.expanded }]" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"/></svg>
                  <svg class="folder-icon" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2-2z"/></svg>
                  <span class="folder-name">{{ folder.name }}</span>
                </div>
                <div class="folder-title-desc">包含 {{ folder.name }} 等 {{ folder.questionCount }} 道试题</div>
                <div class="folder-title-actions">
                  <a-button type="link" size="small" class="batch-move-btn" @click.stop="openBatchMoveModal(folder)">批量移动</a-button>
                </div>
              </div>

              <!-- 题目内容区 -->
              <div class="folder-content">
                <div
                  v-for="(record, index) in folder.questions"
                  :key="record.id"
                  class="question-row"
                  draggable="true"
                  @dragstart="handleQuestionDragStart($event, record, folder)"
                  @dragend="handleDragEnd"
                >
                  <div class="col-folder text-xs text-slate-400">{{ folder.name }}</div>
                  <div class="col-content">
                    <p class="question-content text-sm text-slate-700 font-medium">{{ index + 1 }}. {{ record.content }}</p>
                  </div>
                  <div class="col-type flex justify-center">
                    <span :class="['tag-pill', typeTagColors[record.type]]">{{ typeLabels[record.type] }}</span>
                  </div>
                  <div class="col-diff flex justify-center">
                    <span :class="['tag-pill', difficultyTagColors[record.difficulty]]">{{ record.difficulty }}级</span>
                  </div>
                  <div class="col-score text-center text-sm font-semibold text-slate-600">{{ record.score || 0 }}</div>
                  <div class="col-action text-right flex justify-end gap-4">
                    <a-button type="link" size="small" class="text-slate-400 hover:text-blue-600" @click="openEditModal(record)">详情</a-button>
                    <a-button type="link" size="small" danger class="text-slate-300 hover:text-red-500" @click="handleDelete(record)">
                      <DeleteOutlined />
                    </a-button>
                  </div>
                </div>
                <div v-if="!folder.questions || folder.questions.length === 0" class="empty-folder">
                  该文件夹下暂无题目
                </div>
              </div>
            </div>
          </div>

          <!-- 底部 Footer -->
          <div class="list-footer">
            <div class="footer-info">
              <span>当前展开 {{ expandedFolders.size }} 个目录</span>
              <span class="text-slate-200">|</span>
              <span>列表更新于 {{ currentTime }}</span>
            </div>
            <div class="pagination">
              <a-button size="small" disabled><LeftOutlined /></a-button>
              <a-button size="small" class="current-page">1</a-button>
              <a-button size="small"><RightOutlined /></a-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新增/编辑题目弹窗 -->
    <question-form-modal
      v-model:open="modalOpen"
      :title="editingQuestion ? '编辑题目' : '新增题目'"
      :question="editingQuestion"
      :police-type-options="policeTypeOptions"
      @submit="handleSubmitQuestion"
    />

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
          <a-button type="primary" size="small" @click="openCreateFolderModal">
            <template #icon><PlusOutlined /></template>
            新建文件夹
          </a-button>
        </div>
        <div class="folder-manager-list">
          <div v-for="folder in filteredFolderList" :key="folder.id" class="folder-manager-item">
            <div class="folder-manager-item-left">
              <FolderOutlined />
              <span>{{ folder.name }}</span>
              <span class="text-xs text-slate-400">({{ folder.questionCount }}道题)</span>
            </div>
            <div class="folder-manager-item-actions">
              <a-button type="link" size="small" @click="openEditFolderModal(folder)">编辑</a-button>
              <a-button type="link" size="small" danger @click="handleDeleteFolder(folder)">删除</a-button>
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
      title="批量移动试题"
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
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, DeleteOutlined, LeftOutlined, RightOutlined, FolderOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
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
import QuestionFormModal from './components/QuestionFormModal.vue'

const authStore = useAuthStore()

const loading = ref(false)
const modalOpen = ref(false)
const editingQuestion = ref(null)
const questionList = ref([])
const policeTypeOptions = ref([])
const searchText = ref('')

// 拖拽相关
const draggedQuestion = ref(null)
const draggedFromFolder = ref(null)
const dragOverFolderId = ref(null)

// 统计数据
const statsState = reactive({
  total: 0,
  single: 0,
  multi: 0,
  judge: 0,
})

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

// 每页显示的展开文件夹列表
const expandedFolderList = ref([])

// 带展开状态的文件夹列表
const displayedFolders = computed(() => {
  return expandedFolderList.value.map(folder => ({
    ...folder,
    expanded: expandedFolders.value.has(folder.id),
  }))
})

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

const currentTime = ref('')

const typeLabels = { single: '单选题', multi: '多选题', judge: '判断题' }
const typeTagColors = { single: 'tag-blue', multi: 'tag-purple', judge: 'tag-amber' }
const difficultyTagColors = { 1: 'tag-green', 2: 'tag-cyan', 3: 'tag-blue', 4: 'tag-orange', 5: 'tag-red' }

function updateCurrentTime() {
  const now = new Date()
  currentTime.value = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
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
function handleQuestionDragStart(event, question, folder) {
  draggedQuestion.value = question
  draggedFromFolder.value = folder
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', JSON.stringify({ questionId: question.id, folderId: folder.id }))
}

function handleDragOver(event, folder) {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
  dragOverFolderId.value = folder.id
}

function handleDragLeave(event, folder) {
  // 只有当鼠标离开文件夹标题本身时才清除
  if (!event.currentTarget.contains(event.relatedTarget)) {
    dragOverFolderId.value = null
  }
}

async function handleDropToFolder(event, targetFolder) {
  event.preventDefault()
  dragOverFolderId.value = null
  if (!draggedQuestion.value) return

  const question = draggedQuestion.value
  const newFolderId = targetFolder.id === 0 ? null : targetFolder.id

  try {
    await moveQuestionToFolder(question.id, newFolderId)
    message.success(`已将题目移动到「${targetFolder.name}」`)
    await Promise.all([loadQuestions(), loadStats()])
    // 确保目标文件夹展开
    if (!expandedFolders.value.has(targetFolder.id)) {
      expandedFolders.value.add(targetFolder.id)
      expandedFolders.value = new Set(expandedFolders.value)
    }
  } catch (error) {
    message.error(error.message || '移动失败')
    await loadQuestions()
  }
  draggedQuestion.value = null
  draggedFromFolder.value = null
}

function handleDragEnd() {
  draggedQuestion.value = null
  draggedFromFolder.value = null
  dragOverFolderId.value = null
}

async function loadQuestions() {
  loading.value = true
  try {
    const result = await getQuestions({
      size: -1, // 获取所有题目用于分组
      search: searchText.value || undefined,
    })
    const questions = (result.items || []).map((item) => ({
      ...item,
      knowledgePointNames: item.knowledgePointNames
        || item.knowledgePoints?.map((point) => (typeof point === 'string' ? point : point?.name)).filter(Boolean)
        || [],
    }))
    // 按文件夹分组
    groupQuestionsByFolder(questions)
    pagination.total = result.total || 0
  } catch (error) {
    message.error(error.message || '加载试题失败')
  } finally {
    loading.value = false
  }
}

function groupQuestionsByFolder(questions) {
  // 构建文件夹Map（扁平结构）
  const folderMap = new Map()
  flatFolderList.value.forEach(folder => {
    folderMap.set(folder.id, { ...folder, questions: [] })
  })

  // 将题目分配到文件夹
  questions.forEach(q => {
    if (q.folderId && folderMap.has(q.folderId)) {
      folderMap.get(q.folderId).questions.push(q)
    }
  })

  // 未分类的题目放入"未分类"文件夹
  const uncategorizedQuestions = questions.filter(q => !q.folderId || !folderMap.has(q.folderId))
  if (uncategorizedQuestions.length > 0) {
    folderMap.set(0, { id: 0, name: '未分类', questionCount: uncategorizedQuestions.length, questions: uncategorizedQuestions, children: [], parentId: null, sortOrder: 999 })
  }

  // 更新文件夹列表
  expandedFolderList.value = Array.from(folderMap.values())
}

async function loadFolders() {
  try {
    const result = await getQuestionFolders()
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
    const [allRes, singleRes, multiRes, judgeRes] = await Promise.all([
      getQuestions({ size: 1 }),
      getQuestions({ size: 1, type: 'single' }),
      getQuestions({ size: 1, type: 'multi' }),
      getQuestions({ size: 1, type: 'judge' }),
    ])
    statsState.total = allRes.total || 0
    statsState.single = singleRes.total || 0
    statsState.multi = multiRes.total || 0
    statsState.judge = judgeRes.total || 0
  } catch {
    statsState.total = 0
    statsState.single = 0
    statsState.multi = 0
    statsState.judge = 0
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

const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

function handleSearch() {
  loadQuestions()
  loadFolders()
}

function openAddModal() {
  editingQuestion.value = null
  modalOpen.value = true
}

function openEditModal(record) {
  editingQuestion.value = { ...record }
  modalOpen.value = true
}

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
    await Promise.all([loadQuestions(), loadStats(), loadFolders()])
  } catch (error) {
    message.error(error.message || '保存失败')
  }
}

function handleDelete(record) {
  Modal.confirm({
    title: '确认删除题目',
    content: '删除后无法恢复，是否继续？',
    okType: 'danger',
    async onOk() {
      try {
        await deleteQuestion(record.id)
        message.success('题目已删除')
        await Promise.all([loadQuestions(), loadStats(), loadFolders()])
      } catch (error) {
        message.error(error.message || '删除失败')
      }
    },
  })
}

function openManageFolderModal() {
  folderModalVisible.value = true
}

function openCreateFolderModal() {
  editingFolderId.value = null
  folderForm.name = ''
  folderForm.parentId = null
  folderFormModalVisible.value = true
}

function openEditFolderModal(folder) {
  editingFolderId.value = folder.id
  folderForm.name = folder.name
  folderForm.parentId = folder.parentId
  folderFormModalVisible.value = true
}

function resetFolderFormModal() {
  editingFolderId.value = null
  folderForm.name = ''
  folderForm.parentId = null
  folderFormModalVisible.value = false
}

async function handleFolderSubmit() {
  if (!folderForm.name?.trim()) {
    message.warning('请输入文件夹名称')
    return
  }
  try {
    if (editingFolderId.value) {
      await updateQuestionFolder(editingFolderId.value, {
        name: folderForm.name,
        parentId: folderForm.parentId,
      })
      message.success('文件夹已更新')
    } else {
      await createQuestionFolder({
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

function handleDeleteFolder(folder) {
  Modal.confirm({
    title: '确认删除文件夹',
    content: `删除后无法恢复，是否删除文件夹「${folder.name}」？`,
    okType: 'danger',
    async onOk() {
      try {
        await deleteQuestionFolder(folder.id)
        message.success('文件夹已删除')
        loadFolders()
      } catch (error) {
        message.error(error.message || '删除失败')
      }
    },
  })
}

function resetFolderModal() {
  folderSearchText.value = ''
  folderModalVisible.value = false
}

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
    // 移动该文件夹下的所有题目到目标文件夹
    const folder = folderList.value.find(f => f.id === currentBatchMoveFolderId.value)
    if (folder && folder.questions) {
      for (const q of folder.questions) {
        await moveQuestionToFolder(q.id, batchMoveTargetFolderId.value)
      }
    }
    message.success('批量移动成功')
    batchMoveModalVisible.value = false
    loadQuestions()
    loadFolders()
  } catch (error) {
    message.error(error.message || '移动失败')
  }
}

function formatAnswer(answer) {
  return Array.isArray(answer) ? answer.join('、') : answer
}

onMounted(async () => {
  await loadFolders()
  await loadQuestions()
  loadStats()
  loadPoliceTypeOptions()
  updateCurrentTime()
})
</script>

<style scoped>
.question-bank-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #F8FAFC;
  color: #334155;
  margin: 0;
  padding: 0;
}

/* 顶部通栏 */
.page-header-bar {
  height: 64px;
  background: white;
  border-bottom: 1px solid #E2E8F0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: #2563EB;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.header-title {
  display: flex;
  flex-direction: column;
}

.title-main {
  font-weight: 700;
  color: #1E293B;
  font-size: 14px;
  letter-spacing: -0.01em;
}

.title-sub {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 内容区域 */
.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.content-inner {
  width: 100%;
}

.page-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #1E293B;
  letter-spacing: -0.02em;
  margin: 0;
}

.page-desc {
  margin: 8px 0 0;
  color: #64748B;
  font-size: 14px;
}

.search-box {
  position: relative;
}

/* 主容器 */
.main-container {
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 600px;
}

/* 统计条 */
.stats-bar {
  padding: 20px 32px;
  border-bottom: 1px solid #F1F5F9;
  background: #F8FAFC;
}

.stats-content {
  display: flex;
  align-items: center;
  gap: 48px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 10px;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 2px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #1E293B;
}

.stat-divider {
  width: 1px;
  height: 32px;
  background: #E2E8F0;
}

.stat-legend {
  display: flex;
  gap: 24px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #64748B;
}

/* 列表标题栏 */
.list-header {
  display: flex;
  align-items: center;
  padding: 12px 32px;
  border-bottom: 1px solid #E2E8F0;
  font-size: 11px;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: white;
  position: sticky;
  top: 0;
  z-index: 10;
}

.col-folder { width: 192px; flex-shrink: 0; }
.col-content { flex: 1; padding-right: 32px; }
.col-type { width: 128px; flex-shrink: 0; }
.col-diff { width: 80px; flex-shrink: 0; }
.col-score { width: 80px; flex-shrink: 0; }
.col-action { width: 128px; flex-shrink: 0; }

.text-center { text-align: center; }
.text-right { text-align: right; }

/* 文件夹列表 */
.folder-list {
  flex: 1;
}

.folder-group {
  border-bottom: 1px solid #F1F5F9;
}

.folder-title {
  display: flex;
  align-items: center;
  padding: 14px 32px;
  background: #F8FAFC;
  border-bottom: 1px solid #F1F5F9;
  cursor: pointer;
  transition: background-color 0.15s;
}

.folder-title:hover {
  background: #F1F5F9;
}

.folder-title.folder-drag-over {
  background: #EFF6FF;
  border-color: #2563EB;
}

.folder-title-left {
  width: 192px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.chevron-icon {
  transition: transform 0.2s ease;
  color: #94A3B8;
}

.chevron-icon.rotated {
  transform: rotate(0deg);
}

.chevron-icon:not(.rotated) {
  transform: rotate(-90deg);
}

.folder-icon {
  color: #2563EB;
}

.folder-name {
  font-size: 14px;
  font-weight: 700;
  color: #334155;
}

.folder-title-desc {
  flex: 1;
  font-size: 12px;
  color: #94A3B8;
  font-style: italic;
}

.folder-title-actions {
  width: 128px;
  flex-shrink: 0;
  text-align: right;
  opacity: 0;
  transition: opacity 0.15s;
}

.folder-title:hover .folder-title-actions {
  opacity: 1;
}

.batch-move-btn {
  font-size: 11px;
  font-weight: 600;
  color: #2563EB;
  padding: 0;
}

/* 文件夹内容 */
.folder-content {
  max-height: 2000px;
  overflow: hidden;
  transition: max-height 0.3s ease-out;
}

.folder-collapsed .folder-content {
  max-height: 0;
}

.question-row {
  display: flex;
  align-items: center;
  padding: 16px 32px;
  border-bottom: 1px solid #FAFAFA;
  transition: background-color 0.15s;
}

.question-row:hover {
  background: #EFF6FF;
}

.question-content {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 600px;
}

.empty-folder {
  padding: 20px 40px;
  text-align: center;
  color: #94A3B8;
  font-size: 14px;
}

/* 标签样式 */
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

/* 底部 */
.list-footer {
  padding: 16px 32px;
  border-top: 1px solid #F1F5F9;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  margin-top: auto;
}

.footer-info {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination :deep(.ant-btn) {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pagination .current-page {
  background: #1E293B;
  color: white;
  font-size: 10px;
  font-weight: 700;
}

/* 文件夹管理弹窗 */
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
</style>
