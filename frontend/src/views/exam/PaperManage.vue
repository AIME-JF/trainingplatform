<template>
  <div class="paper-manage-page">
    <!-- 顶部通栏 -->
    <header class="page-header-bar">
      <div class="header-left">
        <div class="logo-icon">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
        </div>
        <div class="header-title">
          <span class="title-main">试卷仓库</span>
          <div class="title-sub">
            <span>考试系统</span>
            <span class="text-slate-200">/</span>
            <span>试卷管理</span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <a-button @click="openManageFolderModal">管理目录</a-button>
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
          :allowed="canManagePaper"
          tips="需要 CREATE_EXAM 权限"
          v-slot="{ disabled }"
        >
          <a-button type="primary" :disabled="disabled" @click="openCreateDrawer">
            <template #icon><PlusOutlined /></template>
            新建试卷
          </a-button>
        </permissions-tooltip>
      </div>
    </header>

    <!-- 内容区域 -->
    <div class="content-area">
      <div class="content-inner">
        <!-- 标题和搜索 -->
        <div class="page-title-row">
          <div>
            <h1 class="page-title">试卷仓库</h1>
            <p class="page-desc">统一维护试卷草稿，智能组卷和智能生成试卷确认后会进入这里</p>
          </div>
          <div class="search-box">
            <a-input-search v-model:value="searchText" placeholder="搜索试卷名称..." allow-clear @search="handleSearch" style="width: 288px" />
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
                <span class="stat-label">试卷总计</span>
                <span class="stat-value">{{ statsState.total }}</span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-legend">
                <span class="legend-item"><i class="w-2 h-2 rounded-full bg-green-500"></i><span class="legend-num">{{ statsState.published }}</span>已发布</span>
                <span class="legend-item"><i class="w-2 h-2 rounded-full bg-orange-500"></i><span class="legend-num">{{ statsState.draft }}</span>草稿</span>
                <span class="legend-item"><i class="w-2 h-2 rounded-full bg-gray-400"></i><span class="legend-num">{{ statsState.archived }}</span>已归档</span>
              </div>
            </div>
          </div>

          <!-- Tab 切换栏 -->
          <div class="view-tabs">
            <div :class="['tab-item', { active: currentView === 'policeType' }]" @click="switchView('policeType')">
              <TeamOutlined /> 警种视角
            </div>
            <div :class="['tab-item', { active: currentView === 'course' }]" @click="switchView('course')">
              <BookOutlined /> 课程视角
            </div>
            <div :class="['tab-item', { active: currentView === 'knowledgePoint' }]" @click="switchView('knowledgePoint')">
              <AimOutlined /> 知识点视角
            </div>
          </div>

          <!-- 警种筛选 -->
          <div v-if="currentView === 'policeType'" class="view-filter">
            <a-select
              v-model="selectedPoliceTypeIds"
              mode="multiple"
              placeholder="请选择警种筛选"
              :options="policeTypeSelectOptions"
              style="width: 400px"
              @change="handleFilterChange"
            />
          </div>

          <!-- 课程筛选 -->
          <div v-if="currentView === 'course'" class="view-filter">
            <a-select
              v-model="selectedCourseIds"
              mode="multiple"
              placeholder="请选择课程"
              :loading="courseLoading"
              :options="courseSelectOptions"
              show-search
              :filter-option="false"
              @search="handleCourseSearch"
              @change="handleFilterChange"
              style="width: 400px"
            />
          </div>

          <!-- 知识点筛选 -->
          <div v-if="currentView === 'knowledgePoint'" class="view-filter">
            <a-select
              v-model="selectedKpIds"
              mode="multiple"
              placeholder="请选择知识点"
              :loading="kpLoading"
              :options="kpSelectOptions"
              show-search
              :filter-option="false"
              style="width: 500px"
              @change="handleFilterChange"
            />
          </div>

          <!-- 列表标题栏 -->
          <div class="list-header">
            <div class="col-folder">所属文件夹</div>
            <div class="col-content">试卷名称</div>
            <div class="col-status text-center">状态</div>
            <div class="col-type text-center">类型</div>
            <div class="col-count text-center">引用数</div>
            <div class="col-action text-right">操作</div>
          </div>

          <!-- 文件夹分组区域 -->
          <div class="folder-list">
            <div
              v-for="group in displayedGroups"
              :key="group.id"
              :class="['folder-group', { 'folder-collapsed': !group.expanded }]"
            >
              <!-- 文件夹标题行 -->
              <div
                class="folder-title"
                :class="{ 'folder-drag-over': currentView === 'folder' && dragOverFolderId === group.id }"
                @click="toggleFolder(group.id)"
                @dragover="currentView === 'folder' && handleDragOver($event, group)"
                @dragleave="currentView === 'folder' && handleDragLeave($event, group)"
                @drop="currentView === 'folder' && handleDropToFolder($event, group)"
              >
                <div class="folder-title-left">
                  <svg :class="['chevron-icon', { 'rotated': group.expanded }]" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"/></svg>
                  <svg v-if="currentView === 'policeType'" class="folder-icon" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
                  <svg v-else-if="currentView === 'course'" class="folder-icon" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
                  <svg v-else-if="currentView === 'knowledgePoint'" class="folder-icon" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                  <span class="folder-name">{{ group.name }}</span>
                </div>
                <div class="folder-title-desc">包含 {{ group.name }} 等 {{ group.paperCount }} 份试卷</div>
                <div class="folder-title-actions" v-if="currentView === 'folder'">
                  <a-button type="link" size="small" class="batch-move-btn" @click.stop="openBatchMoveModal(group)">批量移动</a-button>
                </div>
              </div>

              <!-- 试卷内容区 -->
              <div
                class="folder-content"
                :class="{ 'folder-drag-over': currentView === 'folder' && dragOverFolderId === group.id }"
                @dragover="currentView === 'folder' && handleDragOver($event, group)"
                @dragleave="currentView === 'folder' && handleDragLeave($event, group)"
                @drop="currentView === 'folder' && handleDropToFolder($event, group)"
              >
                <div
                  v-for="(record, index) in group.papers"
                  :key="record.id"
                  class="paper-row"
                  :draggable="currentView === 'folder'"
                  @dragstart="currentView === 'folder' && handlePaperDragStart($event, record, group)"
                  @dragend="handleDragEnd"
                >
                  <div class="col-folder text-xs text-slate-400">{{ group.name }}</div>
                  <div class="col-content">
                    <p class="paper-title text-sm text-slate-700 font-medium">{{ index + 1 }}. {{ record.title }}</p>
                    <p class="paper-desc text-xs text-slate-400">{{ record.description || '暂无描述' }}</p>
                  </div>
                  <div class="col-status flex justify-center">
                    <span :class="['tag-pill', statusTagColors[record.status]]">{{ statusLabels[record.status] }}</span>
                  </div>
                  <div class="col-type flex justify-center">
                    <span :class="['tag-pill', typeTagColors[record.type]]">{{ typeLabels[record.type] }}</span>
                  </div>
                  <div class="col-count text-center text-sm font-semibold text-slate-600">{{ record.usageCount || 0 }}</div>
                  <div class="col-action text-right flex justify-end gap-4">
                    <a-button type="link" size="small" class="text-slate-400 hover:text-blue-600" @click="openViewDrawer(record)">查看</a-button>
                    <permissions-tooltip
                      v-if="record.status === 'draft'"
                      :allowed="canManagePaper"
                      tips="需要 CREATE_EXAM 权限"
                      v-slot="{ disabled }"
                    >
                      <a-button type="link" size="small" class="text-slate-400 hover:text-blue-600" :disabled="disabled" @click="openEditDrawer(record)">编辑</a-button>
                    </permissions-tooltip>
                    <permissions-tooltip
                      v-if="record.status === 'draft'"
                      :allowed="canManagePaper"
                      tips="需要 CREATE_EXAM 权限"
                      v-slot="{ disabled }"
                    >
                      <a-button type="link" size="small" class="text-slate-400 hover:text-green-600" :disabled="disabled" @click="handlePublish(record)">发布</a-button>
                    </permissions-tooltip>
                    <permissions-tooltip
                      v-if="record.status === 'published'"
                      :allowed="canManagePaper"
                      tips="需要 CREATE_EXAM 权限"
                      v-slot="{ disabled }"
                    >
                      <a-button type="link" size="small" class="text-slate-400 hover:text-orange-600" :disabled="disabled" @click="handleArchive(record)">归档</a-button>
                    </permissions-tooltip>
                    <permissions-tooltip
                      v-if="record.usageCount === 0"
                      :allowed="canManagePaper"
                      tips="需要 CREATE_EXAM 权限"
                      v-slot="{ disabled }"
                    >
                      <a-button type="link" size="small" danger class="text-slate-300 hover:text-red-500" :disabled="disabled" @click="handleDelete(record)">
                        <DeleteOutlined />
                      </a-button>
                    </permissions-tooltip>
                  </div>
                </div>
                <div v-if="!group.papers || group.papers.length === 0" class="empty-folder">
                  该{{ currentView === 'folder' ? '文件夹' : '分组' }}下暂无试卷
                </div>
              </div>
            </div>
          </div>

          <!-- 底部 Footer -->
          <div class="list-footer">
            <div class="footer-info">
              <span>当前展开 {{ expandedFolders.size }} 个{{ viewLabel }}分组</span>
              <span class="text-slate-200">|</span>
              <span>列表更新于 {{ currentTime }}</span>
            </div>
            <div class="pagination">
              <a-button size="small" :disabled="pagination.current <= 1" @click="handlePrevPage"><LeftOutlined /></a-button>
              <a-button size="small" class="current-page">{{ pagination.current }}</a-button>
              <a-button size="small" :disabled="pagination.current >= totalPages" @click="handleNextPage"><RightOutlined /></a-button>
            </div>
          </div>
        </div>
      </div>
    </div>

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
          <permissions-tooltip
            :allowed="canManagePaper"
            tips="需要 CREATE_EXAM 权限"
            v-slot="{ disabled }"
          >
            <a-button type="primary" size="small" :disabled="disabled" @click="openCreateFolderModal">
              <template #icon><PlusOutlined /></template>
              新建文件夹
            </a-button>
          </permissions-tooltip>
        </div>
        <div class="folder-manager-list">
          <div v-for="folder in filteredFolderList" :key="folder.id" class="folder-manager-item">
            <div class="folder-manager-item-left">
              <FolderOutlined />
              <span>{{ folder.name }}</span>
              <span class="text-xs text-slate-400">({{ folder.paperCount }}份试卷)</span>
            </div>
            <div class="folder-manager-item-actions">
              <permissions-tooltip
                :allowed="canManagePaper"
                tips="需要 CREATE_EXAM 权限"
                v-slot="{ disabled }"
              >
                <a-button type="link" size="small" :disabled="disabled" @click="openEditFolderModal(folder)">编辑</a-button>
              </permissions-tooltip>
              <permissions-tooltip
                :allowed="canManagePaper"
                tips="需要 CREATE_EXAM 权限"
                v-slot="{ disabled }"
              >
                <a-button type="link" size="small" danger :disabled="disabled" @click="handleDeleteFolder(folder)">删除</a-button>
              </permissions-tooltip>
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
import { PlusOutlined, DeleteOutlined, LeftOutlined, RightOutlined, FolderOutlined, BookOutlined, AimOutlined, DownOutlined, RobotOutlined, SwapOutlined, TeamOutlined } from '@ant-design/icons-vue'
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
    paperList.value = papers.map(paper => ({
      ...paper,
      knowledgePointNames: paper.knowledgePointNames || [],
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
  gap: 32px;
}

.legend-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #64748B;
  font-weight: 600;
}

.legend-num {
  font-size: 24px;
  font-weight: 700;
  color: #1E293B;
  line-height: 1;
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

.col-folder { width: 160px; flex-shrink: 0; }
.col-content { flex: 1; padding-right: 32px; }
.col-status { width: 100px; flex-shrink: 0; }
.col-type { width: 100px; flex-shrink: 0; }
.col-count { width: 80px; flex-shrink: 0; }
.col-action { width: 200px; flex-shrink: 0; }

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
  outline: 2px dashed #2563EB;
  outline-offset: -2px;
}

.folder-title-left {
  width: 160px;
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
  width: 200px;
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
  overflow: visible;
  transition: max-height 0.3s ease-out, background-color 0.15s;
  min-height: 1px;
}

.folder-content.folder-drag-over {
  background: #EFF6FF;
  outline: 2px dashed #2563EB;
  outline-offset: -2px;
}

.folder-collapsed .folder-content {
  max-height: 0;
  overflow: hidden;
}

.paper-row {
  display: flex;
  align-items: center;
  padding: 16px 32px;
  border-bottom: 1px solid #FAFAFA;
  transition: background-color 0.15s;
}

.paper-row:hover {
  background: #EFF6FF;
}

.paper-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 500px;
}

.paper-desc {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 500px;
  margin-top: 4px;
}

.empty-folder {
  padding: 20px 40px;
  text-align: center;
  color: #94A3B8;
  font-size: 14px;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.folder-content:not(.folder-drag-over) .empty-folder {
  color: #94A3B8;
}

.folder-content.folder-drag-over .empty-folder {
  color: #2563EB;
  font-weight: 500;
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
.tag-gray { background: #F1F5F9; color: #64748B; }

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

/* 多维度视图 Tab */
.view-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
}

.tab-item {
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  color: #64748B;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-item:hover {
  background: #F1F5F9;
}

.tab-item.active {
  background: #2563EB;
  color: white;
}

.view-filter {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #F8FAFC;
  border-radius: 8px;
}

/* 通用样式 */
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
