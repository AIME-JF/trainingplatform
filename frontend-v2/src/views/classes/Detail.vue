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
            <p v-if="detail.description" class="header-desc">{{ detail.description }}</p>
          </div>

          <!-- 右侧快捷信息卡片 -->
          <div class="header-cards">
            <div class="info-card info-card--status">
              <div class="info-card-top">
                <span class="info-card-label">班级状态</span>
                <span class="info-card-badge" :class="'badge-' + detail.status">{{ statusLabels[detail.status!] || detail.status }}</span>
              </div>
              <div class="info-card-num">{{ detail.training_type_name || detail.type || '-' }}</div>
              <div class="info-card-extra">
                <span>{{ detail.enrolled_count ?? 0 }}{{ detail.capacity ? '/' + detail.capacity : '' }} 人已报名</span>
                <span v-if="detail.is_locked">· 名单已锁定</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <!-- ====== 主体内容 ====== -->
      <section class="page-content detail-body">

        <!-- 操作按钮区 -->
        <div class="action-bar">
          <!-- 通用按钮 -->
          <a-button v-if="hasFullAccess && (isEnrolled || isClassInstructor)" @click="router.push(`/classes/schedule/${detail.id}`)">
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

            <!-- 非班级成员引导 -->
            <div v-if="showEnrollHint" class="join-hint-card">
              <div class="join-hint-icon"><TeamOutlined /></div>
              <p class="join-hint-title">加入班级查看更多内容</p>
              <p class="join-hint-desc">加入后可查看课程安排、课次签到、考试、动态等完整信息</p>
              <a-button v-if="canEnroll" type="primary" @click="enrollModalVisible = true">
                {{ detail.enrollment_requires_approval ? '报名申请' : '加入班级' }}
              </a-button>
              <a-button v-else-if="detail.current_enrollment_status === 'pending'" disabled>
                <ClockCircleOutlined /> 报名审核中
              </a-button>
              <a-button v-else-if="detail.current_enrollment_status === 'rejected'" disabled danger>
                审核未通过
              </a-button>
            </div>

            <!-- 当前/下一节课次 -->
            <div v-if="hasFullAccess && currentSession" class="overview-section">
              <h3 class="section-label">
                {{ isSessionActive ? '正在进行' : '下一节课' }}
              </h3>
              <CurrentSessionCard
                :session="currentSession"
                :is-instructor="isClassInstructor"
                :is-student="authStore.isStudent"
                :is-enrolled="isEnrolled"
                :has-checked-in="hasCheckedIn"
                :has-checked-out="hasCheckedOut"
                @open-checkin-mgr="checkinMgrVisible = true"
                @open-checkout-mgr="checkoutMgrVisible = true"
                @student-checkin="studentCheckinVisible = true"
                @student-checkout="studentCheckoutVisible = true"
                @student-scan-qr="openQrScanner"
                @gesture-checkin="showGestureCheckin = true"
                @gesture-checkout="showGestureCheckout = true"
              />
            </div>

            <!-- 最近动态 -->
            <div v-if="hasFullAccess" class="overview-section">
              <h3 class="section-label">最近动态</h3>
              <ActivityFeed
                :training-id="detail.id"
                :has-full-access="hasFullAccess"
                :is-student="authStore.isStudent"
                :is-enrolled="isEnrolled"
                :is-class-instructor="isClassInstructor"
                :has-active-checkin="hasActiveCheckin"
                :has-active-checkout="hasActiveCheckout"
                :has-checked-in="hasCheckedIn"
                :has-checked-out="hasCheckedOut"
                :checkin-mode="currentSession?.checkin_mode ?? null"
                :checkout-mode="currentSession?.checkout_mode ?? null"
                :pending-enrollments="pendingEnrollments"
                @student-checkin="studentCheckinVisible = true"
                @student-checkout="studentCheckoutVisible = true"
                @student-scan-qr="openQrScanner"
                @gesture-checkin="showGestureCheckin = true"
                @gesture-checkout="showGestureCheckout = true"
              />
            </div>

            <!-- 公告 -->
            <div v-if="hasFullAccess" class="overview-section">
              <NoticeList
                :notices="notices"
                :can-publish="canPublishNotice"
                :training-id="detail.id"
                @refresh="fetchNotices"
              />
            </div>
          </div>

          <!-- ========== 课程 ========== -->
          <div v-if="activeTab === 'schedule'" class="tab-panel">
            <CourseScheduleTab :courses="courses" />
          </div>

          <!-- ========== 资源 ========== -->
          <div v-if="activeTab === 'resources'" class="tab-panel">
            <ClassResourcesTab
              :courses="courses"
              :active="activeTab === 'resources'"
              :legacy-resources="detail?.resources || []"
            />
          </div>

          <!-- ========== 考试 ========== -->
          <div v-if="activeTab === 'exam'" class="tab-panel">
            <a-empty v-if="!detail.exam_sessions?.length" description="暂无考试安排" />
            <div v-else class="exam-list">
              <div v-for="exam in detail.exam_sessions" :key="exam.id" class="exam-row">
                <div class="exam-info">
                  <span class="exam-title">{{ exam.title || '考试' }}</span>
                  <span class="exam-time">{{ formatDateTime(exam.start_time) }}</span>
                </div>
                <a-button
                  size="small"
                  :type="authStore.isStudent && canTakeExam(exam) ? 'primary' : 'default'"
                  @click="goExamOverview(exam.id)"
                >
                  {{ authStore.isStudent && canTakeExam(exam) ? '参加考试' : '查看详情' }}
                </a-button>
              </div>
            </div>
          </div>

          <!-- ========== 学员名单 ========== -->
          <div v-if="activeTab === 'students'" class="tab-panel">
            <div v-if="students.length" class="student-toolbar">
              <a-input-search
                v-model:value="studentSearch"
                placeholder="搜索学员姓名"
                style="width: 220px"
                allow-clear
              />
              <span class="student-count">共 {{ filteredStudents.length }} 人</span>
            </div>
            <a-empty v-if="!students.length" description="暂无学员" />
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

      <!-- ====== 弹窗组件 ====== -->
      <CheckinManager
        v-model:visible="checkinMgrVisible"
        :training-id="detail.id"
        :session="currentSession"
        :students="students"
        @detail-updated="onCheckinManagerUpdated"
        @gesture-pattern-set="fetchDetail"
      />

      <CheckoutManager
        v-model:visible="checkoutMgrVisible"
        :training-id="detail.id"
        :session="currentSession"
        :students="students"
        @detail-updated="onCheckoutManagerUpdated"
      />

      <StudentCheckinConfirm
        v-model:visible="studentCheckinVisible"
        :training-id="detail.id"
        :session="currentSession"
        @refresh="onCheckinSuccess"
      />

      <StudentCheckoutConfirm
        v-model:visible="studentCheckoutVisible"
        :training-id="detail.id"
        :session="currentSession"
        @refresh="onCheckoutSuccess"
      />

      <!-- QrScannerModal hidden: replaced by gesture check-in
      <QrScannerModal
        v-model:visible="qrScannerVisible"
        :action="qrScannerAction"
        @refresh="fetchDetail"
      />
      -->

      <StudentGestureCheckin
        v-model:open="showGestureCheckin"
        :training-id="detail.id"
        :training-name="detail?.name || ''"
        :session="currentSession"
        :gesture-pattern="checkinGesturePattern"
        @success="onCheckinSuccess"
      />

      <StudentGestureCheckin
        v-model:open="showGestureCheckout"
        :training-id="detail.id"
        :training-name="detail?.name || ''"
        :session="currentSession"
        :gesture-pattern="checkoutGesturePattern"
        :is-checkout="true"
        @success="onCheckoutSuccess"
      />

      <!-- 报名弹窗 -->
      <a-modal
        v-model:open="enrollModalVisible"
        :title="detail.enrollment_requires_approval ? '报名申请' : '加入班级'"
        :confirm-loading="enrollSubmitting"
        ok-text="提交申请"
        centered
        width="480px"
        @ok="handleEnroll"
      >
        <div class="enroll-modal-info">
          <p class="enroll-class-name">{{ detail.name }}</p>
          <div class="enroll-meta">
            <span v-if="detail.start_date"><CalendarOutlined /> {{ detail.start_date?.slice(0, 10) }} ~ {{ detail.end_date?.slice(0, 10) }}</span>
            <span v-if="detail.location"><EnvironmentOutlined /> {{ detail.location }}</span>
          </div>
        </div>
        <a-form layout="vertical" style="margin-top: 16px">
          <a-form-item label="是否需要住宿">
            <a-switch v-model:checked="enrollForm.need_accommodation" checked-children="需要" un-checked-children="不需要" />
          </a-form-item>
          <a-form-item label="备注">
            <a-textarea v-model:value="enrollForm.note" placeholder="如有特殊说明请填写" :rows="3" :maxlength="500" />
          </a-form-item>
        </a-form>
      </a-modal>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  UserOutlined,
  TeamOutlined,
  EnvironmentOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  HistoryOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import {
  getTrainingApiV1TrainingsTrainingIdGet,
  enrollApiV1TrainingsTrainingIdEnrollPost,
  getStudentsApiV1TrainingsTrainingIdStudentsGet,
  getCheckinRecordsApiV1TrainingsTrainingIdCheckinRecordsGet,
  getTrainingCoursesApiV1TrainingsTrainingIdCoursesGet,
} from '@/api/generated/training-management/training-management'
import {
  getNoticesApiV1NoticesGet,
} from '@/api/generated/notice-management/notice-management'
import type { TrainingResponse } from '@/api/generated/model'

