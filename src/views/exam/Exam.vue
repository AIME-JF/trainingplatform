<template>
  <div class="exam-page">
    <!-- 加载中 -->
    <div v-if="loading" style="text-align: center; padding: 100px;">
      <a-spin size="large" tip="正在加载试卷..." />
    </div>

    <div v-else>
      <!-- 考试头部 -->
      <div class="exam-header">
        <div class="exam-info">
          <h3>{{ exam.title }}</h3>
          <div class="exam-meta">
            <a-tag color="blue">{{ exam.questionCount || 0 }}题</a-tag>
            <a-tag color="orange">满分 {{ exam.totalScore || 0 }} 分</a-tag>
            <a-tag color="green">及格 {{ exam.passingScore || 60 }} 分</a-tag>
          </div>
        </div>
        <div class="exam-timer" :class="{ urgent: remainingTime < 300 }">
          <ClockCircleOutlined />
          <span class="time-text">{{ formatTime(remainingTime) }}</span>
        </div>
      </div>

      <a-row :gutter="20">
        <!-- 左：题目区 -->
        <a-col :span="17">
          <a-card :bordered="false" class="question-card">
            <div class="q-progress-bar">
              <span class="q-progress-text">第 {{ currentIdx+1 }} / {{ questions.length }} 题</span>
              <a-progress :percent="questions.length ? Math.round((answeredCount/questions.length)*100) : 0" size="small" style="flex:1;margin:0 16px" />
              <span class="answered-count">已答 {{ answeredCount }} 题</span>
            </div>

          <div class="question-display" v-if="currentQ">
            <div class="q-type-badge">
              <a-tag :color="typeColors[currentQ.type]">{{ typeLabels[currentQ.type] }}</a-tag>
              <span class="q-score">{{ currentQ.score || 2 }}分</span>
            </div>
            <div class="q-stem">{{ currentIdx+1 }}. {{ currentQ.content || currentQ.stem }}</div>

            <!-- 单选题 -->
            <a-radio-group
              v-if="currentQ.type === 'single'"
              v-model:value="answers[currentIdx]"
              class="options-group"
            >
              <a-radio
                v-for="(opt, i) in currentQ.options"
                :key="i"
                :value="opt.key"
                class="option-item"
              >
                <span class="opt-key">{{ opt.key }}</span>
                {{ opt.text }}
              </a-radio>
            </a-radio-group>

            <!-- 多选题 -->
            <a-checkbox-group
              v-if="currentQ.type === 'multi'"
              v-model:value="answers[currentIdx]"
              class="options-group"
            >
              <a-checkbox
                v-for="(opt, i) in currentQ.options"
                :key="i"
                :value="opt.key"
                class="option-item"
              >
                <span class="opt-key">{{ opt.key }}</span>
                {{ opt.text }}
              </a-checkbox>
            </a-checkbox-group>

            <!-- 判断题 -->
            <a-radio-group
              v-if="currentQ.type === 'judge'"
              v-model:value="answers[currentIdx]"
              class="options-group"
            >
              <a-radio value="T" class="option-item"><span class="opt-key">✓</span> 正确</a-radio>
              <a-radio value="F" class="option-item"><span class="opt-key">✗</span> 错误</a-radio>
            </a-radio-group>
          </div>

          <!-- 导航按钮 -->
          <div class="nav-buttons">
            <a-button :disabled="currentIdx === 0" @click="currentIdx--">上一题</a-button>
            <div class="nav-mid">
              <a-button @click="markQuestion(currentIdx)">
                <template #icon><StarOutlined /></template>
                {{ markedQuestions.includes(currentIdx) ? '取消标记' : '标记此题' }}
              </a-button>
            </div>
            <a-button v-if="currentIdx < questions.length-1" type="primary" @click="currentIdx++">下一题</a-button>
            <a-button v-else type="primary" danger @click="confirmSubmit">提交试卷</a-button>
          </div>
        </a-card>
      </a-col>

      <!-- 右：答题卡 -->
      <a-col :span="7">
        <a-card title="答题卡" :bordered="false" class="answer-card">
          <div class="answer-grid">
            <div
              v-for="(q, idx) in questions"
              :key="idx"
              class="answer-cell"
              :class="{
                answered: hasAnswer(idx),
                current: currentIdx === idx,
                marked: markedQuestions.includes(idx)
              }"
              @click="currentIdx = idx"
            >{{ idx+1 }}</div>
          </div>
          <div class="card-legend">
            <div class="legend-item"><span class="legend-dot answered"></span>已答</div>
            <div class="legend-item"><span class="legend-dot"></span>未答</div>
            <div class="legend-item"><span class="legend-dot marked"></span>已标记</div>
          </div>
          <a-button type="primary" danger block @click="confirmSubmit" style="margin-top:16px">
            提交试卷 ({{ answeredCount }}/{{ questions.length }})
          </a-button>
        </a-card>
      </a-col>
    </a-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Modal, message } from 'ant-design-vue'
import { ClockCircleOutlined, StarOutlined } from '@ant-design/icons-vue'
import { getExamDetail, submitExam } from '@/api/exam'

const router = useRouter()
const route = useRoute()
const examId = route.params.id

const loading = ref(true)
const submitting = ref(false)
const exam = ref({})
const questions = ref([])

const currentIdx = ref(0)
const answers = ref([])
const markedQuestions = ref([])
const remainingTime = ref(0)
const startTime = ref(null)

const currentQ = computed(() => questions[currentIdx.value])
const answeredCount = computed(() => answers.value.filter(a => a !== null && (!Array.isArray(a) || a.length > 0)).length)
const hasAnswer = (idx) => answers.value[idx] !== null && (!Array.isArray(answers.value[idx]) || answers.value[idx].length > 0)

