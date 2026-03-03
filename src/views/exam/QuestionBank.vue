<template>
  <div class="question-bank-page">
    <div class="page-header">
      <h2>题库管理</h2>
      <a-space>
        <a-button @click="$router.push('/ai/question-gen')">
          <template #icon><RobotOutlined /></template>AI 生成题目
        </a-button>
        <a-button type="primary" @click="openAddModal">
          <template #icon><PlusOutlined /></template>手动添加
        </a-button>
      </a-space>
    </div>

    <!-- 统计 -->
    <a-row :gutter="16" style="margin-bottom:20px">
      <a-col :span="6" v-for="s in stats" :key="s.label">
        <a-card :bordered="false" size="small" style="text-align:center">
          <div style="font-size:24px;font-weight:700;color:var(--police-primary)">{{ s.value }}</div>
          <div style="font-size:12px;color:#888">{{ s.label }}</div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 过滤 -->
    <a-card :bordered="false" style="margin-bottom:16px">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-input-search v-model:value="searchText" placeholder="搜索题目内容..." allow-clear />
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filterType" style="width:100%">
            <a-select-option value="all">全部题型</a-select-option>
            <a-select-option value="single">单选题</a-select-option>
            <a-select-option value="multi">多选题</a-select-option>
            <a-select-option value="judge">判断题</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filterDiff" style="width:100%">
            <a-select-option value="all">全部难度</a-select-option>
            <a-select-option value="easy">简单</a-select-option>
            <a-select-option value="medium">中等</a-select-option>
            <a-select-option value="hard">困难</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </a-card>

    <!-- 题目列表 -->
    <a-card :bordered="false">
      <a-table
        :dataSource="filteredQuestions"
        :columns="columns"
        :row-selection="rowSelection"
        size="small"
        :pagination="{ pageSize: 10, showTotal: t => `共 ${t} 道题` }"
        row-key="id"
      >
        <template #expandedRowRender="{ record }">
          <div class="expand-row">
            <div class="expand-section" v-if="record.options && record.options.length">
              <span class="expand-label">选项：</span>
              <span v-for="opt in record.options" :key="opt.key" class="expand-opt">
                {{ opt.key }}. {{ opt.text }}
              </span>
            </div>
            <div class="expand-section">
              <span class="expand-label">正确答案：</span>
              <span class="expand-answer">{{ Array.isArray(record.answer) ? record.answer.join('、') : record.answer }}</span>
            </div>
            <div class="expand-section" v-if="record.explanation">
              <span class="expand-label">解析：</span>{{ record.explanation }}
            </div>
            <div class="expand-section" v-if="record.knowledgePoint">
              <span class="expand-label">知识点：</span>{{ record.knowledgePoint }}
            </div>
          </div>
        </template>
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'content'">
            <div class="q-stem-preview">{{ record.content }}</div>
          </template>
          <template v-if="column.key === 'type'">
            <a-tag :color="typeColors[record.type]" size="small">{{ typeLabels[record.type] }}</a-tag>
          </template>
          <template v-if="column.key === 'difficulty'">
            <a-tag :color="diffColors[record.diffLevel]" size="small">{{ diffLabels[record.diffLevel] }}</a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space size="small">
              <a-button type="link" size="small" @click="openEditModal(record)">编辑</a-button>
              <a-button type="link" size="small" danger @click="handleDelete(record)">删除</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 添加/编辑 Modal -->
    <a-modal
      v-model:open="showModal"
      :title="editingQ ? '编辑题目' : '手动添加题目'"
      width="680px"
      @ok="handleSaveQ"
      @cancel="closeModal"
      ok-text="保存"
      cancel-text="取消"
    >
      <a-form :model="qForm" layout="vertical" style="margin-top:12px">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="题型" required>
              <a-select v-model:value="qForm.type" @change="onTypeChange">
                <a-select-option value="single">单选题</a-select-option>
                <a-select-option value="multi">多选题</a-select-option>
                <a-select-option value="judge">判断题</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="难度">
              <a-select v-model:value="qForm.diffLevel">
                <a-select-option value="easy">简单</a-select-option>
                <a-select-option value="medium">中等</a-select-option>
                <a-select-option value="hard">困难</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="题目内容" required>
              <a-textarea v-model:value="qForm.content" :rows="3" placeholder="请输入题目内容..." :maxlength="300" show-count />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="知识点">
              <a-input v-model:value="qForm.knowledgePoint" placeholder="例：刑事诉讼法-强制措施" />
            </a-form-item>
          </a-col>
        </a-row>

        <!-- 选项（单选/多选） -->
        <template v-if="qForm.type !== 'judge'">
          <a-form-item label="选项">
            <div v-for="(opt, idx) in qForm.options" :key="idx" class="option-row">
              <span class="opt-key">{{ opt.key }}.</span>
              <a-input v-model:value="opt.text" :placeholder="`选项 ${opt.key}`" style="flex:1" />
              <a-button type="link" danger size="small" @click="removeOption(idx)" v-if="qForm.options.length > 2">✕</a-button>
            </div>
            <a-button size="small" @click="addOption" v-if="qForm.options.length < 6" style="margin-top:8px">
              + 添加选项
            </a-button>
          </a-form-item>
          <a-form-item label="正确答案" required>
            <template v-if="qForm.type === 'single'">
              <a-radio-group v-model:value="qForm.answer">
                <a-radio v-for="opt in qForm.options" :key="opt.key" :value="opt.key">{{ opt.key }}</a-radio>
              </a-radio-group>
            </template>
            <template v-else>
              <a-checkbox-group v-model:value="qForm.answerArr">
                <a-checkbox v-for="opt in qForm.options" :key="opt.key" :value="opt.key">{{ opt.key }}</a-checkbox>
              </a-checkbox-group>
            </template>
          </a-form-item>
        </template>

        <!-- 判断题答案 -->
        <template v-else>
          <a-form-item label="正确答案" required>
            <a-radio-group v-model:value="qForm.answer">
              <a-radio value="A">正确</a-radio>
              <a-radio value="B">错误</a-radio>
            </a-radio-group>
          </a-form-item>
        </template>

        <a-form-item label="解析">
          <a-textarea v-model:value="qForm.explanation" :rows="2" placeholder="请输入答案解析（选填）" :maxlength="500" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, RobotOutlined } from '@ant-design/icons-vue'
