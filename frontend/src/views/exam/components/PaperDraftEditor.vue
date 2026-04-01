<template>
  <div class="paper-draft-editor">
    <a-form layout="vertical">
      <a-row :gutter="16">
        <a-col :span="24">
          <a-form-item label="试卷名称" required>
            <a-input v-model:value="draft.title" :disabled="disabled" @change="emitChange" />
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="试卷类型">
            <a-select v-model:value="draft.type" :disabled="disabled" @change="emitChange">
              <a-select-option value="formal">正式考核</a-select-option>
              <a-select-option value="quiz">测验</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="考试时长">
            <a-input-number v-model:value="draft.duration" :min="10" :max="300" :disabled="disabled" style="width:100%" @change="emitChange" />
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="及格分">
            <a-input-number v-model:value="draft.passingScore" :min="1" :disabled="disabled" style="width:100%" @change="emitChange" />
          </a-form-item>
        </a-col>
        <a-col :span="24">
          <a-form-item label="试卷说明">
            <a-textarea v-model:value="draft.description" :rows="3" :disabled="disabled" @change="emitChange" />
          </a-form-item>
        </a-col>
      </a-row>
    </a-form>

    <div class="editor-section">
      <div class="editor-header">
        <div>
          <div class="editor-title">试卷题目</div>
          <div class="editor-sub">共 {{ draft.questions.length }} 题，总分 {{ totalScore }} 分</div>
        </div>
        <a-space>
          <a-button v-if="allowQuestionPicker && !disabled" size="small" @click="openQuestionPicker">
            从题库选题
          </a-button>
          <a-button v-if="allowManualQuestion && !disabled" size="small" type="dashed" @click="emit('create-question')">
            手动新增题目
          </a-button>
        </a-space>
      </div>

      <a-empty v-if="!draft.questions.length" description="暂无题目" />
      <div v-else class="question-list">
        <div v-for="(item, index) in draft.questions" :key="item.tempId || item.sourceQuestionId || index" class="question-item">
          <div class="question-meta">
            <a-tag :color="typeColors[item.type]">{{ typeLabels[item.type] || item.type }}</a-tag>
            <span>{{ index + 1 }}.</span>
            <span class="question-origin">{{ originLabels[item.origin] || '任务题目' }}</span>
          </div>
          <div class="question-content">{{ item.content }}</div>
          <div class="question-foot">
            <span>分值 {{ item.score || 0 }}</span>
            <span>难度 {{ item.difficulty || 3 }}</span>
            <span>{{ formatKnowledgePoints(item.knowledgePoints) }}</span>
            <a-space v-if="!disabled && allowQuestionEdit">
              <a-button type="link" size="small" @click="emit('edit-question', item, index)">编辑</a-button>
              <a-button type="link" danger size="small" @click="removeQuestion(index)">移除</a-button>
            </a-space>
            <a-button v-else-if="!disabled" type="link" danger size="small" @click="removeQuestion(index)">移除</a-button>
          </div>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="pickerVisible"
      title="从题库选题"
      width="920px"
      ok-text="加入试卷"
      cancel-text="取消"
      @ok="confirmQuestionPick"
      @cancel="pickerVisible = false"
    >
      <div class="picker-toolbar">
        <a-input-search v-model:value="pickerSearch" placeholder="搜索题干或知识点" style="width:260px" @search="loadPickerQuestions" />
        <a-select v-model:value="pickerType" style="width:120px" @change="loadPickerQuestions">
          <a-select-option value="all">全部题型</a-select-option>
          <a-select-option value="single">单选题</a-select-option>
          <a-select-option value="multi">多选题</a-select-option>
          <a-select-option value="judge">判断题</a-select-option>
        </a-select>
      </div>
      <a-table
        :columns="pickerColumns"
        :data-source="pickerQuestions"
        :loading="pickerLoading"
        :pagination="pickerPagination"
        :row-selection="pickerRowSelection"
        row-key="id"
        size="small"
        @change="handlePickerTableChange"
      />
    </a-modal>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { getQuestions } from '@/api/question'
import { sortQuestionsByType } from '../utils/questionSort'

const props = defineProps({
  modelValue: { type: Object, required: true },
  disabled: { type: Boolean, default: false },
  allowQuestionPicker: { type: Boolean, default: true },
  allowManualQuestion: { type: Boolean, default: false },
  allowQuestionEdit: { type: Boolean, default: true },
  sortByType: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'edit-question', 'create-question'])

const typeLabels = { single: '单选题', multi: '多选题', judge: '判断题' }
const typeColors = { single: 'blue', multi: 'purple', judge: 'orange' }
const originLabels = { existing: '题库题目', generated: '智能生成', manual: '手动新增', ai_generated: 'AI 补充' }