import CurrentSessionCard from '@/components/classes/detail/CurrentSessionCard.vue'
import ActivityFeed from '@/components/classes/detail/ActivityFeed.vue'
import NoticeList from '@/components/classes/detail/NoticeList.vue'
import CourseScheduleTab from '@/components/classes/detail/CourseScheduleTab.vue'
import ClassResourcesTab from '@/components/classes/detail/ClassResourcesTab.vue'
import CheckinManager from '@/components/classes/detail/CheckinManager.vue'
import CheckoutManager from '@/components/classes/detail/CheckoutManager.vue'
import StudentCheckinConfirm from '@/components/classes/detail/StudentCheckinConfirm.vue'
import StudentCheckoutConfirm from '@/components/classes/detail/StudentCheckoutConfirm.vue'
import QrScannerModal from '@/components/classes/detail/QrScannerModal.vue'
import StudentGestureCheckin from '@/components/classes/detail/StudentGestureCheckin.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const activeTab = ref('overview')

const detail = ref<TrainingResponse | null>(null)
const students = ref<any[]>([])
const checkinRecords = ref<any[]>([])
const notices = ref<any[]>([])
const courses = ref<any[]>([])
const studentSearch = ref('')

// 弹窗可见状态
const checkinMgrVisible = ref(false)
const checkoutMgrVisible = ref(false)
const studentCheckinVisible = ref(false)
const studentCheckoutVisible = ref(false)
const qrScannerVisible = ref(false)
const qrScannerAction = ref<'checkin' | 'checkout'>('checkin')
const showGestureCheckin = ref(false)
const showGestureCheckout = ref(false)

