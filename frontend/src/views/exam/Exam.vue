<template>
  <div class="exam-page">
    <div v-if="loading" class="loading-box">
      <a-spin size="large" tip="正在加载试卷..." />
    </div>

    <template v-else>
      <div class="exam-header">
        <div>
          <h3>{{ exam.title }}</h3>
          <div class="exam-meta">
            <a-tag color="blue">{{ questions.length }}题</a-tag>
            <a-tag color="orange">满分 {{ exam.totalScore || 0 }} 分</a-tag>
            <a-tag color="green">及格 {{ exam.passingScore || 0 }} 分</a-tag>
          </div>
        </div>
        <div class="exam-timer" :class="{ urgent: remainingTime < 300 }">{{ formatTime(remainingTime) }}</div>
      </div>

      <a-row :gutter="20">
        <a-col :span="17">
          <a-card :bordered="false">
            <div class="progress-row">
              <span>第 {{ currentIdx + 1 }} / {{ questions.length }} 题</span>
              <a-progress :percent="questions.length ? Math.round((answeredCount / questions.length) * 100) : 0" size="small" style="flex:1;margin:0 16px" />
              <span>已答 {{ answeredCount }} 题</span>
            </div>

            <div v-if="currentQuestion" class="question-body">
              <div class="question-title">
                <a-tag>{{ typeLabels[currentQuestion.type] || currentQuestion.type }}</a-tag>
                <span>{{ currentIdx + 1 }}. {{ currentQuestion.content }}</span>
              </div>

              <a-radio-group
                v-if="currentQuestion.type === 'single' || currentQuestion.type === 'judge'"
                v-model:value="answers[currentIdx]"
                class="option-group"
              >
                <a-radio
                  v-for="option in normalizedOptions(currentQuestion)"
                  :key="option.key"
                  :value="option.key"
                  class="option-item"
                >
                  {{ option.key }}. {{ option.text }}
                </a-radio>
              </a-radio-group>

              <a-checkbox-group
                v-else
                v-model:value="answers[currentIdx]"
                class="option-group"
              >
                <a-checkbox
                  v-for="option in normalizedOptions(currentQuestion)"
                  :key="option.key"
                  :value="option.key"
                  class="option-item"
                >
                  {{ option.key }}. {{ option.text }}
                </a-checkbox>
              </a-checkbox-group>
            </div>

            <div class="nav-row">
              <a-button :disabled="currentIdx === 0" @click="currentIdx--">上一题</a-button>
              <a-button v-if="currentIdx < questions.length - 1" type="primary" @click="currentIdx++">下一题</a-button>
              <a-button v-else type="primary" danger :loading="submitting" @click="confirmSubmit">提交试卷</a-button>
            </div>
          </a-card>
        </a-col>

        <a-col :span="7">
          <a-card title="答题卡" :bordered="false">
            <div class="answer-grid">
              <div
                v-for="(question, index) in questions"
                :key="question.id"
                class="answer-cell"
                :class="{ answered: hasAnswer(index), current: currentIdx === index }"
                @click="currentIdx = index"
              >
                {{ index + 1 }}
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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

const loading = ref(true)
const submitting = ref(false)
const exam = ref({})
const questions = ref([])
const answers = ref([])
const currentIdx = ref(0)
const remainingTime = ref(0)
const startTime = ref(null)

const typeLabels = { single: '单选', multi: '多选', judge: '判断' }
const currentQuestion = computed(() => questions.value[currentIdx.value])
const answeredCount = computed(() => answers.value.filter(item => Array.isArray(item) ? item.length > 0 : item !== null && item !== undefined && item !== '').length)

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

function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, '0')
  const secs = String(seconds % 60).padStart(2, '0')
  return `${minutes}:${secs}`
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
    answers.value = questions.value.map(question => question.type === 'multi' ? [] : null)
    remainingTime.value = (detail.duration || 60) * 60
    startTime.value = new Date().toISOString()
    timer = setInterval(() => {
      if (remainingTime.value > 0) {
        remainingTime.value -= 1
        return
      }
      clearInterval(timer)
      handleSubmit()
    }, 1000)
  } catch (error) {
    message.error(error.message || '加载试卷失败')
    router.replace({ name: 'ExamList' })
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
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
    message.success('交卷成功')
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
    content: `已答 ${answeredCount.value} 题，共 ${questions.value.length} 题。`,
    onOk: () => {
      clearInterval(timer)
      return handleSubmit()
    },
  })
}

onMounted(loadExam)
onUnmounted(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.exam-page { padding: 0; }
.loading-box { padding: 120px 0; text-align: center; }
.exam-header { background: #fff; border-radius: 10px; padding: 18px 20px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.exam-header h3 { margin: 0 0 8px; color: #001234; }
.exam-meta { display: flex; gap: 8px; }
.exam-timer { font-size: 30px; font-weight: 700; color: #003087; }
.exam-timer.urgent { color: #ff4d4f; }
.progress-row { display: flex; align-items: center; margin-bottom: 20px; }
.question-body { min-height: 340px; }
.question-title { display: flex; gap: 10px; align-items: flex-start; margin-bottom: 20px; font-size: 16px; font-weight: 600; }
.option-group { display: flex; flex-direction: column; gap: 12px; width: 100%; }
.option-item { padding: 12px 14px; border: 1px solid #e8e8e8; border-radius: 8px; margin: 0; }
.nav-row { display: flex; justify-content: space-between; margin-top: 24px; }
.answer-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
.answer-cell { height: 40px; border-radius: 6px; background: #f5f5f5; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.answer-cell.answered { background: #003087; color: #fff; }
.answer-cell.current { border: 2px solid #c8a84b; }
</style>
