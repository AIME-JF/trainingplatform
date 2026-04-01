<template>
  <div class="detail-page">
    <a-spin v-if="loading" size="large" style="display: block; text-align: center; padding: 120px 0" />
    <a-empty v-else-if="!detail" description="班级不存在" style="padding: 120px 0" />

    <template v-else>
      <!-- ====== 深色头部横幅 ====== -->
      <header class="detail-header">
        <div class="header-body">
          <div class="header-left">
            <h1 class="header-title">{{ detail.name }}</h1>
            <div class="header-meta-row">
              <span v-if="detail.class_code" class="meta-chip">
                <svg class="chip-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.2"><rect x="2" y="3" width="12" height="10" rx="1.5"/><path d="M5 6h6M5 9h4"/></svg>
                {{ detail.class_code }}
              </span>
              <span class="meta-chip"><UserOutlined class="chip-icon-ant" /> {{ detail.instructor_name || '未指定教官' }}</span>
              <span class="meta-chip"><TeamOutlined class="chip-icon-ant" /> {{ detail.enrolled_count ?? 0 }}{{ detail.capacity ? '/' + detail.capacity : '' }} 人</span>
              <span v-if="detail.location" class="meta-chip"><EnvironmentOutlined class="chip-icon-ant" /> {{ detail.location }}</span>
            </div>
            <div class="header-sub-row">
              <span>{{ formatDate(detail.start_date) }} ~ {{ formatDate(detail.end_date) }}</span>
              <span v-if="detail.department_name">{{ detail.department_name }}</span>
              <span v-if="detail.training_base_name">{{ detail.training_base_name }}</span>
            </div>
          </div>

          <!-- 右侧快捷信息卡片 -->
          <div class="header-cards">
            <div class="info-card info-card--status">
              <div class="info-card-top">
                <span class="info-card-label">班级状态</span>
                <span class="info-card-badge" :class="'badge-' + detail.status">{{ statusLabels[detail.status] || detail.status }}</span>
              </div>
              <div class="info-card-num">{{ detail.training_type_name || detail.type || '-' }}</div>
              <div class="info-card-extra">
                <span>{{ detail.enrolled_count ?? 0 }}{{ detail.capacity ? '/' + detail.capacity : '' }} 人已报名</span>
                <span v-if="detail.is_locked">· 名单已锁定</span>
              </div>
            </div>
            <div class="info-card">
              <div class="info-card-top">
                <span class="info-card-label">课程安排</span>
              </div>
              <div class="info-card-num">{{ detail.courses?.length || 0 }} <span class="info-unit">门课程</span></div>
            </div>
            <div class="info-card">
              <div class="info-card-top">
                <span class="info-card-label">考试安排</span>
              </div>
              <div class="info-card-num">{{ detail.exam_sessions?.length || 0 }} <span class="info-unit">场考试</span></div>
            </div>
          </div>
        </div>
      </header>

      <!-- ====== 主体内容 ====== -->
      <section class="page-content detail-body">

        <!-- 操作按钮区 -->
        <div class="action-bar">
          <!-- 学员按钮 -->
          <template v-if="authStore.isStudent">
            <a-button
              v-if="canEnroll"
              type="primary"
              @click="handleEnroll"
            >
              {{ detail.enrollment_requires_approval ? '报名申请' : '加入班级' }}
            </a-button>
            <a-button v-if="detail.current_enrollment_status === 'pending'" disabled>
              <ClockCircleOutlined /> 待审核
            </a-button>
            <a-button v-if="detail.current_enrollment_status === 'rejected'" disabled danger>
              审核未通过
            </a-button>
            <a-button
              v-if="isEnrolled && hasActiveCheckin"
              type="primary"
              @click="goCheckin"
            >
              <CheckCircleOutlined /> 签到
            </a-button>
            <a-button
              v-if="isEnrolled && hasActiveCheckout"
              @click="goCheckout"
            >
              签退评课
            </a-button>
          </template>

          <!-- 教官按钮（普通教官，非管理员） -->
          <template v-if="authStore.isInstructor">
            <a-button
              v-if="hasActiveCheckin"
              type="primary"
              @click="goCheckin"
            >
              <CheckCircleOutlined /> 签到
            </a-button>
            <a-button
              v-if="hasActiveCheckout"
              @click="goCheckout"
            >
              签退
            </a-button>
          </template>

          <!-- 通用按钮 -->
          <a-button v-if="isEnrolled || authStore.isInstructor" @click="activeTab = 'schedule'">
            <CalendarOutlined /> 查看课表
          </a-button>
          <a-button v-if="detail.status === 'ended'" @click="goHistory">
            <HistoryOutlined /> 训历
          </a-button>
        </div>

        <!-- Tab 内容区 -->
        <div class="content-tabs">
          <div class="tab-bar">
            <span
              v-for="tab in visibleTabs"
              :key="tab.key"
              class="tab-item"
              :class="{ active: activeTab === tab.key }"
              @click="activeTab = tab.key"
            >
              {{ tab.label }}
            </span>
          </div>

          <!-- 概览 -->
          <div v-if="activeTab === 'overview'" class="tab-panel">
            <div v-if="detail.description" class="overview-desc">
              <h3 class="section-label">班级简介</h3>
              <p>{{ detail.description }}</p>
            </div>

            <div v-if="detail.notices?.length" class="overview-notices">
              <h3 class="section-label">最新公告</h3>
              <div v-for="n in detail.notices.slice(0, 3)" :key="n.id" class="notice-row">
                <NotificationOutlined class="notice-icon" />
                <span class="notice-title">{{ n.title }}</span>
                <span class="notice-time">{{ formatDate(n.created_at) }}</span>
              </div>
            </div>

            <a-empty v-if="!detail.description && !detail.notices?.length" description="暂无内容" />
          </div>

          <!-- 课表 -->
          <div v-if="activeTab === 'schedule'" class="tab-panel">
            <a-empty v-if="!detail.courses?.length" description="暂无课程安排" />
            <div v-else class="schedule-list">
              <div v-for="course in detail.courses" :key="course.course_key || course.name" class="schedule-course">
                <div class="schedule-course-header">
                  <span class="course-name">{{ course.name }}</span>
                  <a-tag v-if="course.type" :color="course.type === 'practice' ? 'green' : 'blue'" size="small">
                    {{ course.type === 'practice' ? '实操' : '理论' }}
                  </a-tag>
                </div>
                <div class="schedule-course-meta">
                  <span v-if="course.instructor">{{ course.instructor }}</span>
                  <span v-if="course.hours">{{ course.hours }} 课时</span>
                </div>
                <div v-if="course.schedules?.length" class="schedule-sessions">
                  <div v-for="(s, i) in course.schedules" :key="i" class="session-row">
                    <span class="session-date">{{ s.date }}</span>
                    <span class="session-time">{{ s.time_range }}</span>
                    <span v-if="s.location" class="session-location">{{ s.location }}</span>
                    <a-tag v-if="s.status && s.status !== 'pending'" size="small">{{ sessionStatusLabel(s.status) }}</a-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 考试 -->
          <div v-if="activeTab === 'exam'" class="tab-panel">
            <a-empty v-if="!detail.exam_sessions?.length" description="暂无考试安排" />
            <div v-else class="exam-list">
              <div v-for="exam in detail.exam_sessions" :key="exam.id" class="exam-row">
                <div class="exam-info">
                  <span class="exam-title">{{ exam.title || exam.paper_title || '考试' }}</span>
                  <span class="exam-time">{{ formatDateTime(exam.start_time) }}</span>
                </div>
                <a-button
                  v-if="authStore.isStudent && canTakeExam(exam)"
                  type="primary"
                  size="small"
                  @click="goExam(exam.id)"
                >
                  参加考试
                </a-button>
              </div>
            </div>
          </div>

          <!-- 学员名单（仅教官可见） -->
          <div v-if="activeTab === 'students'" class="tab-panel">
            <div v-if="detail.students?.length" class="student-toolbar">
              <a-input-search
                v-model:value="studentSearch"
                placeholder="搜索学员姓名"
                style="width: 220px"
                allow-clear
              />
              <span class="student-count">共 {{ filteredStudents.length }} 人</span>
            </div>
            <a-empty v-if="!detail.students?.length" description="暂无学员" />
            <div v-else class="student-list">
              <div v-for="s in filteredStudents" :key="s.user_id" class="student-row">
                <a-avatar :size="32" class="student-avatar">{{ studentDisplayName(s).slice(0, 1) }}</a-avatar>
                <div class="student-info">
                  <span class="student-name">{{ studentDisplayName(s) }}</span>
                  <span v-if="s.departments?.length" class="student-dept">{{ s.departments.join(' / ') }}</span>
                </div>
                <a-tag v-if="s.status && s.status !== 'approved'" size="small" :color="s.status === 'pending' ? 'orange' : 'red'">
                  {{ enrollStatusLabel(s.status) }}
                </a-tag>
              </div>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  UserOutlined,
  TeamOutlined,
  EnvironmentOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  HistoryOutlined,
  NotificationOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import axiosInstance from '@/api/custom-instance'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const activeTab = ref('overview')

