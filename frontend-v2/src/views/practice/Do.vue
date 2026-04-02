<template>
  <div class="practice-do-page">
    <header class="practice-header">
      <div class="header-left">
        <button class="btn-back" @click="goBack">
          <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      </div>
      <div class="header-title">刷题练习</div>
      <div class="header-right">
        <span class="progress-text">{{ progressLabel }}</span>
      </div>
    </header>

    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
    </div>

    <div v-if="sourceName" class="source-banner">
      <span class="source-tag">{{ sourceTypeLabel }}</span>
      <span class="source-name">{{ sourceName }}</span>
    </div>

    <main v-if="!finished && currentQuestion" class="practice-main">
      <div class="question-card">
        <div class="question-header">
          <span class="type-tag" :class="getQuestionTypeClass(currentQuestion.type)">
            {{ getQuestionTypeText(currentQuestion.type) }}
          </span>
          <span class="question-score">{{ currentQuestion.score || 1 }}分</span>
        </div>
        <h2 class="question-text">
          {{ currentIndex + 1 }}. {{ currentQuestion.content }}
        </h2>
      </div>

      <div class="options-area">
        <template v-if="currentQuestion.type === 'multi'">
          <div
            v-for="option in currentOptions"
            :key="option.key"
            class="option-card"
            :class="{
              selected: isOptionSelected(option.key),
              correct: showAnswer && isCorrectAnswer(option.key),
              incorrect: showAnswer && isOptionSelected(option.key) && !isCorrectAnswer(option.key),
            }"
            @click="toggleOption(option.key)"
          >
            <div class="option-tag">{{ option.key }}</div>
            <div class="option-text">{{ option.value }}</div>
            <div v-if="showAnswer" class="option-icon">
              <span v-if="isCorrectAnswer(option.key)" class="icon-correct">✓</span>
              <span v-else-if="isOptionSelected(option.key)" class="icon-incorrect">✗</span>
            </div>
          </div>
        </template>
        <template v-else>
          <div
            v-for="option in currentOptions"
            :key="option.key"
            class="option-card"
            :class="{
              selected: answers[currentQuestion.id] === option.key,
              correct: showAnswer && isCorrectAnswer(option.key),
              incorrect: showAnswer && answers[currentQuestion.id] === option.key && !isCorrectAnswer(option.key),
            }"
            @click="selectOption(option.key)"
          >
            <div class="option-tag">{{ option.key }}</div>
            <div class="option-text">{{ option.value }}</div>
            <div v-if="showAnswer" class="option-icon">
              <span v-if="isCorrectAnswer(option.key)" class="icon-correct">✓</span>
              <span v-else-if="answers[currentQuestion.id] === option.key" class="icon-incorrect">✗</span>
            </div>
          </div>
        </template>
      </div>

      <div v-if="showAnswer" class="answer-section">
        <div class="answer-result">
          <span class="result-tag" :class="isCurrentCorrect ? 'correct' : 'incorrect'">
            {{ isCurrentCorrect ? '回答正确' : '回答错误' }}
          </span>
        </div>
        <div class="answer-detail">
          <div class="detail-row">
            <span class="detail-label">正确答案：</span>
            <span class="detail-value correct-text">{{ formatAnswer(currentQuestion.answer, currentQuestion) }}</span>
          </div>
          <div v-if="currentQuestion.explanation" class="detail-row">
            <span class="detail-label">解析：</span>
            <span class="detail-value">{{ currentQuestion.explanation }}</span>
          </div>
        </div>
      </div>

      <div class="action-buttons">
        <button v-if="!showAnswer" class="btn-submit" @click="submitAnswer">
          提交答案
        </button>
        <button v-else class="btn-next" @click="nextQuestion">
          {{ currentIndex < questions.length - 1 ? '下一题' : '完成练习' }}
        </button>
      </div>
    </main>

    <div v-else-if="finished" class="complete-page">
      <div class="complete-card">
        <div class="complete-icon">✓</div>
        <h2 class="complete-title">练习完成</h2>
        <p v-if="sourceName" class="complete-subtitle">{{ sourceTypeLabel }}：{{ sourceName }}</p>
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-value">{{ questions.length }}</span>
            <span class="stat-label">总题数</span>
          </div>
          <div class="stat-item">
            <span class="stat-value correct">{{ correctCount }}</span>
            <span class="stat-label">正确</span>
          </div>
          <div class="stat-item">
            <span class="stat-value incorrect">{{ questions.length - correctCount }}</span>
            <span class="stat-label">错误</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ accuracy }}%</span>
            <span class="stat-label">正确率</span>
          </div>
        </div>
        <button class="btn-restart" @click="restartPractice">重新练习</button>
      </div>
    </div>

    <div v-if="loading" class="loading-overlay">
      <a-spin size="large" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useRoute, useRouter } from 'vue-router'
