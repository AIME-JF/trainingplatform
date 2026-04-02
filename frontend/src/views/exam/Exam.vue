<template>
  <div class="exam-page">
    <div class="exam-page__backdrop"></div>

    <div v-if="loading" class="loading-box">
      <a-spin size="large" tip="正在加载试卷..." />
    </div>

    <template v-else>
      <header class="exam-topbar">
        <div class="exam-topbar__brand">
          <div class="brand-mark"></div>
          <div>
            <div class="brand-eyebrow">{{ resolvedKind === 'admission' ? '准入考试' : '培训班考试' }}</div>
            <h1 class="brand-title">{{ exam.title }}</h1>
          </div>
        </div>

        <div class="exam-topbar__timer" :class="{ urgent: remainingTime < 300 }">
          <span class="timer-icon">◷</span>
          <span>{{ formatTime(remainingTime) }}</span>
        </div>

        <div class="exam-topbar__actions">
          <button class="ghost-pill" @click="openExamGuide">考试说明</button>
          <button class="ghost-icon" @click="toggleFullscreen">
            <span>{{ isFullscreen ? '退出全屏' : '全屏' }}</span>
          </button>
        </div>
      </header>

      <div class="exam-shell">
        <section class="question-panel">
          <div class="question-panel__head">
            <div class="question-progress">
              <span class="question-order">第 {{ currentIdx + 1 }} 题</span>
              <span class="question-split">/</span>
              <span class="question-total">共 {{ questions.length }} 题</span>
            </div>
            <div class="question-tags">
              <span class="tag-chip tag-chip--type">{{ typeLabels[currentQuestion?.type] || currentQuestion?.type || '题目' }}</span>
              <span class="tag-chip">满分 {{ exam.totalScore || 0 }} 分</span>
              <span class="tag-chip">及格 {{ exam.passingScore || 0 }} 分</span>
              <span v-for="courseName in visibleCourseNames" :key="courseName" class="tag-chip tag-chip--course">{{ courseName }}</span>
            </div>
          </div>

          <div class="question-panel__body">
            <div class="question-stem">
              <span class="question-index">{{ currentIdx + 1 }}.</span>
              <span class="question-text">{{ currentQuestion?.content }}</span>
            </div>

            <div
              v-if="currentQuestion && (currentQuestion.type === 'single' || currentQuestion.type === 'judge')"
              class="option-group"
            >
              <button
                v-for="option in normalizedOptions(currentQuestion)"
                :key="option.key"
                type="button"
                class="option-card"
                :class="{ selected: answers[currentIdx] === option.key }"
                @click="selectSingleOption(option.key)"
              >
                <span class="option-control option-control--radio" :class="{ checked: answers[currentIdx] === option.key }"></span>
                <div class="option-card__badge">{{ option.key }}</div>
                <div class="option-card__text">{{ option.text }}</div>
              </button>
            </div>

            <div v-else-if="currentQuestion" class="option-group">
              <button
                v-for="option in normalizedOptions(currentQuestion)"
                :key="option.key"
                type="button"
                class="option-card"
                :class="{ selected: (answers[currentIdx] || []).includes(option.key) }"
                @click="toggleMultiOption(option.key)"
              >
                <span class="option-control option-control--checkbox" :class="{ checked: (answers[currentIdx] || []).includes(option.key) }"></span>
                <div class="option-card__badge">{{ option.key }}</div>
                <div class="option-card__text">{{ option.text }}</div>
              </button>
            </div>
          </div>

          <div class="question-panel__foot">
            <div class="nav-actions">
              <button class="soft-btn" :disabled="currentIdx === 0" @click="currentIdx -= 1">上一题</button>
              <button class="soft-btn soft-btn--primary" @click="goNextQuestion">
                {{ currentIdx < questions.length - 1 ? '下一题' : '检查交卷' }}
              </button>
            </div>

            <button class="mark-btn" :class="{ active: isMarked(currentIdx) }" @click="toggleMark(currentIdx)">
              {{ isMarked(currentIdx) ? '已标记此题' : '标记此题' }}
            </button>
          </div>
        </section>

        <aside class="exam-side">
          <section class="side-card side-card--summary">
            <div class="side-card__title">{{ exam.title }}</div>
            <div class="side-card__meta">
              <span>{{ resolvedKind === 'admission' ? '准入考核' : '班级考核' }}</span>
              <span>{{ exam.duration || 0 }} 分钟</span>
            </div>
            <div v-if="visibleCourseNames.length" class="side-card__courses">
              <span class="side-card__courses-label">绑定课程</span>
              <div class="side-card__course-tags">
                <span v-for="courseName in exam.courseNames || []" :key="courseName" class="course-pill">{{ courseName }}</span>
              </div>
            </div>

            <div class="stats-grid">
              <div class="stat-box">
                <span class="stat-label">总分</span>
                <strong class="stat-value">{{ exam.totalScore || 0 }}</strong>
              </div>
              <div class="stat-box">
                <span class="stat-label">题目数</span>
                <strong class="stat-value">{{ questions.length }}</strong>
              </div>
              <div class="stat-box">
                <span class="stat-label">已答</span>
                <strong class="stat-value">{{ answeredCount }}</strong>
              </div>
              <div class="stat-box">
                <span class="stat-label">未答</span>
                <strong class="stat-value">{{ unansweredCount }}</strong>
              </div>
            </div>

            <div class="summary-progress">
              <div class="summary-progress__text">
                <span>作答进度</span>
                <span>{{ progressPercent }}%</span>
              </div>
              <a-progress :percent="progressPercent" :show-info="false" stroke-color="#6fe2c7" trail-color="rgba(13,27,42,0.08)" />
            </div>
          </section>

          <section class="side-card side-card--sheet">
            <div class="sheet-header">
              <div>
                <h3>答题卡</h3>
                <p>当前题目高亮，绿色为已作答</p>
              </div>
              <button class="submit-btn submit-btn--mini" :loading="submitting" @click="confirmSubmit">提交试卷</button>
            </div>

            <div class="answer-grid">
              <button
                v-for="(question, index) in questions"
                :key="question.id"
                class="answer-cell"
                :class="{
                  answered: hasAnswer(index),
                  current: currentIdx === index,
                  marked: isMarked(index),
                }"
                @click="currentIdx = index"
              >
                {{ index + 1 }}
              </button>
            </div>

            <div class="sheet-legend">
              <span><i class="legend-dot legend-dot--done"></i>已作答</span>
              <span><i class="legend-dot legend-dot--current"></i>当前题</span>
              <span><i class="legend-dot legend-dot--marked"></i>已标记</span>
            </div>

            <button class="submit-btn" :loading="submitting" @click="confirmSubmit">提交试卷</button>
          </section>
        </aside>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { Modal, message } from 'ant-design-vue'