const pickerVisible = ref(false)
const pickerSearch = ref('')
const pickerType = ref('all')
const pickerLoading = ref(false)
const pickerQuestions = ref([])
const pickerPagination = reactive({ current: 1, pageSize: 8, total: 0 })
const pickerSelectedMap = ref(new Map())
const pickerSelectedKeys = ref([])

const pickerColumns = [
  { title: '题干', dataIndex: 'content', key: 'content' },
  { title: '题型', dataIndex: 'type', key: 'type', width: 90 },
  { title: '知识点', dataIndex: 'knowledgePointNames', key: 'knowledgePointNames', width: 220 },
  { title: '分值', dataIndex: 'score', key: 'score', width: 80 },
]

const pickerRowSelection = computed(() => ({
  selectedRowKeys: pickerSelectedKeys.value,
  onChange: (keys, rows) => {
    pickerSelectedKeys.value = keys
    rows.forEach((item) => pickerSelectedMap.value.set(item.id, item))
  },
}))

const draft = computed(() => props.modelValue)
const totalScore = computed(() => (draft.value.questions || []).reduce((sum, item) => sum + Number(item.score || 0), 0))

function emitChange() {
  if (props.sortByType) {
    draft.value.questions = sortQuestionsByType(draft.value.questions || [])
  }
  draft.value.totalScore = totalScore.value
  emit('update:modelValue', JSON.parse(JSON.stringify(draft.value)))
}

function removeQuestion(index) {
  draft.value.questions.splice(index, 1)
  emitChange()
}

function openQuestionPicker() {
  pickerPagination.current = 1
  pickerSelectedMap.value = new Map()
  pickerSelectedKeys.value = []
  pickerVisible.value = true
  loadPickerQuestions()
}

async function loadPickerQuestions() {
  pickerLoading.value = true
  try {
    const result = await getQuestions({
      page: pickerPagination.current,
      size: pickerPagination.pageSize,
      search: pickerSearch.value || undefined,
      type: pickerType.value !== 'all' ? pickerType.value : undefined,
    })
    pickerQuestions.value = (result.items || []).map((item) => ({
      ...item,
      knowledgePointNames: item.knowledgePointNames
        || item.knowledgePoints?.map((point) => (typeof point === 'string' ? point : point?.name)).filter(Boolean)
        || [],
    }))
    pickerPagination.total = result.total || 0
  } catch (error) {
    message.error(error.message || '加载题库失败')
  } finally {
    pickerLoading.value = false
  }
}

function handlePickerTableChange(pagination) {
  pickerPagination.current = pagination.current
  pickerPagination.pageSize = pagination.pageSize
  loadPickerQuestions()
}

function confirmQuestionPick() {
  const existingIds = new Set((draft.value.questions || []).map((item) => item.sourceQuestionId).filter(Boolean))
  pickerSelectedKeys.value.forEach((questionId) => {
    const source = pickerSelectedMap.value.get(questionId)
    if (!source || existingIds.has(source.id)) {
      return
    }
    draft.value.questions.push(mapQuestionToDraft(source))
  })
  emitChange()
  pickerVisible.value = false
}

function mapQuestionToDraft(question) {
  const knowledgePoints = question.knowledgePointNames
    || question.knowledgePoints?.map((item) => (typeof item === 'string' ? item : item?.name)).filter(Boolean)
    || (question.knowledgePoint ? [question.knowledgePoint] : [])
    || []
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
    knowledgePointNames: knowledgePoints,
    policeTypeId: question.policeTypeId,
    score: Number(question.score || 1),
  }
}

function formatKnowledgePoints(points = []) {
  const values = Array.isArray(points)
    ? points.map((item) => (typeof item === 'string' ? item : item?.name)).filter(Boolean)
    : (points ? [String(points)] : [])
  return values.length ? values.join('、') : '未设置知识点'
}
</script>

<style scoped>
.editor-section {
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  padding: 16px;
  background: #fafafa;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

.editor-title {
  font-size: 15px;
  font-weight: 600;
  color: #001234;
}

.editor-sub {
  margin-top: 4px;
  color: #8c8c8c;
  font-size: 12px;
}

.question-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 420px;
  overflow-y: auto;
}

.question-item {
  padding: 12px 14px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #f0f0f0;
}

.question-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.question-origin {
  color: #8c8c8c;
  font-size: 12px;
}

.question-content {
  line-height: 1.6;
  color: #1f1f1f;
}

.question-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
  color: #8c8c8c;
  font-size: 12px;
}

.picker-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
</style>
