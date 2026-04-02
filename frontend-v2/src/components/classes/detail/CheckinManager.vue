<template>
  <a-modal
    :open="visible"
    title="签到管理"
    :footer="null"
    width="640px"
    :class="{ 'checkin-mgr-modal-mobile': isMobile }"
    :style="isMobile ? { top: 0, maxWidth: '100vw', margin: 0, paddingBottom: 0 } : {}"
    :bodyStyle="isMobile ? { height: 'calc(100vh - 55px)', overflow: 'auto' } : {}"
    @update:open="(val: boolean) => emit('update:visible', val)"
  >
    <!-- 上部：签到配置区 -->
    <div class="checkin-config">
      <div class="config-row">
        <span class="config-label">签到途径</span>
        <a-radio-group
          :value="checkinMode"
          :disabled="isCheckinOngoing"
          @change="(e: any) => { checkinMode = e.target.value }"
        >
          <a-radio value="direct">直接签到</a-radio>
          <a-radio value="gesture">手势签到</a-radio>
        </a-radio-group>
      </div>
      <!-- 手势签到设置 -->
      <div v-if="checkinMode === 'gesture'" class="gesture-setting">
        <div class="gesture-title">设置签到手势</div>
        <div class="gesture-card">
          <GesturePattern theme="light" v-model="gesturePattern" />
          <div class="gesture-clear-row">
            <a-button size="small" type="text" class="gesture-clear-btn" @click="gesturePattern = []">
              <ReloadOutlined /> 清空重绘
            </a-button>
          </div>
        </div>
        <div class="gesture-hint">学生签到时需要绘制相同的手势</div>
      </div>
      <div class="config-row">
        <span class="config-label">签到限时</span>
        <a-select
          :value="checkinDuration"
          style="width: 120px"
          :disabled="isCheckinOngoing"
          @change="(val: number) => { checkinDuration = val }"
        >
          <a-select-option :value="5">5 分钟</a-select-option>
          <a-select-option :value="10">10 分钟</a-select-option>
          <a-select-option :value="15">15 分钟</a-select-option>
          <a-select-option :value="30">30 分钟</a-select-option>
        </a-select>
      </div>
      <div v-if="checkinMode === 'gesture' && gesturePattern.length > 0 && isCheckinOngoing" class="gesture-active-hint">
        <span>手势签到进行中，学生需绘制相同手势完成签到</span>
      </div>
    </div>

    <!-- 中部：签到统计 -->
    <div class="checkin-stats">
      <div class="stat-progress">
        <span>已签到 {{ checkedInList.length }} / {{ totalStudents }} 人</span>
        <a-progress :percent="checkinPercent" size="small" :show-info="false" />
      </div>
      <div v-if="countdownText" class="stat-countdown">
        剩余 {{ countdownText }}
      </div>
    </div>

    <!-- 下部：签到名单 -->
    <a-tabs v-model:activeKey="checkinTab" size="small" style="margin-top: 8px">
      <a-tab-pane key="checked" :tab="`已签到 (${checkedInList.length})`">
        <a-empty v-if="!checkedInList.length" description="暂无签到记录" />
        <div v-else class="checkin-list">
          <div v-for="r in checkedInList" :key="r.user_id" class="checkin-row">
            <a-avatar :size="28" class="checkin-avatar">{{ (r.user_nickname || r.user_name || '').slice(0, 1) }}</a-avatar>
            <div class="checkin-info">
              <span class="checkin-name">{{ r.user_nickname || r.user_name }}</span>
              <span class="checkin-time">{{ r.time || '' }} {{ r.status === 'late' ? '(迟到)' : '' }}</span>
            </div>
            <a-button
              v-if="canManageCheckin"
              size="small"
              danger
              @click="toggleCheckin(r.user_id, 'absent')"
              :loading="checkinToggleLoading === r.user_id"
            >
              标记未签到
            </a-button>
          </div>
        </div>
      </a-tab-pane>
      <a-tab-pane key="unchecked" :tab="`未签到 (${uncheckedList.length})`">
        <a-empty v-if="!uncheckedList.length" description="全部已签到" />
        <div v-else class="checkin-list">
          <div v-for="s in uncheckedList" :key="s.user_id" class="checkin-row">
            <a-avatar :size="28" class="checkin-avatar absent">{{ (s.user_nickname || s.user_name || '').slice(0, 1) }}</a-avatar>
            <div class="checkin-info">
              <span class="checkin-name">{{ s.user_nickname || s.user_name }}</span>
              <span class="checkin-absent-label">未签到</span>
            </div>
            <a-button
              v-if="canManageCheckin"
              size="small"
              type="primary"
              @click="toggleCheckin(s.user_id, 'checkin')"
              :loading="checkinToggleLoading === s.user_id"
            >
              标记已签到
            </a-button>
          </div>
        </div>
      </a-tab-pane>
    </a-tabs>

    <!-- 底部按钮区 -->
    <div class="checkin-mgr-footer">
      <a-button
        v-if="session?.action_permissions?.can_start_checkin"
        type="primary"
        :loading="sessionActionLoading"
        @click="doStartCheckin"
      >
        开始签到
      </a-button>
      <a-button
        v-if="session?.action_permissions?.can_end_checkin"
        danger
        :loading="sessionActionLoading"
        @click="doEndCheckin"
      >
        结束签到
      </a-button>
      <a-button v-if="isCheckinEnded" @click="emit('update:visible', false)">
        关闭
      </a-button>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import { ReloadOutlined } from '@ant-design/icons-vue'
