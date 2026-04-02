<template>
  <div class="page-content overview-page">
    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" />
    </div>

    <template v-else-if="exam">
      <!-- 顶部返回栏 -->
      <div class="top-bar">
        <button class="back-btn" @click="router.push('/exam/list')">
          <LeftOutlined /> 返回考试列表
        </button>
      </div>

      <!-- 左侧：考试信息 -->
      <div class="overview-layout">
        <div class="overview-main">
          <!-- 考试信息卡片 -->
          <div class="info-card">
            <div class="info-card-header">
              <div class="exam-badge" :class="getStatusClass(exam.status)">
                {{ getStatusText(exam.status, exam.can_join) }}
              </div>
              <h1 class="exam-title">{{ exam.title }}</h1>
              <p class="exam-desc">{{ exam.description || '暂无考试说明' }}</p>
            </div>

            <div class="info-grid">
              <div class="info-item">
                <div class="info-icon">
                  <ClockCircleOutlined />
                </div>
                <div class="info-text">
                  <span class="info-label">考试时长</span>
                  <span class="info-value">{{ exam.duration || 0 }} 分钟</span>
                </div>
              </div>
              <div class="info-item">
                <div class="info-icon">
                  <QuestionCircleOutlined />
                </div>
                <div class="info-text">
                  <span class="info-label">题目数量</span>
                  <span class="info-value">{{ exam.question_count || 0 }} 题</span>
                </div>
              </div>
              <div class="info-item">
                <div class="info-icon">
                  <SafetyCertificateOutlined />
                </div>
                <div class="info-text">
                  <span class="info-label">满分</span>
                  <span class="info-value">{{ exam.total_score || 0 }} 分</span>
                </div>
              </div>
              <div class="info-item">
                <div class="info-icon">
                  <SafetyOutlined />
                </div>
                <div class="info-text">
                  <span class="info-label">及格分数</span>
                  <span class="info-value">{{ exam.passing_score || 0 }} 分</span>
                </div>
              </div>
              <div class="info-item">
                <div class="info-icon">
                  <CalendarOutlined />
                </div>
                <div class="info-text">
                  <span class="info-label">考试时间</span>
                  <span class="info-value">
                    {{ exam.start_time ? formatTime(exam.start_time) : '不限时' }}
                    <template v-if="exam.start_time && exam.end_time"> - </template>
                    {{ exam.end_time ? formatTime(exam.end_time) : '' }}
                  </span>
                </div>
              </div>
              <div class="info-item">
                <div class="info-icon">
                  <FileTextOutlined />
                </div>
                <div class="info-text">
                  <span class="info-label">作答次数</span>
                  <span class="info-value">
                    <template v-if="exam.attempt_count && exam.attempt_count > 0">
                      已参加 {{ exam.attempt_count }} 次
                    </template>
                    <template v-else>首次参加</template>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 考试须知 -->
          <div class="rules-card">
            <div class="rules-title">
              <WarningOutlined /> 考试须知
            </div>
            <ul class="rules-list">
              <li>请认真阅读题目，确保理解后再作答</li>
              <li>考试时长 <strong>{{ exam.duration || 0 }} 分钟</strong>，超时将自动提交</li>
              <li>考试过程中请保持网络连接稳定</li>
              <li>提交后将无法修改答案，请仔细检查后再提交</li>
              <li>及格线为 <strong>{{ exam.passing_score || 0 }} 分</strong>，满分 {{ exam.total_score || 0 }} 分</li>
            </ul>
          </div>
        </div>

        <!-- 右侧：操作面板 -->
        <div class="overview-side">
          <div class="action-card">
            <div class="action-status">
              <div class="status-icon" :class="getStatusClass(exam.status)">
                <CheckCircleOutlined v-if="exam.status === 'ongoing'" />
                <ClockCircleOutlined v-else-if="exam.status === 'upcoming'" />
                <FileTextOutlined v-else />
              </div>
              <div class="status-label">{{ getStatusText(exam.status, exam.can_join) }}</div>
            </div>

            <div class="action-btn-wrap">
              <template v-if="exam.can_join">
                <a-button type="primary" size="large" block @click="handleStartExam">
                  <template #icon><RightOutlined /></template>
                  开始答题
                </a-button>
                <p class="action-hint">点击开始即表示您已阅读并同意考试须知</p>
              </template>
              <template v-else-if="exam.status === 'finished' || exam.latest_result === 'pass'">
                <a-button type="primary" size="large" block @click="router.push(`/exam/result/${examId}`)">
                  查看成绩
                </a-button>
              </template>
              <template v-else>
                <a-button type="primary" size="large" block disabled>
                  {{ getStatusText(exam.status, exam.can_join) }}
                </a-button>
                <p class="action-hint" v-if="exam.status === 'upcoming'">
                  考试尚未开始，请耐心等待
                </p>
              </template>
            </div>

            <div class="attempt-history" v-if="exam.attempt_count && exam.attempt_count > 0">
              <div class="history-title">历史成绩</div>
              <div class="history-item">
                <span class="history-label">最佳成绩</span>
                <span class="history-score" :class="{ pass: exam.latest_result === 'pass' }">
                  {{ exam.latest_score || '-' }} 分
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <a-empty v-else description="未找到考试信息" />
  </div>
</template>

<script setup lang="ts">
import {
  CalendarOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  LeftOutlined,
  QuestionCircleOutlined,
  RightOutlined,
  SafetyCertificateOutlined,
  SafetyOutlined,
  WarningOutlined,
} from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { ExamResponse } from '@/api/generated/model'
import {
  getAdmissionExamApiV1ExamsAdmissionExamIdGet,
  getExamApiV1ExamsExamIdGet,
} from '@/api/generated/exam-management/exam-management'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const exam = ref<ExamResponse | null>(null)
const examKind = ref<'admission' | 'training'>('training')

