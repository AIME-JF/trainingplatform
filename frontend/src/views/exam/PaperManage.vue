<template>
  <div class="paper-manage-page">
    <div class="page-header">
      <div>
        <h2>试卷管理</h2>
        <p class="page-sub">先从统一题库配置试卷，发布后供准入考试和培训班考试复用</p>
      </div>
      <a-button type="primary" @click="openCreateDrawer">
        <template #icon><PlusOutlined /></template>新建试卷
      </a-button>
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
              <a-button v-if="record.status === 'draft'" type="link" size="small" @click="openEditDrawer(record)">编辑</a-button>
              <a-button v-else type="link" size="small" @click="openViewDrawer(record)">查看</a-button>
              <a-button v-if="record.status === 'draft'" type="link" size="small" @click="handlePublish(record)">发布</a-button>
              <a-button v-if="record.status === 'published'" type="link" size="small" @click="handleArchive(record)">归档</a-button>
              <a-button
                v-if="record.usageCount === 0"
                type="link"
                danger
                size="small"
                @click="handleDelete(record)"
              >
                删除
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-drawer
      v-model:open="drawerVisible"
      :title="drawerTitle"
      width="760"
      @close="resetForm"
    >
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="24">
            <a-form-item label="试卷名称" required>
              <a-input v-model:value="form.title" :disabled="isViewMode" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="试卷类型">
              <a-select v-model:value="form.type" :disabled="isViewMode">
                <a-select-option value="formal">正式考核</a-select-option>
                <a-select-option value="quiz">测验</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="考试时长">
              <a-input-number v-model:value="form.duration" :min="10" :max="300" :disabled="isViewMode" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="及格分">
              <a-input-number v-model:value="form.passingScore" :min="1" :disabled="isViewMode" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="试卷说明">
              <a-textarea v-model:value="form.description" :rows="3" :disabled="isViewMode" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="试卷题目" required>
              <div class="selected-questions">
                <div class="selected-header">
                  <span>已选 {{ form.questionIds.length }} 题，总分 {{ dynamicTotalScore }} 分</span>
                  <a-button v-if="!isViewMode" type="primary" size="small" ghost @click="openQuestionPicker">
                    从题库选题
                  </a-button>
                </div>
                <div v-if="selectedQuestionsCache.length" class="q-cache-list">
                  <div class="q-cache-item" v-for="(item, index) in selectedQuestionsCache" :key="item.id">
                    <span>{{ index + 1 }}.</span>
                    <span>[{{ typeLabels[item.type] || item.type }}]</span>
                    <span class="q-cached-content">{{ item.content }}</span>
                    <span>{{ item.score || 0 }}分</span>
                    <a-button v-if="!isViewMode" type="link" danger size="small" @click="removeSelectedQ(item.id)">移除</a-button>
                  </div>
                </div>
                <a-empty v-else description="暂未配置题目" />
              </div>
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
      <template #footer>
        <a-space style="float:right">
          <a-button @click="resetForm">关闭</a-button>
          <a-button v-if="!isViewMode" type="primary" :loading="submitting" @click="handleSave">保存</a-button>
        </a-space>
      </template>
    </a-drawer>

    <a-modal
      v-model:open="pickerVisible"
      title="从题库选题"
      width="900px"
      @ok="confirmQuestionPick"
      @cancel="pickerVisible = false"
    >
      <div class="picker-toolbar">
        <a-input-search v-model:value="qpSearch" placeholder="搜索题干" style="width:250px" @search="loadPickerQ" />
        <a-select v-model:value="qpType" style="width:120px" @change="loadPickerQ">
          <a-select-option value="all">所有题型</a-select-option>
          <a-select-option value="single">单选</a-select-option>
          <a-select-option value="multi">多选</a-select-option>
          <a-select-option value="judge">判断</a-select-option>
        </a-select>
      </div>
      <a-table
        :columns="qpColumns"
        :data-source="qpList"
        row-key="id"
        :row-selection="qpRowSelection"
        :pagination="qpPagination"
        :loading="qpLoading"
        @change="handleQpTableChange"
        size="small"
      />
    </a-modal>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useRoute } from 'vue-router'
