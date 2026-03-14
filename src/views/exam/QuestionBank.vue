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
          <a-input-search v-model:value="searchText" placeholder="搜索题目内容..." allow-clear @search="onSearch" />
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filterType" style="width:100%" @change="onFilterChange">
            <a-select-option value="all">全部题型</a-select-option>
            <a-select-option value="single">单选题</a-select-option>
            <a-select-option value="multi">多选题</a-select-option>
            <a-select-option value="judge">判断题</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filterDiff" style="width:100%" @change="onFilterChange">
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
        :dataSource="questionList"
        :columns="columns"
        :row-selection="rowSelection"
        size="small"
        :pagination="pagination"
        :loading="loading"
        @change="handleTableChange"
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
            <div class="expand-section" v-if="record.policeTypeName">
              <span class="expand-label">警种：</span>{{ record.policeTypeName }}
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
          <template v-if="column.key === 'policeTypeName'">
            {{ record.policeTypeName || '未设置' }}
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
          <a-col :span="24">
            <a-form-item label="警种">
              <a-select v-model:value="qForm.policeTypeId" allow-clear placeholder="可选，仅用于数据域管理">
                <a-select-option v-for="item in policeTypeOptions" :key="item.id" :value="item.id">
                  {{ item.name }}
                </a-select-option>
              </a-select>
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
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, RobotOutlined } from '@ant-design/icons-vue'
import { getQuestions, createQuestion, updateQuestion, deleteQuestion, batchCreateQuestions } from '@/api/question'
import { getPoliceTypes } from '@/api/user'

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
function diffToNum(str) {
  if (str === 'easy') return 2
  if (str === 'medium') return 3
  return 4
}

const loading = ref(false)
const questionList = ref([])
const policeTypeOptions = ref([])

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showTotal: t => `共 ${t} 道题`
})

const statsData = reactive({
  total: 0,
  single: 0,
  multi: 0,
  judge: 0
})

const stats = computed(() => [
  { label: '题目总数', value: statsData.total },
  { label: '单选题', value: statsData.single },
  { label: '多选题', value: statsData.multi },
  { label: '判断题', value: statsData.judge },
])

async function loadQuestions() {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      size: pagination.pageSize,
      search: searchText.value || undefined,
      type: filterType.value !== 'all' ? filterType.value : undefined,
      difficulty: filterDiff.value !== 'all' ? diffToNum(filterDiff.value) : undefined
    }
    const res = await getQuestions(params)
    questionList.value = (res.items || []).map(q => ({
      ...q,
      key: q.id,
      diffLevel: numToDiff(q.difficulty),
      options: q.options || (q.type === 'judge' ? [{key:'A',text:'正确'},{key:'B',text:'错误'}] : []),
    }))
    pagination.total = res.total || 0
  } catch (e) {
    message.error('加载题目失败')
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const p1 = getQuestions({ size: 1 })
    const p2 = getQuestions({ size: 1, type: 'single' })
    const p3 = getQuestions({ size: 1, type: 'multi' })
    const p4 = getQuestions({ size: 1, type: 'judge' })
    const [r1, r2, r3, r4] = await Promise.all([p1, p2, p3, p4])
    statsData.total = r1.total || 0
    statsData.single = r2.total || 0
    statsData.multi = r3.total || 0
    statsData.judge = r4.total || 0
  } catch { /* ignore */ }
}

async function loadPoliceTypes() {
  try {
    const result = await getPoliceTypes()
    policeTypeOptions.value = result.items || []
  } catch {
    policeTypeOptions.value = []
  }
}

function onSearch() {
  pagination.current = 1
  loadQuestions()
}
function onFilterChange() {
  pagination.current = 1
  loadQuestions()
}
function handleTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadQuestions()
}

onMounted(() => {
  loadQuestions()
  loadStats()
  loadPoliceTypes()
})

const rowSelection = { type: 'checkbox' }

const columns = [
  { title: '题目内容', key: 'content', ellipsis: true },
  { title: '题型', key: 'type', width: 80 },
  { title: '难度', key: 'difficulty', width: 80 },
  { title: '警种', dataIndex: 'policeTypeName', key: 'policeTypeName', width: 120 },
  { title: '操作', key: 'action', width: 120, fixed: 'right' },
]

// ─── 表单 ───
const defaultForm = () => ({
  type: 'single',
  diffLevel: 'medium',
  content: '',
  knowledgePoint: '',
  policeTypeId: undefined,
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
    policeTypeId: record.policeTypeId,
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

const submitting = ref(false)

const handleSaveQ = async () => {
  if (!qForm.content.trim()) { message.warning('请填写题目内容'); return }
  const finalAnswer = qForm.type === 'multi' ? [...qForm.answerArr] : qForm.answer
  if (!finalAnswer || (Array.isArray(finalAnswer) && !finalAnswer.length)) {
    message.warning('请设置正确答案'); return
  }
  const payload = {
    type: qForm.type,
    content: qForm.content,
    knowledge_point: qForm.knowledgePoint,
    policeTypeId: qForm.policeTypeId || undefined,
    options: qForm.type === 'judge'
      ? [{ key: 'A', text: '正确' }, { key: 'B', text: '错误' }]
      : qForm.options.map(o => ({ key: o.key, text: o.text })),
    answer: finalAnswer,
    explanation: qForm.explanation,
    difficulty: diffToNum(qForm.diffLevel),
    score: 2,
  }

  submitting.value = true
  try {
    if (editingQ.value && editingQ.value.id) {
      await updateQuestion(editingQ.value.id, payload)
      message.success('题目已更新')
    } else {
      await createQuestion(payload)
      message.success('题目已添加')
    }
    closeModal()
    loadQuestions()
    loadStats()
  } catch (e) {
    message.error(e.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = (record) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除这道题目吗？`,
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteQuestion(record.id)
        message.success('已删除')
        loadQuestions()
        loadStats()
      } catch (e) {
        message.error('删除失败')
      }
    },
  })
}

// 供 AI 组卷页面调用：保存到题库
window.__addQuestionsToBank = async (questions) => {
  const payloadQuestions = questions.map((q) => ({
    type: q.type || 'single',
    difficulty: 3, // 默认中等
    options: q.options
      ? q.options.map((text, oi) => ({ key: String.fromCharCode(65 + oi), text: String(text) }))
      : [],
    content: q.stem || q.content || '',
    answer: q.answer,
    explanation: q.explanation || '',
    knowledge_point: q.knowledgePoint || ''
  }))
  try {
    await batchCreateQuestions({ questions: payloadQuestions })
    message.success(`已保存 ${payloadQuestions.length} 道 AI 生成题目到真实题库`)
    loadQuestions()
    loadStats()
  } catch (e) {
    message.error('保存失败')
  }
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