const examId = computed(() => Number(route.params.id))

onMounted(async () => {
  // 优先使用列表页传递过来的数据，避免 API 数据不一致
  const passedExam = route.meta?.exam || history.state?.exam
  if (passedExam && passedExam.id === examId.value) {
    exam.value = passedExam as ExamResponse
  } else {
    await fetchExamDetail()
  }
})

async function fetchExamDetail() {
  loading.value = true
  try {
    try {
      exam.value = await getExamApiV1ExamsExamIdGet(examId.value)
      examKind.value = 'training'
    } catch {
      exam.value = await getAdmissionExamApiV1ExamsAdmissionExamIdGet(examId.value)
      examKind.value = 'admission'
    }
  } catch (error) {
    message.error('加载考试信息失败')
  } finally {
    loading.value = false
  }
}

function handleStartExam() {
  if (!exam.value?.can_join) return
  router.push(`/exam/do/${examId.value}`)
}

function getStatusClass(status?: string) {
  switch (status) {
    case 'ongoing': return 'status-ongoing'
    case 'upcoming': return 'status-upcoming'
    case 'finished': return 'status-finished'
    default: return ''
  }
}

function getStatusText(status?: string, canJoin?: boolean | null) {
  if (canJoin === false && status !== 'finished') return '暂不可参加'
  switch (status) {
    case 'ongoing': return '进行中'
    case 'upcoming': return '即将开始'
    case 'finished': return '已结束'
    default: return '未知'
  }
}

function formatTime(date?: string | null) {
  if (!date) return ''
  return dayjs(date).format('MM/DD HH:mm')
}
</script>

<style scoped>
.overview-page {
  padding: 0;
}

.loading-wrapper {
  padding: 80px 0;
  text-align: center;
}

/* 返回栏 */
.top-bar {
  margin-bottom: 24px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 999px;
  border: 1px solid var(--v2-border);
  background: var(--v2-bg-card);
  color: var(--v2-text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  border-color: var(--v2-primary);
  color: var(--v2-primary);
}

/* 布局 */
.overview-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.overview-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.overview-side {
  width: 280px;
  flex-shrink: 0;
}

/* 信息卡片 */
.info-card {
  background: var(--v2-bg-card);
  border-radius: 24px;
  padding: 28px;
  box-shadow: 0 8px 24px rgba(24, 39, 75, 0.06);
}

.info-card-header {
  margin-bottom: 24px;
}

.exam-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 14px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 12px;
}

.status-ongoing.exam-badge {
  color: #2DA44E;
  background: rgba(52, 199, 89, 0.1);
}

.status-upcoming.exam-badge {
  color: #4B6EF5;
  background: rgba(75, 110, 245, 0.1);
}

.status-finished.exam-badge {
  color: #8E8E93;
  background: rgba(142, 142, 147, 0.1);
}

.exam-title {
  margin: 0 0 10px;
  font-size: 26px;
  font-weight: 700;
  color: var(--v2-text-primary);
  line-height: 1.3;
}

.exam-desc {
  margin: 0;
  color: var(--v2-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.info-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: var(--v2-primary-bg);
  color: var(--v2-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.info-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: var(--v2-text-muted);
}

.info-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
}

/* 考试须知 */
.rules-card {
  background: var(--v2-bg-card);
  border-radius: 24px;
  padding: 24px 28px;
  box-shadow: 0 8px 24px rgba(24, 39, 75, 0.06);
}

.rules-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--v2-warning);
  margin-bottom: 16px;
}

.rules-list {
  margin: 0;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rules-list li {
  font-size: 14px;
  color: var(--v2-text-secondary);
  line-height: 1.7;
}

.rules-list li strong {
  color: var(--v2-text-primary);
}

/* 侧边操作卡片 */
.action-card {
  background: var(--v2-bg-card);
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 8px 24px rgba(24, 39, 75, 0.06);
  position: sticky;
  top: 20px;
}

.action-status {
  text-align: center;
  margin-bottom: 20px;
}

.status-icon {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin: 0 auto 12px;
}

.status-icon.status-ongoing {
  background: rgba(52, 199, 89, 0.1);
  color: #2DA44E;
}

.status-icon.status-upcoming {
  background: rgba(75, 110, 245, 0.1);
  color: #4B6EF5;
}

.status-icon.status-finished {
  background: rgba(142, 142, 147, 0.1);
  color: #8E8E93;
}

.status-label {
  font-size: 16px;
  font-weight: 600;
  color: var(--v2-text-primary);
}

.action-btn-wrap {
  margin-bottom: 20px;
}

.action-btn-wrap :deep(.ant-btn) {
  height: 48px;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 600;
}

.action-hint {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--v2-text-muted);
  text-align: center;
  line-height: 1.5;
}

.attempt-history {
  border-top: 1px solid var(--v2-border);
  padding-top: 16px;
}

.history-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--v2-text-secondary);
  margin-bottom: 10px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-label {
  font-size: 13px;
  color: var(--v2-text-secondary);
}

.history-score {
  font-size: 18px;
  font-weight: 700;
  color: var(--v2-text-primary);
}

.history-score.pass {
  color: var(--v2-success);
}

@media (max-width: 900px) {
  .overview-layout {
    flex-direction: column;
  }

  .overview-side {
    width: 100%;
  }

  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