interface ScheduleItem {
  date: string
  time_range: string
  location?: string
  status?: string
  session_id?: string
  hours?: number
}

interface CourseItem {
  course_key?: string
  name: string
  type?: string
  instructor?: string
  hours?: number
  schedules?: ScheduleItem[]
}

interface ExamItem {
  id: number
  title?: string
  paper_title?: string
  start_time?: string
  end_time?: string
  status?: string
}

interface StudentItem {
  user_id: number
  user_name?: string
  user_nickname?: string
  departments?: string[]
  status?: string
}

interface NoticeItem {
  id: number
  title: string
  created_at?: string
}

interface ClassDetail {
  id: number
  name: string
  type: string
  training_type_name: string | null
  status: string
  publish_status: string
  description: string
  start_date: string
  end_date: string
  location: string
  capacity: number | null
  enrolled_count: number
  instructor_id: number | null
  instructor_name: string
  department_name: string
  training_base_name: string
  class_code: string
  is_locked: boolean
  enrollment_requires_approval: boolean
  current_enrollment_status: string | null
  can_enter_training: boolean
  current_step_key: string
  current_session: { session_id: string; status: string } | null
  courses: CourseItem[]
  exam_sessions: ExamItem[]
  students: StudentItem[]
  notices: NoticeItem[]
}

