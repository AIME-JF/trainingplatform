<template>
  <div class="page-content result-page">
    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" />
    </div>

    <template v-else-if="result">
      <div class="result-card" :class="{ passed: isPassed, failed: !isPassed }">
        <div class="result-icon">
          <CheckCircleOutlined v-if="isPassed" />
          <CloseCircleOutlined v-else />
        </div>
        <div class="result-status">
          {{ isPassed ? '考试通过' : '未通过' }}
        </div>
        <div class="result-score">
          <span class="score-value">{{ result.score || 0 }}</span>
          <span class="score-total">满分 {{ passingScore }}</span>
        </div>
      </div>

      <div class="stats-card">
        <div class="stat-item">
          <div class="stat-value correct">{{ result.correct_count || 0 }}</div>
          <div class="stat-label">答对</div>
        </div>
        <div class="stat-item">
          <div class="stat-value wrong">{{ result.wrong_count || 0 }}</div>
          <div class="stat-label">答错</div>
        </div>
        <div class="stat-item">
          <div class="stat-value duration">{{ formatDuration(result.duration) }}</div>
          <div class="stat-label">用时</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ result.attempt_no || 1 }}</div>
          <div class="stat-label">第几次</div>
        </div>
      </div>

      <a-collapse v-if="wrongQuestionDetails.length > 0" class="wrong-questions" ghost>
        <a-collapse-panel key="wrong" header="错题回顾">
          <div class="wrong-list">
            <div v-for="(q, index) in wrongQuestionDetails" :key="q.question_id" class="wrong-item">
              <div class="wrong-header">
                <span class="wrong-index">{{ index + 1 }}</span>
                <a-tag class="type-tag">{{ getQuestionTypeText(q.type) }}</a-tag>
                <span class="wrong-score">{{ q.score || 0 }} 分</span>
              </div>
              <div class="wrong-content">
                {{ q.content }}
              </div>
              <div class="wrong-answers">
                <div class="wrong-answer">
                  <span class="answer-label">你的答案：</span>
                  <span class="answer-value wrong-value">{{ formatAnswer(q.my_answer) }}</span>
                </div>
                <div class="wrong-answer">
                  <span class="answer-label">正确答案：</span>
                  <span class="answer-value correct-value">{{ formatAnswer(q.answer) }}</span>
                </div>
              </div>
              <div v-if="q.explanation" class="wrong-explanation">
                <InfoCircleOutlined /> {{ q.explanation }}
              </div>
            </div>
          </div>
        </a-collapse-panel>
      </a-collapse>

      <div class="action-bar">
        <a-button type="primary" long @click="router.push('/exam/list')">返回考试列表</a-button>
      </div>
    </template>

    <a-empty v-else description="暂无考试结果" />
  </div>
</template>

<script setup lang="ts">
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { ExamRecordResponse, ExamWrongQuestionResponse } from '@/api/generated/model'
import {
  getAdmissionExamResultApiV1ExamsAdmissionExamIdResultGet,
  getExamResultApiV1ExamsExamIdResultGet,
} from '@/api/generated/exam-management/exam-management'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const result = ref<ExamRecordResponse | null>(null)
const examKind = ref<'admission' | 'training'>('training')

const examId = computed(() => Number(route.params.id))

const isPassed = computed(() => {
  if (!result.value) return false
  return result.value.result === 'pass' || result.value.score! >= (result.value.passing_score || 0)
})

const passingScore = computed(() => {
  return result.value?.passing_score || 60
})

const wrongQuestionDetails = computed(() => {
  return result.value?.wrong_question_details || []
})

onMounted(async () => {
  await fetchResult()
})

async function fetchResult() {
  loading.value = true
  try {
    // 判断是准入考试还是培训班考试，尝试获取结果
    try {
      result.value = await getExamResultApiV1ExamsExamIdResultGet(examId.value)
      examKind.value = 'training'
    } catch {
      result.value = await getAdmissionExamResultApiV1ExamsAdmissionExamIdResultGet(examId.value)
      examKind.value = 'admission'
    }
  } catch (error) {
    message.error('加载考试结果失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

function formatDuration(seconds?: number) {
  if (!seconds) return '-'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}分${s}秒`
}

function formatAnswer(answer?: unknown) {
  if (answer === undefined || answer === null) return '未作答'
  if (Array.isArray(answer)) return answer.join('、')
  return String(answer)
}

function getQuestionTypeText(type?: string) {
  switch (type) {
    case 'single_choice':
      return '单选题'
    case 'multiple_choice':
      return '多选题'
    case 'true_false':
      return '判断题'
    default:
      return type || '未知'
  }
}
</script>

<style scoped>
.result-page {
  padding: 20px;
}

.loading-wrapper {
  padding: 80px 0;
  text-align: center;
}

.result-card {
  background: linear-gradient(135deg, var(--v2-danger) 0%, #d42a1f 100%);
  border-radius: 24px;
  padding: 32px;
  text-align: center;
  color: #fff;
  margin-bottom: 20px;
}

.result-card.passed {
  background: linear-gradient(135deg, var(--v2-success) 0%, #248a3d 100%);
}

.result-icon {
  font-size: 56px;
  margin-bottom: 12px;
}

.result-status {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 16px;
}

.result-score {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.score-value {
  font-size: 64px;
  font-weight: 700;
  line-height: 1;
}

.score-total {
  font-size: 16px;
  opacity: 0.85;
}

.stats-card {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  background: var(--v2-bg-card);
  border-radius: 20px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 8px 24px rgba(24, 39, 75, 0.06);
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--v2-text-primary);
  margin-bottom: 4px;
}

.stat-value.correct {
  color: var(--v2-success);
}

.stat-value.wrong {
  color: var(--v2-danger);
}

.stat-value.duration {
  font-size: 22px;
}

.stat-label {
  font-size: 13px;
  color: var(--v2-text-secondary);
}

.wrong-questions {
  margin-bottom: 20px;
}

.wrong-questions :deep(.ant-collapse-header) {
  font-weight: 600;
  font-size: 16px;
}

.wrong-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.wrong-item {
  background: rgba(255, 59, 48, 0.06);
  border-radius: 16px;
  padding: 16px;
}

.wrong-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.wrong-index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--v2-danger);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
}

.type-tag {
  border-radius: 999px;
}

.wrong-score {
  margin-left: auto;
  color: var(--v2-danger);
  font-weight: 600;
}

.wrong-content {
  color: var(--v2-text-primary);
  line-height: 1.7;
  margin-bottom: 12px;
}

.wrong-answers {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.wrong-answer {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.answer-label {
  color: var(--v2-text-secondary);
  font-size: 14px;
  flex-shrink: 0;
}

.answer-value {
  font-weight: 600;
}

.wrong-value {
  color: var(--v2-danger);
}

.correct-value {
  color: var(--v2-success);
}

.wrong-explanation {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 12px;
  background: rgba(75, 110, 245, 0.06);
  border-radius: 10px;
  color: var(--v2-primary);
  font-size: 14px;
  line-height: 1.6;
}

.action-bar {
  margin-top: 20px;
}

.action-bar :deep(.ant-btn) {
  border-radius: 12px;
  height: 48px;
  font-size: 16px;
}

@media (max-width: 768px) {
  .stats-card {
    grid-template-columns: repeat(2, 1fr);
  }

  .result-card {
    padding: 24px;
  }

  .score-value {
    font-size: 48px;
  }
}
</style>
