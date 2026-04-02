<template>
  <div class="exam-do-page">
    <!-- 顶部状态通栏 -->
    <header class="exam-header">
      <div class="header-left">
        <h1 class="exam-title">{{ examDetail?.title || '考试' }}</h1>
        <div class="exam-subtitle">
          <span class="exam-tag">{{ examDetail?.paper_title || '试卷' }}</span>
          <span class="exam-sep">|</span>
          <span class="exam-score">满分：{{ examDetail?.total_score || 100 }}分</span>
        </div>
      </div>

      <!-- 居中进度统计 -->
      <div class="header-center">
        <div class="header-progress-text">
          第 <span class="progress-current">{{ currentIndex + 1 }}</span> / {{ questions.length }} 题
        </div>
        <div class="header-progress-label">Progress: {{ progressPercent }}% Completed</div>
      </div>

      <div class="header-right">
        <!-- 计时器 -->
        <div class="timer-box" :class="{ warning: remainingTime < 300 }">
          <svg class="timer-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <div class="timer-content">
            <span class="timer-label">Remaining Time</span>
            <span class="timer-value">{{ formatDuration(remainingTime) }}</span>
          </div>
        </div>
        <button class="submit-btn" @click="showSubmitConfirm">
          确认交卷
        </button>
      </div>

      <!-- 细线条进度条 -->
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }" />
      </div>
    </header>

    <!-- 主答题区 -->
    <main class="exam-main-area">
      <!-- 左侧题目 -->
      <div class="exam-content-area">
        <div v-if="loading" class="loading-wrapper">
          <a-spin size="large" />
        </div>

        <template v-else-if="questions.length > 0">
          <!-- 题目卡片 -->
          <div class="question-card">
            <!-- 题目头部 -->
            <div class="question-header">
              <div class="question-header-left">
                <span class="type-tag" :class="getQuestionTypeClass(currentQuestion?.type)">
                  {{ getQuestionTypeText(currentQuestion?.type) }}
                </span>
                <span class="question-score">当前分值：{{ currentQuestion?.score || 0 }}分</span>
              </div>
              <div class="question-ref">Question Ref: Q-{{ currentQuestion?.id || 0 }}</div>
            </div>

            <h2 class="question-text">
              {{ currentIndex + 1 }}. {{ currentQuestion?.content }}
            </h2>

            <!-- 题目选项 -->
            <div class="question-options">
              <template v-if="currentQuestion?.type === 'multi'">
                <div
                  v-for="option in currentOptions"
                  :key="option.key"
                  class="option-card"
                  :class="{ selected: isOptionSelected(option.key) }"
                  @click="toggleOption(option.key)"
                >
                  <div class="option-tag">{{ option.key }}</div>
                  <div class="option-text">{{ option.value }}</div>
                </div>
              </template>
              <template v-else>
                <div
                  v-for="option in currentOptions"
                  :key="option.key"
                  class="option-card"
                  :class="{ selected: answers[currentQuestion?.id ?? 0] === option.key }"
                  @click="selectOption(option.key)"
                >
                  <div class="option-tag">{{ option.key }}</div>
                  <div class="option-text">{{ option.value }}</div>
                </div>
              </template>
            </div>

            <!-- 导航 -->
            <div class="question-footer">
              <button class="nav-btn nav-prev" @click="prevQuestion">
                <svg class="nav-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/>
                </svg>
                上一题
              </button>
              <div class="nav-divider" />
              <button class="nav-btn nav-next" @click="nextQuestion">
                下一题
                <svg class="nav-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/>
                </svg>
              </button>
            </div>
          </div>

          <p class="keyboard-tip">Tip: 使用键盘左右方向键切换题目，数字键 1-4 快速选择选项</p>
        </template>
      </div>

      <!-- 右侧答题卡 -->
      <aside class="answer-sidebar">
        <div class="sidebar-header">
          <h3 class="sidebar-title">
            <svg class="sidebar-title-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            答题卡概览
          </h3>
          <span class="sidebar-badge">Total {{ questions.length }} Qs</span>
        </div>

        <div class="sidebar-stats">
          <div class="stat-item stat-answered">
            <div class="stat-label">已作答</div>
            <div class="stat-num">{{ answeredCount }}</div>
          </div>
          <div class="stat-item stat-unanswered">
            <div class="stat-label">未作答</div>
            <div class="stat-num">{{ questions.length - answeredCount }}</div>
          </div>
        </div>

        <div class="sidebar-grid">
          <div
            v-for="(q, index) in questions"
            :key="q.id"
            class="grid-item"
            :class="{
              current: index === currentIndex,
              done: answers[q.id] !== undefined && answers[q.id] !== '' && answers[q.id] !== null,
              unanswered: answers[q.id] === undefined || answers[q.id] === '' || answers[q.id] === null,
            }"
            @click="goToQuestion(index)"
          >
            {{ index + 1 }}
          </div>
        </div>

        <div class="sidebar-legend">
          <div class="legend-item">
            <span class="legend-dot legend-current" />
            <span>当前</span>
          </div>
          <div class="legend-item">
            <span class="legend-dot legend-done" />
            <span>已答</span>
          </div>
          <div class="legend-item">
            <span class="legend-dot legend-unanswered" />
            <span>未答</span>
          </div>
        </div>
      </aside>
    </main>

    <!-- 提交确认弹窗 -->
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

    <!-- 提交中 -->
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
import { message } from 'ant-design-vue'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { ExamDetailResponse, ExamQuestionSnapshotResponse } from '@/api/generated/model'
import {
  getAdmissionExamApiV1ExamsAdmissionExamIdGet,
  getExamApiV1ExamsExamIdGet,
  submitAdmissionExamApiV1ExamsAdmissionExamIdSubmitPost,
  submitExamApiV1ExamsExamIdSubmitPost,
} from '@/api/generated/exam-management/exam-management'
import type { ExamSubmitAnswers } from '@/api/generated/model'
import {
  getExamStatusText,
  resolveExamKind,
  type ExamKind,
} from './examDisplay'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const examId = computed(() => Number(route.params.id))
const examKind = ref<ExamKind>(resolveExamKind(route.query.kind, 'training'))

