<template>
  <section class="page-content dashboard-page">
    <template v-if="isDashboardRoute">
      <section class="hero-card">
        <div class="hero-copy">
          <div class="hero-topline">
            <span class="hero-badge">{{ greetingText }}</span>
            <span class="hero-date-pill">
              <CalendarOutlined />
              {{ todayText }}
            </span>
          </div>
          <h1 class="hero-title">欢迎回来，{{ displayName }}</h1>
          <div class="hero-profile-list">
            <strong>{{ identityCode }}</strong>
            <span class="hero-profile-divider">·</span>
            <span>{{ roleLabel }}</span>
            <span class="hero-profile-divider">·</span>
            <span>{{ authStore.currentUser?.unit || '未设置单位' }}</span>
          </div>
        </div>

        <div class="hero-summary">
          <div v-for="item in overviewStats" :key="item.label" class="summary-card">
            <span class="summary-label">{{ item.label }}</span>
            <strong class="summary-value">
              {{ item.value }}
              <small v-if="item.suffix">{{ item.suffix }}</small>
            </strong>
          </div>
        </div>
      </section>

      <section class="dashboard-workbench">
        <article class="surface-card mini-schedule-card">
          <div class="section-head">
            <div>
              <h2>今日安排</h2>
              <p>点击日期查看当天课程安排</p>
            </div>
            <button type="button" class="section-link" @click="navigateTo('/classes/schedule')">
              完整日历
              <RightOutlined />
            </button>
          </div>

          <div class="mini-week-strip">
            <button
              v-for="day in previewWeekDays"
              :key="day.dateKey"
              type="button"
              class="mini-day-pill"
              :class="{
                today: day.isToday,
                selected: day.dateKey === selectedPreviewDate,
                'has-event': day.hasEvent,
              }"
              :aria-pressed="day.dateKey === selectedPreviewDate"
              @click="selectedPreviewDate = day.dateKey"
            >
              <span>{{ day.label }}</span>
              <strong>{{ day.displayDate }}</strong>
            </button>
          </div>

          <div v-if="calendarLoading" class="mini-state">
            <a-spin size="small" />
            <span>课表加载中...</span>
          </div>
          <div v-else-if="calendarPreviewItems.length" class="mini-event-list">
            <button
              v-for="item in calendarPreviewItems"
              :key="item.key"
              type="button"
              class="mini-event-item"
              :style="{
                '--mini-event-border': item.palette.border,
                '--mini-event-bg-start': item.palette.backgroundStart,
                '--mini-event-bg-end': item.palette.backgroundEnd,
              }"
              @click="navigateTo(item.path)"
            >
              <div class="mini-event-main">
                <strong>{{ item.title }}</strong>
                <span>{{ item.timeLabel }}</span>
              </div>
              <div class="mini-event-meta">
                <span class="mini-event-meta-row">
                  <EnvironmentOutlined class="mini-event-meta-icon" />
                  <span>{{ item.primaryMeta }}</span>
                </span>
                <span class="mini-event-meta-row">
                  <UserOutlined class="mini-event-meta-icon" />
                  <span>{{ item.secondaryMeta }}</span>
                </span>
              </div>
            </button>
          </div>
          <div v-else class="mini-state mini-empty">
            <CalendarOutlined />
            <span>{{ calendarError || '所选日期暂无安排' }}</span>
          </div>
        </article>

        <article class="surface-card quick-surface">
          <div class="section-head">
            <div>
              <h2>快捷入口</h2>
              <p>按当前权限进入常用功能模块</p>
            </div>
          </div>

          <div class="quick-grid quick-grid-compact">
            <button
              v-for="action in quickActions"
              :key="action.path"
              type="button"
              class="quick-item"
              @click="navigateTo(action.path)"
            >
              <span class="quick-icon" :style="{ background: action.background }">
                <component :is="action.icon" />
              </span>
              <span class="quick-text">
                <strong>{{ action.title }}</strong>
                <span>{{ action.description }}</span>
              </span>
              <RightOutlined class="quick-arrow" />
            </button>
          </div>
        </article>
      </section>
    </template>

    <section v-else class="surface-card placeholder-card">
      <span class="hero-badge placeholder-badge">模块建设中</span>
      <h1 class="placeholder-title">{{ currentTitle }}</h1>
      <p class="placeholder-text">
        当前页面已接入整体布局与权限控制，后续业务内容可以在这里继续补充。为了避免首页样式污染其它占位页，这里改成了独立的占位外观。
      </p>
      <div class="placeholder-actions">
        <a-button type="primary" @click="navigateTo('/')">返回工作台</a-button>
        <a-button v-if="quickActions[0]" @click="navigateTo(quickActions[0].path)">
          前往{{ quickActions[0].title }}
        </a-button>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import isoWeek from 'dayjs/plugin/isoWeek'
