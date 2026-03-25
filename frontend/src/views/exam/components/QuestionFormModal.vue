<template>
  <a-modal
    :open="open"
    :title="title"
    width="720px"
    :ok-text="confirmText"
    cancel-text="取消"
    @update:open="emit('update:open', $event)"
    @ok="handleOk"
    @cancel="emit('update:open', false)"
  >
    <a-form layout="vertical">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-form-item label="题型" required>
            <a-select v-model:value="form.type" :disabled="typeOptions.length === 1" @change="handleTypeChange">
              <a-select-option v-for="item in typeOptions" :key="item.value" :value="item.value">
                {{ item.label }}
              </a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="难度" required>
            <a-select v-model:value="form.difficulty">
              <a-select-option v-for="level in [1, 2, 3, 4, 5]" :key="level" :value="level">
                {{ difficultyLabels[level] }}
              </a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="分值" required>
            <a-input-number v-model:value="form.score" :min="1" :max="50" style="width:100%" />
          </a-form-item>
        </a-col>
        <a-col :span="24">
          <a-form-item label="题目内容" required>
            <a-textarea v-model:value="form.content" :rows="3" :maxlength="500" show-count />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item
            label="知识点"
            extra="可输入关键词搜索知识点；不输入时默认展示前 20 条，也可直接输入新知识点。"
          >
            <a-select
              v-model:value="form.knowledgePointNames"
              mode="tags"
              allow-clear
              show-search
              :filter-option="false"
              :loading="knowledgePointLoading"
              :max-tag-count="4"
              placeholder="可输入搜索知识点，也可直接输入新知识点"
              :options="knowledgePointSelectOptions"
              @search="handleKnowledgePointSearch"
              @focus="handleKnowledgePointFocus"
            />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="警种">
            <a-select v-model:value="form.policeTypeId" allow-clear placeholder="可选">
              <a-select-option v-for="item in policeTypeOptions" :key="item.id" :value="item.id">
                {{ item.name }}
              </a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>

      <template v-if="form.type !== 'judge'">
        <a-form-item label="选项" required>
          <div v-for="(option, index) in form.options" :key="option.key" class="option-row">
            <span class="option-key">{{ option.key }}.</span>
            <a-input v-model:value="option.text" :placeholder="`请输入选项 ${option.key}`" />
            <a-button
              v-if="form.options.length > 2"
              type="link"
              danger
              size="small"
              @click="removeOption(index)"
            >
              删除
            </a-button>
          </div>
          <a-button v-if="form.options.length < 6" size="small" @click="addOption">
            添加选项
          </a-button>
        </a-form-item>

        <a-form-item label="正确答案" required>
          <a-radio-group v-if="form.type === 'single'" v-model:value="form.answer">
            <a-radio v-for="option in form.options" :key="option.key" :value="option.key">
              {{ option.key }}
            </a-radio>
          </a-radio-group>
          <a-checkbox-group v-else v-model:value="form.answerMulti">
            <a-checkbox v-for="option in form.options" :key="option.key" :value="option.key">
              {{ option.key }}
            </a-checkbox>
          </a-checkbox-group>
        </a-form-item>
      </template>

      <template v-else>
        <a-form-item label="正确答案" required>
          <a-radio-group v-model:value="form.answer">
            <a-radio value="A">正确</a-radio>
            <a-radio value="B">错误</a-radio>
          </a-radio-group>
        </a-form-item>
      </template>

      <a-form-item label="解析">
        <a-textarea v-model:value="form.explanation" :rows="3" :maxlength="500" show-count />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import { createKnowledgePointRemoteSelect, mergeKnowledgePointOptions } from '../utils/knowledgePointRemoteSelect'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '编辑题目' },
  confirmText: { type: String, default: '保存' },
  question: { type: Object, default: null },
  policeTypeOptions: { type: Array, default: () => [] },
  knowledgePointOptions: { type: Array, default: () => [] },
  allowedTypes: { type: Array, default: () => ['single', 'multi', 'judge'] },
})

const emit = defineEmits(['update:open', 'submit'])

const difficultyLabels = {
  1: '1级',
  2: '2级',
  3: '3级',
  4: '4级',
  5: '5级',
}
const allTypeOptions = [
  { value: 'single', label: '单选题' },
  { value: 'multi', label: '多选题' },
  { value: 'judge', label: '判断题' },
]
const typeOptions = computed(() => {
  const allowedTypes = Array.isArray(props.allowedTypes) ? props.allowedTypes : []
  if (!allowedTypes.length) {
    return allTypeOptions
  }
  return allTypeOptions.filter((item) => allowedTypes.includes(item.value))
})
const {
  knowledgePointSelectOptions,
  knowledgePointLoading,
  pinKnowledgePointOptions,
  loadKnowledgePointOptions,
  handleKnowledgePointSearch,
  handleKnowledgePointFocus,
} = createKnowledgePointRemoteSelect('name')

function createDefaultForm() {
  return {
    tempId: '',
    sourceQuestionId: undefined,
    origin: 'manual',
    type: 'single',
    difficulty: 3,
    score: 2,
    content: '',
    knowledgePointNames: [],
    policeTypeId: undefined,
    options: [
      { key: 'A', text: '' },
      { key: 'B', text: '' },
      { key: 'C', text: '' },
      { key: 'D', text: '' },
    ],
    answer: 'A',
    answerMulti: [],
    explanation: '',
  }
}

const form = reactive(createDefaultForm())