import {
  getAdmissionExamDetail,
  getExamDetail,
  submitAdmissionExam,
  submitExam,
} from '@/api/exam'

const route = useRoute()
const router = useRouter()
const examId = route.params.id
const resolvedKind = ref(route.query.kind === 'admission' ? 'admission' : 'training')
const answerStorageKey = computed(() => `student-exam:${resolvedKind.value}:${examId}`)

const loading = ref(true)
const submitting = ref(false)
const isFullscreen = ref(false)
const exam = ref({})
const questions = ref([])
const answers = ref([])
const currentIdx = ref(0)
const remainingTime = ref(0)
const startTime = ref(null)
const markedQuestions = ref([])

const typeLabels = { single: '单选题', multi: '多选题', judge: '判断题' }
const currentQuestion = computed(() => questions.value[currentIdx.value] || null)
const answeredCount = computed(() => answers.value.filter((item) => (Array.isArray(item) ? item.length > 0 : item !== null && item !== undefined && item !== '')).length)
const unansweredCount = computed(() => Math.max(0, questions.value.length - answeredCount.value))
const progressPercent = computed(() => (questions.value.length ? Math.round((answeredCount.value / questions.value.length) * 100) : 0))
const hasStarted = computed(() => questions.value.length > 0 && !!startTime.value)
const visibleCourseNames = computed(() => (exam.value.courseNames || []).slice(0, 3))

