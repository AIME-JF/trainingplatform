<template>
  <div class="page-content exam-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">在线考试</h1>
        <p class="page-subtitle">检验学习成果，提升执法能力。</p>
      </div>
    </div>

    <a-card :bordered="false" class="filter-card">
      <div class="filter-shell">
        <div class="filter-top">
          <div class="filter-search">
            <a-input-search
              v-model:value="filters.search"
              placeholder="搜索考试名称..."
              @search="fetchExams"
            />
          </div>
          <div class="filter-top-actions">
            <a-select v-model:value="filters.sort" class="sort-select" @change="fetchExams">
              <a-select-option value="latest">按最新</a-select-option>
              <a-select-option value="upcoming">即将开始</a-select-option>
              <a-select-option value="ongoing">进行中</a-select-option>
            </a-select>
          </div>
        </div>

        <div class="category-tabs">
          <a-tag
            v-for="tab in statusTabs"
            :key="tab.key"
            class="cat-tag"
            :class="{ active: filters.status === tab.key }"
            @click="selectStatus(tab.key)"
          >
            {{ tab.label }}
          </a-tag>
        </div>
      </div>
    </a-card>

    <a-tabs v-model:activeKey="activeTab" class="exam-tabs" @change="fetchExams">
      <a-tab-pane key="admission" tab="准入考试" />
      <a-tab-pane key="training" tab="培训班考试" />
    </a-tabs>

    <div class="exam-stats">
      <span>共 <strong>{{ exams.length }}</strong> 场考试</span>
      <span v-if="ongoingCount > 0">进行中 <strong>{{ ongoingCount }}</strong> 场</span>
      <span v-if="upcomingCount > 0">即将开始 <strong>{{ upcomingCount }}</strong> 场</span>
    </div>

    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" />
    </div>

    <a-empty v-else-if="!exams.length" description="暂无考试" class="empty-block" />

    <div v-else class="exam-grid">
      <div
        v-for="(exam, index) in exams"
        :key="exam.id"
        class="exam-card"
        :style="{ '--card-accent': getExamAccent(exam.status) }"
        @click="handleExamClick(exam)"
      >
        <div class="card-cover" :style="{ background: getExamCoverBackground(exam, index) }">
          <div class="cover-labels">
            <a-tag class="cover-tag cover-tag-status" :class="getStatusClass(exam.status)">
              {{ getStatusText(exam.status, exam.can_join) }}
            </a-tag>
            <div class="cover-tag-stack">
              <a-tag v-if="exam.can_join" class="cover-tag cover-tag-action">可参加</a-tag>
              <a-tag v-if="exam.attempt_count && exam.attempt_count > 0" class="cover-tag cover-tag-attempt">
                已考 {{ exam.attempt_count }} 次
              </a-tag>
            </div>
          </div>

          <div class="cover-visual">
            <span class="cover-visual-ring">
              <FileTextOutlined class="cover-visual-icon" />
            </span>
          </div>

          <div class="cover-footer">
            <span class="cover-footer-item">
              <ClockCircleOutlined />
              {{ exam.duration || 0 }} 分钟
            </span>
            <span class="cover-footer-item">
              <QuestionCircleOutlined />
              {{ exam.question_count || 0 }} 题
            </span>
            <span class="cover-footer-item">
              <SafetyCertificateOutlined />
              满分 {{ exam.total_score || 0 }}
            </span>
          </div>
        </div>

        <div class="card-body">
          <div class="card-head">
            <div class="card-head-main">
              <h3>{{ exam.title }}</h3>
              <p>{{ exam.description || '暂无考试说明' }}</p>
            </div>
          </div>

          <div class="meta-grid">
            <span>
              <CalendarOutlined />
              {{ exam.start_time ? formatDate(exam.start_time) : '不限时' }}
            </span>
            <span>
              <SafetyOutlined />
              及格 {{ exam.passing_score || 0 }} 分
            </span>
          </div>

          <div class="action-row">
            <template v-if="exam.status === 'finished' || exam.latest_result === 'pass'">
              <a-button type="primary" block @click.stop="router.push(`/exam/result/${exam.id}`)">
                查看结果
              </a-button>
            </template>
            <template v-else-if="exam.can_join">
              <a-button type="primary" block @click.stop="router.push({ path: `/exam/overview/${exam.id}`, state: { exam } })">
                进入考试
              </a-button>
            </template>
            <template v-else>
              <a-button type="primary" block disabled>
                {{ getStatusText(exam.status, exam.can_join) }}
              </a-button>
            </template>
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
  FileTextOutlined,
  QuestionCircleOutlined,
  SafetyCertificateOutlined,
  SafetyOutlined,
} from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import { computed, onMounted, reactive, ref } from 'vue'
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

