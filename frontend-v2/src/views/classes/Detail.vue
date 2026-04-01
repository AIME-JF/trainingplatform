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
            <a-button v-if="canEnroll" type="primary" @click="handleEnroll">
              {{ detail.enrollment_requires_approval ? '报名申请' : '加入班级' }}
            </a-button>
            <a-button v-if="detail.current_enrollment_status === 'pending'" disabled>
              <ClockCircleOutlined /> 待审核
            </a-button>
            <a-button v-if="detail.current_enrollment_status === 'rejected'" disabled danger>
              审核未通过
            </a-button>
            <a-button v-if="isEnrolled && hasActiveCheckin" type="primary" @click="goCheckin">
              <CheckCircleOutlined /> 签到
            </a-button>
            <a-button v-if="isEnrolled && hasActiveCheckout" @click="goCheckout">
              签退评课
            </a-button>
          </template>

          <!-- 教官按钮 -->
          <template v-if="authStore.isInstructor">
            <a-button v-if="hasActiveCheckin" type="primary" @click="goCheckin">
              <CheckCircleOutlined /> 签到
            </a-button>
            <a-button v-if="hasActiveCheckout" @click="goCheckout">
              签退
            </a-button>
          </template>

          <!-- 通用按钮 -->
          <a-button v-if="hasFullAccess && (isEnrolled || authStore.isInstructor)" @click="activeTab = 'schedule'">
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

          <!-- ========== 概览 ========== -->
          <div v-if="activeTab === 'overview'" class="tab-panel">

            <!-- 最近课次（仅本班人员可见） -->
            <div v-if="hasFullAccess && upcomingSessions.length" class="overview-section">
              <h3 class="section-label">最近课程</h3>
              <div class="upcoming-list">
                <div v-for="s in upcomingSessions" :key="s.key" class="upcoming-item">
                  <div class="upcoming-date-col">
                    <span class="upcoming-day">{{ s.dayNum }}</span>
                    <span class="upcoming-weekday">{{ s.weekday }}</span>
                  </div>
                  <div class="upcoming-body">
                    <div class="upcoming-header">
                      <strong class="upcoming-course">{{ s.courseName }}</strong>
                      <a-tag :color="s.courseType === 'practice' ? 'green' : 'blue'" size="small">
                        {{ s.courseType === 'practice' ? '实操' : '理论' }}
                      </a-tag>
                    </div>
                    <div class="upcoming-meta">
                      <span><ClockCircleOutlined /> {{ s.timeRange }}</span>
                      <span v-if="s.location"><EnvironmentOutlined /> {{ s.location }}</span>
                      <span v-if="s.instructor"><UserOutlined /> {{ s.instructor }}</span>
                    </div>
                  </div>
                  <a-tag v-if="s.status && s.status !== 'pending'" size="small">{{ sessionStatusLabel(s.status) }}</a-tag>
                </div>
              </div>
            </div>

            <!-- 班级简介（始终显示） -->
            <div class="overview-section">
              <h3 class="section-label">班级简介</h3>
              <p v-if="detail.description" class="overview-desc-text">{{ detail.description }}</p>
              <p v-else class="overview-desc-empty">暂无简介</p>
            </div>

            <!-- 公告通知（仅本班人员可见） -->
            <div v-if="hasFullAccess" class="overview-section">
              <div class="section-header">
                <h3 class="section-label">公告通知</h3>
                <a-button v-if="canPublishNotice" size="small" type="primary" @click="openNoticeForm()">
                  <PlusOutlined /> 发布公告
                </a-button>
              </div>
              <a-empty v-if="!detail.notices?.length" description="暂无公告" :image="simpleImage" />
              <div v-else class="notice-list">
                <div
                  v-for="n in detail.notices"
                  :key="n.id"
                  class="notice-card"
                  @click="openNoticeDetail(n)"
                >
                  <div class="notice-card-main">
                    <h4 class="notice-card-title">{{ n.title }}</h4>
                    <p class="notice-card-summary">{{ truncate(n.content, 60) }}</p>
                  </div>
                  <div class="notice-card-side">
                    <span class="notice-card-author" v-if="n.author_name">{{ n.author_name }}</span>
                    <span class="notice-card-time">{{ formatDate(n.created_at) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ========== 课表 ========== -->
          <div v-if="activeTab === 'schedule'" class="tab-panel">
            <!-- 课表统计 -->
            <div v-if="detail.courses?.length" class="sched-stats">
              <div class="sched-stat">
                <span class="sched-stat-num">{{ detail.courses.length }}</span>
                <span class="sched-stat-label">门课程</span>
              </div>
              <div class="sched-stat">
                <span class="sched-stat-num">{{ totalSessions }}</span>
                <span class="sched-stat-label">个课次</span>
              </div>
              <div class="sched-stat">
                <span class="sched-stat-num">{{ totalHours }}</span>
                <span class="sched-stat-label">总课时</span>
              </div>
            </div>

            <a-empty v-if="!detail.courses?.length" description="暂无课程安排" />
            <div v-else class="sched-course-list">
              <div
                v-for="course in detail.courses"
                :key="course.course_key || course.name"
                class="sched-course-card"
                :class="`sched-type-${course.type || 'theory'}`"
              >
                <!-- 课程头 -->
                <div class="sched-course-top">
                  <div class="sched-course-info">
                    <h4 class="sched-course-name">{{ course.name }}</h4>
                    <div class="sched-course-meta">
                      <a-tag :color="course.type === 'practice' ? 'green' : 'blue'" size="small">
                        {{ course.type === 'practice' ? '实操' : '理论' }}
                      </a-tag>
                      <span v-if="course.instructor"><UserOutlined /> {{ course.instructor }}</span>
                      <span v-if="course.hours"><ClockCircleOutlined /> {{ course.hours }} 课时</span>
                      <span>共 {{ (course.schedules || []).length }} 个课次</span>
                    </div>
                  </div>
                </div>

                <!-- 课次时间线 -->
                <div v-if="course.schedules?.length" class="sched-timeline">
                  <div
                    v-for="(s, i) in course.schedules"
                    :key="i"
                    class="sched-session"
                    :class="{ 'is-past': isSessionPast(s), 'is-active': isSessionActive(s) }"
                  >
                    <div class="sched-dot-line">
                      <span class="sched-dot" />
                      <span v-if="i < course.schedules.length - 1" class="sched-line" />
                    </div>
                    <div class="sched-session-body">
                      <div class="sched-session-row">
                        <strong class="sched-session-date">{{ formatSessionDate(s.date) }}</strong>
                        <span class="sched-session-time">{{ s.time_range?.replace('~', ' - ') }}</span>
                        <a-tag v-if="s.status && s.status !== 'pending'" size="small" :color="sessionTagColor(s.status)">
                          {{ sessionStatusLabel(s.status) }}
                        </a-tag>
                      </div>
                      <div v-if="s.location" class="sched-session-location">
                        <EnvironmentOutlined /> {{ s.location }}
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="sched-no-session">暂无排课</div>
              </div>
            </div>
          </div>

          <!-- ========== 考试 ========== -->
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

          <!-- ========== 学员名单 ========== -->
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
                <span class="student-checkin-rate" :class="checkinRateClass(s.checkin_rate)">
                  {{ formatCheckinRate(s.checkin_rate) }}
                </span>
                <a-tag v-if="s.status && s.status !== 'approved'" size="small" :color="s.status === 'pending' ? 'orange' : 'red'">
                  {{ enrollStatusLabel(s.status) }}
                </a-tag>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ====== 公告详情弹窗 ====== -->
      <a-modal v-model:open="noticeDetailVisible" :title="noticeDetailData?.title" :footer="null" width="560px">
        <div v-if="noticeDetailData" class="notice-detail-modal">
          <div class="notice-detail-meta">
            <span v-if="noticeDetailData.author_name">{{ noticeDetailData.author_name }}</span>
            <span>{{ formatDateTime(noticeDetailData.created_at) }}</span>
          </div>
          <div class="notice-detail-content">{{ noticeDetailData.content }}</div>
        </div>
      </a-modal>

      <!-- ====== 发布/编辑公告弹窗 ====== -->
      <a-modal
        v-model:open="noticeFormVisible"
        :title="noticeFormId ? '编辑公告' : '发布公告'"
        @ok="handleNoticeSubmit"
        :confirm-loading="noticeSubmitting"
        ok-text="发布"
      >
        <a-form layout="vertical" style="margin-top: 16px">
          <a-form-item label="标题" required>
            <a-input v-model:value="noticeForm.title" placeholder="请输入公告标题" :maxlength="200" />
          </a-form-item>
          <a-form-item label="内容" required>
            <a-textarea v-model:value="noticeForm.content" placeholder="请输入公告内容" :rows="5" />
          </a-form-item>
        </a-form>
      </a-modal>
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
  PlusOutlined,
} from '@ant-design/icons-vue'
import { Empty, message } from 'ant-design-vue'
import dayjs from 'dayjs'
import axiosInstance from '@/api/custom-instance'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const activeTab = ref('overview')
const simpleImage = Empty.PRESENTED_IMAGE_SIMPLE

// ---- interfaces ----

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
  checkin_rate?: number | null
}