import {
  archiveExamPaper,
  createExamPaper,
  deleteExamPaper,
  getExamPaperDetail,
  getExamPapers,
  publishExamPaper,
  updateExamPaper,
} from '@/api/exam'
import { getQuestions } from '@/api/question'

const route = useRoute()

const statusLabels = { draft: '草稿', published: '已发布', archived: '已归档' }
const statusColors = { draft: 'orange', published: 'green', archived: 'default' }
const typeLabels = { single: '单选', multi: '多选', judge: '判断', formal: '正式考核', quiz: '测验' }

const searchText = ref('')
const filterStatus = ref('all')
const filterType = ref('all')
const loading = ref(false)
const submitting = ref(false)
const paperList = ref([])
const drawerVisible = ref(false)
const drawerMode = ref('create')
const editingId = ref(null)
const handledQuickCreate = ref('')

const pagination = reactive({ current: 1, pageSize: 10, total: 0 })
const columns = [
  { title: '试卷名称', dataIndex: 'title', key: 'title' },
  { title: '状态', key: 'status', width: 100 },
  { title: '类型', key: 'type', width: 100 },
  { title: '题目数', dataIndex: 'questionCount', key: 'questionCount', width: 90 },
  { title: '引用数', dataIndex: 'usageCount', key: 'usageCount', width: 90 },
  { title: '更新时间', key: 'updatedAt', width: 170 },
  { title: '操作', key: 'action', width: 220 },
]

const form = reactive({
  title: '',
  description: '',
  type: 'formal',
  duration: 60,
  passingScore: 60,
  questionIds: [],
})
const selectedQuestionsCache = ref([])
const dynamicTotalScore = computed(() => selectedQuestionsCache.value.reduce((sum, item) => sum + (item.score || 0), 0))
const isViewMode = computed(() => drawerMode.value === 'view')
const drawerTitle = computed(() => {
  if (drawerMode.value === 'edit') return '编辑试卷'
  if (drawerMode.value === 'view') return '查看试卷'
  return '新建试卷'
})