const detail = ref<ClassDetail | null>(null)
const studentSearch = ref('')

const filteredStudents = computed(() => {
  const list = detail.value?.students || []
  const kw = studentSearch.value.trim().toLowerCase()
  if (!kw) return list
  return list.filter((s) => {
    const name = (s.user_nickname || s.user_name || '').toLowerCase()
    return name.includes(kw)
  })
})

function studentDisplayName(s: StudentItem): string {
  return s.user_nickname || s.user_name || String(s.user_id)
}

const statusLabels: Record<string, string> = {
  upcoming: '未开始',
  active: '进行中',
  ended: '已结束',
}


// 是否已报名通过
const isEnrolled = computed(() => detail.value?.current_enrollment_status === 'approved')

// 是否可以报名
const canEnroll = computed(() => {
  const d = detail.value
  if (!d) return false
  if (d.current_enrollment_status) return false // 已有报名记录
  if (d.status === 'ended') return false
  if (d.publish_status !== 'published') return false
  if (d.is_locked) return false
  return true
})

// 签到/签退窗口
const hasActiveCheckin = computed(() => {
  const s = detail.value?.current_session?.status
  return s === 'checkin_open'
})

const hasActiveCheckout = computed(() => {
  const s = detail.value?.current_session?.status
  return s === 'checkout_open'
})

// Tab 列表：教官可看学员名单，学员不可
const visibleTabs = computed(() => {
  const tabs = [
    { key: 'overview', label: '概览' },
    { key: 'schedule', label: '课表' },
    { key: 'exam', label: '考试' },
  ]
  if (authStore.isInstructor) {
    tabs.push({ key: 'students', label: '学员名单' })
  }
  return tabs
})

function sessionStatusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待开始',
    checkin_open: '签到中',
    checkin_closed: '进行中',
    checkout_open: '签退中',
    completed: '已完成',
    skipped: '已跳过',
    missed: '已缺课',
  }
  return map[status] || status
}

function enrollStatusLabel(status: string): string {
  const map: Record<string, string> = {
    approved: '已通过',
    pending: '待审核',
    rejected: '未通过',
  }
  return map[status] || status
}

function canTakeExam(exam: ExamItem): boolean {
  if (!exam.start_time) return false
  const now = Date.now()
  const start = new Date(exam.start_time).getTime()
  const end = exam.end_time ? new Date(exam.end_time).getTime() : start + 2 * 3600 * 1000
  return now >= start && now <= end
}

function formatDate(val: string | null | undefined): string {
  if (!val) return '-'
  return String(val).slice(0, 10)
}

function formatDateTime(val: string | null | undefined): string {
  if (!val) return '-'
  return String(val).slice(0, 16).replace('T', ' ')
}

function handleEnroll() {
  router.push(`/classes/${route.params.id}/enroll`)
}

function goCheckin() {
  router.push(`/classes/${route.params.id}/checkin`)
}

function goCheckout() {
  router.push(`/classes/${route.params.id}/checkout`)
}

function goHistory() {
  // 训历暂用详情页
  message.info('训历功能即将上线')
}

function goExam(examId: number) {
  router.push(`/exam/do/${examId}`)
}

