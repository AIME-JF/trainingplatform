<template>
  <div class="practice-do-page">
    <!-- 顶部导航 -->
    <div class="practice-header">
      <div class="header-left">
        <a-button type="text" @click="handleBack">
          <LeftOutlined /> 返回
        </a-button>
      </div>
      <div class="header-center">
        <span class="progress-text">第 {{ currentIndex + 1 }} / {{ questions.length }} 题</span>
      </div>
      <div class="header-right">
        <a-tag v-if="timeLimit" color="blue">{{ remainingTime }} 分钟</a-tag>
      </div>
    </div>

    <!-- 进度条 -->
    <a-progress
      :percent="progressPercent"
      :show-info="false"
      style="margin-bottom: 16px"
    />

    <!-- 题目区域 -->
    <div class="practice-content">
      <div v-if="questions.length > 0 && currentQuestion" class="question-card">
        <!-- 题目头部 -->
        <div class="question-header">
          <a-space>
            <a-tag :color="getTypeColor(currentQuestion.type)">
              {{ getTypeLabel(currentQuestion.type) }}
            </a-tag>
            <span class="question-id">Q-{{ currentQuestion.id }}</span>
          </a-space>
        </div>

        <!-- 题干 -->
        <div class="question-content">
          {{ currentIndex + 1 }}. {{ currentQuestion.content }}
        </div>

        <!-- 选项 -->
        <div class="question-options">
          <template v-if="currentQuestion.type === 'multi'">
            <div
              v-for="option in currentOptions"
              :key="option.key"
              class="option-item"
              :class="{
                selected: isMultiSelected(option.key),
                correct: shownQuestions[currentQuestion.id] && isCorrectAnswer(option.key),
                incorrect: shownQuestions[currentQuestion.id] && isMultiSelected(option.key) && !isCorrectAnswer(option.key),
              }"
              @click="toggleMultiOption(option.key)"
            >
              <div class="option-checkbox">
                <CheckOutlined v-if="isMultiSelected(option.key)" />
              </div>
              <span class="option-key">{{ option.key }}</span>
              <span class="option-text">{{ option.value }}</span>
            </div>
          </template>
          <template v-else>
            <div
              v-for="option in currentOptions"
              :key="option.key"
              class="option-item"
              :class="{
                selected: answers[currentQuestion.id] === option.key,
                correct: shownQuestions[currentQuestion.id] && isCorrectAnswer(option.key),
                incorrect: shownQuestions[currentQuestion.id] && answers[currentQuestion.id] === option.key && !isCorrectAnswer(option.key),
              }"
              @click="selectOption(option.key)"
            >
              <div class="option-radio">
                <CheckOutlined v-if="answers[currentQuestion.id] === option.key" />
              </div>
              <span class="option-key">{{ option.key }}</span>
              <span class="option-text">{{ option.value }}</span>
            </div>
          </template>
        </div>

        <!-- 答案解析 -->
        <div v-if="shownQuestions[currentQuestion.id] && showExplanation" class="explanation-section">
          <a-alert
            :message="isCurrentCorrect ? '回答正确' : '回答错误'"
            :type="isCurrentCorrect ? 'success' : 'error'"
            show-icon
            style="margin-bottom: 12px"
          >
            <template #description>
              <div v-if="currentQuestion.explanation" style="margin-top: 8px">
                <strong>解析：</strong>{{ currentQuestion.explanation }}
              </div>
            </template>
          </a-alert>
        </div>

        <!-- 导航按钮 -->
        <div class="question-footer">
          <a-space>
            <a-button :disabled="currentIndex === 0" @click="prevQuestion">
              <LeftOutlined /> 上一题
            </a-button>
            <a-button
              v-if="currentQuestion.type === 'multi' && !shownQuestions[currentQuestion.id]"
              type="primary"
              :disabled="!hasMultiSelected"
              @click="confirmAnswer"
            >
              确认答案
            </a-button>
            <a-button
              v-if="currentIndex < questions.length - 1"
              type="primary"
              @click="nextQuestion"
            >
              下一题 <RightOutlined />
            </a-button>
            <a-button
              v-else
              type="primary"
              @click="finishPractice"
            >
              完成练习
            </a-button>
          </a-space>
        </div>
      </div>

      <!-- 完成页面 -->
      <div v-else-if="finished" class="complete-card">
        <a-result
          title="练习完成"
          :sub-title="`${sourceName || '随堂测验'}，共 ${questions.length} 题`"
        >
          <template #icon>
            <CheckCircleFilled style="font-size: 64px; color: #52c41a" />
          </template>
          <template #extra>
            <a-row :gutter="24" justify="center" style="margin-bottom: 24px">
              <a-col>
                <a-statistic title="总题数" :value="questions.length" />
              </a-col>
              <a-col>
                <a-statistic title="正确" :value="correctCount" :value-style="{ color: '#52c41a' }" />
              </a-col>
              <a-col>
                <a-statistic title="错误" :value="questions.length - correctCount" :value-style="{ color: '#ff4d4f' }" />
              </a-col>
              <a-col>
                <a-statistic title="正确率" :value="accuracy" suffix="%" />
              </a-col>
            </a-row>
            <a-space>
              <a-button @click="restartPractice">重新练习</a-button>
              <a-button type="primary" @click="handleBack">返回</a-button>
            </a-space>
          </template>
        </a-result>
      </div>
    </div>

    <!-- 答题卡侧边栏 -->
    <div class="answer-sidebar">
      <div class="sidebar-title">答题卡</div>
      <div class="sidebar-stats">
        <span>已答 {{ answeredCount }} / {{ questions.length }}</span>
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
          <span class="legend-dot legend-current" /> 当前
        </div>
        <div class="legend-item">
          <span class="legend-dot legend-correct" /> 正确
        </div>
        <div class="legend-item">
          <span class="legend-dot legend-wrong" /> 错误
        </div>
        <div class="legend-item">
          <span class="legend-dot legend-unanswered" /> 未答
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import { LeftOutlined, RightOutlined, CheckOutlined, CheckCircleFilled } from '@ant-design/icons-vue'

