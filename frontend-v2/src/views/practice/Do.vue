<template>
  <div class="practice-do-page">
    <!-- 顶部导航 -->
    <header class="practice-header">
      <div class="header-left">
        <button class="btn-back" @click="goBack">
          <svg class="back-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          <span>返回</span>
        </button>
      </div>

      <div class="header-center">
        <div class="header-progress-text">
          第 <span class="progress-current">{{ currentIndex + 1 }}</span> / {{ questions.length }} 题
        </div>
        <div class="header-progress-label">Progress: {{ progressPercent }}% Completed</div>
      </div>

      <div class="header-right">
        <span class="progress-badge">{{ progressPercent }}%</span>
      </div>

      <!-- 进度条 -->
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }" />
      </div>
    </header>

    <!-- 主答题区 -->
    <main class="practice-main-area">
      <!-- 左侧题目 -->
      <div class="practice-content-area">
        <div v-if="loading" class="loading-wrapper">
          <a-spin size="large" />
        </div>

        <template v-else-if="questions.length > 0 && currentQuestion && !finished">
          <!-- 题目卡片 -->
          <div class="question-card">
            <!-- 题目头部 -->
            <div class="question-header">
              <div class="question-header-left">
                <span class="type-tag" :class="getQuestionTypeClass(currentQuestion.type)">
                  {{ getQuestionTypeText(currentQuestion.type) }}
                </span>
                <span class="question-score">{{ currentQuestion.score || 1 }}分</span>
              </div>
              <div class="question-ref">Q-{{ currentQuestion.id }}</div>
            </div>

            <!-- 题干 -->
            <h2 class="question-text">
              {{ currentIndex + 1 }}. {{ currentQuestion.content }}
            </h2>

            <!-- 选项 -->
            <div class="question-options">
              <template v-if="currentQuestion.type === 'multi'">
                <div
                  v-for="option in currentOptions"
                  :key="option.key"
                  class="option-card"
                  :class="{
                    selected: isOptionSelected(option.key),
                    correct: shownQuestions[currentQuestion.id] && isCorrectAnswer(option.key),
                    incorrect: shownQuestions[currentQuestion.id] && isOptionSelected(option.key) && !isCorrectAnswer(option.key),
                  }"
                  @click="toggleOption(option.key)"
                >
                  <div class="option-tag">{{ option.key }}</div>
                  <div class="option-text">{{ option.value }}</div>
                  <div v-if="shownQuestions[currentQuestion.id]" class="option-icon">
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
                    correct: shownQuestions[currentQuestion.id] && isCorrectAnswer(option.key),
                    incorrect: shownQuestions[currentQuestion.id] && answers[currentQuestion.id] === option.key && !isCorrectAnswer(option.key),
                  }"
                  @click="selectOption(option.key)"
                >
                  <div class="option-tag">{{ option.key }}</div>
                  <div class="option-text">{{ option.value }}</div>
                  <div v-if="shownQuestions[currentQuestion.id]" class="option-icon">
                    <span v-if="isCorrectAnswer(option.key)" class="icon-correct">✓</span>
                    <span v-else-if="answers[currentQuestion.id] === option.key" class="icon-incorrect">✗</span>
                  </div>
                </div>
              </template>
            </div>

            <!-- 答案解析 -->
            <div v-if="shownQuestions[currentQuestion.id]" class="explanation-section">
              <div class="result-banner" :class="isCurrentCorrect ? 'result-correct' : 'result-incorrect'">
                <span class="result-icon">{{ isCurrentCorrect ? '✓' : '✗' }}</span>
                <span class="result-text">{{ isCurrentCorrect ? '回答正确' : '回答错误' }}</span>
              </div>
              <div class="explanation-content">
                <div class="explanation-row">
                  <span class="explanation-label">正确答案：</span>
                  <span class="explanation-value correct">{{ formatAnswer(currentQuestion.answer, currentQuestion) }}</span>
                </div>
                <div v-if="currentQuestion.explanation" class="explanation-row">
                  <span class="explanation-label">解析：</span>
                  <span class="explanation-value">{{ currentQuestion.explanation }}</span>
                </div>
              </div>
            </div>

            <!-- 导航 -->
            <div class="question-footer">
              <button class="nav-btn nav-prev" :disabled="currentIndex === 0" @click="prevQuestion">
                <svg class="nav-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/>
                </svg>
                上一题
              </button>
              <div v-if="currentQuestion.type === 'multi' && !shownQuestions[currentQuestion.id]" class="nav-divider" />
              <button
                v-if="currentQuestion.type === 'multi' && !shownQuestions[currentQuestion.id]"
                class="nav-btn nav-confirm"
                :disabled="!hasMultiSelected"
                @click="confirmAnswer"
              >
                确认答案
                <svg class="nav-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
                </svg>
              </button>
              <div v-if="currentQuestion.type === 'multi' && !shownQuestions[currentQuestion.id]" class="nav-divider" />
              <button v-if="currentIndex < questions.length - 1" class="nav-btn nav-next" @click="nextQuestion">
                下一题
                <svg class="nav-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/>
                </svg>
              </button>
              <button v-else class="nav-btn nav-finish" @click="finishPractice">
                完成练习
                <svg class="nav-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
                </svg>
              </button>
            </div>
          </div>
        </template>

        <!-- 完成页面 -->
        <div v-else-if="finished" class="complete-card">
          <div class="complete-icon-ring">
            <svg class="complete-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
            </svg>
          </div>
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
              <span class="stat-value" :class="accuracy >= 60 ? 'good' : 'low'">{{ accuracy }}%</span>
              <span class="stat-label">正确率</span>
            </div>
          </div>
          <div class="complete-actions">
            <button class="btn-restart" @click="restartPractice">重新练习</button>
            <button class="btn-back-home" @click="returnToHome">返回首页</button>
          </div>
        </div>
      </div>

      <!-- 右侧答题卡 -->
      <aside class="answer-sidebar">
        <div class="sidebar-header">
          <h3 class="sidebar-title">
            <svg class="sidebar-title-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            答题卡
          </h3>
          <span class="sidebar-badge">共 {{ questions.length }} 题</span>
        </div>

        <div class="sidebar-stats">
          <div class="stat-item stat-answered">
            <div class="stat-label">已答</div>
            <div class="stat-num">{{ answeredCount }}</div>
          </div>
          <div class="stat-item stat-unanswered">
            <div class="stat-label">未答</div>
            <div class="stat-num">{{ questions.length - answeredCount }}</div>
          </div>
        </div>

        <div class="sidebar-grid">
          <div
            v-for="(q, index) in questions"
            :key="q.id"
            class="grid-item"
            :class="getGridItemClass(q, index)"
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
            <span class="legend-dot legend-correct" />
            <span>正确</span>
          </div>
          <div class="legend-item">
            <span class="legend-dot legend-wrong" />
            <span>错误</span>
          </div>
          <div class="legend-item">
            <span class="legend-dot legend-unanswered" />
            <span>未答</span>
          </div>
        </div>
      </aside>
    </main>

    <div v-if="loading" class="loading-overlay">
      <a-spin size="large" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useRoute, useRouter } from 'vue-router'