import {
  CalendarOutlined,
  DatabaseOutlined,
  EnvironmentOutlined,
  ReadOutlined,
  RightOutlined,
  UserOutlined,
} from '@ant-design/icons-vue'
import axiosInstance from '@/api/custom-instance'
import type { CalendarEventResponse } from '@/api/generated/model/calendarEventResponse'
import type { ExamResponse } from '@/api/generated/model/examResponse'
import { useAuthStore } from '@/stores/auth'
import {
  COURSE_PERMISSIONS,
  EXAM_LIST_PERMISSIONS,
  PROFILE_PERMISSIONS,
  TRAINING_PERMISSIONS,
  TRAINING_SCHEDULE_PERMISSIONS,
} from '@/constants/permissions'

dayjs.extend(isoWeek)

interface MetricItem {
  label: string
  value: string
  suffix?: string
}

interface QuickAction {
  title: string
  description: string
  path: string
  icon: Component
  background: string
  permissions: string[]
}

interface PreviewPalette {
  border: string
  backgroundStart: string
  backgroundEnd: string
}

interface DashboardPreviewItem {
  key: string
  title: string
  timeLabel: string
  primaryMeta: string
  secondaryMeta: string
  sortMin: number
  palette: PreviewPalette
  path: string
}

const previewPalette: PreviewPalette[] = [
  {
    border: '#7A90FF',
    backgroundStart: 'rgba(249, 251, 255, 0.99)',
    backgroundEnd: 'rgba(240, 245, 255, 0.96)',
  },
  {
    border: '#47C97A',
    backgroundStart: 'rgba(248, 255, 250, 0.99)',
    backgroundEnd: 'rgba(238, 251, 243, 0.96)',
  },
  {
    border: '#B67AF8',
    backgroundStart: 'rgba(252, 249, 255, 0.99)',
    backgroundEnd: 'rgba(245, 239, 255, 0.96)',
  },
  {
    border: '#FF9F57',
    backgroundStart: 'rgba(255, 251, 246, 0.99)',
    backgroundEnd: 'rgba(255, 244, 231, 0.96)',
  },
]

const router = useRouter()
const currentRoute = useRoute()
const authStore = useAuthStore()
const calendarLoading = ref(false)
const calendarError = ref('')
const calendarEvents = ref<CalendarEventResponse[]>([])
const examEvents = ref<ExamResponse[]>([])
const selectedPreviewDate = ref(dayjs().format('YYYY-MM-DD'))

const displayName = computed(() => authStore.currentUser?.name || authStore.currentUser?.username || '用户')
const isDashboardRoute = computed(() => currentRoute.path === '/')
const currentTitle = computed(() => currentRoute.meta.title || '当前页面')

const roleLabel = computed(() => {
  if (authStore.isInstructor) return '教官'
  if (authStore.isStudent) return '学员'
  return authStore.role || '已登录用户'
})

const now = new Date()
const hour = now.getHours()
const greetingText = hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好'
const weekdayText = new Intl.DateTimeFormat('zh-CN', { weekday: 'long' }).format(now)
const todayText = `${now.getMonth() + 1}月${now.getDate()}日 ${weekdayText}`

const overviewStats = computed<MetricItem[]>(() => [
  { label: '培训班级', value: '3', suffix: '个' },
  { label: '待办事项', value: '0', suffix: '个' },
  { label: '学习时长', value: formatMetric(authStore.currentUser?.study_hours), suffix: 'h' },
  { label: '考试次数', value: formatMetric(authStore.currentUser?.exam_count), suffix: '次' },
])

