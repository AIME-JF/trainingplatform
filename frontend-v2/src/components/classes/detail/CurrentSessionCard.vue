<template>
  <div v-if="session" class="current-session-card" :class="{ 'is-active': isActive }">
    <div class="cs-left">
      <div class="cs-date-col">
        <span class="cs-day">{{ dayjs(session.date).date() }}</span>
        <span class="cs-weekday">{{ weekdays[dayjs(session.date).day()] }}</span>
      </div>
      <div class="cs-body">
        <div class="cs-header">
          <strong class="cs-course">{{ session.course_name }}</strong>
          <a-tag :color="sessionTagColor(session.status)" size="small">
            {{ sessionStatusLabel(session.status) }}
          </a-tag>
        </div>
        <div class="cs-meta">
          <span><ClockCircleOutlined /> {{ session.time_range?.replace('~', ' - ') }}</span>
          <span v-if="session.location"><EnvironmentOutlined /> {{ session.location }}</span>
          <span v-if="session.primary_instructor_name"><UserOutlined /> {{ session.primary_instructor_name }}</span>
        </div>
      </div>
    </div>
    <div class="cs-actions">
      <!-- 教官流程控制按钮 -->
      <template v-if="isInstructor && session.action_permissions">
        <a-button
          v-if="session.action_permissions.can_start_checkin"
          type="primary"
          size="small"
          @click="$emit('openCheckinMgr')"
        >
          开始签到
        </a-button>
        <a-button
          v-if="session.action_permissions.can_start_checkout"
          type="primary"
          size="small"
          @click="$emit('openCheckoutMgr')"
        >
          开始签退
        </a-button>
      </template>
      <!-- 签到管理按钮 -->
      <a-button
        v-if="isInstructor && (hasActiveCheckin || session.status === 'checkin_closed')"
        size="small"
        @click="$emit('openCheckinMgr')"
      >
        签到管理
      </a-button>
      <!-- 签退管理按钮 -->
      <a-button
        v-if="isInstructor && isCheckoutPhase"
        size="small"
        @click="$emit('openCheckoutMgr')"
      >
        签退管理
      </a-button>
      <!-- 学员签到按钮 -->
      <template v-if="isStudent && isEnrolled && hasActiveCheckin">
        <template v-if="hasCheckedIn">
          <span class="cs-checked-label"><CheckCircleOutlined /> 已签到</span>
        </template>
        <template v-else-if="session.checkin_mode === 'qr'">
          <span class="cs-qr-hint">请扫描教官展示的二维码进行签到</span>
        </template>
        <a-button
          v-else
          type="primary"
          size="small"
          @click="$emit('studentCheckin')"
        >
          <CheckCircleOutlined /> 签到
        </a-button>
      </template>
      <!-- 学员签退按钮 -->
      <template v-if="isStudent && isEnrolled && hasActiveCheckout">
        <template v-if="hasCheckedOut">
          <span class="cs-checked-label"><CheckCircleOutlined /> 已签退</span>
        </template>
        <template v-else-if="session.checkout_mode === 'qr'">
          <span class="cs-qr-hint">请扫描教官展示的二维码进行签退</span>
        </template>
        <a-button
          v-else
          type="primary"
          size="small"
          @click="$emit('studentCheckout')"
        >
          <CheckCircleOutlined /> 签退
        </a-button>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  ClockCircleOutlined,
  EnvironmentOutlined,
  UserOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import type { CurrentSession } from './types'

interface Props {
  session: CurrentSession | null
  isInstructor: boolean
  isStudent: boolean
  isEnrolled: boolean
  hasCheckedIn: boolean
  hasCheckedOut: boolean
}

const props = defineProps<Props>()

defineEmits<{
  (e: 'openCheckinMgr'): void
  (e: 'openCheckoutMgr'): void
  (e: 'studentCheckin'): void
  (e: 'studentCheckout'): void
  (e: 'sessionAction', action: string): void
}>()

const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

const hasActiveCheckin = computed(() => props.session?.status === 'checkin_open')
const hasActiveCheckout = computed(() => props.session?.status === 'checkout_open')
const isCheckoutPhase = computed(() => props.session?.status === 'checkout_open')

const isActive = computed(() => {
  const s = props.session?.status
  if (!s) return false
  return ['checkin_open', 'checkin_closed', 'checkout_open'].includes(s)
})

function sessionTagColor(status: string): string {
  const map: Record<string, string> = {
    checkin_open: 'processing',
    checkin_closed: 'processing',
    checkout_open: 'warning',
    completed: 'success',
    skipped: 'default',
    missed: 'error',
  }
  return map[status] || 'default'
}

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
</script>

<style scoped>
.current-session-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  border-radius: var(--v2-radius);
  background: var(--v2-bg);
  border: 1px solid var(--v2-border-light);
  flex-wrap: wrap;
}

.current-session-card.is-active {
  background: var(--v2-primary-light);
  border-color: rgba(75, 110, 245, 0.2);
}

.cs-left {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
  min-width: 0;
}

.cs-date-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 40px;
}

.cs-day {
  font-size: 22px;
  font-weight: 700;
  color: var(--v2-text-primary);
  line-height: 1;
}

.cs-weekday {
  font-size: 11px;
  color: var(--v2-text-muted);
  margin-top: 2px;
}

.cs-body { flex: 1; min-width: 0; }

.cs-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.cs-course {
  font-size: 15px;
  color: var(--v2-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cs-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--v2-text-muted);
  flex-wrap: wrap;
}

.cs-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.cs-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.cs-qr-hint {
  font-size: 12px;
  color: var(--v2-warning);
  display: flex;
  align-items: center;
}

.cs-checked-label {
  font-size: 13px;
  color: var(--v2-success);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