import { getPracticeQuestions, savePracticeRecord } from '@/api/practice'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const questions = ref([])
const currentIndex = ref(0)
const answers = ref({})
const shownQuestions = ref({})
const finished = ref(false)
const startTime = ref(Date.now())

const questionTypeLabels = {
  single: '单选题',
  multi: '多选题',
  judge: '判断题',
}

const currentQuestion = computed(() => questions.value[currentIndex.value] || null)

const progressPercent = computed(() => {
  if (questions.value.length === 0) return 0
  if (finished.value) return 100
  return Math.round(((currentIndex.value + 1) / questions.value.length) * 100)
})

const answeredCount = computed(() => {
  return Object.keys(answers.value).filter(
    (key) => answers.value[key] !== undefined && answers.value[key] !== '' && answers.value[key] !== null
  ).length
})

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
  if (questions.value.length === 0) return 0
  return Math.round((correctCount.value / questions.value.length) * 100)
})

const isCurrentCorrect = computed(() => {
  if (!currentQuestion.value) return false
  return isAnswerCorrect(currentQuestion.value, answers.value[currentQuestion.value.id])
})

const currentOptions = computed(() => {
  if (!currentQuestion.value) return []
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
    return { sourceType: 'knowledge-point', sourceId: legacyKpId, sourceName }
  }
  return null
})