const examDetail = ref<ExamDetailResponse | null>(null)
const questions = ref<ExamQuestionSnapshotResponse[]>([])
const currentIndex = ref(0)
const answers = ref<Record<number, string | string[]>>({})
const submitModalVisible = ref(false)
const startTime = ref(new Date().toISOString())

// 计时器
const remainingTime = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const currentQuestion = computed(() => questions.value[currentIndex.value])

const currentOptions = computed(() => {
  if (currentQuestion.value?.type === 'judge') {
    return [
      { key: 'A', value: '正确' },
      { key: 'B', value: '错误' },
    ]
  }
  const opts = currentQuestion.value?.options
  if (!opts || !Array.isArray(opts)) return []
  return opts.map((item) => {
    const [key, value] = Object.entries(item)[0]
    return { key, value: String(value) }
  })
})

const answeredCount = computed(() => {
  return Object.keys(answers.value).filter((k) => {
    const v = answers.value[Number(k)]
    return v !== undefined && v !== '' && (Array.isArray(v) ? v.length > 0 : true)
  }).length
})

const progressPercent = computed(() => {
  if (questions.value.length === 0) return 0
  return Math.round((answeredCount.value / questions.value.length) * 100)
})

onMounted(async () => {
  await fetchExamDetail()
  document.addEventListener('keydown', handleKeyDown)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  document.removeEventListener('keydown', handleKeyDown)
})

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'ArrowLeft') {
    prevQuestion()
  } else if (e.key === 'ArrowRight') {
    nextQuestion()
  } else if (['1', '2', '3', '4'].includes(e.key)) {
    const options = currentOptions.value
    const idx = parseInt(e.key) - 1
    if (options[idx]) {
      if (currentQuestion.value?.type === 'multi') {
        toggleOption(options[idx].key)
      } else {
        selectOption(options[idx].key)
      }
    }
  }
}

