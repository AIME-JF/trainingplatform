<template>
  <div class="exam-do-page">
    <div class="exam-header">
      <div class="exam-title">
        <h1>{{ examDetail?.title || '考试' }}</h1>
        <div class="exam-time" :class="{ warning: remainingTime < 300 }">
          <ClockCircleOutlined />
          <span>{{ formatDuration(remainingTime) }}</span>
        </div>
      </div>
      <div class="exam-progress-info">
        <span>第 {{ currentIndex + 1 }} / {{ questions.length }} 题</span>
        <span class="progress-sep">|</span>
        <span>已答 {{ answeredCount }} 题</span>
      </div>
      <a-progress
        :percent="progressPercent"
        :show-info="false"
        class="exam-progress"
      />
    </div>

    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" />
    </div>

    <template v-else-if="questions.length > 0">
      <div class="question-card">
        <div class="question-header">
          <a-tag class="type-tag" :color="getQuestionTypeColor(currentQuestion?.type)">
            {{ getQuestionTypeText(currentQuestion?.type) }}
          </a-tag>
          <span class="question-score">{{ currentQuestion?.score || 0 }} 分</span>
        </div>

        <div class="question-content">
          {{ currentQuestion?.content }}
        </div>

        <div class="question-options">
          <template v-if="currentQuestion?.type === 'multiple_choice'">
            <div
              v-for="(option, index) in currentOptions"
              :key="index"
              class="option-item multiple"
              :class="{ selected: isOptionSelected(option.key) }"
              @click="toggleOption(option.key)"
            >
              <div class="option-checkbox">
                <CheckOutlined v-if="isOptionSelected(option.key)" />
              </div>
              <span class="option-label">{{ option.key }}.</span>
              <span class="option-text">{{ option.value }}</span>
            </div>
          </template>
          <template v-else>
            <div
              v-for="(option, index) in currentOptions"
              :key="index"
              class="option-item single"
              :class="{ selected: answers[currentQuestion?.id ?? 0] === option.key }"
              @click="selectOption(option.key)"
            >
              <div class="option-radio">
                <div v-if="answers[currentQuestion?.id ?? 0] === option.key" class="radio-inner" />
              </div>
              <span class="option-label">{{ option.key }}.</span>
              <span class="option-text">{{ option.value }}</span>
            </div>
          </template>
        </div>
      </div>

      <div v-if="currentQuestion?.explanation" class="question-explanation">
        <div class="explanation-title">
          <InfoCircleOutlined /> 解析
        </div>
        <p>{{ currentQuestion.explanation }}</p>
      </div>

      <div class="question-nav">
        <a-button :disabled="currentIndex === 0" @click="prevQuestion">
          <LeftOutlined /> 上一题
        </a-button>
        <a-button type="primary" @click="showAnswerSheet = !showAnswerSheet">
          <MenuOutlined /> 答题卡
        </a-button>
        <a-button v-if="currentIndex < questions.length - 1" type="primary" @click="nextQuestion">
          下一题 <RightOutlined />
        </a-button>
        <a-button v-else type="primary" @click="showSubmitConfirm">
          提交试卷
        </a-button>
      </div>
    </template>

    <a-drawer
      v-model:open="showAnswerSheet"
      title="答题卡"
      placement="bottom"
      height="auto"
      class="answer-sheet-drawer"
    >
      <div class="answer-sheet">
        <div class="answer-sheet-info">
          <span>共 {{ questions.length }} 题</span>
          <span>已答 {{ answeredCount }} 题</span>
        </div>
        <div class="answer-grid">
          <div
            v-for="(q, index) in questions"
            :key="q.id"
            class="answer-item"
            :class="{
              current: index === currentIndex,
              answered: answers[q.id] !== undefined && answers[q.id] !== '',
            }"
            @click="goToQuestion(index)"
          >
            {{ index + 1 }}
          </div>
        </div>
      </div>
      <div class="answer-sheet-actions">
        <a-button type="primary" long @click="showSubmitConfirm">提交试卷</a-button>
      </div>
    </a-drawer>

    <a-modal
      v-model:open="submitModalVisible"
      title="确认提交"
      @ok="handleSubmit"
      @cancel="submitModalVisible = false"
    >
      <div class="submit-confirm">
        <p>您已回答 <strong>{{ answeredCount }}</strong> / {{ questions.length }} 题</p>
        <p v-if="answeredCount < questions.length" class="warning-text">
          还有 {{ questions.length - answeredCount }} 题未作答，确定要提交吗？
        </p>
        <p>提交后将无法修改答案。</p>
      </div>
    </a-modal>

    <a-modal
      v-model:open="submitting"
      title="提交中"
      :footer="null"
      :closable="false"
      :maskClosable="false"
    >
      <div class="submitting-wrapper">
        <a-spin size="large" />
        <p>正在提交答案...</p>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import {
  CheckOutlined,
  ClockCircleOutlined,
  InfoCircleOutlined,
  LeftOutlined,
  MenuOutlined,
  RightOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { ExamDetailResponse, ExamQuestionSnapshotResponse } from '@/api/generated/model'
import {
  getAdmissionExamApiV1ExamsAdmissionExamIdGet,
  getExamApiV1ExamsExamIdGet,
  submitAdmissionExamApiV1ExamsAdmissionExamIdSubmitPost,
  submitExamApiV1ExamsExamIdSubmitPost,
} from '@/api/generated/exam-management/exam-management'
import type { ExamSubmitAnswers } from '@/api/generated/model'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const examId = computed(() => Number(route.params.id))
const examKind = ref<'admission' | 'training'>('training')

const examDetail = ref<ExamDetailResponse | null>(null)
const questions = ref<ExamQuestionSnapshotResponse[]>([])
const currentIndex = ref(0)
const answers = reactive<Record<number, string | string[]>>({})
const showAnswerSheet = ref(false)
const submitModalVisible = ref(false)

// 计时器
const remainingTime = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const currentQuestion = computed(() => questions.value[currentIndex.value])

const currentOptions = computed(() => {
  const opts = currentQuestion.value?.options
  if (!opts || !Array.isArray(opts)) return []
  return opts.map((item) => {
    const [key, value] = Object.entries(item)[0]
    return { key, value: String(value) }
  })
})

const answeredCount = computed(() => {
  return Object.keys(answers).filter((k) => {
    const v = answers[Number(k)]
    return v !== undefined && v !== '' && (Array.isArray(v) ? v.length > 0 : true)
  }).length
})

const progressPercent = computed(() => {
  if (questions.value.length === 0) return 0
  return Math.round((answeredCount.value / questions.value.length) * 100)
})

onMounted(async () => {
  await fetchExamDetail()
})

onBeforeUnmount(() => {
  if (timer) {
    clearInterval(timer)
  }
})

async function fetchExamDetail() {
  loading.value = true
  try {
    // 判断是准入考试还是培训班考试
    let detail
    try {
      detail = await getExamApiV1ExamsExamIdGet(examId.value)
      examKind.value = 'training'
    } catch {
      detail = await getAdmissionExamApiV1ExamsAdmissionExamIdGet(examId.value)
      examKind.value = 'admission'
    }

    examDetail.value = detail

    if (detail.questions) {
      questions.value = detail.questions
    } else {
      // 如果没有题目数据，获取题目详情
      message.warning('该考试暂无题目')
    }

    // 设置倒计时
    if (detail.duration) {
      remainingTime.value = detail.duration * 60
      startTimer()
    }
  } catch (error) {
    message.error('加载考试详情失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

function startTimer() {
  if (timer) clearInterval(timer)
  timer = setInterval(() => {
    if (remainingTime.value > 0) {
      remainingTime.value--
    } else {
      if (timer) clearInterval(timer)
      message.warning('考试时间已到，自动提交')
      void handleSubmit()
    }
  }, 1000)
}

function formatDuration(seconds: number) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) {
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  return `${m}:${String(s).padStart(2, '0')}`
}

function isOptionSelected(key: string) {
  const answer = answers[currentQuestion.value?.id ?? 0]
  if (Array.isArray(answer)) {
    return answer.includes(key)
  }
  return false
}

function selectOption(key: string) {
  if (currentQuestion.value) {
    answers[currentQuestion.value.id] = key
  }
}

function toggleOption(key: string) {
  const qid = currentQuestion.value?.id
  if (!qid) return

  const current = answers[qid]
  if (!Array.isArray(current)) {
    answers[qid] = [key]
  } else {
    const index = current.indexOf(key)
    if (index === -1) {
      current.push(key)
    } else {
      current.splice(index, 1)
    }
    answers[qid] = [...current]
  }
}

function prevQuestion() {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

function nextQuestion() {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++
  }
}

function goToQuestion(index: number) {
  currentIndex.value = index
  showAnswerSheet.value = false
}

function showSubmitConfirm() {
  submitModalVisible.value = true
}

async function handleSubmit() {
  submitModalVisible.value = false
  submitting.value = true

  try {
    // 构建答案格式
    const answersData: ExamSubmitAnswers = {}
    for (const [qid, answer] of Object.entries(answers)) {
      if (answer !== undefined && answer !== '') {
        answersData[Number(qid)] = answer
      }
    }

    const submitData = {
      answers: answersData,
      start_time: new Date().toISOString(),
    }

    if (examKind.value === 'admission') {
      await submitAdmissionExamApiV1ExamsAdmissionExamIdSubmitPost(examId.value, submitData)
    } else {
      await submitExamApiV1ExamsExamIdSubmitPost(examId.value, submitData)
    }

    message.success('提交成功')
    await router.replace(`/exam/result/${examId.value}`)
  } catch (error) {
    message.error(error instanceof Error ? error.message : '提交失败')
    submitting.value = false
  }
}

function getQuestionTypeColor(type?: string) {
  switch (type) {
    case 'single_choice':
      return 'blue'
    case 'multiple_choice':
      return 'purple'
    case 'true_false':
      return 'green'
    default:
      return 'default'
  }
}

function getQuestionTypeText(type?: string) {
  switch (type) {
    case 'single_choice':
      return '单选题'
    case 'multiple_choice':
      return '多选题'
    case 'true_false':
      return '判断题'
    default:
      return type || '未知'
  }
}
</script>

<style scoped>
.exam-do-page {
  min-height: 100vh;
  background: var(--v2-bg);
  padding: 20px;
}

.exam-header {
  background: var(--v2-bg-card);
  border-radius: 20px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 8px 24px rgba(24, 39, 75, 0.06);
}

.exam-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.exam-title h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: var(--v2-text-primary);
}

.exam-time {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 999px;
  background: var(--v2-primary-light);
  color: var(--v2-primary);
  font-weight: 600;
  font-size: 16px;
}

.exam-time.warning {
  background: rgba(255, 59, 48, 0.1);
  color: var(--v2-danger);
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.exam-progress-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: var(--v2-text-secondary);
  font-size: 14px;
}

.progress-sep {
  color: rgba(0, 0, 0, 0.2);
}

.exam-progress :deep(.ant-progress-bg) {
  background: linear-gradient(90deg, var(--v2-primary) 0%, #6b8cfa 100%);
}

.loading-wrapper {
  padding: 80px 0;
  text-align: center;
}

.question-card {
  background: var(--v2-bg-card);
  border-radius: 20px;
  padding: 24px;
  margin-bottom: 16px;
  box-shadow: 0 8px 24px rgba(24, 39, 75, 0.06);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.type-tag {
  border-radius: 999px;
  padding: 4px 14px;
}

.question-score {
  color: var(--v2-text-secondary);
  font-size: 14px;
}

.question-content {
  font-size: 17px;
  line-height: 1.8;
  color: var(--v2-text-primary);
  margin-bottom: 24px;
}

.question-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 16px;
  border: 2px solid rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.2s ease;
}

.option-item:hover {
  border-color: var(--v2-primary);
  background: var(--v2-primary-light);
}

.option-item.selected {
  border-color: var(--v2-primary);
  background: var(--v2-primary-light);
}

.option-radio,
.option-checkbox {
  width: 22px;
  height: 22px;
  border: 2px solid rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.option-radio {
  border-radius: 50%;
}

.option-checkbox {
  border-radius: 6px;
}

.option-item.selected .option-radio,
.option-item.selected .option-checkbox {
  border-color: var(--v2-primary);
  background: var(--v2-primary);
  color: #fff;
}

.radio-inner {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #fff;
}

.option-label {
  font-weight: 600;
  color: var(--v2-text-primary);
}

.option-text {
  flex: 1;
  color: var(--v2-text-primary);
  line-height: 1.6;
}

.question-explanation {
  background: rgba(75, 110, 245, 0.06);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 16px;
}

.explanation-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-weight: 600;
  color: var(--v2-primary);
}

.question-explanation p {
  margin: 0;
  color: var(--v2-text-secondary);
  line-height: 1.7;
}

.question-nav {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding: 20px 0;
}

.question-nav :deep(.ant-btn) {
  border-radius: 12px;
  height: 44px;
  padding: 0 24px;
}

.answer-sheet-drawer :deep(.ant-drawer-body) {
  padding: 16px;
}

.answer-sheet-info {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  color: var(--v2-text-secondary);
  font-size: 14px;
}

.answer-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.answer-item {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.06);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.answer-item.current {
  background: var(--v2-primary);
  color: #fff;
}

.answer-item.answered {
  background: var(--v2-success);
  color: #fff;
}

.answer-item.answered.current {
  background: var(--v2-primary);
}

.answer-sheet-actions {
  padding-top: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.submit-confirm {
  text-align: center;
}

.submit-confirm p {
  margin: 8px 0;
  color: var(--v2-text-secondary);
}

.warning-text {
  color: var(--v2-danger) !important;
}

.submitting-wrapper {
  text-align: center;
  padding: 20px;
}

.submitting-wrapper p {
  margin-top: 16px;
  color: var(--v2-text-secondary);
}

@media (max-width: 768px) {
  .exam-do-page {
    padding: 12px;
  }

  .question-nav {
    flex-wrap: wrap;
  }

  .answer-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
</style>
