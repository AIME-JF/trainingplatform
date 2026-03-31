<template>
  <div class="paper-manage-page">
    <div class="page-header">
      <div>
        <h2>试卷仓库</h2>
        <p class="page-sub">统一维护试卷草稿，智能组卷和智能生成试卷确认后会进入这里</p>
      </div>
      <a-space>
        <permissions-tooltip
          :allowed="canOpenAiAssembleTask"
          tips="需要 GET_AI_PAPER_ASSEMBLY_TASKS 或 CREATE_AI_PAPER_ASSEMBLY_TASK 权限"
          v-slot="{ disabled }"
        >
          <a-button :disabled="disabled" @click="$router.push('/paper/ai-assemble')">
            <template #icon><RobotOutlined /></template>
            智能组卷
          </a-button>
        </permissions-tooltip>
        <permissions-tooltip
          :allowed="canOpenAiGenerateTask"
          tips="需要 GET_AI_PAPER_GENERATION_TASKS 或 CREATE_AI_PAPER_GENERATION_TASK 权限"
          v-slot="{ disabled }"
        >
          <a-button :disabled="disabled" @click="$router.push('/paper/ai-assemble')">
            <template #icon><RobotOutlined /></template>
            智能出卷
          </a-button>
        </permissions-tooltip>
        <permissions-tooltip
          :allowed="canManagePaper"
          tips="需要 CREATE_EXAM 权限"
          v-slot="{ disabled }"
        >
          <a-button type="primary" :disabled="disabled" @click="openCreateDrawer">
            <template #icon><PlusOutlined /></template>
            新建试卷
          </a-button>
        </permissions-tooltip>
      </a-space>
    </div>

    <a-card :bordered="false">
      <div class="content-layout">
        <!-- 左侧文件夹树 -->
        <div class="folder-panel">
          <div class="folder-panel-header">
            <a-input-search v-model:value="folderSearchText" placeholder="搜索文件夹..." allow-clear style="margin-bottom: 8px" />
            <permissions-tooltip
              :allowed="canManagePaper"
              tips="需要 CREATE_EXAM 权限"
              v-slot="{ disabled }"
            >
              <a-button type="link" size="small" :disabled="disabled" @click="openCreateFolderModal">
                <template #icon><FolderAddOutlined /></template>
                新建文件夹
              </a-button>
            </permissions-tooltip>
          </div>
          <div class="folder-tree-container">
            <a-tree
              v-if="folderTree.length > 0"
              :treeData="folderTree"
              :selectedKeys="selectedFolderKeys"
              :expandedKeys="expandedFolderKeys"
              @select="handleFolderSelect"
              @expand="handleFolderExpand"
            >
              <template #title="node">
                <div class="folder-item" @contextmenu="(e) => handleFolderContextMenu(e, node)">
                  <FolderOutlined />
                  <span class="folder-name">{{ node.name }}</span>
                  <span class="paper-count">({{ node.paperCount }})</span>
                </div>
              </template>
            </a-tree>
            <div v-else class="empty-tip">暂无文件夹</div>
          </div>
        </div>

        <!-- 右侧试卷列表 -->
        <div class="paper-list-panel">
          <div class="paper-list-header">
            <a-row :gutter="16">
              <a-col :span="8">
                <a-input-search v-model:value="searchText" placeholder="搜索试卷名称..." allow-clear @search="loadPapers" />
              </a-col>
              <a-col :span="5">
                <a-select v-model:value="filterStatus" style="width:100%" @change="loadPapers">
                  <a-select-option value="all">全部状态</a-select-option>
                  <a-select-option value="draft">草稿</a-select-option>
                  <a-select-option value="published">已发布</a-select-option>
                  <a-select-option value="archived">已归档</a-select-option>
                </a-select>
              </a-col>
              <a-col :span="5">
                <a-select v-model:value="filterType" style="width:100%" @change="loadPapers">
                  <a-select-option value="all">全部类型</a-select-option>
                  <a-select-option value="formal">正式考核</a-select-option>
                  <a-select-option value="quiz">测验</a-select-option>
                </a-select>
              </a-col>
            </a-row>
          </div>

          <a-table
            :columns="columns"
            :data-source="paperList"
            row-key="id"
            :loading="loading"
            :pagination="pagination"
            @change="handleTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="statusColors[record.status]">{{ statusLabels[record.status] }}</a-tag>
              </template>
              <template v-else-if="column.key === 'type'">
                {{ typeLabels[record.type] || record.type }}
              </template>
              <template v-else-if="column.key === 'updatedAt'">
                {{ formatDateTime(record.updatedAt || record.createdAt) }}
              </template>
              <template v-else-if="column.key === 'action'">
                <a-space>
                  <permissions-tooltip
                    v-if="record.status === 'draft'"
                    :allowed="canManagePaper"
                    tips="需要 CREATE_EXAM 权限"
                    v-slot="{ disabled }"
                  >
                    <a-button type="link" size="small" :disabled="disabled" @click="openEditDrawer(record)">编辑</a-button>
                  </permissions-tooltip>
                  <a-button v-else type="link" size="small" @click="openViewDrawer(record)">查看</a-button>
                  <permissions-tooltip
                    v-if="record.status === 'draft'"
                    :allowed="canManagePaper"
                    tips="需要 CREATE_EXAM 权限"
                    v-slot="{ disabled }"
                  >
                    <a-button type="link" size="small" :disabled="disabled" @click="handlePublish(record)">发布</a-button>
                  </permissions-tooltip>
                  <permissions-tooltip
                    v-if="record.status === 'published'"
                    :allowed="canManagePaper"
                    tips="需要 CREATE_EXAM 权限"
                    v-slot="{ disabled }"
                  >
                    <a-button type="link" size="small" :disabled="disabled" @click="handleArchive(record)">归档</a-button>
                  </permissions-tooltip>
                  <a-dropdown>
                    <a-button type="link" size="small">
                      <EllipsisOutlined />
                    </a-button>
                    <template #overlay>
                      <a-menu>
                        <permissions-tooltip
                          :allowed="canManagePaper"
                          tips="需要 CREATE_EXAM 权限"
                          v-slot="{ disabled }"
                        >
                          <a-menu-item key="move" :disabled="disabled" @click="openMoveModal(record)">
                            <SwapOutlined /> 移动到文件夹
                          </a-menu-item>
                        </permissions-tooltip>
                        <permissions-tooltip
                          v-if="record.usageCount === 0"
                          :allowed="canManagePaper"
                          tips="需要 CREATE_EXAM 权限"
                          v-slot="{ disabled }"
                        >
                          <a-menu-item key="delete" :disabled="disabled" danger @click="handleDelete(record)">
                            <DeleteOutlined /> 删除
                          </a-menu-item>
                        </permissions-tooltip>
                      </a-menu>
                    </template>
                  </a-dropdown>
                </a-space>
              </template>
            </template>
          </a-table>
        </div>
      </div>
    </a-card>

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
          <permissions-tooltip
            v-if="!isViewMode"
            :allowed="canManagePaper"
            tips="需要 CREATE_EXAM 权限"
            v-slot="{ disabled }"
          >
            <a-button type="primary" :loading="submitting" :disabled="disabled" @click="handleSave">保存</a-button>
          </permissions-tooltip>
        </a-space>
      </template>
    </a-drawer>

    <!-- 新建/编辑文件夹弹窗 -->
    <a-modal
      v-model:open="folderModalVisible"
      :title="folderModalMode === 'create' ? '新建文件夹' : '编辑文件夹'"
      @ok="handleFolderSubmit"
      @cancel="resetFolderModal"
    >
      <a-form :model="folderForm" layout="vertical">
        <a-form-item label="文件夹名称" name="name" :rules="[{ required: true, message: '请输入文件夹名称' }]">
          <a-input v-model:value="folderForm.name" placeholder="请输入文件夹名称" :maxlength="100" />
        </a-form-item>
        <a-form-item v-if="folderModalMode === 'edit'" label="移动到">
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

    <!-- 移动试卷到文件夹弹窗 -->
    <a-modal
      v-model:open="moveModalVisible"
      title="移动试卷到文件夹"
      @ok="handleMoveSubmit"
    >
      <a-form layout="vertical">
        <a-form-item label="选择目标文件夹">
          <a-tree-select
            v-model:value="moveTargetFolderId"
            :treeData="folderTreeData"
            placeholder="根目录（移出文件夹）"
            allow-clear
            tree-default-expand-all
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, RobotOutlined, FolderOutlined, FolderAddOutlined, EllipsisOutlined, SwapOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { useRoute, useRouter } from 'vue-router'
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
import PaperDraftEditor from './components/PaperDraftEditor.vue'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

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
const filterStatus = ref('all')
const filterType = ref('all')

