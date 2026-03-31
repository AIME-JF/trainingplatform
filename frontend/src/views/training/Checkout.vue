<template>
  <div class="checkout-page">
    <div class="header-card">
      <h2>{{ training.name }}</h2>
      <p>{{ currentSessionLabel }}</p>
    </div>

    <a-card :bordered="false">
      <a-form layout="vertical">
        <a-form-item label="签到场次">
          <a-select v-model:value="currentSessionKey">
            <a-select-option v-for="session in sessionOptions" :key="session.value" :value="session.value">
              {{ session.label }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="课程满意度">
          <a-rate v-model:value="evaluationScore" />
        </a-form-item>
        <a-form-item label="评课意见">
          <a-textarea v-model:value="evaluationComment" :rows="4" />
        </a-form-item>
        <div class="actions">
          <a-button @click="$router.back()">返回</a-button>
          <a-button type="primary" :loading="submitting" @click="submitAll">提交签退与评课</a-button>
        </div>
      </a-form>
    </a-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { checkout, getTraining, submitTrainingEvaluation } from '@/api/training'

const route = useRoute()
const trainingId = route.params.id
const currentSessionKey = ref(route.params.sessionKey || '')
const training = ref({ name: '', courses: [], currentSession: null })
const evaluationScore = ref(5)
const evaluationComment = ref('')
const submitting = ref(false)

const sessionOptions = computed(() => {
  const options = []
  ;(training.value.courses || []).forEach((course) => {
    ;(course.schedules || []).forEach((schedule) => {
      options.push({
        value: schedule.sessionId,
        label: `${course.name} (${schedule.date} ${schedule.timeRange})`,
      })
    })
  })
  return options
})

const currentSessionLabel = computed(() => {
  return sessionOptions.value.find(item => item.value === currentSessionKey.value)?.label || '未选择课次'
})

async function loadTraining() {
  try {
    training.value = await getTraining(trainingId)
    const optionKeys = sessionOptions.value.map((item) => item.value)
    if (!currentSessionKey.value || !optionKeys.includes(currentSessionKey.value)) {
      currentSessionKey.value = training.value.currentSession?.sessionId || sessionOptions.value[0]?.value || ''
    }
  } catch (error) {
    message.error(error.message || '加载培训班失败')
  }
}

async function submitAll() {
  if (!currentSessionKey.value) {
    message.warning('当前没有可签退课次')
    return
  }
  submitting.value = true
  try {
    await checkout(trainingId, { sessionKey: currentSessionKey.value })
    await submitTrainingEvaluation(trainingId, {
      sessionKey: currentSessionKey.value,
      score: evaluationScore.value,
      comment: evaluationComment.value || undefined,
    })
    message.success('签退与评课已提交')
  } catch (error) {
    message.error(error.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadTraining)
</script>

<style scoped>
.checkout-page { max-width: 720px; margin: 0 auto; }
.header-card { background: #fff; border-radius: 10px; padding: 24px; margin-bottom: 16px; box-shadow: 0 4px 18px rgba(0, 32, 96, 0.06); }
.header-card h2 { margin: 0 0 8px; color: #001234; }
.header-card p { margin: 0; color: #8c8c8c; }
.actions { display: flex; justify-content: flex-end; gap: 12px; }
</style>