let timer = null

function normalizedOptions(question) {
  if (question.type === 'judge') {
    return [
      { key: 'A', text: '正确' },
      { key: 'B', text: '错误' },
    ]
  }
  return question.options || []
}

function hasAnswer(index) {
  const answer = answers.value[index]
  return Array.isArray(answer) ? answer.length > 0 : answer !== null && answer !== undefined && answer !== ''
}

function isMarked(index) {
  return markedQuestions.value.includes(index)
}

function toggleMark(index) {
  if (isMarked(index)) {
    markedQuestions.value = markedQuestions.value.filter((item) => item !== index)
    return
  }
  markedQuestions.value = [...markedQuestions.value, index]
}

function selectSingleOption(optionKey) {
  answers.value[currentIdx.value] = optionKey
}

function toggleMultiOption(optionKey) {
  const currentAnswer = Array.isArray(answers.value[currentIdx.value]) ? [...answers.value[currentIdx.value]] : []
  const optionIndex = currentAnswer.indexOf(optionKey)
  if (optionIndex >= 0) {
    currentAnswer.splice(optionIndex, 1)
  } else {
    currentAnswer.push(optionKey)
  }
  answers.value[currentIdx.value] = currentAnswer
}

function goNextQuestion() {
  if (currentIdx.value < questions.value.length - 1) {
    currentIdx.value += 1
    return
  }
  confirmSubmit()
}

function formatTime(seconds) {
  const hours = Math.floor(seconds / 3600).toString().padStart(2, '0')
  const minutes = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0')
  const secs = String(seconds % 60).padStart(2, '0')
  return `${hours}:${minutes}:${secs}`
}

function serializeProgress() {
  if (!questions.value.length) return
  sessionStorage.setItem(answerStorageKey.value, JSON.stringify({
    answers: answers.value,
    currentIdx: currentIdx.value,
    remainingTime: remainingTime.value,
    startTime: startTime.value,
    markedQuestions: markedQuestions.value,
  }))
}

function clearProgress() {
  sessionStorage.removeItem(answerStorageKey.value)
}

function restoreProgress() {
  const raw = sessionStorage.getItem(answerStorageKey.value)
  if (!raw) return false
  try {
    const saved = JSON.parse(raw)
    if (Array.isArray(saved.answers) && saved.answers.length === questions.value.length) {
      answers.value = saved.answers
    }
    if (Number.isInteger(saved.currentIdx) && saved.currentIdx >= 0 && saved.currentIdx < questions.value.length) {
      currentIdx.value = saved.currentIdx
    }
    if (Number.isFinite(saved.remainingTime) && saved.remainingTime > 0) {
      remainingTime.value = saved.remainingTime
    }
    if (saved.startTime) {
      startTime.value = saved.startTime
    }
    if (Array.isArray(saved.markedQuestions)) {
      markedQuestions.value = saved.markedQuestions.filter((item) => Number.isInteger(item))
    }
    return true
  } catch {
    clearProgress()
    return false
  }
}

function handleBeforeUnload(event) {
  if (!hasStarted.value || submitting.value) return
  event.preventDefault()
  event.returnValue = ''
}

function syncFullscreenState() {
  isFullscreen.value = !!document.fullscreenElement
}

async function toggleFullscreen() {
  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen()
    } else {
      await document.documentElement.requestFullscreen()
    }
    syncFullscreenState()
  } catch {
    message.warning('当前环境不支持全屏切换')
  }
}

