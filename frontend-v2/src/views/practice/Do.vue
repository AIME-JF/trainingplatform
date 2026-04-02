<template>
  <div class="practice-do-page">
    <!-- 顶部导航 -->
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

      <!-- 细线条进度条 -->
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
    </header>

    <!-- 来源横幅 -->
    <div v-if="sourceName" class="source-banner">
      <div class="source-banner-main">
        <span class="source-tag">{{ sourceTypeLabel }}</span>
        <span class="source-name">{{ sourceName }}</span>
      </div>
      <div v-if="filterSummary" class="source-summary">{{ filterSummary }}</div>
    </div>

    <!-- 主内容区 -->
    <main v-if="!finished && currentQuestion" class="practice-main">
      <div class="question-wrapper">
        <!-- 题目卡片 -->
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

        <!-- 选项区域 -->
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

        <!-- 答案解析 -->
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

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <button v-if="!showAnswer" class="btn-submit" @click="submitAnswer">
            提交答案
          </button>
          <button v-else class="btn-next" @click="nextQuestion">
            {{ currentIndex < questions.length - 1 ? '下一题' : '完成练习' }}
          </button>
        </div>
      </div>
    </main>

    <!-- 完成页面 -->
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

const questionTypeLabels = {
  single: '单选题',
  multi: '多选题',
  judge: '判断题',
}

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
    return Object.entries(options).map(([key, value]) => ({ key, value: String(value) }))
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

const practiceFilters = computed(() => ({
  questionLimit: parseQuestionLimit(getSingleQueryValue(route.query.questionLimit)),
  questionType: normalizeQuestionType(getSingleQueryValue(route.query.questionType)),
  difficulty: parsePositiveInt(getSingleQueryValue(route.query.difficulty)),
  policeTypeId: parsePositiveInt(getSingleQueryValue(route.query.policeTypeId)),
  policeTypeName: getSingleQueryValue(route.query.policeTypeName),
  keyword: getSingleQueryValue(route.query.keyword).trim(),
}))

const sourceName = computed(() => practiceSource.value?.sourceName || '')

const sourceTypeLabel = computed(() => (
  practiceSource.value?.sourceType === 'question-folder' ? '题库/科目' : '知识点'
))

const filterSummary = computed(() => {
  const tags = []

  if (practiceFilters.value.questionLimit) {
    tags.push(`抽取 ${practiceFilters.value.questionLimit} 题`)
  } else {
    tags.push('题量不限')
  }
  if (practiceFilters.value.questionType) {
    tags.push(questionTypeLabels[practiceFilters.value.questionType] || practiceFilters.value.questionType)
  }
  if (practiceFilters.value.difficulty) {
    tags.push(`难度 ${practiceFilters.value.difficulty}`)
  }
  if (practiceFilters.value.policeTypeName) {
    tags.push(`警种：${practiceFilters.value.policeTypeName}`)
  }
  if (practiceFilters.value.keyword) {
    tags.push(`关键词：${practiceFilters.value.keyword}`)
  }

  return tags.join(' · ')
})

const hasExtraFilters = computed(() => (
  Boolean(
    practiceFilters.value.questionType
    || practiceFilters.value.difficulty
    || practiceFilters.value.policeTypeId
    || practiceFilters.value.keyword,
  )
))

function getSingleQueryValue(value) {
  if (Array.isArray(value)) {
    return value[0] || ''
  }
  return value ? String(value) : ''
}

function parsePositiveInt(value) {
  if (!value) {
    return null
  }
  const parsed = Number(value)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null
}

function parseQuestionLimit(value) {
  if (!value) {
    return 20
  }
  if (value === 'all') {
    return null
  }
  return parsePositiveInt(value)
}

function normalizeSourceType(value) {
  if (value === 'knowledge-point' || value === 'question-folder') {
    return value
  }
  return ''
}

function normalizeQuestionType(value) {
  if (value === 'single' || value === 'multi' || value === 'judge') {
    return value
  }
  return ''
}

function shuffleQuestions(list) {
  const shuffled = [...list]
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1))
    ;[shuffled[index], shuffled[randomIndex]] = [shuffled[randomIndex], shuffled[index]]
  }
  return shuffled
}