async function fetchExamDetail() {
  loading.value = true
  try {
    let detail
    if (examKind.value === 'admission') {
      detail = await getAdmissionExamApiV1ExamsAdmissionExamIdGet(examId.value)
    } else {
      detail = await getExamApiV1ExamsExamIdGet(examId.value)
    }
    examDetail.value = detail
  } catch (primaryError) {
    try {
      examKind.value = examKind.value === 'admission' ? 'training' : 'admission'
      examDetail.value = examKind.value === 'admission'
        ? await getAdmissionExamApiV1ExamsAdmissionExamIdGet(examId.value)
        : await getExamApiV1ExamsExamIdGet(examId.value)
    } catch {
      throw primaryError
    }
  }

  try {
    const detail = examDetail.value
    if (!detail) return

    if (!detail.can_join) {
      message.warning(`当前考试${getExamStatusText(detail)}`)
      await router.replace({ path: `/exam/overview/${examId.value}`, query: { kind: examKind.value } })
      return
    }

    if (detail.questions) {
      questions.value = detail.questions
    } else {
      message.warning('该考试暂无题目')
    }

    if (detail.duration) {
      remainingTime.value = detail.duration * 60
      startTimer()
    }
    startTime.value = new Date().toISOString()
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
  const answer = answers.value[currentQuestion.value?.id ?? 0]
  if (Array.isArray(answer)) {
    return answer.includes(key)
  }
  return false
}

function selectOption(key: string) {
  if (currentQuestion.value) {
    answers.value[currentQuestion.value.id] = key
  }
}

function toggleOption(key: string) {
  const qid = currentQuestion.value?.id
  if (!qid) return

  const current = answers.value[qid]
  if (!Array.isArray(current)) {
    answers.value[qid] = [key]
  } else {
    const index = current.indexOf(key)
    if (index === -1) {
      current.push(key)
    } else {
      current.splice(index, 1)
    }
    answers.value[qid] = [...current]
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
}

function showSubmitConfirm() {
  submitModalVisible.value = true
}

async function handleSubmit() {
  submitModalVisible.value = false
  submitting.value = true

  try {
    const answersData: ExamSubmitAnswers = {}
    for (const [qid, answer] of Object.entries(answers.value)) {
      if (answer !== undefined && answer !== '') {
        answersData[Number(qid)] = answer
      }
    }

    const submitData = {
      answers: answersData,
      start_time: startTime.value,
    }

    if (examKind.value === 'admission') {
      await submitAdmissionExamApiV1ExamsAdmissionExamIdSubmitPost(examId.value, submitData)
    } else {
      await submitExamApiV1ExamsExamIdSubmitPost(examId.value, submitData)
    }

    message.success('提交成功')
    await router.replace({ path: `/exam/result/${examId.value}`, query: { kind: examKind.value } })
  } catch (error) {
    message.error(error instanceof Error ? error.message : '提交失败')
    submitting.value = false
  }
}

function getQuestionTypeClass(type?: string) {
  switch (type) {
    case 'single':
      return 'type-single'
    case 'multi':
      return 'type-multi'
    case 'judge':
      return 'type-judge'
    default:
      return 'type-default'
  }
}

function getQuestionTypeText(type?: string) {
  switch (type) {
    case 'single':
      return '单选题'
    case 'multi':
      return '多选题'
    case 'judge':
      return '判断题'
    default:
      return type || '未知'
  }
}
</script>

<style scoped>
/* =====================
   页面基础
   ===================== */
.exam-do-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #F8FAFC;
  overflow: hidden;
}

/* =====================
   顶部通栏
   ===================== */
.exam-header {
  height: 72px;
  background: #fff;
  border-bottom: 1px solid #E2E8F0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 40px;
  position: relative;
  flex-shrink: 0;
  z-index: 30;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.exam-title {
  font-size: 20px;
  font-weight: 700;
  color: #0F172A;
  margin: 0;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.exam-subtitle {
  display: flex;
  align-items: center;
  gap: 8px;
}

.exam-tag {
  font-size: 12px;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.exam-sep {
  color: #E2E8F0;
  font-size: 12px;
}

.exam-score {
  font-size: 12px;
  font-weight: 700;
  color: #2563EB;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
}

.header-progress-text {
  font-size: 14px;
  font-weight: 700;
  color: #334155;
}

.progress-current {
  font-size: 18px;
  color: #2563EB;
}

.header-progress-label {
  font-size: 10px;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 2px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.timer-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 20px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 999px;
}

.timer-icon {
  width: 20px;
  height: 20px;
  color: #3B82F6;
}

.timer-content {
  display: flex;
  flex-direction: column;
}

.timer-label {
  font-size: 9px;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.timer-value {
  font-size: 20px;
  font-weight: 700;
  color: #0F172A;
  font-family: monospace;
  line-height: 1;
}

.timer-box.warning .timer-icon,
.timer-box.warning .timer-value {
  color: #EF4444;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.submit-btn {
  background: #2563EB;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  padding: 12px 32px;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.submit-btn:hover {
  background: #1D4ED8;
}

.submit-btn:active {
  transform: scale(0.98);
}

/* 进度条 */
.progress-bar {
  height: 4px;
  background: #E2E8F0;
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3B82F6 0%, #2563EB 100%);
  transition: width 0.5s ease;
}

/* =====================
   主答题区
   ===================== */
.exam-main-area {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.exam-content-area {
  flex: 1;
  overflow-y: auto;
  padding: 32px 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.loading-wrapper {
  padding: 80px 0;
}

/* =====================
   题目卡片
   ===================== */
.question-card {
  width: 100%;
  background: #fff;
  border: 1px solid #E2E8F0;
  border-radius: 32px;
  overflow: hidden;
}

.question-header {
  padding: 40px 48px 24px;
  border-bottom: 1px solid #F1F5F9;
  background: #F8FAFC;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.question-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.type-tag {
  padding: 6px 14px;
  font-size: 11px;
  font-weight: 700;
  border-radius: 8px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.type-single {
  background: #EFF6FF;
  color: #2563EB;
  border: 1px solid #BFDBFE;
}

.type-multi {
  background: #F5F3FF;
  color: #7C3AED;
  border: 1px solid #DDD6FE;
}

.type-judge {
  background: #F0FDF4;
  color: #16A34A;
  border: 1px solid #BBF7D0;
}

.type-default {
  background: #F8FAFC;
  color: #64748B;
  border: 1px solid #E2E8F0;
}

.question-score {
  font-size: 12px;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
}

.question-ref {
  font-size: 10px;
  font-weight: 700;
  color: #CBD5E1;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.question-text {
  font-size: 24px;
  font-weight: 700;
  color: #0F172A;
  line-height: 1.5;
  padding: 32px 48px;
  margin: 0;
}

/* =====================
   选项卡片
   ===================== */
.question-options {
  padding: 0 48px 48px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.option-card {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 24px;
  border: 1.5px solid #E2E8F0;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: #fff;
}

.option-card:hover {
  border-color: #CBD5E1;
  background: #F8FAFC;
  transform: translateY(-2px);
}

.option-card.selected {
  border-color: #2563EB;
  background: #EFF6FF;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08);
}

.option-card.selected .option-tag {
  background: #2563EB;
  color: #fff;
}

.option-tag {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: #F1F5F9;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  color: #64748B;
  flex-shrink: 0;
  transition: all 0.2s;
}

.option-text {
  flex: 1;
  font-size: 16px;
  font-weight: 500;
  color: #334155;
  line-height: 1.6;
}

/* =====================
   导航按钮
   ===================== */
.question-footer {
  padding: 24px 48px;
  background: #F8FAFC;
  border-top: 1px solid #E2E8F0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.nav-prev {
  color: #94A3B8;
  background: transparent;
}

.nav-prev:hover {
  color: #334155;
  background: #E2E8F0;
}

.nav-next {
  color: #2563EB;
  background: transparent;
}

.nav-next:hover {
  color: #1D4ED8;
  background: #EFF6FF;
}

.nav-icon {
  width: 20px;
  height: 20px;
}

.nav-divider {
  width: 1px;
  height: 40px;
  background: #E2E8F0;
}

.keyboard-tip {
  margin-top: 24px;
  font-size: 11px;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0.6;
}

/* =====================
   右侧答题卡
   ===================== */
.answer-sidebar {
  width: 360px;
  background: #fff;
  border-left: 1px solid #E2E8F0;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  z-index: 20;
}

.sidebar-header {
  padding: 32px;
  border-bottom: 1px solid #F1F5F9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-title {
  font-size: 16px;
  font-weight: 700;
  color: #0F172A;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  letter-spacing: -0.01em;
}

.sidebar-title-icon {
  width: 20px;
  height: 20px;
  color: #3B82F6;
}

.sidebar-badge {
  font-size: 10px;
  font-weight: 700;
  color: #94A3B8;
  background: #F8FAFC;
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid #E2E8F0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.sidebar-stats {
  padding: 24px 32px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-item {
  padding: 16px;
  border-radius: 16px;
  text-align: center;
}

.stat-answered {
  background: #F0FDF4;
  border: 1px solid #BBF7D0;
}

.stat-unanswered {
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
}

.stat-label {
  font-size: 10px;
  font-weight: 700;
  color: #16A34A;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-bottom: 4px;
}

.stat-unanswered .stat-label {
  color: #94A3B8;
}

.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: #15803D;
  line-height: 1;
}

.stat-unanswered .stat-num {
  color: #0F172A;
}

.sidebar-grid {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  align-content: start;
}

.grid-item {
  aspect-ratio: 1 / 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
  cursor: pointer;
}

.grid-item.current {
  background: #2563EB;
  color: #fff;
  box-shadow: 0 4px 8px rgba(37, 99, 235, 0.3);
}

.grid-item.done {
  background: #DCFCE7;
  color: #166534;
  border: 1px solid #BBF7D0;
}

.grid-item.unanswered {
  background: #fff;
  color: #64748B;
  border: 1px solid #E2E8F0;
}

.sidebar-legend {
  padding: 24px 32px;
  border-top: 1px solid #F1F5F9;
  background: #F8FAFC;
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-current {
  background: #2563EB;
}

.legend-done {
  background: #86EFAC;
}

.legend-unanswered {
  background: #E2E8F0;
}

/* =====================
   弹窗样式
   ===================== */
.submit-confirm {
  text-align: center;
}

.submit-confirm p {
  margin: 8px 0;
  color: #64748B;
}

.warning-text {
  color: #EF4444 !important;
}

.submitting-wrapper {
  text-align: center;
  padding: 20px;
}

.submitting-wrapper p {
  margin-top: 16px;
  color: #64748B;
}

/* =====================
   响应式
   ===================== */
@media (max-width: 1200px) {
  .exam-header {
    padding: 0 24px;
  }

  .header-center {
    display: none;
  }

  .exam-content-area {
    padding: 24px;
  }

  .question-header {
    padding: 24px 32px 16px;
  }

  .question-text {
    padding: 24px 32px;
    font-size: 20px;
  }

  .question-options {
    padding: 0 32px 32px;
  }

  .question-footer {
    padding: 16px 32px;
  }

  .answer-sidebar {
    width: 300px;
  }
}

@media (max-width: 768px) {
  .exam-do-page {
    height: auto;
    overflow: auto;
  }

  .exam-header {
    height: auto;
    flex-wrap: wrap;
    padding: 16px;
    gap: 12px;
  }

  .header-left {
    width: 100%;
  }

  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .timer-box {
    padding: 6px 14px;
  }

  .timer-value {
    font-size: 16px;
  }

  .submit-btn {
    padding: 10px 20px;
    font-size: 13px;
  }

  .exam-main-area {
    flex-direction: column;
  }

  .exam-content-area {
    padding: 16px;
  }

  .answer-sidebar {
    width: 100%;
    border-left: none;
    border-top: 1px solid #E2E8F0;
  }

  .sidebar-header {
    padding: 16px;
  }

  .sidebar-stats {
    padding: 16px;
  }

  .sidebar-grid {
    padding: 16px;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
  }

  .sidebar-legend {
    padding: 16px;
  }

  .question-header {
    padding: 16px;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .question-ref {
    display: none;
  }

  .question-text {
    padding: 16px;
    font-size: 18px;
  }

  .question-options {
    padding: 0 16px 16px;
  }

  .option-card {
    padding: 16px;
    gap: 16px;
  }

  .option-tag {
    width: 32px;
    height: 32px;
    font-size: 14px;
    border-radius: 8px;
  }

  .option-text {
    font-size: 14px;
  }

  .question-footer {
    padding: 16px;
    flex-wrap: wrap;
    gap: 8px;
  }

  .nav-btn {
    flex: 1;
    justify-content: center;
  }

  .nav-divider {
    display: none;
  }
}
</style>