const practiceFilters = computed(() => ({
  questionLimit: parseQuestionLimit(getSingleQueryValue(route.query.questionLimit)),
  questionTypes: normalizeQuestionTypeList(getSingleQueryValue(route.query.questionType)),
  difficulties: parsePositiveIntList(getSingleQueryValue(route.query.difficulty)),
  policeTypeId: parsePositiveInt(getSingleQueryValue(route.query.policeTypeId)),
  policeTypeName: getSingleQueryValue(route.query.policeTypeName),
  keyword: getSingleQueryValue(route.query.keyword).trim(),
  courseId: parsePositiveInt(getSingleQueryValue(route.query.courseId)),
  courseName: getSingleQueryValue(route.query.courseName),
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
  if (practiceFilters.value.questionTypes.length) {
    tags.push(practiceFilters.value.questionTypes.map((item) => questionTypeLabels[item] || item).join(' / '))
  }
  if (practiceFilters.value.difficulties.length) {
    tags.push(`难度 ${practiceFilters.value.difficulties.join(' / ')}`)
  }
  if (practiceFilters.value.policeTypeName) {
    tags.push(`警种：${practiceFilters.value.policeTypeName}`)
  }
  if (practiceFilters.value.courseName) {
    tags.push(`课程：${practiceFilters.value.courseName}`)
  }
  if (practiceFilters.value.keyword) {
    tags.push(`关键词：${practiceFilters.value.keyword}`)
  }
  return tags.join(' · ')
})

function getSingleQueryValue(value) {
  if (Array.isArray(value)) return value[0] || ''
  return value ? String(value) : ''
}

function parsePositiveInt(value) {
  if (!value) return null
  const parsed = Number(value)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null
}

function parseQuestionLimit(value) {
  if (!value) return 20
  if (value === 'all') return null
  return parsePositiveInt(value)
}

function normalizeSourceType(value) {
  if (value === 'knowledge-point' || value === 'question-folder') return value
  return ''
}

function normalizeQuestionType(value) {
  if (value === 'single' || value === 'multi' || value === 'judge') return value
  return ''
}

function normalizeQuestionTypeList(value) {
  if (!value) return []
  return String(value)
    .split(',')
    .map((item) => normalizeQuestionType(item.trim()))
    .filter(Boolean)
}

function parsePositiveIntList(value) {
  if (!value) return []
  return String(value)
    .split(',')
    .map((item) => parsePositiveInt(item.trim()))
    .filter((item) => Number.isInteger(item) && item > 0)
}

function shuffleQuestions(list) {
  const shuffled = [...list]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

function applyQuestionLimit(list, limit) {
  if (!limit || list.length <= limit) return list
  return shuffleQuestions(list).slice(0, limit)
}

function filterQuestionsByConditions(list, options = {}) {
  const questionTypes = options.questionTypes || []
  const difficulties = options.difficulties || []
  return list.filter((question) => {
    const matchedType = !questionTypes.length || questionTypes.includes(String(question?.type || ''))
    const matchedDifficulty = !difficulties.length || difficulties.includes(Number(question?.difficulty || 0))
    return matchedType && matchedDifficulty
  })
}

function buildSelectionTiers() {
  const questionTypes = practiceFilters.value.questionTypes
  const difficulties = practiceFilters.value.difficulties
  const tiers = [
    {
      label: '所选题型和难度',
      options: { questionTypes, difficulties },
    },
  ]

  if (questionTypes.length && difficulties.length) {
    tiers.push({
      label: '所选题型，不限难度',
      options: { questionTypes, difficulties: [] },
    })
    tiers.push({
      label: '不限题型，所选难度',
      options: { questionTypes: [], difficulties },
    })
  }

  if (questionTypes.length || difficulties.length) {
    tiers.push({
      label: '当前知识点/题库下全部题目',
      options: { questionTypes: [], difficulties: [] },
    })
  }

  return tiers
}

function applyPracticeFilters(list, limit) {
  const tiers = buildSelectionTiers()
  const strictMatches = shuffleQuestions(filterQuestionsByConditions(list, tiers[0]?.options || {}))

  if (!limit) {
    if (strictMatches.length) {
      return { questions: strictMatches, notice: '' }
    }
    for (const tier of tiers.slice(1)) {
      const fallbackMatches = shuffleQuestions(filterQuestionsByConditions(list, tier.options))
      if (fallbackMatches.length) {
        return {
          questions: fallbackMatches,
          notice: `未找到完全符合条件的题目，已自动放宽为“${tier.label}”。`,
        }
      }
    }
    return { questions: [], notice: '' }
  }

  const selected = []
  const selectedIds = new Set()
  const usedTiers = []

  for (const tier of tiers) {
    if (selected.length >= limit) break
    const tierMatches = shuffleQuestions(filterQuestionsByConditions(list, tier.options))
    for (const question of tierMatches) {
      if (selected.length >= limit) break
      if (selectedIds.has(question.id)) continue
      selected.push(question)
      selectedIds.add(question.id)
      if (!usedTiers.includes(tier.label)) {
        usedTiers.push(tier.label)
      }
    }
  }

  if (strictMatches.length >= limit || usedTiers.length <= 1) {
    if (selected.length > 0 && selected.length < limit) {
      return {
        questions: selected,
        notice: `当前筛选仅找到 ${selected.length} 题，将按现有题目开始练习。`,
      }
    }
    return { questions: selected, notice: '' }
  }

  if (strictMatches.length > 0) {
    return {
      questions: selected,
      notice: `当前筛选仅匹配 ${strictMatches.length} 题，已自动放宽条件补足到 ${selected.length} 题。`,
    }
  }

  return {
    questions: selected,
    notice: `未找到完全符合条件的题目，已自动放宽为“${usedTiers[usedTiers.length - 1]}”。`,
  }
}

function getQuestionTypeClass(type) {
  return { single: 'type-single', multi: 'type-multi', judge: 'type-judge' }[type] || 'type-default'
}

function getQuestionTypeText(type) {
  return questionTypeLabels[type] || type
}

function isOptionSelected(key) {
  const answer = answers.value[currentQuestion.value?.id]
  if (Array.isArray(answer)) return answer.includes(key)
  return answer === key
}

function normalizeAnswerValue(question, answer) {
  if (answer === null || answer === undefined) return null
  if (question?.type === 'judge') {
    if (answer === true || answer === 'true' || answer === 1 || answer === '1' || answer === 'A') return 'A'
    if (answer === false || answer === 'false' || answer === 0 || answer === '0' || answer === 'B') return 'B'
  }
  if (Array.isArray(answer)) return answer.map((item) => String(item))
  return String(answer)
}

function isCorrectAnswer(key) {
  if (currentQuestion.value?.answer === undefined || currentQuestion.value?.answer === null) return false
  const correct = normalizeAnswerValue(currentQuestion.value, currentQuestion.value.answer)
  if (Array.isArray(correct)) return correct.includes(key)
  return correct === String(key)
}

function isAnswerCorrect(question, userAnswer) {
  if (question?.answer === undefined || question?.answer === null || userAnswer === undefined) return false
  const correct = normalizeAnswerValue(question, question.answer)
  const normalizedUser = normalizeAnswerValue(question, userAnswer)
  if (Array.isArray(correct)) {
    if (!Array.isArray(normalizedUser)) return false
    return [...correct].sort().join(',') === [...normalizedUser].sort().join(',')
  }
  return correct === normalizedUser
}

function formatAnswer(answer, question = currentQuestion.value) {
  if (answer === undefined || answer === null) return '-'
  const normalized = normalizeAnswerValue(question, answer)
  if (question?.type === 'judge') return normalized === 'A' ? '正确' : '错误'
  if (Array.isArray(normalized)) return normalized.join('、')
  return String(normalized)
}

function selectOption(key) {
  if (shownQuestions.value[currentQuestion.value?.id] || !currentQuestion.value) return
  answers.value[currentQuestion.value.id] = key
  submitAnswer()
}

function toggleOption(key) {
  if (shownQuestions.value[currentQuestion.value?.id]) return
  const qid = currentQuestion.value?.id
  if (!qid) return
  const current = answers.value[qid]
  if (!Array.isArray(current)) {
    answers.value[qid] = [key]
  } else {
    const idx = current.indexOf(key)
    if (idx === -1) current.push(key)
    else current.splice(idx, 1)
    answers.value[qid] = [...current]
  }
}

function submitAnswer() {
  const qid = currentQuestion.value?.id
  if (!qid || answers.value[qid] === undefined) return
  shownQuestions.value[qid] = true
}

function confirmAnswer() {
  const qid = currentQuestion.value?.id
  if (!qid) return
  const answer = answers.value[qid]
  if (!answer || (Array.isArray(answer) && answer.length === 0)) return
  shownQuestions.value[qid] = true
}

const hasMultiSelected = computed(() => {
  if (!currentQuestion.value || currentQuestion.value.type !== 'multi') return false
  const answer = answers.value[currentQuestion.value.id]
  return Array.isArray(answer) && answer.length > 0
})

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

function getGridItemClass(q, index) {
  const answer = answers.value[q.id]
  const hasAnswer = answer !== undefined && answer !== '' && answer !== null
  const isCorrect = hasAnswer && isAnswerCorrect(q, answer)
  const isShown = !!shownQuestions.value[q.id]

  if (index === currentIndex.value) return 'current'
  if (!hasAnswer) return 'unanswered'
  if (!isShown) return 'done'
  return isCorrect ? 'correct' : 'wrong'
}

function goToQuestion(index) {
  currentIndex.value = index
}

async function finishPractice() {
  const duration = Math.round((Date.now() - startTime.value) / 1000)
  const source = practiceSource.value

  try {
    await savePracticeRecord({
      source_type: source?.sourceType || '',
      source_id: Number(source?.sourceId) || 0,
      source_name: source?.sourceName || '',
      total_count: questions.value.length,
      correct_count: correctCount.value,
      wrong_count: questions.value.length - correctCount.value,
      accuracy: accuracy.value,
      duration,
      question_limit: practiceFilters.value.questionLimit ? String(practiceFilters.value.questionLimit) : 'all',
      question_type: practiceFilters.value.questionTypes.length ? practiceFilters.value.questionTypes.join(',') : undefined,
      difficulty: practiceFilters.value.difficulties.length === 1 ? practiceFilters.value.difficulties[0] : undefined,
    })
  } catch (e) {
    // 记录保存失败不影响完成流程
  }

  finished.value = true
}

function restartPractice() {
  currentIndex.value = 0
  answers.value = {}
  shownQuestions.value = {}
  finished.value = false
  startTime.value = Date.now()
}

function returnToHome() {
  router.replace({ path: '/practice' })
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
      page: 1,
      size: 1000,
    }
    if (practiceFilters.value.keyword) params.search = practiceFilters.value.keyword
    if (practiceFilters.value.questionTypes.length === 1) params.type = practiceFilters.value.questionTypes[0]
    if (practiceFilters.value.difficulties.length === 1) params.difficulty = practiceFilters.value.difficulties[0]
    if (practiceFilters.value.policeTypeId) params.police_type_id = practiceFilters.value.policeTypeId
    if (practiceFilters.value.courseId) params.course_id = practiceFilters.value.courseId
    if (source.sourceType === 'knowledge-point') {
      params.knowledge_point_id = Number(source.sourceId)
    } else if (source.sourceType === 'question-folder') {
      params.folder_id = Number(source.sourceId)
      params.recursive = true
    } else {
      throw new Error('暂不支持的练习来源')
    }

    const response = await getPracticeQuestions(params)
    const resolved = applyPracticeFilters(response?.items || [], practiceFilters.value.questionLimit)
    questions.value = resolved.questions

    if (resolved.notice) {
      message.warning(resolved.notice)
    }

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

onMounted(() => { void loadQuestions() })
</script>

<style scoped>
.practice-do-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #F8FAFC;
}

/* =====================
   顶部导航
   ===================== */
.practice-header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  height: 72px;
  background: #fff;
  border-bottom: 1px solid #E2E8F0;
  flex-shrink: 0;
}

