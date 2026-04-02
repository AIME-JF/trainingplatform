<template>
  <div class="page-content exam-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">在线考试</h1>
        <p class="page-subtitle">检验学习成果，提升执法能力。</p>
      </div>
    </div>

    <a-tabs v-model:activeKey="activeTab" class="exam-tabs" @change="fetchExams">
      <a-tab-pane key="admission" tab="准入考试" />
      <a-tab-pane key="training" tab="培训班考试" />
    </a-tabs>

    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" />
    </div>

    <a-empty v-else-if="!exams.length" description="暂无考试" class="empty-block" />

    <div v-else class="exam-list">
      <div
        v-for="exam in exams"
        :key="exam.id"
        class="exam-card"
        @click="handleExamClick(exam)"
      >
        <div class="exam-card-header">
          <div class="exam-info">
            <h3>{{ exam.title }}</h3>
            <p v-if="exam.description">{{ exam.description }}</p>
          </div>
          <a-tag class="status-tag" :class="getStatusClass(exam.status)">
            {{ getStatusText(exam.status, exam.can_join) }}
          </a-tag>
        </div>

        <div class="exam-meta">
          <div class="meta-item">
            <ClockCircleOutlined />
            <span>时长 {{ exam.duration || 0 }} 分钟</span>
          </div>
          <div class="meta-item">
            <QuestionCircleOutlined />
            <span>{{ exam.question_count || 0 }} 题</span>
          </div>
          <div class="meta-item">
            <ScoreOutlined />
            <span>满分 {{ exam.total_score || 0 }} 分</span>
          </div>
          <div class="meta-item">
            <SafetyOutlined />
            <span>及格 {{ exam.passing_score || 0 }} 分</span>
          </div>
        </div>

        <div v-if="exam.start_time || exam.end_time" class="exam-time">
          <CalendarOutlined />
          <span>{{ formatTimeRange(exam.start_time, exam.end_time) }}</span>
        </div>

        <div class="exam-card-footer">
          <template v-if="exam.status === 'finished' || exam.latest_result === 'pass'">
            <a-button type="primary" @click.stop="router.push(`/exam/result/${exam.id}`)">查看结果</a-button>
          </template>
          <template v-else-if="exam.can_join">
            <a-button type="primary" @click.stop="router.push(`/exam/do/${exam.id}`)">进入考试</a-button>
          </template>
          <template v-else>
            <a-button type="primary" disabled>{{ getStatusText(exam.status, exam.can_join) }}</a-button>
          </template>

          <div v-if="exam.attempt_count && exam.attempt_count > 0" class="attempt-info">
            已参加 {{ exam.attempt_count }} 次
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  CalendarOutlined,
  ClockCircleOutlined,
  QuestionCircleOutlined,
  SafetyOutlined,
  ScoreOutlined,
} from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { ExamResponse } from '@/api/generated/model'
import {
  getAdmissionExamsApiV1ExamsAdmissionGet,
  getExamsApiV1ExamsGet,
} from '@/api/generated/exam-management/exam-management'

const router = useRouter()
const loading = ref(false)
const activeTab = ref<'admission' | 'training'>('admission')
const exams = ref<ExamResponse[]>([])

onMounted(() => {
  void fetchExams()
})

async function fetchExams() {
  loading.value = true
  try {
    const params = { page: 1, size: 50 }
    const response = activeTab.value === 'admission'
      ? await getAdmissionExamsApiV1ExamsAdmissionGet(params)
      : await getExamsApiV1ExamsGet(params)

    exams.value = response.items || []
  } catch (error) {
    message.error(error instanceof Error ? error.message : '考试列表加载失败')
  } finally {
    loading.value = false
  }
}

function handleExamClick(exam: ExamResponse) {
  if (exam.can_join) {
    void router.push(`/exam/do/${exam.id}`)
  } else if (exam.status === 'finished' || exam.latest_result === 'pass') {
    void router.push(`/exam/result/${exam.id}`)
  }
}

function getStatusClass(status?: string) {
  switch (status) {
    case 'ongoing':
      return 'status-ongoing'
    case 'upcoming':
      return 'status-upcoming'
    case 'finished':
      return 'status-finished'
    default:
      return ''
  }
}

function getStatusText(status?: string, canJoin?: boolean | null) {
  if (canJoin === false && status !== 'finished') return '暂不可参加'
  switch (status) {
    case 'ongoing':
      return '进行中'
    case 'upcoming':
      return '即将开始'
    case 'finished':
      return '已结束'
    default:
      return '未知'
  }
}

function formatTimeRange(start?: string | null, end?: string | null) {
  if (!start && !end) return '不限时'
  const startStr = start ? dayjs(start).format('MM/DD HH:mm') : ''
  const endStr = end ? dayjs(end).format('MM/DD HH:mm') : ''
  return `${startStr} - ${endStr}`
}
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.page-title {
  margin: 0 0 6px;
  font-size: 28px;
  font-weight: 700;
  color: var(--v2-text-primary);
}

.page-subtitle {
  margin: 0;
  color: var(--v2-text-secondary);
}

.exam-tabs {
  margin-bottom: 20px;
}

.exam-tabs :deep(.ant-tabs-nav::before) {
  border-bottom: none;
}

.loading-wrapper,
.empty-block {
  padding: 80px 0;
}

.exam-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.exam-card {
  background: var(--v2-bg-card);
  border-radius: 20px;
  padding: 22px;
  box-shadow: 0 8px 24px rgba(24, 39, 75, 0.06);
  cursor: pointer;
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.exam-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(75, 110, 245, 0.1);
}

.exam-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

.exam-info {
  flex: 1;
}

.exam-info h3 {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 600;
  color: var(--v2-text-primary);
}

.exam-info p {
  margin: 0;
  color: var(--v2-text-secondary);
  font-size: 14px;
}

.status-tag {
  border-radius: 999px;
  padding: 4px 14px;
  font-weight: 600;
  border: none;
}

.status-ongoing {
  color: #fff;
  background: linear-gradient(135deg, #34C759 0%, #248a3d 100%);
}

.status-upcoming {
  color: #905500;
  background: linear-gradient(135deg, #FFD60A 0%, #e6c000 100%);
}

.status-finished {
  color: #666;
  background: rgba(102, 102, 102, 0.12);
}

.exam-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 12px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--v2-text-secondary);
  font-size: 14px;
}

.exam-time {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 16px;
  color: var(--v2-text-secondary);
  font-size: 14px;
}

.exam-card-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.attempt-info {
  color: var(--v2-text-secondary);
  font-size: 13px;
}

@media (max-width: 768px) {
  .exam-card-header {
    flex-direction: column;
  }

  .exam-meta {
    gap: 12px;
  }
}
</style>