import GesturePattern from './GesturePattern.vue'
import { useAuthStore } from '@/stores/auth'
import {
  getCheckinRecordsApiV1TrainingsTrainingIdCheckinRecordsGet,
  startSessionCheckinApiV1TrainingsTrainingIdSessionsSessionKeyCheckinStartPost,
  endSessionCheckinApiV1TrainingsTrainingIdSessionsSessionKeyCheckinEndPost,
  checkinApiV1TrainingsTrainingIdCheckinPost,
} from '@/api/generated/training-management/training-management'
import type { CheckinResponse, TrainingCheckinQrResponse, TrainingResponse } from '@/api/generated/model'
import type { CurrentSession, StudentItem } from './types'
import { useAttendanceManager } from './useAttendanceManager'
import { getAttendanceQr } from '@/services/attendance'

const props = defineProps<{
  visible: boolean
  trainingId: number | string
  session: CurrentSession | null
  students: StudentItem[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'detail-updated', val: TrainingResponse): void
  (e: 'gesture-pattern-set', pattern: number[]): void
}>()

const authStore = useAuthStore()

const sessionActionLoading = ref(false)
const checkinTab = ref('checked')
const checkinRecords = ref<CheckinResponse[]>([])
const checkinToggleLoading = ref<number | null>(null)
const gesturePattern = ref<number[]>([])
const isMobile = ref(window.innerWidth <= 768)

function handleResize() {
  isMobile.value = window.innerWidth <= 768
}
window.addEventListener('resize', handleResize)
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

const {
  mode: checkinMode,
  duration: checkinDuration,
  qrUrl: checkinQrUrl,
  countdownText,
  syncFromSession,
} = useAttendanceManager({
  action: 'checkin',
  visible: computed(() => props.visible),
  session: computed(() => props.session),
  fetchQrPayload: (sessionId: string, action: 'checkin' | 'checkout'): Promise<TrainingCheckinQrResponse> =>
    getAttendanceQr(
      Number(props.trainingId),
      { session_key: sessionId, action },
    ),
})

const isCheckinOngoing = computed(() => props.session?.status === 'checkin_open')

const isCheckinEnded = computed(() => {
  const s = props.session?.status
  return s === 'checkin_closed' || s === 'checkout_open' || s === 'completed'
})

const canManageCheckin = computed(() => {
  return authStore.isInstructor && props.session?.action_permissions != null
})

const checkedInList = computed(() =>
  checkinRecords.value.filter((r) => r.status === 'on_time' || r.status === 'late'),
)

const uncheckedList = computed(() => {
  const checkedIds = new Set(checkedInList.value.map((r) => r.user_id))
  return props.students
    .filter((s) => !checkedIds.has(s.user_id))
    .map((s) => ({ user_id: s.user_id, user_name: s.user_name, user_nickname: s.user_nickname, status: 'absent', time: '' }))
})

const totalStudents = computed(() => props.students.length || 0)

const checkinPercent = computed(() => {
  if (!totalStudents.value) return 0
  return Math.round((checkedInList.value.length / totalStudents.value) * 100)
})

watch(
  [() => props.visible, () => props.session?.session_id],
  async ([visible, sessionId]) => {
    if (!visible || !sessionId) {
      checkinRecords.value = []
      return
    }
    checkinTab.value = 'checked'
    await fetchCheckinRecords(sessionId)
  },
  { immediate: true },
)

async function fetchCheckinRecords(sessionId = props.session?.session_id) {
  if (!sessionId) return
  try {
    const data = await getCheckinRecordsApiV1TrainingsTrainingIdCheckinRecordsGet(
      Number(props.trainingId),
      { session_key: sessionId },
    )
    checkinRecords.value = data || []
  } catch {
    checkinRecords.value = []
  }
}