const enrollModalVisible = ref(false)
const enrollSubmitting = ref(false)
const enrollForm = ref({ note: '', need_accommodation: false })

function openQrScanner(action: 'checkin' | 'checkout') {
  qrScannerAction.value = action
  qrScannerVisible.value = true
}

// ---- computed ----

const statusLabels: Record<string, string> = {
  upcoming: '未开始',
  active: '进行中',
  ended: '已结束',
}

const isEnrolled = computed(() => detail.value?.current_enrollment_status === 'approved')

// 是否是本班教官（班主任、管理员、或当前课次的任课教官）
const isClassInstructor = computed(() => {
  const d = detail.value
  if (!d) return false
  if (d.can_manage_all || d.can_manage_training || d.can_edit_training) return true
  // 当前课次有操作权限，说明是任课教官
  const perms = currentSession.value?.action_permissions
  if (perms && (perms.can_start_checkin || perms.can_start_checkout)) return true
  return false
})

const canEnroll = computed(() => {
  const d = detail.value
  if (!d) return false
  // 已有报名记录（pending/approved/rejected）不显示报名按钮
  if (d.current_enrollment_status) return false
  // 本班教官不需要报名
  if (isClassInstructor.value) return false
  // 后端条件：已发布且未锁定
  if (d.publish_status !== 'published') return false
  if (d.is_locked) return false
  return true
})

