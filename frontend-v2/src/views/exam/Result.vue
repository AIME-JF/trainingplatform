<template>
  <div class="page-content result-page">
    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" />
    </div>

    <template v-else-if="result">
      <!-- 结果头部 -->
      <div class="section-block result-hero" :class="{ passed: isPassed, failed: !isPassed }">
        <div class="hero-left">
          <div class="hero-icon">
            <CheckCircleOutlined v-if="isPassed" />
            <CloseCircleOutlined v-else />
          </div>
          <div class="hero-text">
            <div class="hero-title">{{ isPassed ? '考试通过' : '未通过' }}</div>
            <div class="hero-exam">{{ result.exam_title || '考试成绩' }}</div>
          </div>
        </div>
        <div class="hero-right">
          <div class="score-big">{{ result.score || 0 }}</div>
          <div class="score-label">及格线 {{ result.passing_score || passingScore }} 分</div>
        </div>
      </div>

      <div class="divider" />

      <!-- 基本信息 -->
      <div class="section-block info-grid">
        <div class="info-item">
          <span class="info-label">提交时间</span>
          <span class="info-value">{{ formatDateTime(result.end_time) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">用时</span>
          <span class="info-value">{{ formatDuration(result.duration) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">答题情况</span>
          <span class="info-value">{{ result.correct_count || 0 }} 答对 / {{ result.wrong_count || 0 }} 答错</span>
        </div>
        <div class="info-item">
          <span class="info-label">正确率</span>
          <span class="info-value">{{ accuracyPercent }}%</span>
        </div>
        <div class="info-item">
          <span class="info-label">考试次数</span>
          <span class="info-value">第 {{ result.attempt_no || 1 }} 次</span>
        </div>
      </div>

      <div class="divider" />

      <!-- 错题回顾 -->
      <div v-if="wrongQuestionDetails.length > 0" class="section-block wrong-section">
        <div class="section-header">
          <WarningOutlined /> 错题回顾 · {{ wrongQuestionDetails.length }} 题
        </div>

        <div
          v-for="(q, index) in wrongQuestionDetails"
          :key="q.question_id"
          class="wrong-block"
        >
          <div class="wrong-top">
            <span class="wrong-num">{{ index + 1 }}</span>
            <a-tag class="type-tag">{{ getQuestionTypeText(q.type) }}</a-tag>
            <span class="wrong-score">-{{ q.score || 0 }} 分</span>
          </div>

          <div class="wrong-body">
            <div class="wrong-question">{{ q.content }}</div>

            <div class="answer-rows">
              <div class="answer-row">
                <span class="answer-key">你的答案</span>
                <span class="answer-val wrong-val">{{ formatAnswer(q.my_answer) }}</span>
              </div>
              <div class="answer-row">
                <span class="answer-key">正确答案</span>
                <span class="answer-val correct-val">{{ formatAnswer(q.answer) }}</span>
              </div>
            </div>

            <div v-if="q.explanation" class="explanation-row">
              <BulbOutlined /> {{ q.explanation }}
            </div>
          </div>
        </div>
      </div>

      <a-empty v-else-if="isPassed" class="all-correct">
        <template #description><span>恭喜您全部答对，继续保持！</span></template>
      </a-empty>

      <div class="divider" />

      <!-- 操作 -->
      <div class="section-block action-row">
        <a-button size="large" @click="router.push('/exam/list')">
          <RollbackOutlined /> 返回考试列表
        </a-button>
        <a-button v-if="!isPassed" type="primary" size="large" @click="router.push({ path: `/exam/do/${examId}`, query: { kind: examKind } })">
          <RedoOutlined /> 重新考试
        </a-button>
      </div>
    </template>

    <a-empty v-else description="暂无考试结果" />
  </div>
</template>

<script setup lang="ts">
import {
  BulbOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  RedoOutlined,
  RollbackOutlined,
  WarningOutlined,
} from '@ant-design/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { AdmissionExamRecordResponse, ExamRecordResponse } from '@/api/generated/model'
import {
  getAdmissionExamResultApiV1ExamsAdmissionExamIdResultGet,
  getExamResultApiV1ExamsExamIdResultGet,
} from '@/api/generated/exam-management/exam-management'
import { resolveExamKind, type ExamKind } from './examDisplay'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const result = ref<ExamRecordResponse | AdmissionExamRecordResponse | null>(null)
const examKind = ref<ExamKind>(resolveExamKind(route.query.kind, 'training'))

const examId = computed(() => Number(route.params.id))

const isPassed = computed(() => {
  if (!result.value) return false
  return result.value.result === 'pass' || result.value.score! >= (result.value.passing_score || 0)
})

const passingScore = computed(() => result.value?.passing_score || 60)

const accuracyPercent = computed(() => {
  if (!result.value) return 0
  const correct = result.value.correct_count || 0
  const wrong = result.value.wrong_count || 0
  const total = correct + wrong
  if (total === 0) return 0
  return Math.round((correct / total) * 100)
})

const wrongQuestionDetails = computed(() => result.value?.wrong_question_details || [])

onMounted(async () => {
  await fetchResult()
})

async function fetchResult() {
  loading.value = true
  try {
    try {
      result.value = examKind.value === 'admission'
        ? await getAdmissionExamResultApiV1ExamsAdmissionExamIdResultGet(examId.value)
        : await getExamResultApiV1ExamsExamIdResultGet(examId.value)
    } catch (primaryError) {
      examKind.value = examKind.value === 'admission' ? 'training' : 'admission'
      result.value = examKind.value === 'admission'
        ? await getAdmissionExamResultApiV1ExamsAdmissionExamIdResultGet(examId.value)
        : await getExamResultApiV1ExamsExamIdResultGet(examId.value)
    }
  } catch {
    message.error('加载考试结果失败')
  } finally {
    loading.value = false
  }
}

function formatDuration(minutes?: number) {
  if (minutes === undefined || minutes === null) return '-'
  return `${minutes} 分钟`
}

function formatDateTime(time?: string | null) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}

function formatAnswer(answer?: unknown) {
  if (answer === undefined || answer === null) return '未作答'
  if (Array.isArray(answer)) return answer.join('、')
  return String(answer)
}

function getQuestionTypeText(type?: string) {
  switch (type) {
    case 'single': return '单选题'
    case 'multi': return '多选题'
    case 'judge': return '判断题'
    default: return type || '未知'
  }
}
</script>

<style scoped>
.result-page {
  padding: 20px;
  max-width: 100%;
}

.loading-wrapper {
  padding: 80px 0;
  text-align: center;
}

.divider {
  height: 1px;
  background: var(--v2-border);
  margin: 0;
}

.section-block {
  padding: 24px 28px;
  background: var(--v2-bg-card);
}

.section-block:first-child {
  border-radius: 20px 20px 0 0;
}

.section-block:last-child {
  border-radius: 0 0 20px 20px;
}

.info-grid {
  display: flex;
  gap: 0;
}

.info-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 0 16px;
  border-right: 1px solid var(--v2-border);
}

.info-item:first-child {
  padding-left: 0;
}

.info-item:last-child {
  border-right: none;
}

.info-label {
  font-size: 13px;
  color: var(--v2-text-secondary);
}

.info-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
}

/* 结果头部 */
.result-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
}