import { MOCK_QUESTIONS } from '@/mock/exams'

const router = useRouter()
const searchText = ref('')
const filterType = ref('all')
const filterDiff = ref('all')
const showModal = ref(false)
const editingQ = ref(null)

const typeColors = { single: 'blue', multi: 'purple', judge: 'orange' }
const typeLabels = { single: '单选', multi: '多选', judge: '判断' }
const diffColors  = { easy: 'green', medium: 'orange', hard: 'red' }
const diffLabels  = { easy: '简单', medium: '中等', hard: '困难' }

// 难度数字→字符串
function numToDiff(n) {
  if (n <= 2) return 'easy'
  if (n === 3) return 'medium'
  return 'hard'
}

// 本地可编辑题库列表
const questionList = ref(
  MOCK_QUESTIONS.map((q, i) => ({
    ...q,
    key: q.id || String(i),
    diffLevel: numToDiff(q.difficulty),
    // 判断题补充选项
    options: q.options || [
      { key: 'A', text: '正确' },
      { key: 'B', text: '错误' },
    ],
  }))
)

const filteredQuestions = computed(() => {
  let list = questionList.value
  if (searchText.value) list = list.filter(q => q.content?.includes(searchText.value))
  if (filterType.value !== 'all') list = list.filter(q => q.type === filterType.value)
  if (filterDiff.value !== 'all') list = list.filter(q => q.diffLevel === filterDiff.value)
  return list
})

const stats = computed(() => [
  { label: '题目总数', value: questionList.value.length },
  { label: '单选题', value: questionList.value.filter(q => q.type === 'single').length },
  { label: '多选题', value: questionList.value.filter(q => q.type === 'multi').length },
  { label: '判断题', value: questionList.value.filter(q => q.type === 'judge').length },
])

const rowSelection = { type: 'checkbox' }

const columns = [
  { title: '题目内容', key: 'content', ellipsis: true },
  { title: '题型', key: 'type', width: 80 },
  { title: '难度', key: 'difficulty', width: 80 },
  { title: '操作', key: 'action', width: 120, fixed: 'right' },
]

// ─── 表单 ───
const defaultForm = () => ({
  type: 'single',
  diffLevel: 'medium',
  content: '',
  knowledgePoint: '',
  options: [
    { key: 'A', text: '' },
    { key: 'B', text: '' },
    { key: 'C', text: '' },
    { key: 'D', text: '' },
  ],
  answer: 'A',
  answerArr: [],
  explanation: '',
})