const filters = reactive({
  search: '',
  status: 'all',
  sort: 'latest',
})

const statusTabs = [
  { key: 'all', label: '全部' },
  { key: 'ongoing', label: '进行中' },
  { key: 'upcoming', label: '即将开始' },
  { key: 'finished', label: '已结束' },
]

const ongoingCount = computed(() => exams.value.filter((e) => e.status === 'ongoing').length)
const upcomingCount = computed(() => exams.value.filter((e) => e.status === 'upcoming').length)

onMounted(() => {
  void fetchExams()
})

async function fetchExams() {
  loading.value = true
  try {
    const params = { page: 1, size: 50, search: filters.search || undefined }
    const response = activeTab.value === 'admission'
      ? await getAdmissionExamsApiV1ExamsAdmissionGet(params)
      : await getExamsApiV1ExamsGet(params)

    let items = response.items || []

    // Filter by status
    if (filters.status !== 'all') {
      items = items.filter((item) => item.status === filters.status)
    }

    // Sort
    if (filters.sort === 'upcoming') {
      items = items.filter((i) => i.status === 'upcoming')
    } else if (filters.sort === 'ongoing') {
      items = items.filter((i) => i.status === 'ongoing')
    }

    exams.value = items
  } catch (error) {
    message.error(error instanceof Error ? error.message : '考试列表加载失败')
  } finally {
    loading.value = false
  }
}

function selectStatus(status: string) {
  filters.status = status
  void fetchExams()
}