const currentSession = computed(() => detail.value?.current_session || null)

const checkinGesturePattern = computed<number[]>(() => {
  try {
    return JSON.parse((currentSession.value as any)?.checkin_gesture_pattern || '[]')
  } catch { return [] }
})

const checkoutGesturePattern = computed<number[]>(() => {
  try {
    return JSON.parse((currentSession.value as any)?.checkout_gesture_pattern || '[]')
  } catch { return [] }
})

const hasActiveCheckin = computed(() => currentSession.value?.status === 'checkin_open')
const hasActiveCheckout = computed(() => currentSession.value?.status === 'checkout_open')

const hasCheckedIn = computed(() => {
  const sess = currentSession.value
  if (!sess) return false
  return checkinRecords.value.some((r) => r.session_key === sess.session_id && r.status !== 'absent')
})

const hasCheckedOut = computed(() => {
  const sess = currentSession.value
  if (!sess) return false
  return checkinRecords.value.some((r) => r.session_key === sess.session_id && r.checkout_status === 'completed')
})

// 是否可查看班级完整内容（课程、考试等）
const hasFullAccess = computed(() => {
  const d = detail.value
  if (!d) return false
  if (isEnrolled.value || isClassInstructor.value) return true
  // 已发布的班级对所有用户开放查看（方便了解后报名）
  if (d.publish_status === 'published') return true
  return false
})

// 是否需要显示报名引导（未加入班级的用户）
const showEnrollHint = computed(() => {
  if (!detail.value) return false
  if (isEnrolled.value || isClassInstructor.value) return false
  return true
})

const canPublishNotice = computed(() => isClassInstructor.value)

const pendingEnrollments = computed(() =>
  students.value.filter((s) => s.status === 'pending'),
)

const isSessionActive = computed(() => {
  const s = currentSession.value?.status
  if (!s) return false
  return ['checkin_open', 'checkin_closed', 'checkout_open'].includes(s)
})

const visibleTabs = computed(() => {
  if (!hasFullAccess.value) {
    return [{ key: 'overview', label: '概览' }]
  }
  const tabs = [
    { key: 'overview', label: '概览' },
    { key: 'schedule', label: '课程' },
    { key: 'resources', label: '班级资源' },
    { key: 'exam', label: '考试' },
  ]
  if (isClassInstructor.value) {
    tabs.push({ key: 'students', label: '学员名单' })
  }
  return tabs
})

const filteredStudents = computed(() => {
  const list = students.value
  const kw = studentSearch.value.trim().toLowerCase()
  if (!kw) return list
  return list.filter((s) => {
    const name = (s.user_nickname || s.user_name || '').toLowerCase()
    return name.includes(kw)
  })
})

// ---- methods ----