// 文件夹相关
const folderTree = ref([])
const folderSearchText = ref('')
const selectedFolderKeys = ref([])
const expandedFolderKeys = ref([])
const folderModalVisible = ref(false)
const folderModalMode = ref('create')
const editingFolderId = ref(null)
const folderForm = reactive({ name: '', parentId: null })
const moveModalVisible = ref(false)
const moveTargetFolderId = ref(null)
const movingPaperId = ref(null)

const statusLabels = { draft: '草稿', published: '已发布', archived: '已归档' }
const statusColors = { draft: 'orange', published: 'green', archived: 'default' }
const typeLabels = { formal: '正式考核', quiz: '测验', single: '单选题', multi: '多选题', judge: '判断题' }

const columns = [
  { title: '试卷名称', dataIndex: 'title', key: 'title' },
  { title: '状态', key: 'status', width: 100 },
  { title: '类型', key: 'type', width: 100 },
  { title: '题目数', dataIndex: 'questionCount', key: 'questionCount', width: 90 },
  { title: '引用数', dataIndex: 'usageCount', key: 'usageCount', width: 90 },
  { title: '更新时间', key: 'updatedAt', width: 170 },
  { title: '操作', key: 'action', width: 220 },
]

const pagination = reactive({ current: 1, pageSize: 10, total: 0 })
const paperDraft = reactive(createEmptyDraft())