import { getQuestionsApiV1QuestionsGet } from '@/api/generated/question-management/question-management'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const questions = ref([])
const currentIndex = ref(0)
const answers = ref({})
const showAnswer = ref(false)
const finished = ref(false)

const currentQuestion = computed(() => questions.value[currentIndex.value] || null)

const progressPercent = computed(() => {
  if (questions.value.length === 0) {
    return 0
  }
  if (finished.value) {
    return 100
  }
  return ((currentIndex.value + 1) / questions.value.length) * 100
})

const progressLabel = computed(() => (
  finished.value ? '已完成' : `${Math.min(currentIndex.value + 1, questions.value.length)}/${questions.value.length || 0}`
))

const correctCount = computed(() => {
  let count = 0
  for (const question of questions.value) {
    if (isAnswerCorrect(question, answers.value[question.id])) {
      count += 1
    }
  }
  return count
})

const accuracy = computed(() => {
  if (questions.value.length === 0) {
    return 0
  }
  return Math.round((correctCount.value / questions.value.length) * 100)
})

const isCurrentCorrect = computed(() => {
  if (!currentQuestion.value) {
    return false
  }
  return isAnswerCorrect(currentQuestion.value, answers.value[currentQuestion.value.id])
})

const currentOptions = computed(() => {
  if (!currentQuestion.value) {
    return []
  }
  if (currentQuestion.value.type === 'judge') {
    return [
      { key: 'A', value: '正确' },
      { key: 'B', value: '错误' },
    ]
  }
  const options = currentQuestion.value.options || []
  if (Array.isArray(options)) {
    return options
      .map((option) => ({
        key: String(option?.key ?? ''),
        value: String(option?.text ?? option?.value ?? ''),
      }))
      .filter((option) => option.key && option.value)
  }
  if (typeof options === 'object' && !Array.isArray(options)) {
    return Object.entries(options).map(([key, value]) => ({ key, value }))
  }
  return []
})

const practiceSource = computed(() => {
  const sourceType = normalizeSourceType(getSingleQueryValue(route.query.sourceType))
  const sourceId = getSingleQueryValue(route.query.sourceId)
  const sourceName = getSingleQueryValue(route.query.sourceName)
  const legacyKpId = getSingleQueryValue(route.query.kpId)

  if (sourceType && sourceId) {
    return { sourceType, sourceId, sourceName }
  }

  if (legacyKpId) {
    return {
      sourceType: 'knowledge-point',
      sourceId: legacyKpId,
      sourceName,
    }
  }

  return null
})

const sourceName = computed(() => practiceSource.value?.sourceName || '')

const sourceTypeLabel = computed(() => (
  practiceSource.value?.sourceType === 'question-folder' ? '题库/科目' : '知识点'
))

function getSingleQueryValue(value) {
  if (Array.isArray(value)) {
    return value[0] || ''
  }
  return value ? String(value) : ''
}

function normalizeSourceType(value) {
  if (value === 'knowledge-point' || value === 'question-folder') {
    return value
  }
  return ''
}

function getQuestionTypeClass(type) {
  const typeClassMap = {
    single: 'type-single',
    multi: 'type-multi',
    judge: 'type-judge',
  }
  return typeClassMap[type] || 'type-single'
}

function getQuestionTypeText(type) {
  const typeTextMap = {
    single: '单选题',
    multi: '多选题',
    judge: '判断题',
  }
  return typeTextMap[type] || type
}

function isOptionSelected(key) {
  const answer = answers.value[currentQuestion.value?.id]
  if (Array.isArray(answer)) {
    return answer.includes(key)
  }
  return answer === key
}