function openExamGuide() {
  const lines = [
    `考试名称：${exam.value.title || '-'}`,
    `考试类型：${resolvedKind.value === 'admission' ? '准入考试' : '培训班考试'}`,
    `考试时长：${exam.value.duration || 0} 分钟`,
    `题目数量：${questions.value.length} 题`,
    `满分 / 及格：${exam.value.totalScore || 0} / ${exam.value.passingScore || 0} 分`,
    `绑定课程：${exam.value.courseNames?.length ? exam.value.courseNames.join('、') : '未绑定课程'}`,
    `考试说明：${exam.value.description || '请在限定时间内独立完成作答，提交后不可修改。'}`,
  ]

  Modal.info({
    title: '考试说明',
    width: 620,
    content: lines.map((item) => item).join('\n'),
  })
}

async function loadExam() {
  try {
    let detail
    if (resolvedKind.value === 'admission') {
      try {
        detail = await getAdmissionExamDetail(examId)
      } catch {
        detail = await getExamDetail(examId)
        resolvedKind.value = 'training'
      }
    } else {
      try {
        detail = await getExamDetail(examId)
      } catch {
        detail = await getAdmissionExamDetail(examId)
        resolvedKind.value = 'admission'
      }
    }

    exam.value = detail
    questions.value = detail.questions || []
    answers.value = questions.value.map((question) => (question.type === 'multi' ? [] : null))
    remainingTime.value = (detail.duration || 60) * 60
    startTime.value = new Date().toISOString()
    markedQuestions.value = []

    restoreProgress()

    timer = setInterval(() => {
      if (remainingTime.value > 0) {
        remainingTime.value -= 1
        return
      }
      clearInterval(timer)
      handleSubmit(true)
    }, 1000)
  } catch (error) {
    message.error(error.message || '加载试卷失败')
    router.replace({ name: 'ExamList' })
  } finally {
    loading.value = false
  }
}

async function handleSubmit(isAutoSubmit = false) {
  submitting.value = true
  try {
    const payload = { startTime: startTime.value, answers: {} }
    questions.value.forEach((question, index) => {
      payload.answers[question.id] = answers.value[index]
    })
    if (resolvedKind.value === 'admission') {
      await submitAdmissionExam(examId, payload)
    } else {
      await submitExam(examId, payload)
    }
    clearProgress()
    message.success(isAutoSubmit ? '考试时间结束，系统已自动交卷' : '交卷成功')
    router.replace({ name: 'ExamResult', params: { id: examId }, query: { kind: resolvedKind.value } })
  } catch (error) {
    message.error(error.message || '交卷失败')
  } finally {
    submitting.value = false
  }
}

function confirmSubmit() {
  Modal.confirm({
    title: '确认提交试卷？',
    content: unansweredCount.value > 0
      ? `当前已完成 ${answeredCount.value} 题，仍有 ${unansweredCount.value} 题未作答，确认提交吗？`
      : `已完成全部 ${questions.value.length} 题，确认提交吗？`,
    okText: '确认交卷',
    cancelText: '继续答题',
    onOk: () => {
      clearInterval(timer)
      return handleSubmit(false)
    },
  })
}

watch([answers, currentIdx, remainingTime, markedQuestions], () => {
  serializeProgress()
}, { deep: true })

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
  document.addEventListener('fullscreenchange', syncFullscreenState)
  loadExam()
})

onUnmounted(() => {
  clearInterval(timer)
  window.removeEventListener('beforeunload', handleBeforeUnload)
  document.removeEventListener('fullscreenchange', syncFullscreenState)
})

onBeforeRouteLeave(() => {
  if (!hasStarted.value || submitting.value) {
    return true
  }
  return window.confirm('考试进行中，离开页面后仍可返回继续作答，确认离开吗？')
})
</script>