function applyQuestionLimit(list, limit) {
  if (!limit || list.length <= limit) {
    return list
  }
  return shuffleQuestions(list).slice(0, limit)
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
  return questionTypeLabels[type] || type
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
    const params = {
      size: -1,
      search: practiceFilters.value.keyword || undefined,
      type: practiceFilters.value.questionType || undefined,
      difficulty: practiceFilters.value.difficulty || undefined,
      police_type_id: practiceFilters.value.policeTypeId || undefined,
    }

    if (source.sourceType === 'knowledge-point') {
      params.knowledge_point_id = Number(source.sourceId)
    } else if (source.sourceType === 'question-folder') {
      params.folder_id = Number(source.sourceId)
      params.recursive = true
    } else {
      throw new Error('暂不支持的练习来源')
    }

    const response = await getQuestionsApiV1QuestionsGet(params)
    const matchedQuestions = response?.items || []
    questions.value = applyQuestionLimit(matchedQuestions, practiceFilters.value.questionLimit)

    if (questions.value.length === 0) {
      if (hasExtraFilters.value) {
        message.warning('当前筛选条件下暂无题目')
      } else {
        message.warning(source.sourceType === 'knowledge-point' ? '该知识点暂无题目' : '该题库暂无题目')
      }
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
  background: var(--v2-bg, #F5F6FA);
  display: flex;
  flex-direction: column;
}

/* =====================
   顶部导航
   ===================== */
.practice-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--v2-bg-card, #FFFFFF);
  border-bottom: 1px solid var(--v2-border-light, #F2F2F7);
}

.header-left,
.header-right {
  width: 72px;
}

.header-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--v2-text-primary, #1D1D1F);
}

.btn-back {
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  color: var(--v2-text-secondary, #86868B);
  border-radius: var(--v2-radius, 12px);
  transition: all 0.2s;
}

.btn-back:hover {
  background: var(--v2-bg, #F5F6FA);
  color: var(--v2-primary, #4B6EF5);
}

.progress-text {
  display: block;
  text-align: right;
  font-size: 14px;
  font-weight: 700;
  color: var(--v2-primary, #4B6EF5);
}

.progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--v2-border, #E5E5EA);
}

.progress-fill {
  height: 100%;
  background: var(--v2-primary, #4B6EF5);
  transition: width 0.3s ease;
}

/* =====================
   来源横幅
   ===================== */
.source-banner {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 24px;
  background: linear-gradient(135deg, var(--v2-primary-light, #EEF2FF), var(--v2-bg, #F5F6FA));
  border-bottom: 1px solid var(--v2-border-light, #F2F2F7);
}

.source-banner-main {
  display: flex;
  align-items: center;
  gap: 10px;
}

.source-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 10px;
  border-radius: var(--v2-radius-full, 9999px);
  background: var(--v2-primary, #4B6EF5);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
}

.source-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--v2-text-primary, #1D1D1F);
}

.source-summary {
  font-size: 12px;
  color: var(--v2-text-secondary, #86868B);
}

/* =====================
   主内容区
   ===================== */
.practice-main {
  flex: 1;
  display: flex;
  justify-content: center;
  padding: 24px;
}

.question-wrapper {
  width: 100%;
  max-width: 720px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 题目卡片 */
.question-card {
  background: var(--v2-bg-card, #FFFFFF);
  border-radius: var(--v2-radius-lg, 16px);
  padding: 24px;
  box-shadow: var(--v2-shadow, 0 2px 8px rgba(0, 0, 0, 0.06));
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.type-tag {
  padding: 5px 12px;
  border-radius: var(--v2-radius-sm, 8px);
  font-size: 12px;
  font-weight: 700;
}

.type-single {
  background: var(--v2-primary-light, #EEF2FF);
  color: var(--v2-primary, #4B6EF5);
}

.type-multi {
  background: rgba(52, 199, 89, 0.1);
  color: var(--v2-success, #34C759);
}

.type-judge {
  background: rgba(255, 149, 0, 0.1);
  color: var(--v2-warning, #FF9500);
}

.question-score {
  font-size: 13px;
  font-weight: 600;
  color: var(--v2-text-muted, #AEAEB2);
}

.question-text {
  font-size: 17px;
  font-weight: 600;
  color: var(--v2-text-primary, #1D1D1F);
  line-height: 1.6;
  margin: 0;
}

/* 选项区域 */
.options-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--v2-bg-card, #FFFFFF);
  border: 2px solid var(--v2-border, #E5E5EA);
  border-radius: var(--v2-radius, 12px);
  cursor: pointer;
  transition: all 0.2s;
}

.option-card:hover {
  border-color: var(--v2-primary, #4B6EF5);
  background: var(--v2-primary-light, #EEF2FF);
}

.option-card.selected {
  border-color: var(--v2-primary, #4B6EF5);
  background: var(--v2-primary-light, #EEF2FF);
}

.option-card.correct {
  border-color: var(--v2-success, #34C759);
  background: rgba(52, 199, 89, 0.08);
}

.option-card.incorrect {
  border-color: var(--v2-danger, #FF3B30);
  background: rgba(255, 59, 48, 0.08);
}

.option-tag {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--v2-bg, #F5F6FA);
  border-radius: var(--v2-radius-sm, 8px);
  font-size: 14px;
  font-weight: 700;
  color: var(--v2-text-secondary, #86868B);
  flex-shrink: 0;
  transition: all 0.2s;
}

.option-card.selected .option-tag {
  background: var(--v2-primary, #4B6EF5);
  color: #fff;
}

.option-card.correct .option-tag {
  background: var(--v2-success, #34C759);
  color: #fff;
}

.option-card.incorrect .option-tag {
  background: var(--v2-danger, #FF3B30);
  color: #fff;
}

.option-text {
  flex: 1;
  font-size: 15px;
  font-weight: 500;
  color: var(--v2-text-primary, #1D1D1F);
  line-height: 1.5;
}

.option-icon {
  margin-left: 8px;
}

.icon-correct {
  color: var(--v2-success, #34C759);
  font-size: 18px;
  font-weight: 700;
}

.icon-incorrect {
  color: var(--v2-danger, #FF3B30);
  font-size: 18px;
  font-weight: 700;
}

/* 答案解析 */
.answer-section {
  background: var(--v2-bg-card, #FFFFFF);
  border-radius: var(--v2-radius-lg, 16px);
  padding: 20px;
  box-shadow: var(--v2-shadow, 0 2px 8px rgba(0, 0, 0, 0.06));
}

.answer-result {
  margin-bottom: 14px;
}

.result-tag {
  display: inline-block;
  padding: 5px 14px;
  border-radius: var(--v2-radius-full, 9999px);
  font-size: 13px;
  font-weight: 700;
}

.result-tag.correct {
  background: rgba(52, 199, 89, 0.12);
  color: var(--v2-success, #34C759);
}

.result-tag.incorrect {
  background: rgba(255, 59, 48, 0.12);
  color: var(--v2-danger, #FF3B30);
}

.answer-detail {
  font-size: 14px;
  line-height: 1.6;
}

.detail-row {
  margin-bottom: 8px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-label {
  color: var(--v2-text-secondary, #86868B);
}

.detail-value {
  color: var(--v2-text-primary, #1D1D1F);
}

.correct-text {
  color: var(--v2-success, #34C759);
  font-weight: 600;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 12px;
}

.btn-submit,
.btn-next {
  flex: 1;
  height: 52px;
  border: none;
  border-radius: var(--v2-radius, 12px);
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-submit {
  background: var(--v2-primary, #4B6EF5);
  color: #fff;
  box-shadow: 0 4px 16px rgba(75, 110, 245, 0.25);
}

.btn-submit:hover {
  background: var(--v2-primary-hover, #3B5DE0);
}

.btn-next {
  background: var(--v2-success, #34C759);
  color: #fff;
  box-shadow: 0 4px 16px rgba(52, 199, 89, 0.25);
}

.btn-next:hover {
  background: #2DB84D;
}

/* =====================
   完成页面
   ===================== */
.complete-page {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.complete-card {
  background: var(--v2-bg-card, #FFFFFF);
  border-radius: var(--v2-radius-xl, 20px);
  padding: 40px;
  text-align: center;
  max-width: 420px;
  width: 100%;
  box-shadow: var(--v2-shadow-lg, 0 8px 24px rgba(0, 0, 0, 0.08));
}

.complete-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(52, 199, 89, 0.12);
  color: var(--v2-success, #34C759);
  font-size: 32px;
  font-weight: 700;
}

.complete-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--v2-text-primary, #1D1D1F);
  margin: 0 0 8px 0;
}

.complete-subtitle {
  margin: 0 0 28px;
  font-size: 14px;
  color: var(--v2-text-secondary, #86868B);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}

.stat-item {
  padding: 18px;
  background: var(--v2-bg, #F5F6FA);
  border-radius: var(--v2-radius, 12px);
}

.stat-value {
  display: block;
  font-size: 26px;
  font-weight: 700;
  color: var(--v2-text-primary, #1D1D1F);
  margin-bottom: 4px;
}

.stat-value.correct {
  color: var(--v2-success, #34C759);
}

.stat-value.incorrect {
  color: var(--v2-danger, #FF3B30);
}

.stat-label {
  font-size: 13px;
  color: var(--v2-text-secondary, #86868B);
}

.btn-restart {
  width: 100%;
  height: 52px;
  background: var(--v2-primary, #4B6EF5);
  color: #fff;
  border: none;
  border-radius: var(--v2-radius, 12px);
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 16px rgba(75, 110, 245, 0.25);
}

.btn-restart:hover {
  background: var(--v2-primary-hover, #3B5DE0);
}

/* 加载状态 */
.loading-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.95);
  z-index: 100;
}

/* =====================
   响应式设计
   ===================== */

/* 平板 */
@media (max-width: 768px) {
  .practice-header {
    padding: 10px 16px;
  }

  .header-title {
    font-size: 16px;
  }

  .source-banner {
    padding: 12px 16px;
  }

  .practice-main {
    padding: 16px;
  }

  .question-wrapper {
    gap: 14px;
  }

  .question-card {
    padding: 20px;
  }

  .question-text {
    font-size: 16px;
  }

  .option-card {
    padding: 14px 16px;
  }

  .option-text {
    font-size: 14px;
  }

  .complete-card {
    padding: 32px 24px;
  }
}

/* 手机 */
@media (max-width: 480px) {
  .practice-header {
    padding: 10px 14px;
  }

  .header-left,
  .header-right {
    width: 60px;
  }

  .header-title {
    font-size: 15px;
  }

  .btn-back {
    padding: 6px;
  }

  .source-banner {
    padding: 10px 14px;
  }

  .practice-main {
    padding: 12px;
  }

  .question-card {
    padding: 16px;
    border-radius: var(--v2-radius, 12px);
  }

  .question-header {
    margin-bottom: 12px;
  }

  .type-tag {
    padding: 4px 10px;
    font-size: 11px;
  }

  .question-score {
    font-size: 12px;
  }

  .question-text {
    font-size: 15px;
  }

  .options-area {
    gap: 10px;
  }

  .option-card {
    padding: 12px 14px;
    gap: 12px;
  }

  .option-tag {
    width: 28px;
    height: 28px;
    font-size: 13px;
  }

  .option-text {
    font-size: 14px;
  }

  .answer-section {
    padding: 16px;
    border-radius: var(--v2-radius, 12px);
  }

  .action-buttons {
    gap: 10px;
  }

  .btn-submit,
  .btn-next {
    height: 48px;
    font-size: 15px;
  }

  .complete-page {
    padding: 16px;
  }

  .complete-card {
    padding: 28px 20px;
  }

  .complete-icon {
    width: 60px;
    height: 60px;
    font-size: 28px;
  }

  .complete-title {
    font-size: 20px;
  }

  .stats-grid {
    gap: 12px;
    margin-bottom: 24px;
  }

  .stat-item {
    padding: 14px;
  }

  .stat-value {
    font-size: 22px;
  }

  .btn-restart {
    height: 48px;
    font-size: 15px;
  }
}
</style>