.header-left {
  flex: 1;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
}

.header-progress-text {
  font-size: 15px;
  font-weight: 700;
  color: #0F172A;
}

.progress-current {
  color: #4B6EF5;
  font-size: 18px;
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
  flex: 1;
  display: flex;
  justify-content: flex-end;
}

.progress-badge {
  font-size: 14px;
  font-weight: 700;
  color: #4B6EF5;
  background: #EEF2FF;
  padding: 6px 14px;
  border-radius: 999px;
}

.btn-back {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  padding: 10px 16px;
  cursor: pointer;
  color: #64748B;
  font-size: 14px;
  font-weight: 600;
  border-radius: 10px;
  transition: all 0.2s;
}

.btn-back:hover {
  background: #F8FAFC;
  color: #4B6EF5;
}

.back-icon {
  width: 18px;
  height: 18px;
}

.progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: #E2E8F0;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4B6EF5 0%, #6B8EFF 100%);
  transition: width 0.3s ease;
}

/* =====================
   主答题区
   ===================== */
.practice-main-area {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.practice-content-area {
  flex: 1;
  overflow-y: auto;
  padding: 32px 48px;
  display: flex;
  flex-direction: column;
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
  border-radius: 24px;
  overflow: hidden;
}

.question-header {
  padding: 32px 40px 20px;
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
  color: #4B6EF5;
  border: 1px solid #BFDBFE;
}

.type-multi {
  background: #F0FDF4;
  color: #34C759;
  border: 1px solid #BBF7D0;
}

.type-judge {
  background: #FEF3C7;
  color: #FF9500;
  border: 1px solid #FCD34D;
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
  font-size: 20px;
  font-weight: 700;
  color: #0F172A;
  line-height: 1.6;
  padding: 28px 40px;
  margin: 0;
}

/* =====================
   选项
   ===================== */
.question-options {
  padding: 0 40px 32px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.option-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px 24px;
  border: 1.5px solid #E2E8F0;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: #fff;
}

.option-card:hover {
  border-color: #4B6EF5;
  background: #F8FAFC;
  transform: translateY(-2px);
}

.option-card.selected {
  border-color: #4B6EF5;
  background: #EEF2FF;
  box-shadow: 0 4px 12px rgba(75, 110, 245, 0.1);
}

.option-card.correct {
  border-color: #34C759;
  background: #F0FDF4;
}

.option-card.incorrect {
  border-color: #FF3B30;
  background: #FEF2F2;
}

.option-tag {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: #F1F5F9;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #64748B;
  flex-shrink: 0;
  transition: all 0.2s;
}

.option-card.selected .option-tag {
  background: #4B6EF5;
  color: #fff;
}

.option-card.correct .option-tag {
  background: #34C759;
  color: #fff;
}

.option-card.incorrect .option-tag {
  background: #FF3B30;
  color: #fff;
}

.option-text {
  flex: 1;
  font-size: 15px;
  font-weight: 500;
  color: #334155;
  line-height: 1.6;
}

.option-icon {
  margin-left: 8px;
}

.icon-correct {
  color: #34C759;
  font-size: 20px;
  font-weight: 700;
}

.icon-incorrect {
  color: #FF3B30;
  font-size: 20px;
  font-weight: 700;
}

/* =====================
   答案解析
   ===================== */
.explanation-section {
  margin: 0 40px 24px;
  background: #fff;
  border: 1px solid #E2E8F0;
  border-radius: 16px;
  overflow: hidden;
}

.result-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  font-size: 14px;
  font-weight: 700;
}