<style scoped>
.exam-page {
  --exam-ink: #0f1c2f;
  --exam-muted: #728099;
  --exam-panel: rgba(255, 255, 255, 0.9);
  --exam-panel-strong: rgba(255, 255, 255, 0.96);
  --exam-line: rgba(16, 30, 48, 0.08);
  --exam-accent: #6fe2c7;
  --exam-accent-deep: #29c39f;
  --exam-shadow: 0 18px 48px rgba(26, 42, 66, 0.12);
  min-height: 100vh;
  padding: 22px 26px 28px;
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(124, 134, 204, 0.18), transparent 22%),
    radial-gradient(circle at right 20%, rgba(111, 226, 199, 0.16), transparent 20%),
    linear-gradient(180deg, #edf1f8 0%, #f7f9fc 38%, #eef2f7 100%);
  color: var(--exam-ink);
  font-family: Georgia, "Noto Serif SC", "Source Han Serif SC", serif;
}

.exam-page__backdrop {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 12% 14%, rgba(255, 255, 255, 0.7), transparent 18%),
    radial-gradient(circle at 82% 72%, rgba(255, 255, 255, 0.65), transparent 22%);
}

.loading-box {
  padding: 160px 0;
  text-align: center;
}

.exam-topbar,
.exam-shell {
  position: relative;
  z-index: 1;
}

.exam-topbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: 18px;
  padding: 16px 22px;
  margin-bottom: 18px;
  border-radius: 24px;
  background: linear-gradient(135deg, #2f344b 0%, #3a4056 55%, #31364b 100%);
  box-shadow: 0 20px 36px rgba(28, 34, 53, 0.22);
  color: #f7f8fb;
}

.exam-topbar__brand {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.brand-mark {
  width: 54px;
  height: 54px;
  border-radius: 18px;
  background:
    linear-gradient(145deg, rgba(255,255,255,0.18), rgba(255,255,255,0.03)),
    repeating-linear-gradient(135deg, rgba(255,255,255,0.22) 0 2px, transparent 2px 6px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  flex-shrink: 0;
}

.brand-eyebrow {
  font-size: 12px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  opacity: 0.7;
  margin-bottom: 4px;
}

.brand-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.exam-topbar__timer {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  justify-self: center;
  padding: 10px 18px;
  border-radius: 999px;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.08em;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.14);
}

.exam-topbar__timer.urgent {
  color: #ffd2d1;
  background: rgba(255, 91, 91, 0.14);
}

.timer-icon {
  font-size: 22px;
  line-height: 1;
}

.exam-topbar__actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.ghost-pill,
.ghost-icon {
  border: 1px solid rgba(255, 255, 255, 0.28);
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
  border-radius: 999px;
  padding: 10px 18px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.ghost-pill:hover,
.ghost-icon:hover {
  background: rgba(255, 255, 255, 0.14);
  transform: translateY(-1px);
}

.exam-shell {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(320px, 0.62fr);
  gap: 20px;
  align-items: start;
}

.question-panel,
.side-card {
  background: var(--exam-panel-strong);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: var(--exam-shadow);
  backdrop-filter: blur(10px);
}

.question-panel {
  border-radius: 28px;
  min-height: calc(100vh - 170px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.question-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 28px 32px 18px;
}

.question-progress {
  display: flex;
  align-items: baseline;
  gap: 8px;
  color: var(--exam-ink);
}

.question-order {
  font-size: 30px;
  font-weight: 700;
}

.question-split,
.question-total {
  font-size: 16px;
  color: var(--exam-muted);
}

.question-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.tag-chip {
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(15, 28, 47, 0.05);
  color: var(--exam-muted);
  font-size: 13px;
}

.tag-chip--type {
  background: rgba(111, 226, 199, 0.18);
  color: #127f66;
  font-weight: 700;
}

.tag-chip--course {
  background: rgba(38, 98, 255, 0.08);
  color: #3558b8;
}

.question-panel__body {
  flex: 1;
  padding: 8px 32px 24px;
  display: flex;
  flex-direction: column;
}

.question-stem {
  display: flex;
  gap: 14px;
  margin-bottom: 32px;
  font-size: 30px;
  line-height: 1.75;
  color: #253249;
}

.question-index {
  font-weight: 700;
  color: #0c1627;
}

.question-text {
  font-size: 20px;
  font-weight: 600;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 18px;
  width: 100%;
}

.option-card {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding: 18px 20px;
  border-radius: 22px;
  border: 1px solid var(--exam-line);
  background: rgba(255, 255, 255, 0.84);
  transition: all 0.22s ease;
  cursor: pointer;
  text-align: left;
}

.option-card:hover {
  transform: translateX(4px);
  border-color: rgba(111, 226, 199, 0.72);
  box-shadow: 0 14px 28px rgba(52, 171, 145, 0.12);
}

.option-card.selected {
  border-color: rgba(111, 226, 199, 0.92);
  background: linear-gradient(135deg, rgba(111, 226, 199, 0.18), rgba(111, 226, 199, 0.06));
  box-shadow: 0 16px 28px rgba(52, 171, 145, 0.16);
}

.option-control {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  margin: 0;
  flex-shrink: 0;
  border: 2px solid rgba(15, 28, 47, 0.22);
  background: #fff;
}

.option-control--radio {
  border-radius: 50%;
}

.option-control--checkbox {
  border-radius: 7px;
}

.option-control.checked {
  border-color: var(--exam-accent-deep);
  background: rgba(111, 226, 199, 0.14);
}

.option-control--radio.checked::after {
  content: "";
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--exam-accent-deep);
}

.option-control--checkbox.checked::after {
  content: "";
  width: 10px;
  height: 6px;
  border-left: 2px solid var(--exam-accent-deep);
  border-bottom: 2px solid var(--exam-accent-deep);
  transform: rotate(-45deg) translateY(-1px);
}

.option-card__badge {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 28, 47, 0.06);
  color: #1e2d45;
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
}

.option-card.selected .option-card__badge {
  background: linear-gradient(135deg, var(--exam-accent), var(--exam-accent-deep));
  color: #fff;
}

.option-card__text {
  font-size: 18px;
  line-height: 1.75;
  color: #1e2d45;
}

.question-panel__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 28px 22px;
  border-top: 1px solid rgba(15, 28, 47, 0.06);
  background: linear-gradient(180deg, rgba(255,255,255,0.72), rgba(250,252,255,0.96));
}

