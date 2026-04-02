<template>
  <div class="practice-do-page">
    <!-- 顶部导航 -->
    <header class="practice-header">
      <div class="header-left">
        <button class="btn-back" @click="goBack">
          <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
        </button>
      </div>
      <div class="header-title">刷题练习</div>
      <div class="header-right">
        <span class="progress-text">{{ currentIndex + 1 }}/{{ questions.length }}</span>
      </div>
    </header>

    <!-- 进度条 -->
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
    </div>

    <!-- 题目区域 -->
    <main class="practice-main" v-if="currentQuestion">
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
              incorrect: showAnswer && isOptionSelected(option.key) && !isCorrectAnswer(option.key)
            }"
            @click="toggleOption(option.key)"
          >
            <div class="option-tag">{{ option.key }}</div>
            <div class="option-text">{{ option.value }}</div>
            <div class="option-icon" v-if="showAnswer">
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
              incorrect: showAnswer && answers[currentQuestion.id] === option.key && !isCorrectAnswer(option.key)
            }"
            @click="selectOption(option.key)"
          >
            <div class="option-tag">{{ option.key }}</div>
            <div class="option-text">{{ option.value }}</div>
            <div class="option-icon" v-if="showAnswer">
              <span v-if="isCorrectAnswer(option.key)" class="icon-correct">✓</span>
              <span v-else-if="answers[currentQuestion.id] === option.key" class="icon-incorrect">✗</span>
            </div>
          </div>
        </template>
      </div>

      <!-- 答案解析 -->
      <div class="answer-section" v-if="showAnswer">
        <div class="answer-result">
          <span class="result-tag" :class="isCurrentCorrect ? 'correct' : 'incorrect'">
            {{ isCurrentCorrect ? '回答正确' : '回答错误' }}
          </span>
        </div>
        <div class="answer-detail">
          <div class="detail-row">
            <span class="detail-label">正确答案：</span>
            <span class="detail-value correct-text">{{ formatAnswer(currentQuestion.answer) }}</span>
          </div>
          <div class="detail-row" v-if="currentQuestion.explanation">
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
    </main>

    <!-- 完成页面 -->
    <div class="complete-page" v-else-if="finished">
      <div class="complete-card">
        <div class="complete-icon">🎉</div>
        <h2 class="complete-title">练习完成</h2>
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

    <div class="loading-overlay" v-if="loading">
      <a-spin size="large" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
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
  if (questions.value.length === 0) return 0
  return ((currentIndex.value + 1) / questions.value.length) * 100
})

const correctCount = computed(() => {
  let count = 0
  for (const q of questions.value) {
    const userAnswer = answers.value[q.id]
    if (isAnswerCorrect(q, userAnswer)) {
      count++
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
  if (typeof options === 'object' && !Array.isArray(options)) {
    return Object.entries(options).map(([key, value]) => ({ key, value }))
  }
  return []
})

function getQuestionTypeClass(type) {
  const map = { single: 'type-single', multi: 'type-multi', judge: 'type-judge' }
  return map[type] || 'type-single'
}

function getQuestionTypeText(type) {
  const map = { single: '单选题', multi: '多选题', judge: '判断题' }
  return map[type] || type
}

function isOptionSelected(key) {
  const answer = answers.value[currentQuestion.value?.id]
  if (Array.isArray(answer)) {
    return answer.includes(key)
  }
  return answer === key
}

function isCorrectAnswer(key) {
  if (!currentQuestion.value?.answer) return false
  const correct = currentQuestion.value.answer
  if (Array.isArray(correct)) {
    return correct.includes(key)
  }
  return String(correct) === String(key)
}

function isAnswerCorrect(question, userAnswer) {
  if (!question?.answer || userAnswer === undefined) return false
  const correct = question.answer
  if (Array.isArray(correct)) {
    if (!Array.isArray(userAnswer)) return false
    const sortedCorrect = [...correct].sort()
    const sortedUser = [...userAnswer].sort()
    return sortedCorrect.join(',') === sortedUser.join(',')
  }
  return String(correct) === String(userAnswer)
}

function formatAnswer(answer) {
  if (!answer) return '-'
  if (Array.isArray(answer)) return answer.join('、')
  return String(answer)
}

function selectOption(key) {
  if (showAnswer.value) return
  if (currentQuestion.value) {
    answers.value[currentQuestion.value.id] = key
  }
}

function toggleOption(key) {
  if (showAnswer.value) return
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

function submitAnswer() {
  if (answers.value[currentQuestion.value?.id] === undefined) {
    message.warning('请先选择答案')
    return
  }
  showAnswer.value = true
}

function nextQuestion() {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++
    showAnswer.value = false
  } else {
    finished.value = true
  }
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

async function loadQuestions() {
  const kpId = route.query.kpId
  if (!kpId) {
    message.error('缺少知识点参数')
    router.back()
    return
  }
  loading.value = true
  try {
    const res = await getQuestionsApiV1QuestionsGet({
      knowledge_point: String(kpId),
      size: 20
    })
    questions.value = res.data?.items || []
    if (questions.value.length === 0) {
      message.warning('该知识点暂无题目')
      router.back()
    }
  } catch (e) {
    message.error('加载题目失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadQuestions()
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

.header-left, .header-right {
  width: 60px;
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

.btn-submit, .btn-next {
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
  font-size: 48px;
  margin-bottom: 16px;
}

.complete-title {
  font-size: 20px;
  font-weight: 700;
  color: #1E293B;
  margin: 0 0 24px 0;
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
