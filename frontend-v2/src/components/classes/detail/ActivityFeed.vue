<template>
  <div class="activity-feed">
    <!-- 报名申请提示（仅班级教官可见） -->
    <div v-if="isClassInstructor && pendingEnrollments?.length" class="activity-checkin-prompt activity-enroll-prompt">
      <span v-if="pendingEnrollments.length === 1">
        {{ pendingEnrollments[0].user_nickname || pendingEnrollments[0].user_name }} 申请加入班级
      </span>
      <span v-else>
        {{ pendingEnrollments[0].user_nickname || pendingEnrollments[0].user_name }} 等 {{ pendingEnrollments.length }} 人申请加入班级
      </span>
    </div>

    <!-- 签到快捷提示 -->
    <div v-if="isStudent && isEnrolled && hasActiveCheckin && !hasCheckedIn" class="activity-checkin-prompt">
      <span>当前课次正在签到中</span>
      <a-button v-if="checkinMode === 'qr'" type="primary" size="small" @click="$emit('studentScanQr', 'checkin')">
        <ScanOutlined /> 扫码签到
      </a-button>
      <a-button v-else type="primary" size="small" @click="$emit('studentCheckin')">
        立即签到
      </a-button>
    </div>
    <!-- 签退快捷提示 -->
    <div v-if="isStudent && isEnrolled && hasActiveCheckout && !hasCheckedOut" class="activity-checkin-prompt activity-checkout-prompt">
      <span>当前课次正在签退中</span>
      <a-button v-if="checkoutMode === 'qr'" type="primary" size="small" @click="$emit('studentScanQr', 'checkout')">
        <ScanOutlined /> 扫码签退
      </a-button>
      <a-button v-else type="primary" size="small" @click="$emit('studentCheckout')">
        立即签退
      </a-button>
    </div>
    <div v-for="(a, idx) in activityList" :key="a.id ?? idx" class="activity-item">
      <span class="activity-dot" :class="'dot-' + a.action_type" />
      <div class="activity-body">
        <span class="activity-content">{{ a.content }}</span>
        <span class="activity-time">{{ formatRelativeTime(a.created_at) }}</span>
      </div>
    </div>
    <div v-if="!activityList.length" class="activity-empty">暂无动态</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ScanOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import { getTrainingActivitiesApiV1TrainingsTrainingIdActivitiesGet } from '@/api/generated/training-management/training-management'
import type { TrainingActivityResponse } from '@/api/generated/model'

interface PendingEnrollment {
  user_id: number
  user_name?: string | null
  user_nickname?: string | null
  status?: string
}

interface Props {
  trainingId: number | string
  hasFullAccess: boolean
  isStudent: boolean
  isEnrolled: boolean
  isClassInstructor?: boolean
  hasActiveCheckin: boolean
  hasActiveCheckout: boolean
  hasCheckedIn: boolean
  hasCheckedOut: boolean
  checkinMode?: string | null
  checkoutMode?: string | null
  pendingEnrollments?: PendingEnrollment[]
}

const props = defineProps<Props>()

defineEmits<{
  (e: 'studentCheckin'): void
  (e: 'studentCheckout'): void
  (e: 'studentScanQr', action: 'checkin' | 'checkout'): void
}>()

const activityList = ref<TrainingActivityResponse[]>([])
let activityWs: WebSocket | null = null

async function fetchActivities() {
  try {
    const data = await getTrainingActivitiesApiV1TrainingsTrainingIdActivitiesGet(
      Number(props.trainingId),
      { limit: 5 },
    )
    activityList.value = data || []
  } catch {
    activityList.value = []
  }
}

function connectActivityWs() {
  const token = localStorage.getItem('token')
  if (!token) return
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = import.meta.env.VITE_API_BASE_URL
    ? new URL(import.meta.env.VITE_API_BASE_URL as string).host
    : location.host
  const url = `${protocol}//${host}/ws/trainings/${props.trainingId}/activities?token=${token}`

  activityWs = new WebSocket(url)
  activityWs.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as TrainingActivityResponse
      activityList.value.unshift(data)
      if (activityList.value.length > 10) activityList.value.pop()
    } catch { /* ignore malformed messages */ }
  }
  activityWs.onclose = () => { activityWs = null }
}

function disconnectActivityWs() {
  if (activityWs) { activityWs.close(); activityWs = null }
}

function formatRelativeTime(time: string | null | undefined): string {
  if (!time) return ''
  const diff = Date.now() - new Date(time).getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return dayjs(time).format('MM/DD HH:mm')
}

onMounted(() => {
  if (props.hasFullAccess) {
    fetchActivities()
    connectActivityWs()
  }
})

onUnmounted(() => {
  disconnectActivityWs()
})
</script>

<style scoped>
.activity-feed {
  display: flex;
  flex-direction: column;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 0;
}

.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
  background: var(--v2-text-muted);
}

.dot-checkin { background: var(--v2-success); }
.dot-checkout { background: var(--v2-primary); }
.dot-session_checkin_start,
.dot-session_checkin_end,
.dot-session_checkout_start,
.dot-session_checkout_end,
.dot-notice { background: var(--v2-warning); }
.dot-enroll { background: #8b5cf6; }

.activity-body {
  flex: 1;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
}

.activity-content {
  font-size: 13px;
  color: var(--v2-text-secondary);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.activity-time {
  font-size: 12px;
  color: var(--v2-text-muted);
  flex-shrink: 0;
  text-align: right;
}

.activity-empty {
  padding: 16px 0;
  text-align: center;
  font-size: 13px;
  color: var(--v2-text-muted);
}

.activity-checkin-prompt {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  margin-bottom: 8px;
  border-radius: var(--v2-radius-sm);
  background: rgba(52, 199, 89, 0.08);
  font-size: 13px;
  color: var(--v2-success);
  font-weight: 500;
}

.activity-checkout-prompt {
  background: rgba(75, 110, 245, 0.08);
  color: var(--v2-primary);
}

.activity-enroll-prompt {
  background: rgba(255, 149, 0, 0.08);
  color: var(--v2-warning);
}

@media (max-width: 768px) {
  .activity-body {
    flex-direction: column;
    gap: 2px;
  }
  .activity-time {
    text-align: left;
  }
}
</style>