interface NoticeItem {
  id: number
  title: string
  content?: string
  author_name?: string
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

// ---- 公告相关 ----
const noticeDetailVisible = ref(false)
const noticeDetailData = ref<NoticeItem | null>(null)
const noticeFormVisible = ref(false)
const noticeFormId = ref<number | null>(null)
const noticeSubmitting = ref(false)
const noticeForm = ref({ title: '', content: '' })

// ---- computed ----

const filteredStudents = computed(() => {
  const list = detail.value?.students || []
  const kw = studentSearch.value.trim().toLowerCase()
  if (!kw) return list
  return list.filter((s) => {
    const name = (s.user_nickname || s.user_name || '').toLowerCase()
    return name.includes(kw)
  })
})

const statusLabels: Record<string, string> = {
  upcoming: '未开始',
  active: '进行中',
  ended: '已结束',
}

const isEnrolled = computed(() => detail.value?.current_enrollment_status === 'approved')

const canEnroll = computed(() => {
  const d = detail.value
  if (!d) return false
  if (d.current_enrollment_status) return false
  if (d.status === 'ended') return false
  if (d.publish_status !== 'published') return false
  if (d.is_locked) return false
  return true
})

const hasActiveCheckin = computed(() => detail.value?.current_session?.status === 'checkin_open')
const hasActiveCheckout = computed(() => detail.value?.current_session?.status === 'checkout_open')

// 判断当前用户是否有完整访问权限（后端对非相关用户返回空课表/通知）
const hasFullAccess = computed(() => {
  const d = detail.value
  if (!d) return false
  return !!(d.courses?.length || d.notices?.length || d.exam_sessions?.length || isEnrolled.value)
})

// 教官可以在班级内发布公告（且需要有完整访问权限）
const canPublishNotice = computed(() => authStore.isInstructor && hasFullAccess.value)

// 课表统计
const totalSessions = computed(() =>
  (detail.value?.courses || []).reduce((sum, c) => sum + (c.schedules || []).length, 0),
)
const totalHours = computed(() => {
  const h = (detail.value?.courses || []).reduce((sum, c) => sum + (c.hours || 0), 0)
  return Number.isInteger(h) ? h : h.toFixed(1)
})

function isSessionPast(s: ScheduleItem): boolean {
  if (!s.date) return false
  return s.date < dayjs().format('YYYY-MM-DD')
}

function isSessionActive(s: ScheduleItem): boolean {
  if (!s.status) return false
  return ['checkin_open', 'checkin_closed', 'checkout_open'].includes(s.status)
}

function formatSessionDate(date: string | undefined): string {
  if (!date) return '-'
  const d = dayjs(date)
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${d.format('MM/DD')} ${weekdays[d.day()]}`
}

function sessionTagColor(status: string): string {
  const map: Record<string, string> = {
    checkin_open: 'processing', checkin_closed: 'processing', checkout_open: 'warning',
    completed: 'success', skipped: 'default', missed: 'error',
  }
  return map[status] || 'default'
}

const visibleTabs = computed(() => {
  if (!hasFullAccess.value) {
    return [{ key: 'overview', label: '概览' }]
  }
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

// 最近课次：从所有课程的 schedules 中展开，取当天及之后最近 5 条
interface UpcomingSession {
  key: string
  courseName: string
  courseType: string
  date: string
  dayNum: string
  weekday: string
  timeRange: string
  location: string
  instructor: string
  status: string
}

const upcomingSessions = computed<UpcomingSession[]>(() => {
  if (!detail.value?.courses?.length) return []
  const today = dayjs().format('YYYY-MM-DD')
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  const items: UpcomingSession[] = []

  for (const course of detail.value.courses) {
    for (const s of course.schedules || []) {
      if (!s.date || s.date < today) continue
      const d = dayjs(s.date)
      items.push({
        key: `${course.course_key || course.name}-${s.session_id || s.date}-${s.time_range}`,
        courseName: course.name,
        courseType: course.type || 'theory',
        date: s.date,
        dayNum: String(d.date()),
        weekday: weekdays[d.day()],
        timeRange: s.time_range?.replace('~', ' - ') || '',
        location: s.location || course.instructor || '',
        instructor: course.instructor || '',
        status: s.status || 'pending',
      })
    }
  }

  items.sort((a, b) => `${a.date} ${a.timeRange}`.localeCompare(`${b.date} ${b.timeRange}`))
  return items.slice(0, 5)
})

// ---- methods ----

function studentDisplayName(s: StudentItem): string {
  return s.user_nickname || s.user_name || String(s.user_id)
}

function formatCheckinRate(rate: number | null | undefined): string {
  if (rate === null || rate === undefined) return '-'
  return `${Math.round(rate * 100)}%`
}

function checkinRateClass(rate: number | null | undefined): string {
  if (rate === null || rate === undefined) return 'rate-na'
  if (rate >= 0.9) return 'rate-good'
  if (rate >= 0.6) return 'rate-warn'
  return 'rate-bad'
}

function sessionStatusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待开始', checkin_open: '签到中', checkin_closed: '进行中',
    checkout_open: '签退中', completed: '已完成', skipped: '已跳过', missed: '已缺课',
  }
  return map[status] || status
}

function enrollStatusLabel(status: string): string {
  const map: Record<string, string> = { approved: '已通过', pending: '待审核', rejected: '未通过' }
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

function truncate(text: string | undefined | null, len: number): string {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}

function handleEnroll() { router.push(`/classes/${route.params.id}/enroll`) }
function goCheckin() { router.push(`/classes/${route.params.id}/checkin`) }
function goCheckout() { router.push(`/classes/${route.params.id}/checkout`) }
function goHistory() { message.info('训历功能即将上线') }
function goExam(examId: number) { router.push(`/exam/do/${examId}`) }

// 公告详情弹窗
function openNoticeDetail(n: NoticeItem) {
  noticeDetailData.value = n
  noticeDetailVisible.value = true
}

// 发布公告
function openNoticeForm() {
  noticeFormId.value = null
  noticeForm.value = { title: '', content: '' }
  noticeFormVisible.value = true
}

async function handleNoticeSubmit() {
  if (!noticeForm.value.title.trim() || !noticeForm.value.content.trim()) {
    message.warning('请填写标题和内容')
    return
  }
  noticeSubmitting.value = true
  try {
    const payload = {
      title: noticeForm.value.title.trim(),
      content: noticeForm.value.content.trim(),
      type: 'training',
      training_id: Number(route.params.id),
    }
    await axiosInstance.post('/notices', payload)
    message.success('公告发布成功')
    noticeFormVisible.value = false
    await fetchDetail()
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '发布失败')
  } finally {
    noticeSubmitting.value = false
  }
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

/* -- 右侧信息卡片 -- */
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

.info-card:hover { background: rgba(255, 255, 255, 0.12); }

.info-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.info-card--status { flex: 1.6; min-width: 180px; }

.info-card-extra {
  margin-top: 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  display: flex;
  gap: 4px;
}

.info-card-label { font-size: 12px; color: rgba(255, 255, 255, 0.5); }

.info-card-badge {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: var(--v2-radius-full);
}

.badge-upcoming { background: rgba(75, 110, 245, 0.25); color: #8DA6F8; }
.badge-active   { background: rgba(52, 199, 89, 0.25);  color: #6EE49A; }
.badge-ended    { background: rgba(255, 255, 255, 0.1);  color: rgba(255, 255, 255, 0.4); }

.info-card-num { font-size: 18px; font-weight: 600; color: #fff; }
.info-unit { font-size: 12px; font-weight: 400; color: rgba(255, 255, 255, 0.45); }

/* ====== 主体 ====== */
.detail-body { padding-top: 20px; }

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

.tab-panel { padding: 20px; min-height: 200px; }

/* ====== 概览 ====== */
.overview-section { margin-bottom: 28px; }
.overview-section:last-child { margin-bottom: 0; }

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-header .section-label { margin-bottom: 0; }

.section-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin-bottom: 12px;
}

.overview-desc-text {
  white-space: pre-wrap;
  color: var(--v2-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.overview-desc-empty {
  color: var(--v2-text-muted);
  font-size: 14px;
}

/* -- 最近课次 -- */
.upcoming-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.upcoming-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  border-radius: var(--v2-radius-sm);
  background: var(--v2-bg);
  transition: background 0.15s;
}

.upcoming-item:hover { background: var(--v2-primary-light); }

.upcoming-date-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 40px;
}

.upcoming-day {
  font-size: 20px;
  font-weight: 700;
  color: var(--v2-text-primary);
  line-height: 1;
}

.upcoming-weekday {
  font-size: 11px;
  color: var(--v2-text-muted);
  margin-top: 2px;
}

.upcoming-body { flex: 1; min-width: 0; }

.upcoming-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.upcoming-course {
  font-size: 14px;
  color: var(--v2-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upcoming-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--v2-text-muted);
  flex-wrap: wrap;
}

.upcoming-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* -- 公告卡片 -- */
.notice-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.notice-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-radius: var(--v2-radius-sm);
  border: 1px solid var(--v2-border-light);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.notice-card:hover {
  background: var(--v2-bg);
  border-color: var(--v2-border);
}

.notice-card-main { flex: 1; min-width: 0; }

.notice-card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin: 0 0 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notice-card-summary {
  font-size: 13px;
  color: var(--v2-text-muted);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notice-card-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}

.notice-card-author { font-size: 12px; color: var(--v2-text-secondary); }
.notice-card-time { font-size: 11px; color: var(--v2-text-muted); }

/* -- 公告详情弹窗 -- */
.notice-detail-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: var(--v2-text-muted);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--v2-border-light);
}

.notice-detail-content {
  font-size: 14px;
  color: var(--v2-text-primary);
  line-height: 1.8;
  white-space: pre-wrap;
}

/* ====== 课表 ====== */
.sched-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.sched-stat {
  display: flex;
  align-items: baseline;
  gap: 4px;
  padding: 10px 16px;
  border-radius: var(--v2-radius-sm);
  background: var(--v2-bg);
}

.sched-stat-num { font-size: 20px; font-weight: 700; color: var(--v2-primary); }
.sched-stat-label { font-size: 12px; color: var(--v2-text-muted); }

.sched-course-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sched-course-card {
  border-radius: var(--v2-radius);
  border: 1px solid var(--v2-border-light);
  overflow: hidden;
}

.sched-course-top {
  padding: 16px 18px;
  border-bottom: 1px solid var(--v2-border-light);
}

.sched-type-theory .sched-course-top { background: linear-gradient(135deg, rgba(75,110,245,0.04) 0%, transparent 100%); }
.sched-type-practice .sched-course-top { background: linear-gradient(135deg, rgba(52,199,89,0.04) 0%, transparent 100%); }

.sched-course-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin: 0 0 8px;
}

.sched-course-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 12px;
  color: var(--v2-text-muted);
  flex-wrap: wrap;
}

.sched-course-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* -- 时间线 -- */
.sched-timeline {
  padding: 16px 18px 12px;
}

.sched-session {
  display: flex;
  gap: 14px;
  position: relative;
}

.sched-dot-line {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 12px;
  flex-shrink: 0;
  padding-top: 6px;
}

.sched-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--v2-border);
  flex-shrink: 0;
  z-index: 1;
}

.sched-session.is-active .sched-dot {
  background: var(--v2-primary);
  box-shadow: 0 0 0 3px rgba(75,110,245,0.2);
}

.sched-session.is-past .sched-dot { background: var(--v2-text-muted); }

.sched-line {
  width: 1px;
  flex: 1;
  background: var(--v2-border-light);
  margin: 4px 0;
}

.sched-session-body {
  flex: 1;
  padding-bottom: 16px;
  min-width: 0;
}

.sched-session:last-child .sched-session-body { padding-bottom: 4px; }

.sched-session-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 2px;
}

.sched-session-date {
  font-size: 14px;
  color: var(--v2-text-primary);
  min-width: 90px;
}

.sched-session.is-past .sched-session-date { color: var(--v2-text-muted); }

.sched-session-time {
  font-size: 13px;
  color: var(--v2-text-secondary);
  min-width: 110px;
  font-variant-numeric: tabular-nums;
}

.sched-session.is-past .sched-session-time { color: var(--v2-text-muted); }

.sched-session-location {
  font-size: 12px;
  color: var(--v2-text-muted);
  display: flex;
  align-items: center;
  gap: 4px;
}

.sched-no-session {
  padding: 20px 18px;
  font-size: 13px;
  color: var(--v2-text-muted);
  text-align: center;
}

@media (max-width: 768px) {
  .sched-stats { flex-wrap: wrap; }
  .sched-stat { flex: 1; min-width: 80px; }
}

/* ====== 考试 ====== */
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

/* ====== 学员名单 ====== */
.student-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 12px;
}

.student-count { font-size: 13px; color: var(--v2-text-muted); white-space: nowrap; }

.student-list { display: flex; flex-direction: column; }

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

.student-avatar { background: var(--v2-primary); color: #fff; font-size: 13px; flex-shrink: 0; }

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

.student-checkin-rate {
  font-size: 13px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  min-width: 40px;
  text-align: right;
  flex-shrink: 0;
}

.rate-na { color: var(--v2-text-muted); }
.rate-good { color: var(--v2-success); }
.rate-warn { color: var(--v2-warning); }
.rate-bad { color: var(--v2-danger); }
</style>