const isViewMode = computed(() => drawerMode.value === 'view')
const canManagePaper = computed(() => authStore.hasPermission('CREATE_EXAM'))
const canOpenAiAssembleTask = computed(() => authStore.hasAnyPermission(['GET_AI_PAPER_ASSEMBLY_TASKS', 'CREATE_AI_PAPER_ASSEMBLY_TASK']))
const canOpenAiGenerateTask = computed(() => authStore.hasAnyPermission(['GET_AI_PAPER_GENERATION_TASKS', 'CREATE_AI_PAPER_GENERATION_TASK']))
const drawerTitle = computed(() => {
  if (drawerMode.value === 'edit') return '编辑试卷'
  if (drawerMode.value === 'view') return '查看试卷'
  return '新建试卷'
})

// 将文件夹树转换为树形选择器数据
const folderTreeData = computed(() => {
  const convert = (folders, level = 0) => {
    return folders.map(f => ({
      value: f.id,
      label: f.name,
      children: f.children ? convert(f.children, level + 1) : []
    }))
  }
  return [{ value: 0, label: '根目录', children: convert(folderTree.value) }]
})

// 选中的文件夹ID（null表示根目录）
const selectedFolderId = computed(() => {
  if (selectedFolderKeys.value.length === 0) return null
  return selectedFolderKeys.value[0]
})

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

async function loadFolders() {
  try {
    const result = await getPaperFolders()
    folderTree.value = result || []
    // 默认展开第一层
    expandedFolderKeys.value = folderTree.value.map(f => f.id)
  } catch (error) {
    console.error('加载文件夹失败:', error)
  }
}

async function loadPapers() {
  loading.value = true
  try {
    const result = await getExamPapers({
      page: pagination.current,
      size: pagination.pageSize,
      status: filterStatus.value !== 'all' ? filterStatus.value : undefined,
      type: filterType.value !== 'all' ? filterType.value : undefined,
      search: searchText.value || undefined,
      folder_id: selectedFolderId.value || undefined,
    })
    paperList.value = result.items || []
    pagination.total = result.total || 0
  } catch (error) {
    message.error(error.message || '加载试卷失败')
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadPapers()
}

function handleFolderSelect(keys) {
  selectedFolderKeys.value = keys
  pagination.current = 1
  loadPapers()
}

function handleFolderExpand(keys) {
  expandedFolderKeys.value = keys
}

function openCreateDrawer() {
  if (!canManagePaper.value) return
  resetDraft()
  paperDraft.folderId = selectedFolderId.value
  drawerMode.value = 'create'
  drawerVisible.value = true
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
      } catch (error) {
        message.error(error.message || '删除失败')
      }
    },
  })
}