.result-correct {
  background: #F0FDF4;
  color: #34C759;
  border-bottom: 1px solid #BBF7D0;
}

.result-incorrect {
  background: #FEF2F2;
  color: #FF3B30;
  border-bottom: 1px solid #FECACA;
}

.result-icon {
  font-size: 18px;
  font-weight: 700;
}

.explanation-content {
  padding: 16px 20px;
  font-size: 14px;
  line-height: 1.7;
}

.explanation-row {
  margin-bottom: 8px;
}

.explanation-row:last-child {
  margin-bottom: 0;
}

.explanation-label {
  color: #64748B;
  font-weight: 600;
}

.explanation-value {
  color: #334155;
}

.explanation-value.correct {
  color: #34C759;
  font-weight: 700;
}

/* =====================
   导航按钮
   ===================== */
.question-footer {
  padding: 20px 40px;
  background: #F8FAFC;
  border-top: 1px solid #E2E8F0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.nav-prev {
  color: #94A3B8;
  background: transparent;
}

.nav-prev:hover:not(:disabled) {
  color: #334155;
  background: #E2E8F0;
}

.nav-next {
  color: #4B6EF5;
  background: transparent;
}

.nav-next:hover {
  background: #EEF2FF;
}

.nav-finish {
  color: #34C759;
  background: transparent;
}