.result-hero.passed {
  background: linear-gradient(135deg, #2DA44E 0%, #1a7a37 100%);
}

.result-hero.failed {
  background: linear-gradient(135deg, #FF3B30 0%, #d42a1f 100%);
}

.hero-left {
  display: flex;
  align-items: center;
  gap: 18px;
}

.hero-icon {
  font-size: 52px;
}

.hero-title {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.hero-exam {
  font-size: 14px;
  opacity: 0.85;
  margin-top: 4px;
}

.hero-right {
  text-align: right;
}

.score-big {
  font-size: 64px;
  font-weight: 700;
  line-height: 1;
}

.score-label {
  font-size: 14px;
  opacity: 0.85;
  margin-top: 6px;
}

/* 错题回顾 */
.wrong-section {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 600;
  color: var(--v2-danger);
  margin-bottom: 18px;
}

.wrong-block {
  padding: 16px 0;
  border-top: 1px solid var(--v2-border);
}

.wrong-block:first-of-type {
  border-top: none;
  padding-top: 0;
}

.wrong-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.wrong-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--v2-danger);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.type-tag {
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.wrong-score {
  margin-left: auto;
  color: var(--v2-danger);
  font-weight: 700;
  font-size: 14px;
}

.wrong-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.wrong-question {
  font-size: 15px;
  line-height: 1.8;
  color: var(--v2-text-primary);
}

.answer-rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 10px;
  padding: 12px 16px;
}

.answer-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.answer-key {
  font-size: 13px;
  color: var(--v2-text-secondary);
  width: 68px;
  flex-shrink: 0;
}

.answer-val {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.6;
}

.wrong-val {
  color: var(--v2-danger);
}

.correct-val {
  color: var(--v2-success);
}

.explanation-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(75, 110, 245, 0.06);
  border-radius: 10px;
  font-size: 14px;
  color: var(--v2-primary);
  line-height: 1.8;
}

.all-correct {
  background: var(--v2-bg-card);
  border-radius: 20px;
  padding: 40px 0;
}

/* 操作 */
.action-row {
  display: flex;
  gap: 14px;
  justify-content: center;
}

.action-row :deep(.ant-btn) {
  border-radius: 12px;
  height: 44px;
  padding: 0 28px;
  font-size: 14px;
  font-weight: 600;
}

@media (max-width: 768px) {
  .result-hero {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }

  .hero-right {
    text-align: center;
  }

  .info-grid {
    flex-wrap: wrap;
    gap: 12px;
  }

  .info-item {
    flex: 0 0 calc(50% - 8px);
    border-right: none;
    padding: 0;
  }

  .action-row {
    flex-direction: column;
  }
}
</style>