function studentDisplayName(s: { user_nickname?: string | null; user_name?: string | null; user_id: number }): string {
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

function enrollStatusLabel(status: string): string {
  const map: Record<string, string> = { approved: '已通过', pending: '待审核', rejected: '未通过' }
  return map[status] || status
}

function canTakeExam(exam: { start_time?: string | null; end_time?: string | null }): boolean {
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

async function handleEnroll() {
  const d = detail.value
  if (!d) return
  enrollSubmitting.value = true
  try {
    await enrollApiV1TrainingsTrainingIdEnrollPost(d.id, {
      note: enrollForm.value.note || undefined,
      need_accommodation: enrollForm.value.need_accommodation,
    })
    message.success(d.enrollment_requires_approval ? '报名申请已提交，等待审核' : '加入成功')
    enrollModalVisible.value = false
    enrollForm.value = { note: '', need_accommodation: false }
    fetchDetail()
    fetchStudents()
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '操作失败')
  } finally {
    enrollSubmitting.value = false
  }
}
function goHistory() { message.info('训历功能即将上线') }
function goExamOverview(examId: number) { router.push(`/exam/overview/${examId}?kind=training`) }

function onCheckinSuccess() {
  fetchDetail()
  fetchCheckinRecords()
}

function onCheckoutSuccess() {
  fetchDetail()
  fetchCheckinRecords()
}

function onCheckinManagerUpdated(nextDetail: TrainingResponse) {
  detail.value = nextDetail
  fetchCheckinRecords()
  fetchStudents()
}

function onCheckoutManagerUpdated(nextDetail: TrainingResponse) {
  detail.value = nextDetail
  fetchCheckinRecords()
}

function applyDetail(nextDetail: TrainingResponse) {
  detail.value = nextDetail
}

const trainingId = computed(() => Number(route.params.id))

async function fetchDetail() {
  const id = route.params.id
  if (!id) return
  loading.value = true
  try {
    detail.value = await getTrainingApiV1TrainingsTrainingIdGet(Number(id))
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '加载班级详情失败')
  } finally {
    loading.value = false
  }
}

async function fetchStudents() {
  if (!trainingId.value) return
  try {
    const res = await getStudentsApiV1TrainingsTrainingIdStudentsGet(trainingId.value, { size: -1 })
    students.value = (res as any)?.items || res || []
  } catch {
    students.value = []
  }
}

async function fetchCheckinRecords() {
  if (!trainingId.value) return
  try {
    const res = await getCheckinRecordsApiV1TrainingsTrainingIdCheckinRecordsGet(trainingId.value)
    checkinRecords.value = (res as any) || []
  } catch {
    checkinRecords.value = []
  }
}

async function fetchNotices() {
  if (!trainingId.value) return
  try {
    const res = await getNoticesApiV1NoticesGet({ training_id: trainingId.value, size: -1 })
    notices.value = (res as any)?.items || res || []
  } catch {
    notices.value = []
  }
}

async function fetchCourses() {
  if (!trainingId.value) return
  try {
    const res = await getTrainingCoursesApiV1TrainingsTrainingIdCoursesGet(trainingId.value)
    courses.value = (res as any) || []
  } catch {
    courses.value = []
  }
}

onMounted(() => {
  fetchDetail()
  fetchCourses()
  fetchNotices()
  fetchCheckinRecords()
})

// Lazy-load students when tab is activated (only instructors have access)
watch(activeTab, (tab) => {
  if (tab === 'students' && students.value.length === 0) {
    fetchStudents()
  }
})
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

.header-desc {
  margin-top: 10px;
  font-size: 13px;
  color: rgba(255,255,255,0.55);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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
  font-size: 16px;
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

.tab-panel { padding: 20px; }

/* ====== 加入引导 ====== */
.join-hint-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 48px 24px;
  gap: 8px;
}

.join-hint-icon {
  font-size: 36px;
  color: var(--v2-primary);
  margin-bottom: 4px;
}

.join-hint-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin: 0;
}

.join-hint-desc {
  font-size: 13px;
  color: var(--v2-text-muted);
  margin: 0 0 8px;
}

/* ====== 报名弹窗 ====== */
.enroll-modal-info {
  padding: 16px;
  background: var(--v2-bg);
  border-radius: var(--v2-radius-sm);
}

.enroll-class-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin: 0 0 8px;
}

.enroll-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--v2-text-muted);
  flex-wrap: wrap;
}

.enroll-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* ====== 概览 ====== */
.overview-section { margin-bottom: 28px; }
.overview-section:last-child { margin-bottom: 0; }

.section-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin-bottom: 12px;
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
