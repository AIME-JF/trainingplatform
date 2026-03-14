<template>
  <div class="question-bank-page">
    <div class="page-header">
      <div>
        <h2>试题仓库</h2>
        <p class="page-sub">统一维护题库题目，AI 智能出题任务确认后会进入这里</p>
      </div>
      <a-space>
        <a-button @click="$router.push('/question/ai')">
          <template #icon><RobotOutlined /></template>
          AI 智能出题
        </a-button>
        <a-button type="primary" @click="openAddModal">
          <template #icon><PlusOutlined /></template>
          手动新增
        </a-button>
      </a-space>
    </div>

    <a-row :gutter="16" class="stats-row">
      <a-col v-for="item in stats" :key="item.label" :span="6">
        <a-card :bordered="false" size="small" class="stats-card">
          <div class="stats-value">{{ item.value }}</div>
          <div class="stats-label">{{ item.label }}</div>
        </a-card>
      </a-col>
    </a-row>

    <a-card :bordered="false" style="margin-bottom:16px">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-input-search v-model:value="searchText" placeholder="搜索题干或知识点" allow-clear @search="reloadQuestions" />
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filterType" style="width:100%" @change="reloadQuestions">
            <a-select-option value="all">全部题型</a-select-option>
            <a-select-option value="single">单选题</a-select-option>
            <a-select-option value="multi">多选题</a-select-option>
            <a-select-option value="judge">判断题</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filterDifficulty" style="width:100%" @change="reloadQuestions">
            <a-select-option value="all">全部难度</a-select-option>
            <a-select-option v-for="level in [1, 2, 3, 4, 5]" :key="level" :value="level">
              {{ difficultyLabels[level] }}
            </a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </a-card>

    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data-source="questionList"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #expandedRowRender="{ record }">
          <div class="expand-row">
            <div class="expand-item" v-if="record.options?.length">
              <span class="expand-label">选项：</span>
              <span v-for="item in record.options" :key="item.key" class="expand-tag">
                {{ item.key }}. {{ item.text }}
              </span>
            </div>
            <div class="expand-item">
              <span class="expand-label">答案：</span>
              <span class="expand-answer">{{ formatAnswer(record.answer) }}</span>
            </div>
            <div class="expand-item" v-if="record.explanation">
              <span class="expand-label">解析：</span>
              <span>{{ record.explanation }}</span>
            </div>
            <div class="expand-item" v-if="record.knowledgePoint">
              <span class="expand-label">知识点：</span>
              <span>{{ record.knowledgePoint }}</span>
            </div>
            <div class="expand-item" v-if="record.policeTypeName">
              <span class="expand-label">警种：</span>
              <span>{{ record.policeTypeName }}</span>
            </div>
          </div>
        </template>

        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'content'">
            <div class="content-cell">{{ record.content }}</div>
          </template>
          <template v-else-if="column.key === 'type'">
            <a-tag :color="typeColors[record.type]">{{ typeLabels[record.type] }}</a-tag>
          </template>
          <template v-else-if="column.key === 'difficulty'">
            <a-tag :color="difficultyColors[record.difficulty]">{{ difficultyLabels[record.difficulty] }}</a-tag>
          </template>
          <template v-else-if="column.key === 'score'">
            {{ record.score || 0 }} 分
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="openEditModal(record)">编辑</a-button>
              <a-button type="link" danger size="small" @click="handleDelete(record)">删除</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

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
import { computed, onMounted, reactive, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, RobotOutlined } from '@ant-design/icons-vue'
import { createQuestion, deleteQuestion, getQuestions, updateQuestion } from '@/api/question'
import { getPoliceTypes } from '@/api/user'
import QuestionFormModal from './components/QuestionFormModal.vue'

const loading = ref(false)
const modalOpen = ref(false)
const editingQuestion = ref(null)
const questionList = ref([])
const policeTypeOptions = ref([])
const searchText = ref('')
const filterType = ref('all')
const filterDifficulty = ref('all')

const typeLabels = { single: '单选题', multi: '多选题', judge: '判断题' }
const typeColors = { single: 'blue', multi: 'purple', judge: 'orange' }
const difficultyLabels = { 1: '1级', 2: '2级', 3: '3级', 4: '4级', 5: '5级' }
const difficultyColors = { 1: 'green', 2: 'cyan', 3: 'blue', 4: 'orange', 5: 'red' }

const columns = [
  { title: '题干', key: 'content' },
  { title: '题型', key: 'type', width: 110 },
  { title: '难度', key: 'difficulty', width: 100 },
  { title: '分值', key: 'score', width: 90 },
  { title: '警种', dataIndex: 'policeTypeName', key: 'policeTypeName', width: 120 },
  { title: '操作', key: 'action', width: 120 },
]

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showTotal: (total) => `共 ${total} 道题`,
})

const statsState = reactive({
  total: 0,
  single: 0,
  multi: 0,
  judge: 0,
})

const stats = computed(() => ([
  { label: '题目总数', value: statsState.total },
  { label: '单选题', value: statsState.single },
  { label: '多选题', value: statsState.multi },
  { label: '判断题', value: statsState.judge },
]))

function openAddModal() {
  editingQuestion.value = null
  modalOpen.value = true
}

function openEditModal(record) {
  editingQuestion.value = { ...record }
  modalOpen.value = true
}

function reloadQuestions() {
  pagination.current = 1
  loadQuestions()
}

async function loadQuestions() {
  loading.value = true
  try {
    const result = await getQuestions({
      page: pagination.current,
      size: pagination.pageSize,
      search: searchText.value || undefined,
      type: filterType.value !== 'all' ? filterType.value : undefined,
      difficulty: filterDifficulty.value !== 'all' ? filterDifficulty.value : undefined,
    })
    questionList.value = (result.items || []).map((item) => ({
      ...item,
      options: item.options || (item.type === 'judge'
        ? [{ key: 'A', text: '正确' }, { key: 'B', text: '错误' }]
        : []),
    }))
    pagination.total = result.total || 0
  } catch (error) {
    message.error(error.message || '加载试题失败')
  } finally {
    loading.value = false
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
    await Promise.all([loadQuestions(), loadStats()])
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
        await Promise.all([loadQuestions(), loadStats()])
      } catch (error) {
        message.error(error.message || '删除失败')
      }
    },
  })
}

function handleTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadQuestions()
}

function formatAnswer(answer) {
  return Array.isArray(answer) ? answer.join('、') : answer
}

onMounted(() => {
  loadQuestions()
  loadStats()
  loadPoliceTypeOptions()
})
</script>

<style scoped>
.question-bank-page {
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

.stats-row {
  margin-bottom: 20px;
}

.stats-card {
  text-align: center;
}

.stats-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--police-primary);
}

.stats-label {
  margin-top: 6px;
  color: #8c8c8c;
  font-size: 12px;
}

.content-cell {
  max-width: 460px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.expand-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.expand-item {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  color: #434343;
}

.expand-label {
  color: #8c8c8c;
}

.expand-tag {
  padding: 2px 8px;
  border-radius: 999px;
  background: #f5f5f5;
}

.expand-answer {
  color: #389e0d;
  font-weight: 600;
}
</style>