async function fetchDetail() {
  const id = route.params.id
  if (!id) return
  loading.value = true
  try {
    const res = await axiosInstance.get(`/trainings/${id}`)
    detail.value = res.data as ClassDetail
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '加载班级详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchDetail)
</script>

<style scoped>
/* ====== 深色头部 ====== */
.detail-header {
  background: var(--v2-bg-header);
  padding: 28px 32px 24px;
}

@media (max-width: 768px) {
  .detail-header { padding: 20px 16px 16px; }
}

.header-body {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

@media (max-width: 900px) {
  .header-body { flex-direction: column; }
}

.header-left { flex: 1; min-width: 0; }

.header-title {
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 14px;
  line-height: 1.2;
}

.header-meta-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: rgba(255,255,255,0.82);
}

.chip-icon { width: 14px; height: 14px; }
.chip-icon-ant { font-size: 13px; }

.header-sub-row {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: rgba(255,255,255,0.5);
  flex-wrap: wrap;
}

/* -- 右侧信息卡片（毛玻璃融入深色头部） -- */
.header-cards {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

@media (max-width: 900px) {
  .header-cards { width: 100%; }
}

.info-card {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--v2-radius-sm);
  padding: 14px 18px;
  min-width: 120px;
  flex: 1;
  transition: background 0.2s;
}

.info-card:hover {
  background: rgba(255, 255, 255, 0.12);
}

.info-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.info-card--status {
  flex: 1.6;
  min-width: 180px;
}

.info-card-extra {
  margin-top: 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  display: flex;
  gap: 4px;
}

.info-card-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.info-card-badge {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: var(--v2-radius-full);
}

.badge-upcoming { background: rgba(75, 110, 245, 0.25); color: #8DA6F8; }
.badge-active   { background: rgba(52, 199, 89, 0.25);  color: #6EE49A; }
.badge-ended    { background: rgba(255, 255, 255, 0.1);  color: rgba(255, 255, 255, 0.4); }

.info-card-num {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.info-unit {
  font-size: 12px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.45);
}

/* ====== 主体 ====== */
.detail-body {
  padding-top: 20px;
}

/* -- 操作按钮栏 -- */
.action-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

/* -- Tab 栏 -- */
.content-tabs {
  background: var(--v2-bg-card);
  border-radius: var(--v2-radius);
  overflow: hidden;
}

.tab-bar {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--v2-border-light);
  padding: 0 20px;
}

.tab-item {
  padding: 14px 18px;
  font-size: 14px;
  color: var(--v2-text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s;
  white-space: nowrap;
}

.tab-item:hover { color: var(--v2-text-secondary); }

.tab-item.active {
  color: var(--v2-primary);
  font-weight: 500;
  border-bottom-color: var(--v2-primary);
}

.tab-panel {
  padding: 20px;
  min-height: 200px;
}

/* -- 概览 -- */
.section-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin-bottom: 10px;
}

.overview-desc {
  margin-bottom: 24px;
}

.overview-desc p {
  white-space: pre-wrap;
  color: var(--v2-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.notice-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid var(--v2-border-light);
}

.notice-row:last-child { border-bottom: none; }
.notice-icon { color: var(--v2-warning); font-size: 14px; }
.notice-title { flex: 1; font-size: 14px; color: var(--v2-text-primary); }
.notice-time { font-size: 12px; color: var(--v2-text-muted); }

/* -- 课表 -- */
.schedule-course {
  padding: 16px 0;
  border-bottom: 1px solid var(--v2-border-light);
}

.schedule-course:last-child { border-bottom: none; }

.schedule-course-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.course-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--v2-text-primary);
}

.schedule-course-meta {
  font-size: 12px;
  color: var(--v2-text-muted);
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.schedule-sessions {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.session-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--v2-text-secondary);
  padding: 4px 0;
}

.session-date { font-weight: 500; min-width: 90px; }
.session-time { color: var(--v2-text-muted); }
.session-location { color: var(--v2-text-muted); }

/* -- 考试 -- */
.exam-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--v2-border-light);
}

.exam-row:last-child { border-bottom: none; }
.exam-title { font-size: 14px; font-weight: 500; color: var(--v2-text-primary); }
.exam-time { font-size: 12px; color: var(--v2-text-muted); margin-top: 2px; }
.exam-info { display: flex; flex-direction: column; }

/* -- 学员名单 -- */
/* -- 学员名单 -- */
.student-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 12px;
}

.student-count {
  font-size: 13px;
  color: var(--v2-text-muted);
  white-space: nowrap;
}

.student-list {
  display: flex;
  flex-direction: column;
}

.student-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 8px;
  border-bottom: 1px solid var(--v2-border-light);
  transition: background 0.15s;
}

.student-row:last-child { border-bottom: none; }
.student-row:hover { background: var(--v2-bg); }

.student-avatar {
  background: var(--v2-primary);
  color: #fff;
  font-size: 13px;
  flex-shrink: 0;
}

.student-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.student-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--v2-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.student-dept {
  font-size: 12px;
  color: var(--v2-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