const qForm = reactive(defaultForm())

const onTypeChange = () => {
  qForm.answer = 'A'
  qForm.answerArr = []
  if (qForm.type === 'judge') {
    qForm.options = [{ key: 'A', text: '正确' }, { key: 'B', text: '错误' }]
  } else if (qForm.options.length < 4) {
    qForm.options = [
      { key: 'A', text: '' }, { key: 'B', text: '' },
      { key: 'C', text: '' }, { key: 'D', text: '' },
    ]
  }
}

const addOption = () => {
  const keys = 'ABCDEF'
  const nextKey = keys[qForm.options.length]
  if (nextKey) qForm.options.push({ key: nextKey, text: '' })
}

const removeOption = (idx) => {
  qForm.options.splice(idx, 1)
}

const openAddModal = () => {
  editingQ.value = null
  Object.assign(qForm, defaultForm())
  showModal.value = true
}

const openEditModal = (record) => {
  editingQ.value = record
  Object.assign(qForm, {
    type: record.type,
    diffLevel: record.diffLevel,
    content: record.content,
    knowledgePoint: record.knowledgePoint || '',
    options: record.options ? record.options.map(o => ({ ...o })) : [],
    answer: Array.isArray(record.answer) ? record.answer[0] : record.answer,
    answerArr: Array.isArray(record.answer) ? [...record.answer] : [],
    explanation: record.explanation || '',
  })
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingQ.value = null
}

const handleSaveQ = () => {
  if (!qForm.content.trim()) { message.warning('请填写题目内容'); return }
  const finalAnswer = qForm.type === 'multi' ? [...qForm.answerArr] : qForm.answer
  if (!finalAnswer || (Array.isArray(finalAnswer) && !finalAnswer.length)) {
    message.warning('请设置正确答案'); return
  }
  const newQ = {
    id: editingQ.value?.id || `q${Date.now()}`,
    key: editingQ.value?.id || `q${Date.now()}`,
    type: qForm.type,
    diffLevel: qForm.diffLevel,
    content: qForm.content,
    knowledgePoint: qForm.knowledgePoint,
    options: qForm.type === 'judge'
      ? [{ key: 'A', text: '正确' }, { key: 'B', text: '错误' }]
      : qForm.options.map(o => ({ ...o })),
    answer: finalAnswer,
    explanation: qForm.explanation,
    difficulty: qForm.diffLevel === 'easy' ? 2 : qForm.diffLevel === 'medium' ? 3 : 4,
    score: 2,
  }
  if (editingQ.value) {
    const idx = questionList.value.findIndex(q => q.id === editingQ.value.id)
    if (idx !== -1) questionList.value[idx] = newQ
    message.success('题目已更新')
  } else {
    questionList.value.unshift(newQ)
    message.success('题目已添加到题库')
  }
  closeModal()
}

const handleDelete = (record) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除这道题目吗？`,
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: () => {
      questionList.value = questionList.value.filter(q => q.id !== record.id)
      message.success('已删除')
    },
  })
}

// 供 AI 组卷页面调用：保存到题库
window.__addQuestionsToBank = (questions) => {
  const newQs = questions.map((q, i) => ({
    ...q,
    id: `ai_${Date.now()}_${i}`,
    key: `ai_${Date.now()}_${i}`,
    diffLevel: 'medium',
    options: q.options
      ? q.options.map((text, oi) => ({ key: String.fromCharCode(65 + oi), text }))
      : [],
    content: q.stem || q.content || '',
  }))
  questionList.value.unshift(...newQs)
  message.success(`已保存 ${newQs.length} 道 AI 生成题目到题库`)
}
</script>

<style scoped>
.question-bank-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.q-stem-preview { max-width: 420px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; color: #1a1a1a; }

/* 展开行 */
.expand-row { padding: 4px 0; display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: #444; }
.expand-section { display: flex; align-items: flex-start; gap: 6px; flex-wrap: wrap; }
.expand-label { color: #888; white-space: nowrap; }
.expand-opt { background: #f5f5f5; padding: 1px 8px; border-radius: 4px; margin-right: 4px; }
.expand-answer { color: #52c41a; font-weight: 700; }

/* 选项编辑 */
.option-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.opt-key { width: 20px; font-weight: 700; color: var(--police-primary); }
</style>