.nav-actions {
  display: flex;
  gap: 14px;
}

.soft-btn,
.mark-btn,
.submit-btn {
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.soft-btn {
  min-width: 124px;
  padding: 14px 24px;
  border-radius: 999px;
  background: rgba(111, 226, 199, 0.16);
  color: #1d8f75;
  font-size: 16px;
  font-weight: 700;
}

.soft-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  background: rgba(111, 226, 199, 0.26);
}

.soft-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.soft-btn--primary {
  background: linear-gradient(135deg, #81efd2, #47c8a7);
  color: #fff;
  box-shadow: 0 12px 24px rgba(64, 192, 160, 0.22);
}

.mark-btn {
  padding: 12px 18px;
  border-radius: 999px;
  background: rgba(15, 28, 47, 0.06);
  color: var(--exam-muted);
  font-size: 15px;
  font-weight: 700;
}

.mark-btn.active {
  background: rgba(255, 204, 94, 0.2);
  color: #b57c00;
}

.exam-side {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.side-card {
  border-radius: 26px;
  padding: 22px;
}

.side-card--summary {
  background:
    linear-gradient(180deg, rgba(255,255,255,0.98), rgba(250,252,255,0.9)),
    radial-gradient(circle at top right, rgba(111,226,199,0.14), transparent 28%);
}

.side-card__title {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.5;
  color: #233045;
  margin-bottom: 8px;
  word-break: break-word;
}

.side-card__meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  color: var(--exam-muted);
  font-size: 13px;
  margin-bottom: 18px;
}

.side-card__courses {
  margin-bottom: 18px;
}

.side-card__courses-label {
  display: block;
  margin-bottom: 10px;
  color: var(--exam-muted);
  font-size: 13px;
}

.side-card__course-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.course-pill {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(53, 88, 184, 0.08);
  color: #3558b8;
  font-size: 12px;
  font-weight: 700;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stat-box {
  padding: 16px 14px;
  border-radius: 18px;
  background: linear-gradient(180deg, #f7fffd, #eefbf7);
  border: 1px solid rgba(111, 226, 199, 0.22);
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 13px;
  color: var(--exam-muted);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 34px;
  line-height: 1;
  color: #213047;
}

.summary-progress {
  margin-top: 18px;
}

.summary-progress__text {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 13px;
  color: var(--exam-muted);
}

.sheet-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.sheet-header h3 {
  margin: 0 0 6px;
  font-size: 30px;
  color: #26344c;
}

.sheet-header p {
  margin: 0;
  color: var(--exam-muted);
  font-size: 13px;
}

.answer-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.answer-cell {
  height: 54px;
  border-radius: 16px;
  border: 1px solid rgba(15, 28, 47, 0.1);
  background: #fff;
  color: #627189;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.5);
  transition: all 0.2s ease;
}

.answer-cell:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(34, 51, 72, 0.1);
}

.answer-cell.answered {
  background: linear-gradient(180deg, rgba(111, 226, 199, 0.26), rgba(111, 226, 199, 0.18));
  color: #177f68;
  border-color: rgba(111, 226, 199, 0.5);
}

.answer-cell.current {
  border-color: rgba(111, 226, 199, 0.95);
  box-shadow: 0 0 0 4px rgba(111, 226, 199, 0.18);
}

.answer-cell.marked:not(.answered) {
  background: rgba(255, 225, 153, 0.26);
  color: #9d7100;
}

.sheet-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin: 18px 0 20px;
  color: var(--exam-muted);
  font-size: 13px;
}

.legend-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 6px;
}