function openCreateFolderModal() {
  if (!canManagePaper.value) return
  folderModalMode.value = 'create'
  editingFolderId.value = null
  folderForm.name = ''
  folderForm.parentId = selectedFolderKeys.value.length > 0 ? selectedFolderKeys.value[0] : null
  folderModalVisible.value = true
}

function openEditFolderModal(folder) {
  if (!canManagePaper.value) return
  folderModalMode.value = 'edit'
  editingFolderId.value = folder.id
  folderForm.name = folder.name
  folderForm.parentId = folder.parentId
  folderModalVisible.value = true
}

function resetFolderModal() {
  folderForm.name = ''
  folderForm.parentId = null
  editingFolderId.value = null
  folderModalVisible.value = false
}

async function handleFolderSubmit() {
  if (!folderForm.name?.trim()) {
    message.warning('请输入文件夹名称')
    return
  }
  try {
    if (folderModalMode.value === 'create') {
      await createPaperFolder({
        name: folderForm.name,
        parentId: folderForm.parentId,
      })
      message.success('文件夹已创建')
    } else {
      await updatePaperFolder(editingFolderId.value, {
        name: folderForm.name,
        parentId: folderForm.parentId,
      })
      message.success('文件夹已更新')
    }
    resetFolderModal()
    loadFolders()
  } catch (error) {
    message.error(error.message || '操作失败')
  }
}

function handleFolderContextMenu(e, node) {
  e.preventDefault()
  if (!canManagePaper.value) return
  Modal.confirm({
    title: '文件夹操作',
    content: `对文件夹「${node.name}」进行操作`,
    okText: '编辑',
    cancelText: '删除',
    async onOk() {
      openEditFolderModal(node)
    },
    onCancel() {
      handleDeleteFolder(node)
    },
  })
}

function handleDeleteFolder(folder) {
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
        if (selectedFolderKeys.value.includes(folder.id)) {
          selectedFolderKeys.value = []
          loadPapers()
        }
      } catch (error) {
        message.error(error.message || '删除失败')
      }
    },
  })
}

function openMoveModal(record) {
  if (!canManagePaper.value) return
  movingPaperId.value = record.id
  moveTargetFolderId.value = record.folderId
  moveModalVisible.value = true
}

async function handleMoveSubmit() {
  try {
    await movePaperToFolder(movingPaperId.value, moveTargetFolderId.value)
    message.success('试卷已移动')
    moveModalVisible.value = false
    loadPapers()
    loadFolders()
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

function formatDateTime(value) {
  if (!value) return '未设置'
  return String(value).replace('T', ' ').slice(0, 16)
}

onMounted(() => {
  loadFolders()
  loadPapers()
  applyQuickCreateFromRoute()
})

watch(() => route.fullPath, () => {
  pagination.current = 1
  loadPapers()
  applyQuickCreateFromRoute()
})
</script>

<style scoped>
.paper-manage-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #001234;
}

.page-sub {
  margin: 6px 0 0;
  color: #8c8c8c;
  font-size: 13px;
}

.content-layout {
  display: flex;
  gap: 16px;
  min-height: 500px;
}

.folder-panel {
  width: 260px;
  flex-shrink: 0;
  border-right: 1px solid #f0f0f0;
  padding-right: 16px;
}

.folder-panel-header {
  margin-bottom: 8px;
}

.folder-tree-container {
  overflow-y: auto;
  max-height: 600px;
}

.folder-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
}

.folder-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.paper-count {
  color: #8c8c8c;
  font-size: 12px;
}

.empty-tip {
  color: #8c8c8c;
  text-align: center;
  padding: 20px 0;
}

.paper-list-panel {
  flex: 1;
  min-width: 0;
}

.paper-list-header {
  margin-bottom: 16px;
}
</style>