function normalizeAnswerValue(question, answer) {
  if (answer === null || answer === undefined) {
    return null
  }

  if (question?.type === 'judge') {
    if (answer === true || answer === 'true' || answer === 1 || answer === '1' || answer === 'A') {
      return 'A'
    }
    if (answer === false || answer === 'false' || answer === 0 || answer === '0' || answer === 'B') {
      return 'B'
    }
  }

  if (Array.isArray(answer)) {
    return answer.map((item) => String(item))
  }

  return String(answer)
}

function isCorrectAnswer(key) {
  if (currentQuestion.value?.answer === undefined || currentQuestion.value?.answer === null) {
    return false
  }
  const correctAnswer = normalizeAnswerValue(currentQuestion.value, currentQuestion.value.answer)
  if (Array.isArray(correctAnswer)) {
    return correctAnswer.includes(key)
  }
  return correctAnswer === String(key)
}

function isAnswerCorrect(question, userAnswer) {
  if (question?.answer === undefined || question?.answer === null || userAnswer === undefined) {
    return false
  }
  const correctAnswer = normalizeAnswerValue(question, question.answer)
  const normalizedUserAnswer = normalizeAnswerValue(question, userAnswer)
  if (Array.isArray(correctAnswer)) {
    if (!Array.isArray(normalizedUserAnswer)) {
      return false
    }
    return [...correctAnswer].sort().join(',') === [...normalizedUserAnswer].sort().join(',')
  }
  return correctAnswer === normalizedUserAnswer
}

function formatAnswer(answer, question = currentQuestion.value) {
  if (answer === undefined || answer === null) {
    return '-'
  }
  const normalizedAnswer = normalizeAnswerValue(question, answer)
  if (question?.type === 'judge') {
    return normalizedAnswer === 'A' ? '正确' : '错误'
  }
  if (Array.isArray(normalizedAnswer)) {
    return normalizedAnswer.join('、')
  }
  return String(normalizedAnswer)
}

function selectOption(key) {
  if (showAnswer.value || !currentQuestion.value) {
    return
  }
  answers.value[currentQuestion.value.id] = key
}

function toggleOption(key) {
  if (showAnswer.value) {
    return
  }
  const questionId = currentQuestion.value?.id
  if (!questionId) {
    return
  }

  const selected = answers.value[questionId]
  if (!Array.isArray(selected)) {
    answers.value[questionId] = [key]
    return
  }

  const index = selected.indexOf(key)
  if (index === -1) {
    selected.push(key)
  } else {
    selected.splice(index, 1)
  }
  answers.value[questionId] = [...selected]
}

function submitAnswer() {
  if (answers.value[currentQuestion.value?.id] === undefined) {
    message.warning('请先选择答案')
    return
  }
  showAnswer.value = true
}

function nextQuestion() {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value += 1
    showAnswer.value = false
    return
  }
  finished.value = true
}

function restartPractice() {
  currentIndex.value = 0
  answers.value = {}
  showAnswer.value = false
  finished.value = false
}

function goBack() {
  router.back()
}

function returnToPracticeHome() {
  router.replace({ path: '/practice' })
}

async function loadQuestions() {
  const source = practiceSource.value

  if (!source?.sourceId) {
    message.error('缺少练习来源参数')
    returnToPracticeHome()
    return
  }

  loading.value = true
  try {
    const params = { size: 20 }

    if (source.sourceType === 'knowledge-point') {
      params.knowledge_point_id = Number(source.sourceId)
    } else if (source.sourceType === 'question-folder') {
      params.folder_id = Number(source.sourceId)
      params.recursive = true
    } else {
      throw new Error('暂不支持的练习来源')
    }

    const response = await getQuestionsApiV1QuestionsGet(params)
    questions.value = response?.items || []

    if (questions.value.length === 0) {
      message.warning(source.sourceType === 'knowledge-point' ? '该知识点暂无题目' : '该题库暂无题目')
      returnToPracticeHome()
    }
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载题目失败')
    returnToPracticeHome()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadQuestions()
})
</script>

<style scoped>
.practice-do-page {
  min-height: 100vh;
  background: #F8FAFC;
  display: flex;
  flex-direction: column;
}

.practice-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #E2E8F0;
}

.header-left,
.header-right {
  width: 72px;
}