.legend-dot--done {
  background: #52d4b5;
}

.legend-dot--current {
  background: #1aa88a;
}

.legend-dot--marked {
  background: #f0bc41;
}

.submit-btn {
  width: 100%;
  padding: 14px 20px;
  border-radius: 999px;
  background: linear-gradient(135deg, #87f0d6, #39c6a3);
  color: #fff;
  font-size: 17px;
  font-weight: 700;
  box-shadow: 0 18px 30px rgba(53, 192, 160, 0.2);
}

.submit-btn:hover {
  transform: translateY(-1px);
}

.submit-btn--mini {
  width: auto;
  padding: 10px 16px;
  font-size: 14px;
  box-shadow: none;
}

@media (max-width: 1200px) {
  .exam-shell {
    grid-template-columns: 1fr;
  }

  .question-panel {
    min-height: auto;
  }
}

@media (max-width: 900px) {
  .exam-page {
    padding: 14px 12px 24px;
  }

  .exam-topbar {
    grid-template-columns: 1fr;
    justify-items: stretch;
  }

  .exam-topbar__timer {
    justify-self: flex-start;
  }

  .exam-topbar__actions {
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .question-panel__head,
  .question-panel__body,
  .question-panel__foot,
  .side-card {
    padding-left: 18px;
    padding-right: 18px;
  }

  .question-panel__head,
  .question-panel__foot {
    flex-direction: column;
    align-items: flex-start;
  }

  .question-stem {
    font-size: 24px;
  }

  .question-text {
    font-size: 18px;
  }

  .option-card {
    padding: 14px 15px;
  }

  .option-card__text {
    font-size: 16px;
  }

  .answer-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .brand-title {
    white-space: normal;
  }

  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }

  .nav-actions {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 1fr;
  }

  .soft-btn,
  .mark-btn {
    width: 100%;
  }

  .question-panel__foot {
    align-items: stretch;
  }
}
</style>