const props = defineProps({
  questions: { type: Array, default: () => [] },
  practiceMode: { type: Boolean, default: true },
  showExplanation: { type: Boolean, default: true },
  timeLimit: { type: Number, default: 0 },
  sourceName: { type: String, default: '' },
})

const emit = defineEmits(['finish', 'close'])

// 状态
const currentIndex = ref(0)
const answers = ref({})
const shownQuestions = ref({})
const finished = ref(false)
const multiTempAnswers = ref({})
const timer = ref(null)
const remainingTime = ref(0)

// 计算属性
const currentQuestion = computed(() => props.questions[currentIndex.value] || null)

const progressPercent = computed(() => {
  if (props.questions.length === 0) return 0
  if (finished.value) return 100
  return Math.round(((currentIndex.value + 1) / props.questions.length) * 100)
})

const answeredCount = computed(() => {
  return Object.keys(answers.value).filter(
    (key) => answers.value[key] !== undefined && answers.value[key] !== ''
  ).length
})

const correctCount = computed(() => {
  let count = 0
  for (const question of props.questions) {
    if (isAnswerCorrect(question, answers.value[question.id])) {
      count += 1
    }
  }
  return count
})

const accuracy = computed(() => {
  if (props.questions.length === 0) return 0
  return Math.round((correctCount.value / props.questions.length) * 100)
})

const isCurrentCorrect = computed(() => {
  if (!currentQuestion.value) return false
  return isAnswerCorrect(currentQuestion.value, answers.value[currentQuestion.value.id])
})

const hasMultiSelected = computed(() => {
  if (!currentQuestion.value) return false
  const selected = multiTempAnswers.value[currentQuestion.value.id] || []
  return selected.length > 0
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
    return options.map((option) => ({
      key: String(option?.key ?? ''),
      value: String(option?.text ?? option?.value ?? ''),
    })).filter((option) => option.key && option.value)
  }
  if (typeof options === 'object') {
    return Object.entries(options).map(([key, value]) => ({ key, value: String(value) }))
  }
  return []
})

// 方法
function getTypeLabel(type) {
  const labels = { single: '单选题', multi: '多选题', judge: '判断题', gap: '填空题' }
  return labels[type] || '未知'
}

function getTypeColor(type) {
  const colors = { single: 'blue', multi: 'purple', judge: 'orange', gap: 'cyan' }
  return colors[type] || 'default'
}

function isAnswerCorrect(question, answer) {
  if (!question || !answer) return false
  const correct = question.answer
  if (Array.isArray(correct)) {
    if (Array.isArray(answer)) {
      return correct.length === answer.length && correct.every((a) => answer.includes(a))
    }
    return correct.includes(answer)
  }
  if (Array.isArray(answer)) {
    return answer.length === 1 && answer[0] === correct
  }
  return String(answer) === String(correct)
}

function isMultiSelected(key) {
  const selected = multiTempAnswers.value[currentQuestion.value.id] || []
  return selected.includes(key)
}

function selectOption(key) {
  if (!currentQuestion.value) return
  if (shownQuestions.value[currentQuestion.value.id]) return

  answers.value[currentQuestion.value.id] = key

  if (props.practiceMode) {
    shownQuestions.value[currentQuestion.value.id] = true
  }
}

function toggleMultiOption(key) {
  if (!currentQuestion.value) return
  if (shownQuestions.value[currentQuestion.value.id]) return

  const selected = multiTempAnswers.value[currentQuestion.value.id] || []
  const index = selected.indexOf(key)
  if (index > -1) {
    selected.splice(index, 1)
  } else {
    selected.push(key)
  }
  multiTempAnswers.value[currentQuestion.value.id] = selected
}