const quickActionConfigs: QuickAction[] = [
  {
    title: '班级列表',
    description: '查看训练班、时间安排与详情',
    path: '/classes',
    icon: ReadOutlined,
    background: 'var(--v2-cover-blue)',
    permissions: TRAINING_PERMISSIONS,
  },
  {
    title: '训练日历',
    description: '进入周训练计划与课程排期',
    path: '/classes/schedule',
    icon: CalendarOutlined,
    background: 'var(--v2-cover-green)',
    permissions: TRAINING_SCHEDULE_PERMISSIONS,
  },
  {
    title: '学习资源',
    description: '继续课程学习与资源浏览',
    path: '/resource/courses',
    icon: DatabaseOutlined,
    background: 'var(--v2-cover-purple)',
    permissions: COURSE_PERMISSIONS,
  },
  {
    title: '个人中心',
    description: '查看和维护当前登录账号信息',
    path: '/profile',
    icon: UserOutlined,
    background: 'var(--v2-cover-orange)',
    permissions: PROFILE_PERMISSIONS,
  },
]

const quickActions = computed(() => quickActionConfigs.filter((item) => authStore.hasAnyPermission(item.permissions)))

const identityCode = computed(() => authStore.currentUser?.police_id || authStore.currentUser?.username || '未设置警号')

const previewWeekDays = computed(() => {
  const today = dayjs()
  const weekStart = today.startOf('isoWeek')
  const datesWithEvents = new Set([
    ...calendarEvents.value.map((event) => event.date),
    ...examEvents.value
      .map((exam) => getExamDateKey(exam))
      .filter((dateKey): dateKey is string => Boolean(dateKey)),
  ])

  return Array.from({ length: 7 }, (_, index) => {
    const date = weekStart.add(index, 'day')
    const dateKey = date.format('YYYY-MM-DD')

    return {
      label: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][index],
      dateKey,
      displayDate: date.format('MM-DD'),
      isToday: date.isSame(today, 'day'),
      hasEvent: datesWithEvents.has(dateKey),
    }
  })
})

const calendarPreviewItems = computed<DashboardPreviewItem[]>(() => {
  const courseItems = calendarEvents.value
    .filter((event) => event.date === selectedPreviewDate.value)
    .map((event) => {
      const parsedRange = parseTimeRange(event.time_range)
      return {
        key: event.session_id || `${event.training_id}-${event.date}-${event.time_range}-${event.course_name}`,
        title: getEventTitle(event),
        timeLabel: parsedRange.timeLabel,
        primaryMeta: event.location || '地点待定',
        secondaryMeta: event.instructor || '教师待定',
        sortMin: parsedRange.startMin,
        palette: getPreviewPalette(event),
        path: '/classes/schedule',
      }
    })

  const examItems = examEvents.value
    .filter((exam) => getExamDateKey(exam) === selectedPreviewDate.value)
    .map((exam) => {
      const parsedRange = parseExamTime(exam)
      return {
        key: `exam-${exam.id}`,
        title: `考试：${exam.title || exam.paper_title || '未命名考试'}`,
        timeLabel: parsedRange.timeLabel,
        primaryMeta: '考试地点待定',
        secondaryMeta: '监考信息待定',
        sortMin: parsedRange.startMin,
        palette: getExamPalette(exam),
        path: '/exam/list',
      }
    })

  return [...courseItems, ...examItems]
    .sort((left, right) => left.sortMin - right.sortMin)
    .slice(0, 6)
})

function formatMetric(value: number | undefined) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '0'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function parseTimeRange(timeRange: string) {
  if (!timeRange || !timeRange.includes('~')) {
    return { startMin: Number.MAX_SAFE_INTEGER, timeLabel: '时间待定' }
  }

  const [start, end] = timeRange.split('~').map((part) => part.trim())
  const [startHour = 0, startMinute = 0] = start.split(':').map(Number)

  return {
    startMin: startHour * 60 + startMinute,
    timeLabel: `${start.slice(0, 5)} - ${end.slice(0, 5)}`,
  }
}