async function doStartCheckin() {
  const sess = props.session
  if (!sess) return
  if (checkinMode.value === 'gesture' && gesturePattern.value.length < 3) {
    message.warning('请至少连接3个点来设置签到手势')
    return
  }
  sessionActionLoading.value = true
  try {
    const apiMode = checkinMode.value === 'gesture' ? 'direct' : checkinMode.value
    const params: Record<string, any> = { checkin_mode: apiMode, checkin_duration_minutes: checkinDuration.value }
    if (checkinMode.value === 'gesture') {
      params.checkin_gesture_pattern = JSON.stringify(gesturePattern.value)
    }
    const detail = await startSessionCheckinApiV1TrainingsTrainingIdSessionsSessionKeyCheckinStartPost(
      Number(props.trainingId),
      sess.session_id,
      params,
    )
    if (checkinMode.value === 'gesture') {
      emit('gesture-pattern-set', gesturePattern.value)
    }
    message.success('签到已开始')
    if (detail) emit('detail-updated', detail)
    await syncFromSession((detail?.current_session as CurrentSession | null) ?? sess)
    await fetchCheckinRecords(sess.session_id)
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '操作失败')
  } finally {
    sessionActionLoading.value = false
  }
}

async function doEndCheckin() {
  const sess = props.session
  if (!sess) return
  sessionActionLoading.value = true
  try {
    const detail = await endSessionCheckinApiV1TrainingsTrainingIdSessionsSessionKeyCheckinEndPost(
      Number(props.trainingId),
      sess.session_id,
    )
    message.success('操作成功')
    if (detail) emit('detail-updated', detail)
    await syncFromSession((detail?.current_session as CurrentSession | null) ?? null)
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '操作失败')
  } finally {
    sessionActionLoading.value = false
  }
}

async function toggleCheckin(userId: number, action: 'checkin' | 'absent') {
  const sess = props.session
  if (!sess) return
  checkinToggleLoading.value = userId
  try {
    if (action === 'checkin') {
      await checkinApiV1TrainingsTrainingIdCheckinPost(
        Number(props.trainingId),
        { user_id: userId, session_key: sess.session_id },
      )
    } else {
      await checkinApiV1TrainingsTrainingIdCheckinPost(
        Number(props.trainingId),
        { user_id: userId, session_key: sess.session_id, status: 'absent' },
      )
    }
    await fetchCheckinRecords(sess.session_id)
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '操作失败')
  } finally {
    checkinToggleLoading.value = null
  }
}
</script>

<style scoped>
.checkin-config {
  padding: 16px;
  background: var(--v2-bg);
  border-radius: var(--v2-radius-sm);
  margin-bottom: 16px;
}

.config-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.config-row:last-child { margin-bottom: 0; }

.gesture-setting {
  margin: 12px 0;
}

.gesture-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--v2-text-primary);
  margin-bottom: 10px;
}

.gesture-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.gesture-clear-row {
  margin-top: 12px;
  text-align: center;
}
.gesture-clear-btn {
  color: #999;
  font-size: 13px;
}
.gesture-clear-btn:hover {
  color: #1677ff;
}
.gesture-hint {
  font-size: 12px;
  color: var(--v2-text-muted);
  margin-top: 8px;
}

.gesture-active-hint {
  margin-top: 12px;
  padding: 10px 14px;
  background: var(--v2-bg);
  border-radius: var(--v2-radius-sm);
  font-size: 13px;
  color: var(--v2-text-secondary);
}

.config-label {
  font-size: 14px;
  color: var(--v2-text-secondary);
  min-width: 70px;
  flex-shrink: 0;
}

.qr-display {
  margin-top: 16px;
  padding: 24px;
  background: #fff;
  border: 1px solid var(--v2-border-light);
  border-radius: var(--v2-radius);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.qr-hint {
  font-size: 13px;
  color: var(--v2-text-muted);
}

.checkin-stats {
  padding: 12px 16px;
  background: var(--v2-bg);
  border-radius: var(--v2-radius-sm);
  margin-bottom: 12px;
}

.stat-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--v2-text-primary);
}

.stat-progress span { white-space: nowrap; flex-shrink: 0; }
.stat-progress .ant-progress { flex: 1; }

.stat-countdown {
  margin-top: 8px;
  font-size: 13px;
  color: var(--v2-warning);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.checkin-list {
  display: flex;
  flex-direction: column;
}

.checkin-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 4px;
  border-bottom: 1px solid var(--v2-border-light);
}

.checkin-row:last-child { border-bottom: none; }

.checkin-avatar {
  background: var(--v2-success);
  color: #fff;
  font-size: 12px;
  flex-shrink: 0;
}

.checkin-avatar.absent {
  background: var(--v2-text-muted);
}

.checkin-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.checkin-name {
  font-size: 14px;
  color: var(--v2-text-primary);
}

.checkin-time {
  font-size: 12px;
  color: var(--v2-text-muted);
}

.checkin-absent-label {
  font-size: 12px;
  color: var(--v2-danger);
}

.checkin-mgr-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--v2-border-light);
}

@media (max-width: 768px) {
  .checkin-config {
    padding: 12px;
  }

  .config-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .checkin-list .checkin-row {
    padding: 8px 2px;
    gap: 8px;
  }

  .checkin-mgr-footer {
    flex-direction: column;
  }

  .checkin-mgr-footer .ant-btn {
    min-height: 44px;
    width: 100%;
  }
}
</style>