function resetForm() {
  Object.assign(form, {
    title: '',
    description: '',
    type: 'formal',
    duration: 60,
    passingScore: 60,
    questionIds: [],
  })
  selectedQuestionsCache.value = []
  drawerVisible.value = false
  drawerMode.value = 'create'
  editingId.value = null
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
    message.error(error.message || '加载试卷列表失败')
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadPapers()
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

function openCreateDrawer() {
  resetForm()
  drawerMode.value = 'create'
  drawerVisible.value = true
}

async function loadPaperDetail(id, mode) {
  resetForm()
  drawerMode.value = mode
  editingId.value = id
  try {
    const detail = await getExamPaperDetail(id)
    form.title = detail.title
    form.description = detail.description || ''
    form.type = detail.type || 'formal'
    form.duration = detail.duration || 60
    form.passingScore = detail.passingScore || 60
    form.questionIds = (detail.questions || []).map(item => item.id)
    selectedQuestionsCache.value = detail.questions || []
    drawerVisible.value = true
  } catch (error) {
    message.error(error.message || '加载试卷详情失败')
  }
}

function openEditDrawer(record) {
  loadPaperDetail(record.id, 'edit')
}

function openViewDrawer(record) {
  loadPaperDetail(record.id, 'view')
}

function removeSelectedQ(id) {
  form.questionIds = form.questionIds.filter(item => item !== id)
  selectedQuestionsCache.value = selectedQuestionsCache.value.filter(item => item.id !== id)
}

async function handleSave() {
  if (!form.title) {
    message.warning('请输入试卷名称')
    return
  }
  if (!form.questionIds.length) {
    message.warning('请至少选择一道题目')
    return
  }

  submitting.value = true
  try {
    const payload = {
      title: form.title,
      description: form.description || undefined,
      type: form.type,
      duration: form.duration,
      passingScore: form.passingScore,
      totalScore: dynamicTotalScore.value,
      questionIds: form.questionIds,
    }
    if (drawerMode.value === 'edit') {
      await updateExamPaper(editingId.value, payload)
      message.success('试卷已更新')
    } else {
      await createExamPaper(payload)
      message.success('试卷已创建')
    }
    resetForm()
    loadPapers()
  } catch (error) {
    message.error(error.message || '保存失败')
  } finally {
    submitting.value = false
  }
}

function handlePublish(record) {
  Modal.confirm({
    title: '确认发布试卷',
    content: `发布后【${record.title}】将不能再修改试题，是否继续？`,
    async onOk() {
      try {
        await publishExamPaper(record.id)
        message.success('试卷已发布')
        loadPapers()
      } catch (error) {
        message.error(error.message || '发布试卷失败')
      }
    },
  })
}

function handleArchive(record) {
  Modal.confirm({
    title: '确认归档试卷',
    content: `归档后【${record.title}】将不再出现在考试创建列表中，是否继续？`,
    async onOk() {
      try {
        await archiveExamPaper(record.id)
        message.success('试卷已归档')
        loadPapers()
      } catch (error) {
        message.error(error.message || '归档试卷失败')
      }
    },
  })
}

function handleDelete(record) {
  Modal.confirm({
    title: '确认删除试卷',
    content: `删除后无法恢复，是否删除【${record.title}】？`,
    async onOk() {
      try {
        await deleteExamPaper(record.id)
        message.success('试卷已删除')
        loadPapers()
      } catch (error) {
        message.error(error.message || '删除试卷失败')
      }
    },
  })
}

const pickerVisible = ref(false)
const qpSearch = ref('')
const qpType = ref('all')
const qpLoading = ref(false)
const qpList = ref([])
const qpPagination = reactive({ current: 1, pageSize: 10, total: 0 })
const tempSelectedRowKeys = ref([])
const tempSelectedRowsMap = ref(new Map())

const qpColumns = [
  { title: '题干', dataIndex: 'content', key: 'content' },
  { title: '题型', dataIndex: 'type', key: 'type', width: 80 },
  { title: '分值', dataIndex: 'score', key: 'score', width: 80 },
]

const qpRowSelection = computed(() => ({
  selectedRowKeys: tempSelectedRowKeys.value,
  onChange: (keys, rows) => {
    tempSelectedRowKeys.value = keys
    rows.forEach(item => tempSelectedRowsMap.value.set(item.id, item))
  },
}))

async function loadPickerQ() {
  qpLoading.value = true
  try {
    const result = await getQuestions({
      page: qpPagination.current,
      size: qpPagination.pageSize,
      search: qpSearch.value || undefined,
      type: qpType.value !== 'all' ? qpType.value : undefined,
    })
    qpList.value = result.items || []
    qpPagination.total = result.total || 0
  } catch (error) {
    message.error(error.message || '加载题库失败')
  } finally {
    qpLoading.value = false
  }
}

function openQuestionPicker() {
  qpPagination.current = 1
  tempSelectedRowKeys.value = [...form.questionIds]
  tempSelectedRowsMap.value = new Map(selectedQuestionsCache.value.map(item => [item.id, item]))
  pickerVisible.value = true
  loadPickerQ()
}

function handleQpTableChange(pag) {
  qpPagination.current = pag.current
  qpPagination.pageSize = pag.pageSize
  loadPickerQ()
}

function confirmQuestionPick() {
  form.questionIds = [...tempSelectedRowKeys.value]
  selectedQuestionsCache.value = form.questionIds.map(id => tempSelectedRowsMap.value.get(id)).filter(Boolean)
  pickerVisible.value = false
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
.paper-manage-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 16px; }
.page-header h2 { margin: 0; color: #001234; }
.page-sub { margin: 6px 0 0; font-size: 13px; color: #8c8c8c; }
.selected-questions { border: 1px solid #e8e8e8; border-radius: 8px; padding: 12px; background: #fafafa; }
.selected-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.q-cache-list { display: flex; flex-direction: column; gap: 8px; max-height: 360px; overflow-y: auto; }
.q-cache-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #fff; border: 1px solid #f0f0f0; border-radius: 6px; }
.q-cached-content { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.picker-toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
</style>