function getExamDateKey(exam: ExamResponse) {
  return exam.start_time ? dayjs(exam.start_time).format('YYYY-MM-DD') : ''
}

function parseExamTime(exam: ExamResponse) {
  if (!exam.start_time) {
    return { startMin: Number.MAX_SAFE_INTEGER, timeLabel: '考试时间待定' }
  }

  const start = dayjs(exam.start_time)
  const end = exam.end_time ? dayjs(exam.end_time) : start.add(exam.duration || 120, 'minute')

  return {
    startMin: start.hour() * 60 + start.minute(),
    timeLabel: `${start.format('HH:mm')} - ${end.format('HH:mm')}`,
  }
}

function getPreviewPalette(event: CalendarEventResponse) {
  const seed = `${event.course_name || ''}-${event.training_name || ''}-${event.course_type || ''}`
  let hash = 0

  for (let index = 0; index < seed.length; index += 1) {
    hash = (hash * 31 + seed.charCodeAt(index)) >>> 0
  }

  return previewPalette[hash % previewPalette.length]
}

function getExamPalette(exam: ExamResponse) {
  const seed = `${exam.title || ''}-${exam.training_name || ''}-${exam.type || ''}`
  let hash = 0

  for (let index = 0; index < seed.length; index += 1) {
    hash = (hash * 31 + seed.charCodeAt(index)) >>> 0
  }

  return previewPalette[(hash + 1) % previewPalette.length]
}

function getEventTitle(event: CalendarEventResponse) {
  return event.course_name?.trim() || event.training_name?.trim() || '未命名课程'
}

async function fetchDashboardCalendar() {
  if (!isDashboardRoute.value) return

  calendarLoading.value = true
  calendarError.value = ''

  try {
    const shouldLoadExams = authStore.hasAnyPermission(EXAM_LIST_PERMISSIONS)
    const calendarRequest = axiosInstance.get('/trainings/calendar')
    const examRequest = shouldLoadExams
      ? axiosInstance.get('/exams', { params: { page: 1, size: -1 } })
      : null

    const [calendarResult, examsResult] = await Promise.allSettled([
      calendarRequest,
      ...(examRequest ? [examRequest] : []),
    ])

    if (calendarResult.status === 'fulfilled') {
      calendarEvents.value = (calendarResult.value.data as CalendarEventResponse[]) || []
    } else {
      calendarEvents.value = []
      calendarError.value = calendarResult.reason instanceof Error ? calendarResult.reason.message : '课表暂时无法加载'
    }

    if (shouldLoadExams && examsResult?.status === 'fulfilled') {
      const examData = examsResult.value.data as { items?: ExamResponse[] }
      examEvents.value = examData.items || []
    } else {
      examEvents.value = []
    }
  } catch (error: unknown) {
    calendarEvents.value = []
    examEvents.value = []
    calendarError.value = error instanceof Error ? error.message : '课表暂时无法加载'
  } finally {
    calendarLoading.value = false
  }
}

function navigateTo(path: string) {
  router.push(path)
}

watch(
  previewWeekDays,
  (days) => {
    if (!days.some((day) => day.dateKey === selectedPreviewDate.value)) {
      const fallbackDay = days.find((day) => day.isToday) || days[0]
      if (fallbackDay) {
        selectedPreviewDate.value = fallbackDay.dateKey
      }
    }
  },
  { immediate: true },
)

watch(
  isDashboardRoute,
  (active) => {
    if (active) {
      void fetchDashboardCalendar()
    }
  },
  { immediate: true },
)
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  background:
    radial-gradient(circle at top right, rgba(75, 110, 245, 0.1), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.78) 0%, rgba(245, 246, 250, 0.92) 100%);
}

.hero-card {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.48fr) minmax(280px, 0.92fr);
  gap: 20px;
  padding: 24px 24px 22px;
  border-radius: 28px;
  overflow: hidden;
  background:
    radial-gradient(circle at 18% 22%, rgba(255, 255, 255, 0.24), transparent 18%),
    linear-gradient(135deg, #1c2a8f 0%, #2548d6 42%, #2b57f8 100%);
  color: var(--v2-text-white);
  box-shadow: 0 24px 40px rgba(29, 65, 194, 0.24);
}