.btn-back {
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  color: #334155;
}

.header-title {
  font-size: 16px;
  font-weight: 700;
  color: #1E293B;
}

.progress-text {
  display: block;
  text-align: right;
  font-size: 14px;
  font-weight: 600;
  color: #2563EB;
}

.progress-bar {
  height: 3px;
  background: #E2E8F0;
}

.progress-fill {
  height: 100%;
  background: #2563EB;
  transition: width 0.3s;
}

.source-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #EFF6FF, #F8FAFC);
  border-bottom: 1px solid #E2E8F0;
}

.source-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: #DBEAFE;
  color: #1D4ED8;
  font-size: 12px;
  font-weight: 700;
}

.source-name {
  font-size: 13px;
  color: #334155;
  font-weight: 600;
}

.practice-main {
  flex: 1;
  padding: 16px;
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
}

.question-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.type-tag {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.type-single {
  background: #EFF6FF;
  color: #2563EB;
}

.type-multi {
  background: #F0FDF4;
  color: #16A34A;
}

.type-judge {
  background: #FEF3C7;
  color: #D97706;
}

.question-score {
  font-size: 13px;
  color: #64748B;
}

.question-text {
  font-size: 16px;
  font-weight: 600;
  color: #1E293B;
  line-height: 1.6;
  margin: 0;
}

.options-area {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.option-card {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  background: #fff;
  border: 2px solid #E2E8F0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.option-card:hover {
  border-color: #CBD5E1;
  background: #F8FAFC;
}

.option-card.selected {
  border-color: #2563EB;
  background: #EFF6FF;
}

.option-card.correct {
  border-color: #16A34A;
  background: #F0FDF4;
}

.option-card.incorrect {
  border-color: #EF4444;
  background: #FEF2F2;
}

.option-tag {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F1F5F9;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 700;
  color: #334155;
  margin-right: 12px;
}

.option-card.selected .option-tag {
  background: #2563EB;
  color: #fff;
}

.option-card.correct .option-tag {
  background: #16A34A;
  color: #fff;
}

.option-card.incorrect .option-tag {
  background: #EF4444;
  color: #fff;
}

.option-text {
  flex: 1;
  font-size: 14px;
  color: #334155;
}

.option-icon {
  margin-left: 8px;
}

.icon-correct {
  color: #16A34A;
  font-size: 18px;
  font-weight: 700;
}

.icon-incorrect {
  color: #EF4444;
  font-size: 18px;
  font-weight: 700;
}

.answer-section {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.answer-result {
  margin-bottom: 12px;
}

.result-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
}

.result-tag.correct {
  background: #DCFCE7;
  color: #16A34A;
}

.result-tag.incorrect {
  background: #FEE2E2;
  color: #EF4444;
}

.answer-detail {
  font-size: 14px;
}

.detail-row {
  margin-bottom: 8px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-label {
  color: #64748B;
}

.detail-value {
  color: #334155;
}

.correct-text {
  color: #16A34A;
  font-weight: 600;
}

.action-buttons {
  text-align: center;
}

.btn-submit,
.btn-next {
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-submit {
  background: #2563EB;
  color: #fff;
}

.btn-submit:hover {
  background: #1D4ED8;
}

.btn-next {
  background: #10B981;
  color: #fff;
}

.btn-next:hover {
  background: #059669;
}

.complete-page {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.complete-card {
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  text-align: center;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.complete-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #DCFCE7;
  color: #16A34A;
  font-size: 30px;
  font-weight: 700;
}

.complete-title {
  font-size: 20px;
  font-weight: 700;
  color: #1E293B;
  margin: 0 0 8px 0;
}

.complete-subtitle {
  margin: 0 0 24px;
  font-size: 13px;
  color: #64748B;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  padding: 16px;
  background: #F8FAFC;
  border-radius: 12px;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #1E293B;
  margin-bottom: 4px;
}

.stat-value.correct {
  color: #16A34A;
}

.stat-value.incorrect {
  color: #EF4444;
}

.stat-label {
  font-size: 13px;
  color: #64748B;
}

.btn-restart {
  width: 100%;
  height: 48px;
  background: #2563EB;
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-restart:hover {
  background: #1D4ED8;
}

.loading-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.9);
}
</style>