const typeColors = { single: 'blue', multi: 'purple', judge: 'orange' }
const typeLabels = { single: '单选题', multi: '多选题', judge: '判断题' }

const formatTime = (secs) => {
  const m = Math.floor(secs / 60).toString().padStart(2, '0')
  const s = (secs % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

const markQuestion = (idx) => {
  const i = markedQuestions.value.indexOf(idx)
  if (i >= 0) markedQuestions.value.splice(i, 1)
  else markedQuestions.value.push(idx)
}

const startTimer = () => {
  timer = setInterval(() => { 
    if (remainingTime.value > 0) remainingTime.value--; 
    else {
      clearInterval(timer)
      message.warning('考试时间到，正在自动交卷...')
      submit()
    }
  }, 1000)
}

const loadExam = async () => {
  try {
    const res = await getExamDetail(examId)
    const data = res.data || res
    exam.value = {
      title: data.title,
      questionCount: data.question_count,
      totalScore: data.total_score,
      passingScore: data.passing_score,
      duration: data.duration
    }
    questions.value = data.questions || []
    answers.value = Array(questions.value.length).fill(null)
    
    // 初始化多选题答案为数组
    questions.value.forEach((q, idx) => {
      if (q.type === 'multi') {
        answers.value[idx] = []
      }
    })

    remainingTime.value = (data.duration || 60) * 60
    startTime.value = new Date().toISOString()
    startTimer()
    loading.value = false
  } catch (e) {
    message.error('加载试卷失败')
    router.replace('/exam/list')
  }
}

const submit = async () => {
  submitting.value = true
  try {
    const submitAnswers = {}
    questions.value.forEach((q, idx) => {
      submitAnswers[q.id] = answers.value[idx]
    })
    
    await submitExam(examId, {
      start_time: startTime.value,
      answers: submitAnswers
    })
    
    message.success('交卷成功！')
    router.replace(`/exam/result/${examId}`)
  } catch (e) {
    message.error('交卷失败，请重试')
    submitting.value = false
  }
}

const confirmSubmit = () => {
  Modal.confirm({
    title: '确认提交试卷？',
    content: `已答 ${answeredCount.value} 题，共 ${questions.value.length} 题。提交后不可修改。`,
    okText: '确认提交',
    cancelText: '继续作答',
    okType: 'danger',
    onOk: () => {
      clearInterval(timer)
      submit()
    }
  })
}

onMounted(() => {
  loadExam()
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.exam-page { padding: 0; }
.exam-header { display: flex; justify-content: space-between; align-items: center; background: #fff; padding: 16px 20px; border-radius: 8px; margin-bottom: 16px; border-left: 4px solid var(--police-primary); }
.exam-info h3 { margin: 0 0 8px; font-size: 18px; color: #1a1a1a; }
.exam-meta { display: flex; gap: 8px; }
.exam-timer { display: flex; align-items: center; gap: 8px; font-size: 28px; font-weight: 700; color: var(--police-primary); font-variant-numeric: tabular-nums; }
.exam-timer.urgent { color: #ff4d4f; animation: blink 1s step-end infinite; }
@keyframes blink { 50% { opacity: 0.5; } }
.time-text { font-size: 32px; }
.question-card { }
.q-progress-bar { display: flex; align-items: center; margin-bottom: 20px; }
.q-progress-text, .answered-count { white-space: nowrap; font-size: 13px; color: #888; }
.question-display { padding: 16px 0; }
.q-type-badge { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.q-score { font-size: 12px; color: #888; }
.q-stem { font-size: 16px; color: #1a1a1a; line-height: 1.7; margin-bottom: 20px; font-weight: 500; }
.options-group { display: flex; flex-direction: column; gap: 12px; width: 100%; }
.option-item { padding: 12px 16px; border: 1px solid #e8e8e8; border-radius: 6px; transition: all 0.2s; cursor: pointer; display: flex; align-items: flex-start; font-size: 14px; line-height: 1.6; }
.option-item:hover { border-color: var(--police-primary); background: #f0f5ff; }
.opt-key { font-weight: 700; color: var(--police-primary); margin-right: 8px; min-width: 20px; }
.nav-buttons { display: flex; justify-content: space-between; align-items: center; margin-top: 24px; padding-top: 16px; border-top: 1px solid #f0f0f0; }
.nav-mid { display: flex; gap: 8px; }
.answer-card { }
.answer-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 16px; }
.answer-cell { width: 100%; aspect-ratio: 1; border-radius: 4px; background: #f5f5f5; border: 2px solid #e0e0e0; display: flex; align-items: center; justify-content: center; font-size: 12px; cursor: pointer; transition: all 0.2s; font-weight: 500; }
.answer-cell:hover { border-color: var(--police-primary); }
.answer-cell.answered { background: var(--police-primary); border-color: var(--police-primary); color: #fff; }
.answer-cell.current { border-color: var(--police-gold); box-shadow: 0 0 0 2px rgba(200,168,75,0.3); }
.answer-cell.marked { background: #fff7e6; border-color: #fa8c16; color: #fa8c16; }
.card-legend { display: flex; gap: 12px; }
.legend-item { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #888; }
.legend-dot { width: 12px; height: 12px; border-radius: 2px; background: #f5f5f5; border: 1px solid #e0e0e0; }
.legend-dot.answered { background: var(--police-primary); border-color: var(--police-primary); }
.legend-dot.marked { background: #fff7e6; border-color: #fa8c16; }
</style>