.nav-finish:hover {
  background: #F0FDF4;
}

.nav-confirm {
  color: #fff;
  background: #4B6EF5;
  font-weight: 700;
}

.nav-confirm:hover:not(:disabled) {
  background: #3B5DE0;
}

.nav-confirm:disabled {
  color: #94A3B8;
  background: #E2E8F0;
  cursor: not-allowed;
}

.nav-icon {
  width: 18px;
  height: 18px;
}

.nav-divider {
  width: 1px;
  height: 36px;
  background: #E2E8F0;
}

/* =====================
   右侧答题卡
   ===================== */
.answer-sidebar {
  width: 320px;
  background: #fff;
  border-left: 1px solid #E2E8F0;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 28px 24px;
  border-bottom: 1px solid #F1F5F9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-title {
  font-size: 15px;
  font-weight: 700;
  color: #0F172A;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sidebar-title-icon {
  width: 18px;
  height: 18px;
  color: #4B6EF5;
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
  padding: 20px 24px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stat-item {
  padding: 14px;
  border-radius: 12px;
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
  color: #34C759;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-bottom: 4px;
}

.stat-unanswered .stat-label {
  color: #94A3B8;
}

.stat-num {
  font-size: 24px;
  font-weight: 700;
  color: #16A34A;
  line-height: 1;
}

.stat-unanswered .stat-num {
  color: #0F172A;
}

.sidebar-grid {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  align-content: start;
}

.grid-item {
  aspect-ratio: 1 / 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s;
  cursor: pointer;
}

.grid-item.current {
  background: #4B6EF5;
  color: #fff;
  box-shadow: 0 4px 8px rgba(75, 110, 245, 0.3);
}

.grid-item.done {
  background: #DCFCE7;
  color: #166534;
  border: 1px solid #BBF7D0;
}

.grid-item.correct {
  background: #34C759;
  color: #fff;
  border: 1px solid #25A049;
}

.grid-item.wrong {
  background: #FF3B30;
  color: #fff;
  border: 1px solid #E52B2B;
}

.grid-item.unanswered {
  background: #fff;
  color: #64748B;
  border: 1px solid #E2E8F0;
}

.sidebar-legend {
  padding: 16px 24px;
  border-top: 1px solid #F1F5F9;
  background: #F8FAFC;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
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

.legend-current { background: #4B6EF5; }
.legend-correct { background: #34C759; }
.legend-wrong { background: #FF3B30; }
.legend-unanswered { background: #E2E8F0; }

/* =====================
   完成页面
   ===================== */
.complete-card {
  width: 100%;
  background: #fff;
  border-radius: 24px;
  padding: 48px;
  text-align: center;
  box-shadow: 0 24px 56px rgba(24, 39, 75, 0.1);
}

.complete-icon-ring {
  width: 88px;
  height: 88px;
  margin: 0 auto 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(52, 199, 89, 0.1);
  border: 2px solid rgba(52, 199, 89, 0.2);
}

.complete-icon {
  width: 44px;
  height: 44px;
  color: #34C759;
}

.complete-title {
  font-size: 26px;
  font-weight: 700;
  color: #0F172A;
  margin: 0 0 10px 0;
}

.complete-subtitle {
  margin: 0 0 32px;
  font-size: 14px;
  color: #64748B;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-item {
  padding: 20px;
  background: #F8FAFC;
  border-radius: 14px;
}

.stat-value {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: #0F172A;
  margin-bottom: 6px;
}

.stat-value.correct { color: #34C759; }
.stat-value.incorrect { color: #FF3B30; }
.stat-value.good { color: #34C759; }
.stat-value.low { color: #FF3B30; }

.stat-label {
  font-size: 13px;
  color: #64748B;
}

.complete-actions {
  display: flex;
  gap: 12px;
}

.btn-restart {
  flex: 1;
  height: 48px;
  background: #4B6EF5;
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-restart:hover {
  background: #3B5DE0;
}

.btn-back-home {
  flex: 1;
  height: 48px;
  background: #F8FAFC;
  color: #64748B;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-back-home:hover {
  background: #F1F5F9;
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
   响应式
   ===================== */
@media (max-width: 1200px) {
  .practice-header {
    padding: 0 24px;
  }

  .header-center {
    display: none;
  }

  .practice-content-area {
    padding: 24px;
  }

  .question-header {
    padding: 24px 28px 16px;
  }

  .question-text {
    padding: 24px 28px;
    font-size: 18px;
  }

  .question-options {
    padding: 0 28px 24px;
  }

  .explanation-section {
    margin: 0 28px 20px;
  }

  .question-footer {
    padding: 16px 28px;
  }

  .answer-sidebar {
    width: 280px;
  }

  .sidebar-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 900px) {
  .answer-sidebar {
    display: none;
  }

  .practice-header {
    height: 64px;
  }

  .practice-content-area {
    padding: 16px;
  }

  .question-card {
    border-radius: 20px;
  }

  .question-header {
    padding: 20px 24px 14px;
  }

  .question-text {
    padding: 20px 24px;
    font-size: 17px;
  }

  .question-options {
    padding: 0 24px 20px;
    gap: 10px;
  }

  .option-card {
    padding: 16px 18px;
    gap: 14px;
  }

  .option-tag {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }

  .option-text {
    font-size: 14px;
  }

  .explanation-section {
    margin: 0 24px 16px;
    border-radius: 12px;
  }

  .question-footer {
    padding: 14px 24px;
  }

  .nav-btn {
    padding: 10px 18px;
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .practice-header {
    padding: 0 14px;
    height: 56px;
  }

  .btn-back span {
    display: none;
  }

  .btn-back {
    padding: 8px;
  }

  .back-icon {
    width: 20px;
    height: 20px;
  }

  .progress-badge {
    font-size: 12px;
    padding: 5px 12px;
  }

  .practice-content-area {
    padding: 12px 12px 80px;
  }

  .question-card {
    border-radius: 16px;
  }

  .question-header {
    padding: 16px 18px 12px;
    flex-wrap: wrap;
    gap: 8px;
  }

  .question-header-left {
    gap: 8px;
  }

  .type-tag {
    padding: 4px 10px;
    font-size: 10px;
  }

  .question-ref {
    font-size: 9px;
  }

  .question-text {
    padding: 16px 18px;
    font-size: 15px;
  }

  .question-options {
    padding: 0 18px 16px;
    gap: 8px;
  }

  .option-card {
    padding: 12px 14px;
    gap: 12px;
    border-radius: 10px;
  }

  .option-tag {
    width: 28px;
    height: 28px;
    font-size: 13px;
    border-radius: 8px;
  }

  .option-text {
    font-size: 14px;
  }

  .explanation-section {
    margin: 0 18px 12px;
    border-radius: 10px;
  }

  .question-footer {
    padding: 12px 18px;
    flex-wrap: wrap;
    gap: 8px;
  }

  .nav-btn {
    flex: 1;
    justify-content: center;
    padding: 10px 12px;
    font-size: 13px;
  }

  .nav-divider {
    display: none;
  }

  .complete-card {
    padding: 32px 24px;
    border-radius: 20px;
  }

  .complete-icon-ring {
    width: 72px;
    height: 72px;
  }

  .complete-icon {
    width: 36px;
    height: 36px;
  }

  .complete-title {
    font-size: 22px;
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

  .complete-actions {
    flex-direction: column;
  }
}
</style>