function handleExamClick(exam: ExamResponse) {
  if (exam.can_join) {
    void router.push({ path: `/exam/overview/${exam.id}`, state: { exam } })
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

function formatDate(date?: string | null) {
  if (!date) return ''
  return dayjs(date).format('MM/DD HH:mm')
}

const coverGradients = [
  'linear-gradient(135deg, #edf1fb 0%, #e4eaf5 100%)',
  'linear-gradient(135deg, #edf3ee 0%, #e1eae3 100%)',
  'linear-gradient(135deg, #f6eee7 0%, #eee2d7 100%)',
  'linear-gradient(135deg, #edf4f3 0%, #e2ece9 100%)',
]

const statusAccents: Record<string, string> = {
  ongoing: '#34C759',
  upcoming: '#4B6EF5',
  finished: '#8E8E93',
}

function getExamAccent(status?: string) {
  return statusAccents[status || ''] || '#4B6EF5'
}

function getExamCoverBackground(exam: ExamResponse, index: number) {
  if (exam.status === 'ongoing') {
    return 'linear-gradient(135deg, #edf7ed 0%, #e3f0e6 100%)'
  }
  if (exam.status === 'upcoming') {
    return 'linear-gradient(135deg, #edf1fb 0%, #e4eaf5 100%)'
  }
  if (exam.status === 'finished') {
    return 'linear-gradient(135deg, #f5f5f7 0%, #ececed 100%)'
  }
  return coverGradients[index % coverGradients.length]
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

.filter-card {
  margin-bottom: 20px;
  border-radius: 24px;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.06);
}

.filter-shell {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.filter-top {
  display: flex;
  align-items: center;
  gap: 16px;
}

.filter-search {
  flex: 1;
}

.filter-top-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sort-select {
  width: 150px;
}

.category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

:deep(.cat-tag.ant-tag) {
  cursor: pointer;
  margin: 0;
  padding: 7px 14px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 600;
  color: var(--v2-text-secondary);
  border: 1px solid rgba(75, 110, 245, 0.12);
  background: rgba(255, 255, 255, 0.92);
  transition:
    color 0.2s ease,
    border-color 0.2s ease,
    background 0.2s ease,
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

:deep(.cat-tag.ant-tag:hover),
:deep(.cat-tag.active.ant-tag) {
  color: var(--v2-primary);
  border-color: rgba(75, 110, 245, 0.28);
  background: var(--v2-primary-light);
  box-shadow: 0 10px 24px rgba(75, 110, 245, 0.12);
  transform: translateY(-1px);
}

.exam-tabs {
  margin-bottom: 20px;
}

.exam-tabs :deep(.ant-tabs-nav::before) {
  border-bottom: none;
}

.exam-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
  color: var(--v2-text-secondary);
}

.loading-wrapper,
.empty-block {
  padding: 80px 0;
}

.exam-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.exam-card {
  overflow: hidden;
  background: var(--v2-bg-card);
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba(24, 39, 75, 0.08);
  cursor: pointer;
  transition:
    transform 0.22s ease,
    box-shadow 0.22s ease;
}

.exam-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 24px 48px rgba(75, 110, 245, 0.12);
}

.card-cover {
  position: relative;
  height: 180px;
  padding: 18px;
  overflow: hidden;
}

.card-cover::before {
  content: '';
  position: absolute;
  right: -34px;
  bottom: -70px;
  width: 210px;
  height: 210px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  filter: blur(8px);
}

.cover-labels {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.cover-tag-stack {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

:deep(.cover-tag.ant-tag) {
  margin: 0;
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.35;
  border: 1px solid rgba(255, 255, 255, 0.72);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

:deep(.cover-tag-status.ant-tag) {
  color: #405f7f;
}

:deep(.cover-tag-action.ant-tag) {
  color: #2DA44E;
  border-color: rgba(52, 199, 89, 0.48);
  background: rgba(52, 199, 89, 0.08);
}

:deep(.cover-tag-attempt.ant-tag) {
  color: #7867c6;
}

.cover-visual {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-visual-ring {
  position: relative;
  width: 82px;
  height: 82px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.78);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.7));
  box-shadow:
    0 16px 28px var(--card-accent, rgba(75, 110, 245, 0.14)),
    inset 0 1px 0 rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
}

.cover-visual-icon {
  position: relative;
  z-index: 1;
  font-size: 34px;
  color: var(--card-accent, #4B6EF5);
}

.cover-footer {
  position: absolute;
  left: 12px;
  right: 22px;
  bottom: 10px;
  z-index: 2;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.cover-footer-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 28px;
  padding: 0 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(18, 25, 38, 0.78);
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.72);
}

.card-body {
  padding: 22px 22px 24px;
}

.card-head {
  margin-bottom: 16px;
}

.card-head-main h3 {
  margin: 0 0 10px;
  font-size: 21px;
  line-height: 1.35;
  color: var(--v2-text-primary);
}

.card-head-main p {
  margin: 0;
  min-height: 44px;
  color: var(--v2-text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 14px;
  margin-bottom: 16px;
  color: var(--v2-text-secondary);
  font-size: 14px;
}

.meta-grid span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.action-row {
  padding-top: 4px;
}

:deep(.status-ongoing) {
  color: #2DA44E;
  background: rgba(52, 199, 89, 0.1);
  border: none;
}

:deep(.status-upcoming) {
  color: #4B6EF5;
  background: rgba(75, 110, 245, 0.1);
  border: none;
}

:deep(.status-finished) {
  color: #8E8E93;
  background: rgba(142, 142, 147, 0.1);
  border: none;
}

@media (max-width: 768px) {
  .filter-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .sort-select {
    width: 100%;
  }

  .filter-grid,
  .exam-grid,
  .meta-grid {
    grid-template-columns: 1fr;
  }

  .card-cover {
    height: 164px;
  }

  .cover-labels {
    flex-direction: column;
  }

  .cover-tag-stack {
    justify-content: flex-start;
  }
}
</style>