function confirmAnswer() {
  if (!currentQuestion.value) return
  const selected = multiTempAnswers.value[currentQuestion.value.id] || []
  if (selected.length === 0) {
    message.warning('请至少选择一个选项')
    return
  }
  answers.value[currentQuestion.value.id] = selected
  shownQuestions.value[currentQuestion.value.id] = true
}

function prevQuestion() {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

function nextQuestion() {
  if (currentIndex.value < props.questions.length - 1) {
    currentIndex.value++
  }
}

function goToQuestion(index) {
  currentIndex.value = index
}

function getGridItemClass(question, index) {
  const isAnswered = answers.value[question.id] !== undefined && answers.value[question.id] !== ''
  const isCorrect = isAnswerCorrect(question, answers.value[question.id])
  const isCurrent = index === currentIndex.value

  return {
    'grid-current': isCurrent,
    'grid-correct': isAnswered && isCorrect,
    'grid-wrong': isAnswered && !isCorrect,
    'grid-unanswered': !isAnswered,
  }
}

function finishPractice() {
  finished.value = true
  if (timer.value) {
    clearInterval(timer.value)
  }
  emit('finish', {
    totalCount: props.questions.length,
    correctCount: correctCount.value,
    wrongCount: props.questions.length - correctCount.value,
    correctRate: accuracy.value + '%',
  })
}

function restartPractice() {
  currentIndex.value = 0
  answers.value = {}
  shownQuestions.value = {}
  multiTempAnswers.value = {}
  finished.value = false
  if (props.timeLimit) {
    remainingTime.value = props.timeLimit
    startTimer()
  }
}

function startTimer() {
  if (!props.timeLimit) return
  remainingTime.value = props.timeLimit
  timer.value = setInterval(() => {
    remainingTime.value--
    if (remainingTime.value <= 0) {
      message.warning('时间到，自动提交')
      finishPractice()
    }
  }, 60000)
}

function handleBack() {
  emit('close')
}

onMounted(() => {
  if (props.timeLimit) {
    startTimer()
  }
})

onUnmounted(() => {
  if (timer.value) {
    clearInterval(timer.value)
  }
})
</script>

<style scoped>
.practice-do-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
}

.practice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-center {
  font-size: 16px;
  font-weight: 500;
}

.practice-content {
  flex: 1;
}

.question-card {
  background: #fff;
}

.question-header {
  margin-bottom: 12px;
}

.question-id {
  color: #999;
  font-size: 12px;
}

.question-content {
  font-size: 16px;
  line-height: 1.8;
  margin-bottom: 20px;
  color: #333;
}

.question-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.option-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.option-item:hover {
  border-color: #1890ff;
  background: #f0f7ff;
}

.option-item.selected {
  border-color: #1890ff;
  background: #e6f7ff;
}

.option-item.correct {
  border-color: #52c41a;
  background: #f6ffed;
}

.option-item.incorrect {
  border-color: #ff4d4f;
  background: #fff2f0;
}

.option-checkbox,
.option-radio {
  width: 20px;
  height: 20px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  margin-right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.option-radio {
  border-radius: 50%;
}

.option-item.selected .option-checkbox,
.option-item.selected .option-radio {
  border-color: #1890ff;
  background: #1890ff;
  color: #fff;
}

.option-item.correct .option-checkbox,
.option-item.correct .option-radio {
  border-color: #52c41a;
  background: #52c41a;
  color: #fff;
}

.option-item.incorrect .option-checkbox,
.option-item.incorrect .option-radio {
  border-color: #ff4d4f;
  background: #ff4d4f;
  color: #fff;
}

.option-key {
  font-weight: 600;
  margin-right: 8px;
  min-width: 20px;
}

.option-text {
  flex: 1;
}

.explanation-section {
  margin-bottom: 16px;
}

.question-footer {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.complete-card {
  padding: 40px 20px;
  text-align: center;
}

/* 答题卡 */
.answer-sidebar {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 200px;
  background: #fff;
  border-left: 1px solid #f0f0f0;
  padding: 16px;
  overflow-y: auto;
}

.sidebar-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #333;
}

.sidebar-stats {
  font-size: 12px;
  color: #666;
  margin-bottom: 12px;
}

.sidebar-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}

.grid-item {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  border: 1px solid #d9d9d9;
  background: #fff;
}

.grid-current {
  border-color: #1890ff;
  background: #e6f7ff;
  font-weight: 600;
}

.grid-correct {
  border-color: #52c41a;
  background: #f6ffed;
  color: #52c41a;
}

.grid-wrong {
  border-color: #ff4d4f;
  background: #fff2f0;
  color: #ff4d4f;
}

.grid-unanswered {
  background: #fafafa;
}

.sidebar-legend {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 11px;
  color: #666;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-current {
  border: 1px solid #1890ff;
  background: #e6f7ff;
}

.legend-correct {
  border: 1px solid #52c41a;
  background: #f6ffed;
}

.legend-wrong {
  border: 1px solid #ff4d4f;
  background: #fff2f0;
}

.legend-unanswered {
  border: 1px solid #d9d9d9;
  background: #fafafa;
}
</style>
