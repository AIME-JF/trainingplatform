<template>
  <div class="paper-manage-page">
    <div class="page-header">
      <div>
        <h2>试卷仓库</h2>
        <p class="page-sub">统一维护试卷草稿，AI 自动组卷和 AI 自动生成试卷确认后会进入这里</p>
      </div>
      <a-space>
        <permissions-tooltip
          :allowed="canOpenAiAssembleTask"
          tips="需要 GET_AI_PAPER_ASSEMBLY_TASKS 或 CREATE_AI_PAPER_ASSEMBLY_TASK 权限"
          v-slot="{ disabled }"
        >
          <a-button :disabled="disabled" @click="$router.push('/paper/ai-assemble')">
            <template #icon><RobotOutlined /></template>
            AI 自动组卷
          </a-button>
        </permissions-tooltip>
        <permissions-tooltip
          :allowed="canOpenAiGenerateTask"
          tips="需要 GET_AI_PAPER_GENERATION_TASKS 或 CREATE_AI_PAPER_GENERATION_TASK 权限"
          v-slot="{ disabled }"
        >
          <a-button :disabled="disabled" @click="$router.push('/paper/ai-generate')">
            <template #icon><RobotOutlined /></template>
            AI 自动生成试卷
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

    <a-card :bordered="false" style="margin-bottom:16px">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-input-search v-model:value="searchText" placeholder="搜索试卷名称..." allow-clear @search="loadPapers" />
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filterStatus" style="width:100%" @change="loadPapers">
            <a-select-option value="all">全部状态</a-select-option>
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="published">已发布</a-select-option>
            <a-select-option value="archived">已归档</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filterType" style="width:100%" @change="loadPapers">
            <a-select-option value="all">全部类型</a-select-option>
            <a-select-option value="formal">正式考核</a-select-option>
            <a-select-option value="quiz">测验</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </a-card>

    <a-card :bordered="false">
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
              <permissions-tooltip
                v-if="record.usageCount === 0"
                :allowed="canManagePaper"
                tips="需要 CREATE_EXAM 权限"
                v-slot="{ disabled }"
              >
                <a-button type="link" danger size="small" :disabled="disabled" @click="handleDelete(record)">删除</a-button>
              </permissions-tooltip>
            </a-space>
          </template>
        </template>
      </a-table>
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
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, RobotOutlined } from '@ant-design/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  archiveExamPaper,
  createExamPaper,
  deleteExamPaper,
  getExamPaperDetail,
  getExamPapers,
  publishExamPaper,
  updateExamPaper,
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

function createEmptyDraft() {
  return {
    title: '',
    description: '',
    type: 'formal',
    duration: 60,
    passingScore: 60,
    totalScore: 0,
    questions: [],
  }
}

function resetDraft() {
  Object.assign(paperDraft, createEmptyDraft())
  drawerVisible.value = false
  drawerMode.value = 'create'
  editingId.value = null
}

function mapPaperQuestion(question) {
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
    knowledgePoint: question.knowledgePoint,
    policeTypeId: question.policeTypeId,
    score: Number(question.score || 1),
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

function openCreateDrawer() {
  if (!canManagePaper.value) return
  resetDraft()
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
</style>