.hero-card::before,
.hero-card::after {
  content: '';
  position: absolute;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
}

.hero-card::before {
  width: 208px;
  height: 208px;
  top: -104px;
  right: -50px;
}

.hero-card::after {
  width: 148px;
  height: 148px;
  right: 180px;
  bottom: -86px;
}

.hero-copy,
.hero-summary {
  position: relative;
  z-index: 1;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 12px;
  justify-content: center;
}

.hero-topline {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.hero-badge {
  display: inline-flex;
  width: fit-content;
  align-items: center;
  padding: 5px 12px;
  border-radius: var(--v2-radius-full);
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.14);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.hero-date-pill {
  display: inline-flex;
  width: fit-content;
  align-items: center;
  gap: 7px;
  padding: 7px 14px;
  border-radius: var(--v2-radius-full);
  background: rgba(133, 164, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: rgba(255, 255, 255, 0.96);
  font-size: 13px;
  font-weight: 600;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.hero-title {
  font-size: clamp(26px, 2.8vw, 38px);
  line-height: 1.1;
  margin: 0;
}

.hero-profile-list {
  display: inline-flex;
  width: fit-content;
  max-width: 100%;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 9px 16px;
  border-radius: 18px;
  background: rgba(17, 34, 99, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(16px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.hero-profile-list,
.hero-profile-list span,
.hero-profile-list strong {
  font-size: 14px;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.98);
}

.hero-profile-list strong {
  font-weight: 700;
}

.hero-profile-divider {
  color: rgba(255, 255, 255, 0.56);
  font-weight: 500;
}

.hero-profile-list span,
.hero-profile-list strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hero-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.summary-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 102px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(16px);
}

.summary-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.66);
  letter-spacing: 0.06em;
}

.summary-value {
  font-size: 28px;
  line-height: 1;
  font-weight: 700;
}

.summary-value small {
  font-size: 14px;
  margin-left: 4px;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
}

.dashboard-workbench {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(380px, 0.92fr);
  gap: 20px;
  align-items: stretch;
}

.surface-card {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 24px;
  padding: 24px;
  box-shadow: var(--v2-shadow);
  backdrop-filter: blur(16px);
  height: 100%;
}

.mini-schedule-card,
.quick-surface {
  display: flex;
  flex-direction: column;
  min-height: 344px;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.section-head h2 {
  font-size: 18px;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 6px;
}

.section-head p {
  color: var(--v2-text-secondary);
  line-height: 1.7;
}

.section-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  border-radius: var(--v2-radius-full);
  background: rgba(75, 110, 245, 0.1);
  color: var(--v2-primary);
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, background 0.2s ease;
}

.section-link:hover {
  background: rgba(75, 110, 245, 0.16);
  transform: translateY(-1px);
}

.mini-week-strip {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.mini-day-pill {
  appearance: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 8px;
  border-radius: 16px;
  border: 1px solid rgba(231, 234, 242, 0.9);
  background: linear-gradient(180deg, rgba(248, 249, 253, 0.94) 0%, rgba(255, 255, 255, 0.98) 100%);
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.mini-day-pill:hover {
  transform: translateY(-1px);
  border-color: rgba(75, 110, 245, 0.24);
}

.mini-day-pill span {
  font-size: 12px;
  color: var(--v2-text-secondary);
}

.mini-day-pill strong {
  font-size: 14px;
  color: var(--v2-text-primary);
}

.mini-day-pill.has-event {
  border-color: rgba(75, 110, 245, 0.18);
}

.mini-day-pill.today {
  background: linear-gradient(180deg, rgba(75, 110, 245, 0.1) 0%, rgba(255, 255, 255, 0.98) 100%);
}

.mini-day-pill.selected {
  border-color: rgba(75, 110, 245, 0.32);
  background: linear-gradient(180deg, rgba(236, 241, 255, 1) 0%, rgba(248, 250, 255, 0.98) 100%);
  box-shadow:
    inset 0 0 0 1px rgba(75, 110, 245, 0.14),
    0 10px 18px rgba(75, 110, 245, 0.08);
}

.mini-day-pill.selected span,
.mini-day-pill.selected strong {
  color: var(--v2-primary);
}

.mini-event-list {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 10px;
}

.mini-event-item {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(120px, 0.9fr);
  align-items: center;
  gap: 12px;
  padding: 14px 16px 14px 20px;
  border: 1px solid rgba(233, 236, 243, 0.96);
  border-radius: 18px;
  background: linear-gradient(135deg, var(--mini-event-bg-start) 0%, var(--mini-event-bg-end) 100%);
  box-shadow: 0 12px 22px rgba(36, 42, 71, 0.05);
  text-align: left;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.mini-event-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 12px;
  bottom: 12px;
  width: 5px;
  border-radius: 10px;
  background: var(--mini-event-border);
}

.mini-event-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 18px 28px rgba(36, 42, 71, 0.08);
}

.mini-event-main,
.mini-event-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.mini-event-main strong {
  font-size: 15px;
  color: var(--v2-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mini-event-main > span,
.mini-event-meta-row > span {
  font-size: 13px;
  color: var(--v2-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mini-event-meta {
  align-items: flex-end;
}

.mini-event-meta-row {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  min-width: 0;
}

.mini-event-meta-icon {
  flex-shrink: 0;
  font-size: 12px;
  color: rgba(120, 129, 150, 0.82);
}

.mini-state {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 220px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(248, 249, 253, 0.94) 0%, rgba(255, 255, 255, 0.98) 100%);
  color: var(--v2-text-secondary);
}

.mini-empty {
  font-size: 14px;
}

.mini-empty :deep(.anticon) {
  font-size: 18px;
  color: var(--v2-primary);
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.quick-grid-compact {
  flex: 1;
  align-content: stretch;
  grid-auto-rows: minmax(0, 1fr);
}

.quick-item {
  display: flex;
  align-items: center;
  gap: 14px;
  height: 100%;
  padding: 15px;
  border: 1px solid rgba(229, 229, 234, 0.9);
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(245, 246, 250, 0.92) 100%);
  text-align: left;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.quick-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--v2-shadow-lg);
  border-color: rgba(75, 110, 245, 0.18);
}

.quick-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: 15px;
  color: rgba(255, 255, 255, 0.98);
  font-size: 21px;
  flex-shrink: 0;
  box-shadow:
    0 10px 20px rgba(75, 110, 245, 0.16),
    0 0 0 1px rgba(255, 255, 255, 0.22) inset;
}

.quick-text {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.quick-text strong {
  font-size: 15px;
  color: var(--v2-text-primary);
}

.quick-text span {
  font-size: 13px;
  color: var(--v2-text-secondary);
  line-height: 1.6;
}

.quick-arrow {
  color: var(--v2-text-muted);
  font-size: 13px;
  flex-shrink: 0;
}

.placeholder-card {
  min-height: 320px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 18px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(240, 243, 255, 0.92) 100%),
    var(--v2-bg-card);
}

.placeholder-badge {
  background: var(--v2-primary-light);
  border-color: transparent;
  color: var(--v2-primary);
}

.placeholder-title {
  font-size: clamp(28px, 3vw, 40px);
  line-height: 1.1;
}

.placeholder-text {
  max-width: 760px;
  color: var(--v2-text-secondary);
  line-height: 1.8;
}

.placeholder-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

@media (max-width: 1200px) {
  .hero-card,
  .dashboard-workbench {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-page {
    gap: 16px;
  }

  .hero-card,
  .surface-card {
    padding: 18px;
    border-radius: 20px;
  }

  .hero-summary,
  .quick-grid {
    grid-template-columns: 1fr;
  }

  .mini-week-strip {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .mini-event-item {
    grid-template-columns: 1fr;
  }

  .mini-event-meta {
    align-items: flex-start;
  }

  .hero-profile-list {
    width: 100%;
  }

  .summary-card {
    min-height: 96px;
  }

  .quick-item,
  .mini-event-item {
    padding: 14px;
  }

  .placeholder-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