function resetForm(question = null) {
  const allowedTypes = typeOptions.value.map((item) => item.value)
  const resolvedType = allowedTypes.includes(question?.type) ? question?.type : (allowedTypes[0] || 'single')
  const next = createDefaultForm()
  Object.assign(next, {
    tempId: question?.tempId || question?.id || `draft-${Date.now()}`,
    sourceQuestionId: question?.sourceQuestionId || question?.source_question_id,
    origin: question?.origin || 'manual',
    type: resolvedType,
    difficulty: Number(question?.difficulty || 3),
    score: Number(question?.score || 2),
    content: question?.content || '',
    knowledgePointNames: resolveKnowledgePointNames(question),
    policeTypeId: question?.policeTypeId || question?.police_type_id,
    options: normalizeOptions(resolvedType, question?.options),
    explanation: question?.explanation || '',
  })
  next.answer = resolvedType === 'multi'
    ? 'A'
    : normalizeSingleAnswer(question?.answer)
  next.answerMulti = resolvedType === 'multi'
    ? normalizeMultiAnswer(question?.answer)
    : []
  Object.assign(form, next)
  pinKnowledgePointOptions(
    mergeKnowledgePointOptions(
      props.knowledgePointOptions,
      next.knowledgePointNames.map((item) => ({ name: item })),
    ),
  )
}

function normalizeOptions(type, options) {
  if (type === 'judge') {
    return [
      { key: 'A', text: '正确' },
      { key: 'B', text: '错误' },
    ]
  }
  const fallback = ['A', 'B', 'C', 'D'].map((key) => ({ key, text: '' }))
  if (!Array.isArray(options) || !options.length) {
    return fallback
  }
  return options.map((item, index) => ({
    key: item.key || String.fromCharCode(65 + index),
    text: item.text || '',
  }))
}

function normalizeSingleAnswer(answer) {
  if (Array.isArray(answer)) {
    return answer[0] || 'A'
  }
  return answer || 'A'
}

function normalizeMultiAnswer(answer) {
  if (Array.isArray(answer)) {
    return answer
  }
  return answer ? [answer] : []
}

function resolveKnowledgePointNames(question) {
  const rawValue = question?.knowledgePointNames
    || question?.knowledge_point_names
    || question?.knowledgePoints
    || question?.knowledge_points
    || question?.knowledgePoint
    || question?.knowledge_point

  const rawItems = Array.isArray(rawValue)
    ? rawValue
    : (rawValue ? [rawValue] : [])

  return [...new Set(rawItems.map((item) => {
    if (typeof item === 'string') {
      return item.trim()
    }
    return String(item?.name || '').trim()
  }).filter(Boolean))]
}

function normalizeKnowledgePointNames(names = []) {
  return [...new Set((names || []).map((item) => String(item || '').trim()).filter(Boolean))]
}

function handleTypeChange() {
  if (form.type === 'judge') {
    form.options = normalizeOptions('judge')
    form.answer = 'A'
    form.answerMulti = []
    return
  }
  if (form.options.length < 4) {
    form.options = normalizeOptions(form.type)
  }
  form.answer = 'A'
  form.answerMulti = []
}

function addOption() {
  const optionKey = String.fromCharCode(65 + form.options.length)
  form.options.push({ key: optionKey, text: '' })
}

function removeOption(index) {
  form.options.splice(index, 1)
}

function handleOk() {
  if (!form.content.trim()) {
    message.warning('请填写题目内容')
    return
  }

  if (form.type !== 'judge') {
    if (form.options.some((item) => !item.text?.trim())) {
      message.warning('请完整填写所有选项')
      return
    }
    if (form.type === 'multi' && form.answerMulti.length === 0) {
      message.warning('请至少选择一个正确答案')
      return
    }
    if (form.type === 'single' && !form.answer) {
      message.warning('请选择正确答案')
      return
    }
  }

  const knowledgePointNames = normalizeKnowledgePointNames(form.knowledgePointNames)
  emit('submit', {
    tempId: form.tempId || `draft-${Date.now()}`,
    sourceQuestionId: form.sourceQuestionId || undefined,
    origin: form.origin || 'manual',
    type: form.type,
    difficulty: Number(form.difficulty || 3),
    score: Number(form.score || 2),
    content: form.content.trim(),
    knowledgePointNames,
    knowledgePoints: [...knowledgePointNames],
    policeTypeId: form.policeTypeId || undefined,
    options: form.type === 'judge' ? normalizeOptions('judge') : form.options.map((item) => ({ ...item })),
    answer: form.type === 'multi' ? [...form.answerMulti] : form.answer,
    explanation: form.explanation?.trim() || undefined,
  })
  emit('update:open', false)
}

watch(
  () => props.open,
  (value) => {
    if (value) {
      resetForm(props.question)
      loadKnowledgePointOptions().catch(() => {})
    }
  },
  { immediate: true }
)

watch(
  () => props.allowedTypes,
  () => {
    if (props.open) {
      resetForm(props.question)
    }
  },
  { deep: true }
)

watch(
  () => props.knowledgePointOptions,
  (value) => {
    pinKnowledgePointOptions(value)
  },
  { deep: true, immediate: true }
)

watch(
  () => form.knowledgePointNames,
  (value) => {
    pinKnowledgePointOptions((value || []).map((item) => ({ name: item })))
  },
  { deep: true, immediate: true }
)
</script>

<style scoped>
.option-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.option-key {
  width: 24px;
  font-weight: 700;
  color: var(--police-primary);
}
</style>
